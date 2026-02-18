#!/usr/bin/env python3
"""
Simplified theHarvester Integration Module
Clean, minimal, production-ready implementation
"""

import subprocess
import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import your result dataclass
from core.job_result import HarvestJobResult

# Configure logging
logger = logging.getLogger(__name__)

# Regex patterns for parsing
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')


def build_theharvester_command(
    domain: str,
    sources: List[str],
    limit: int,
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Build minimal theHarvester command.
    
    Args:
        domain: Target domain (e.g. 'example.com')
        sources: List of sources (e.g. ['duckduckgo', 'crtsh'])
        limit: Result limit per source
        config: Optional config dict (can specify binary path)
    
    Returns:
        Command as list of strings
    """
    cfg = config or {}
    binary = cfg.get("theharvester", {}).get("path", "theHarvester")
    
    # Minimal command - just what we need
    cmd = [
        binary,
        "-d", domain,
        "-b", ",".join(sources),
        "-l", str(limit),
    ]
    
    return cmd


def parse_theharvester_output(stdout: str) -> Dict[str, Any]:
    """
    Parse theHarvester stdout to extract emails and hosts.
    
    theHarvester prints results like:
    [*] Emails found: 3
    ------------------
    email1@example.com
    email2@example.com
    
    [*] Hosts found: 5
    ------------------
    www.example.com:1.2.3.4
    mail.example.com
    
    Args:
        stdout: Raw stdout from theHarvester
    
    Returns:
        Dict with emails, hosts, and ips lists
    """
    # Extract emails with regex (most reliable)
    emails = set(re.findall(EMAIL_REGEX, stdout))
    
    # Extract IPs with regex
    ips = set(re.findall(IP_REGEX, stdout))
    
    # Parse hosts from stdout sections
    hosts = []
    lines = stdout.splitlines()
    in_hosts_section = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Detect start of hosts section
        if "hosts found" in line_stripped.lower() or "interesting" in line_stripped.lower():
            in_hosts_section = True
            continue
        
        # Detect end of hosts section (next section starts)
        if in_hosts_section and line_stripped.startswith("[*]"):
            in_hosts_section = False
            continue
        
        # Parse host lines
        if in_hosts_section and line_stripped:
            # Skip separator lines and headers
            if line_stripped.startswith("-") or "hostname" in line_stripped.lower():
                continue
            
            # Extract hostname (before : or first word)
            host = line_stripped.split(":")[0].strip()
            
            # Filter out noise
            if host and len(host) > 3 and "." in host:
                hosts.append(host)
    
    return {
        "emails": sorted(list(emails)),
        "hosts": sorted(list(set(hosts))),
        "ips": sorted(list(ips))
    }


def run_harvest_job(
    domain: str,
    sources: List[str],
    limit: int,
    output_base: Path,
    export_windows: bool = False,
    runner=subprocess.run,
    config: Optional[Dict[str, Any]] = None
) -> HarvestJobResult:
    """
    Execute theHarvester for a single domain.
    
    Args:
        domain: Target domain
        sources: List of data sources
        limit: Results per source
        output_base: Base output directory
        export_windows: Unused (for backwards compatibility)
        runner: subprocess.run function (for testing)
        config: Optional configuration dict
    
    Returns:
        HarvestJobResult with status, data, and errors
    """
    started = datetime.now()
    
    # Create safe filename
    domain_slug = domain.replace(".", "_").replace("/", "_")
    timestamp = started.strftime('%Y%m%d_%H%M%S')
    filename = f"{domain_slug}_{timestamp}"
    
    # Setup output directories
    output_base.mkdir(parents=True, exist_ok=True)
    raw_dir = output_base / "raw_leads"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Build command
    cmd = build_theharvester_command(domain, sources, limit, config)
    
    # Get timeout from config or use default (5 minutes)
    timeout_val = (config or {}).get("theharvester", {}).get("timeout", 300)
    
    # Log the command we're about to run
    logger.info(f"Running theHarvester: {' '.join(cmd)}")
    logger.info(f"Domain: {domain}, Sources: {sources}, Limit: {limit}")
    
    try:
        # Execute theHarvester
        proc = runner(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_val,
            env=os.environ.copy()
        )
        
    except FileNotFoundError:
        error_msg = f"theHarvester binary not found. Is it installed? Tried: {cmd[0]}"
        logger.error(error_msg)
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=started,
            finished_at=datetime.now(),
            status="error",
            raw_output_path=None,
            error_message=error_msg,
            parsed_data=None,
            stdout=None,
            stderr=None,
        )
        
    except subprocess.TimeoutExpired:
        error_msg = f"theHarvester timed out after {timeout_val}s"
        logger.error(error_msg)
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=started,
            finished_at=datetime.now(),
            status="error",
            raw_output_path=None,
            error_message=error_msg,
            parsed_data=None,
            stdout=None,
            stderr=None,
        )
        
    except Exception as exc:
        error_msg = f"Unexpected error: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=started,
            finished_at=datetime.now(),
            status="error",
            raw_output_path=None,
            error_message=error_msg,
            parsed_data=None,
            stdout=None,
            stderr=None,
        )
    
    # Extract stdout and stderr
    stdout_text = proc.stdout or ""
    stderr_text = proc.stderr or ""
    
    # Log output summary
    logger.info(f"theHarvester completed with return code: {proc.returncode}")
    logger.debug(f"Stdout length: {len(stdout_text)} chars")
    logger.debug(f"Stderr length: {len(stderr_text)} chars")
    
    if stdout_text:
        logger.debug(f"First 500 chars of stdout: {stdout_text[:500]}")
    if stderr_text:
        logger.debug(f"Stderr: {stderr_text[:500]}")
    
    # Check for errors
    if proc.returncode != 0:
        error_msg = stderr_text or "theHarvester returned non-zero exit code"
        logger.error(f"theHarvester failed: {error_msg}")
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=started,
            finished_at=datetime.now(),
            status="error",
            raw_output_path=None,
            error_message=error_msg,
            parsed_data=None,
            stdout=stdout_text,
            stderr=stderr_text,
        )
    
    # Parse the output
    try:
        parsed = parse_theharvester_output(stdout_text)
        logger.info(f"Parsed {len(parsed['emails'])} emails, {len(parsed['hosts'])} hosts")
    except Exception as parse_err:
        error_msg = f"Failed to parse theHarvester output: {str(parse_err)}"
        logger.error(error_msg, exc_info=True)
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=started,
            finished_at=datetime.now(),
            status="error",
            raw_output_path=None,
            error_message=error_msg,
            parsed_data=None,
            stdout=stdout_text,
            stderr=stderr_text,
        )
    
    # Save raw output
    raw_path = raw_dir / f"{filename}.txt"
    try:
        raw_path.write_text(stdout_text)
        logger.info(f"Saved raw output to: {raw_path}")
    except Exception as write_err:
        logger.warning(f"Failed to save raw output: {write_err}")
    
    # Return success result
    return HarvestJobResult(
        domain=domain,
        sources=sources,
        limit=limit,
        started_at=started,
        finished_at=datetime.now(),
        status="success",
        raw_output_path=str(raw_path),
        error_message=None,
        parsed_data=parsed,
        stdout=stdout_text,
        stderr=stderr_text,
    )


def main():
    """CLI entry point for testing"""
    import argparse
    
    # Setup logging for CLI
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(
        description="theHarvester wrapper for lead generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan
  python wsl_harvester.py -d example.com
  
  # Custom sources and limit
  python wsl_harvester.py -d example.com -s duckduckgo,crtsh -l 100
  
  # Custom output directory
  python wsl_harvester.py -d example.com -o /tmp/results
        """
    )
    
    parser.add_argument(
        "-d", "--domain",
        required=True,
        help="Target domain to scan"
    )
    parser.add_argument(
        "-s", "--sources",
        default="duckduckgo,crtsh,virustotal",
        help="Comma-separated list of sources"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=50,
        help="Result limit per source"
    )
    parser.add_argument(
        "-o", "--output",
        default="harvester_results",
        help="Output directory"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse sources
    sources = [s.strip() for s in args.sources.split(",")]
    output_base = Path(args.output)
    
    print(f"\n{'='*60}")
    print(f"theHarvester Lead Generation")
    print(f"{'='*60}")
    print(f"Domain: {args.domain}")
    print(f"Sources: {', '.join(sources)}")
    print(f"Limit: {args.limit}")
    print(f"Output: {output_base}")
    print(f"{'='*60}\n")
    
    # Run harvest job
    result = run_harvest_job(
        domain=args.domain,
        sources=sources,
        limit=args.limit,
        output_base=output_base
    )
    
    # Display results
    print(f"\n{'='*60}")
    print(f"Results")
    print(f"{'='*60}")
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
        
        print(f"\nRaw output saved to: {result.raw_output_path}")
    else:
        print(f"\nError: {result.error_message}")
        if result.stderr:
            print(f"\nStderr:\n{result.stderr[:500]}")
    
    print(f"{'='*60}\n")
    
    # Exit with appropriate code
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    exit(main())