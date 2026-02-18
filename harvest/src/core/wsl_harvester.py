#!/usr/bin/env python3
"""
Simplified theHarvester wrapper used by /harvest-domain.
- Minimal command
- Regex parsing of stdout only
- Structured errors (never raises)
- STANDALONE: Includes HarvestJobResult inline to avoid import issues
"""

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IP_REGEX = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")


# Inline dataclass to avoid import issues
@dataclass
class HarvestJobResult:
    """Result of a harvest job"""
    domain: str
    sources: List[str]
    limit: int
    started_at: datetime
    finished_at: datetime
    status: str  # "success" or "error"
    raw_output_path: Optional[str]
    error_message: Optional[str]
    parsed_data: Optional[Dict[str, Any]]
    stdout: Optional[str]
    stderr: Optional[str]


def build_theharvester_command(
    domain: str, sources: List[str], limit: int, config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Build minimal theHarvester command"""
    cfg = config or {}
    binary = cfg.get("theharvester", {}).get("path") or "theHarvester"
    # base file path (no extension) for theHarvester outputs
    output_base_path = cfg.get("theharvester", {}).get("output_base_path")
    base_path = output_base_path or cfg.get("base_path")  # optional override from config
    # If a caller wants to supply an explicit -f target, they can put it into cfg["base_path"]
    cmd = [binary, "-d", domain, "-b", ",".join(sources), "-l", str(limit)]
    if base_path:
        cmd.extend(["-f", str(base_path)])
    return cmd


def parse_theharvester_output(stdout: str) -> Dict[str, Any]:
    """Parse emails and hosts from theHarvester stdout"""
    emails = set(re.findall(EMAIL_REGEX, stdout))
    ips = set(re.findall(IP_REGEX, stdout))

    hosts: List[str] = []
    in_hosts = False
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        if "hosts found" in lower or "interesting" in lower:
            in_hosts = True
            continue
        if in_hosts and line.startswith("[*]"):
            in_hosts = False
            continue
        if in_hosts:
            if line.startswith("-") or "hostname" in lower:
                continue
            host = line.split(":")[0].strip()
            if host and "." in host and len(host) > 3:
                hosts.append(host)

    return {
        "emails": sorted(emails),
        "hosts": sorted(set(hosts)),
        "ips": sorted(ips)
    }


def run_harvest_job(
    domain: str,
    sources: List[str],
    limit: int,
    output_base: Path,
    export_windows: bool = False,
    runner=subprocess.run,
    config: Optional[Dict[str, Any]] = None,
) -> HarvestJobResult:
    """Execute theHarvester and return structured result"""
    started = datetime.now()
    domain_slug = domain.replace(".", "_").replace("/", "_")
    filename = f"{domain_slug}_{started.strftime('%Y%m%d_%H%M%S')}"
    output_base.mkdir(parents=True, exist_ok=True)
    raw_dir = output_base / "raw_leads"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Build the -f base path inside raw_dir so theHarvester emits JSON there
    cfg_with_base = dict(config or {})
    cfg_with_base.setdefault("theharvester", {})
    cfg_with_base["theharvester"]["output_base_path"] = str(raw_dir / filename)

    cmd = build_theharvester_command(domain, sources, limit, cfg_with_base)
    timeout_val = (config or {}).get("theharvester", {}).get("timeout", 300)
    
    logger.info("harvest.command %s", cmd)
    logger.info("harvest.domain=%s sources=%s limit=%s", domain, sources, limit)
    
    try:
        proc = runner(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_val,
            env=os.environ.copy(),
        )
    except FileNotFoundError:
        msg = f"theHarvester binary not found. Tried: {cmd[0]}"
        logger.error(msg)
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=started,
            finished_at=datetime.now(),
            status="error",
            raw_output_path=None,
            error_message=msg,
            parsed_data=None,
            stdout=None,
            stderr=None,
        )
    except subprocess.TimeoutExpired:
        msg = f"theHarvester timed out after {timeout_val}s"
        logger.error(msg)
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=started,
            finished_at=datetime.now(),
            status="error",
            raw_output_path=None,
            error_message=msg,
            parsed_data=None,
            stdout=None,
            stderr=None,
        )
    except Exception as exc:
        msg = f"Unexpected error: {exc}"
        logger.error(msg, exc_info=True)
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=started,
            finished_at=datetime.now(),
            status="error",
            raw_output_path=None,
            error_message=msg,
            parsed_data=None,
            stdout=None,
            stderr=None,
        )

    stdout_text = proc.stdout or ""
    stderr_text = proc.stderr or ""
    
    logger.info("harvest.returncode=%s stdout_len=%s stderr_len=%s", 
                proc.returncode, len(stdout_text), len(stderr_text))
    logger.debug("harvest.stdout: %s", stdout_text[:500])
    logger.debug("harvest.stderr: %s", stderr_text[:500])

    if proc.returncode != 0:
        msg = stderr_text or "theHarvester returned non-zero exit code"
        logger.error("theHarvester failed (code=%s): %s", proc.returncode, msg)
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=started,
            finished_at=datetime.now(),
            status="error",
            raw_output_path=None,
            error_message=msg,
            parsed_data=None,
            stdout=stdout_text,
            stderr=stderr_text,
        )

    # Prefer JSON output if present
    parsed = {"emails": [], "hosts": [], "ips": []}
    json_path = raw_dir / f"{filename}.json"
    if json_path.exists():
        try:
            import json
            data = json.loads(json_path.read_text())
            emails = []
            hosts = []
            for item in data.get("emails", []) or []:
                val = item.get("value") or item.get("email")
                if val:
                    emails.append(val)
            for item in data.get("hosts", []) or []:
                host = item.get("hostname") or item.get("host") or item
                if host:
                    hosts.append(str(host).split(":")[0])
            parsed = {"emails": sorted(set(emails)), "hosts": sorted(set(hosts)), "ips": []}
            logger.info("harvest.parsed (json) emails=%s hosts=%s", len(parsed["emails"]), len(parsed["hosts"]))
        except Exception as exc:
            logger.warning("Failed to parse JSON output, falling back to stdout: %s", exc)
            parsed = parse_theharvester_output(stdout_text)
    else:
        try:
            parsed = parse_theharvester_output(stdout_text)
            logger.info("harvest.parsed (stdout) emails=%s hosts=%s", len(parsed["emails"]), len(parsed["hosts"]))
        except Exception as exc:
            msg = f"Failed to parse theHarvester output: {exc}"
            logger.error(msg, exc_info=True)
            return HarvestJobResult(
                domain=domain,
                sources=sources,
                limit=limit,
                started_at=started,
                finished_at=datetime.now(),
                status="error",
                raw_output_path=None,
                error_message=msg,
                parsed_data=None,
                stdout=stdout_text,
                stderr=stderr_text,
            )

    raw_path = json_path if json_path.exists() else raw_dir / f"{filename}.txt"
    if not json_path.exists():
        try:
            raw_path.write_text(stdout_text)
        except Exception:
            raw_path = None

    return HarvestJobResult(
        domain=domain,
        sources=sources,
        limit=limit,
        started_at=started,
        finished_at=datetime.now(),
        status="success",
        raw_output_path=str(raw_path) if raw_path else None,
        error_message=None,
        parsed_data=parsed,
        stdout=stdout_text,
        stderr=stderr_text,
    )


def main():
    """CLI entry point"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    parser = argparse.ArgumentParser(description="Run theHarvester scan")
    parser.add_argument("-d", "--domain", required=True, help="Target domain")
    parser.add_argument("-s", "--sources", default="duckduckgo,crtsh,virustotal,netlas,yahoo,baidu,linkedin,censys,dnsdumpster,hackertarget,hunter,shodan,threatcrowd,urlscan", help="Comma-separated sources")
    parser.add_argument("-l", "--limit", type=int, default=50, help="Limit per source")
    parser.add_argument("-o", "--output", default="harvester_results", help="Output directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    output_base = Path(args.output)
    
    print(f"\n{'='*70}")
    print(f"theHarvester Lead Generation")
    print(f"{'='*70}")
    print(f"Domain: {args.domain}")
    print(f"Sources: {', '.join(sources)}")
    print(f"Limit: {args.limit}")
    print(f"Output: {output_base}")
    print(f"{'='*70}\n")
    
    result = run_harvest_job(args.domain, sources, args.limit, output_base)
    
    print(f"\n{'='*70}")
    print(f"Results")
    print(f"{'='*70}")
    print(f"Status: {result.status}")
    print(f"Duration: {(result.finished_at - result.started_at).total_seconds():.1f}s")
    
    if result.status == "success":
        print(f"\nEmails found: {len(result.parsed_data.get('emails', []))}")
        for email in result.parsed_data.get('emails', [])[:10]:
            print(f"  - {email}")
        if len(result.parsed_data.get('emails', [])) > 10:
            print(f"  ... and {len(result.parsed_data.get('emails', [])) - 10} more")
        
        print(f"\nHosts found: {len(result.parsed_data.get('hosts', []))}")
        for host in result.parsed_data.get('hosts', [])[:10]:
            print(f"  - {host}")
        if len(result.parsed_data.get('hosts', [])) > 10:
            print(f"  ... and {len(result.parsed_data.get('hosts', [])) - 10} more")
        
        if result.raw_output_path:
            print(f"\nRaw output: {result.raw_output_path}")
    else:
        print(f"\nError: {result.error_message}")
        if result.stderr:
            print(f"\nStderr:\n{result.stderr[:500]}")
    
    print(f"{'='*70}\n")
    
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
