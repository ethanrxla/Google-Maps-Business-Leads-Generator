#!/usr/bin/env python3
"""
Main entry point for WSL theHarvester Automation Module
"""

import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.wsl_harvester import WSLHarvesterAutomator
from core.batch_processor import WSLBatchProcessor
from utils.helpers import display_banner, check_dependencies
from utils.wsl_integration import WSLEnvironment

def main():
    """Main CLI interface"""
    display_banner()
    
    parser = argparse.ArgumentParser(
        description="WSL theHarvester Automation - Business Intelligence Gathering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single domain scan
  python main.py -d example.com
  
  # Comprehensive scan with custom sources
  python main.py -d example.com -s "google,bing,linkedin,github" -l 1000
  
  # Batch processing from file
  python main.py -f data/inputs/domains/targets.txt
  
  # Use predefined scan profile
  python main.py -d example.com --profile comprehensive
  
  # Web dashboard mode
  python main.py --dashboard
        """
    )
    
    # Input options
    input_group = parser.add_argument_group('Input Options')
    input_group.add_argument("-d", "--domain", help="Single domain to investigate")
    input_group.add_argument("-f", "--file", help="File containing list of domains")
    input_group.add_argument("--profile", choices=["quick", "standard", "comprehensive"],
                           default="standard", help="Scan profile to use")
    
    # Scan options
    scan_group = parser.add_argument_group('Scan Options')
    scan_group.add_argument("-s", "--sources", 
                           help="Data sources (comma-separated, overrides profile)")
    scan_group.add_argument("-l", "--limit", type=int, 
                           help="Limit results per source (overrides profile)")
    scan_group.add_argument("--dns-bruteforce", action="store_true",
                           help="Enable DNS bruteforcing")
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument("-o", "--output", help="Custom output directory")
    output_group.add_argument("--no-windows-export", action="store_true",
                            help="Disable Windows export")
    output_group.add_argument("--formats", nargs="+", 
                            choices=["json", "csv", "md", "html", "all"],
                            help="Output formats")
    
    # Mode options
    mode_group = parser.add_argument_group('Mode Options')
    mode_group.add_argument("--dashboard", action="store_true",
                          help="Start web dashboard")
    mode_group.add_argument("--batch", action="store_true",
                          help="Force batch processing mode")
    mode_group.add_argument("--monitor", action="store_true",
                          help="Start resource monitor")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.domain, args.file, args.dashboard, args.monitor]):
        parser.error("No action specified. Use -d, -f, --dashboard, or --monitor")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Initialize WSL environment
    wsl_env = WSLEnvironment()
    print(f"[*] WSL Environment: {wsl_env.wsl_version}")
    
    try:
        if args.dashboard:
            start_dashboard()
        elif args.monitor:
            start_monitor()
        elif args.file or args.batch:
            process_batch(args, wsl_env)
        else:
            process_single(args, wsl_env)
            
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Fatal error: {e}")
        sys.exit(1)

def process_single(args, wsl_env):
    """Process single domain"""
    automator = WSLHarvesterAutomator(args.output)
    
    # Configure scan based on profile or arguments
    config = automator.load_scan_profile(args.profile)
    
    # Override with CLI arguments if provided
    if args.sources:
        config['sources'] = args.sources.split(',')
    if args.limit:
        config['limit'] = args.limit
    if args.dns_bruteforce:
        config['dns_bruteforce'] = True
    
    results = automator.run_harvester(
        domain=args.domain,
        sources=config['sources'],
        limit=config['limit'],
        dns_bruteforce=config.get('dns_bruteforce', False)
    )
    
    print(f"\n[+] Scan completed for {args.domain}")
    print(f"    Emails: {len(results.get('emails', []))}")
    print(f"    Hosts: {len(results.get('hosts', []))}")
    print(f"    Reports: {automator.output_dir}/reports/")

def process_batch(args, wsl_env):
    """Process multiple domains"""
    domains_file = args.file
    
    if not domains_file or not os.path.exists(domains_file):
        print("[!] Domains file not found")
        sys.exit(1)
    
    processor = WSLBatchProcessor(max_threads=2)
    processor.process_domains_file(domains_file, args.output)

def start_dashboard():
    """Start web dashboard"""
    from web.dashboard.app import create_app
    app = create_app()
    print("[*] Starting web dashboard on http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)

def start_monitor():
    """Start resource monitor"""
    from scripts.monitoring.resource_monitor import ResourceMonitor
    monitor = ResourceMonitor()
    monitor.start()

if __name__ == "__main__":
    main()