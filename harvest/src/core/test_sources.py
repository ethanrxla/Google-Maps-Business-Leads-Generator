#!/usr/bin/env python3
"""
Test each theHarvester source individually to find which ones work
"""

import subprocess
import sys

def test_source(domain, source, limit=10):
    """Test a single source"""
    print(f"\n{'='*70}")
    print(f"Testing source: {source}")
    print(f"{'='*70}")
    
    cmd = ['theHarvester', '-d', domain, '-b', source, '-l', str(limit)]
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)} chars")
        print(f"Stderr length: {len(result.stderr)} chars")
        
        if result.returncode == 0:
            print(f"✅ SUCCESS - {source} works!")
            
            # Count results
            emails = result.stdout.count('@')
            print(f"   Found ~{emails} results with @ symbols")
            
            # Show sample output
            lines = [l for l in result.stdout.split('\n') if '@' in l or 'found' in l.lower()]
            if lines:
                print("\n   Sample output:")
                for line in lines[:5]:
                    print(f"   {line.strip()}")
            
            return True
        else:
            print(f"❌ FAILED - {source} returned error")
            
            # Show error details
            if result.stderr:
                print(f"\n   Stderr:\n{result.stderr[:500]}")
            
            # Check stdout for error messages
            error_lines = [l for l in result.stdout.split('\n') 
                          if 'error' in l.lower() or 'exception' in l.lower() 
                          or 'failed' in l.lower() or 'invalid' in l.lower()]
            if error_lines:
                print(f"\n   Error messages in stdout:")
                for line in error_lines[:5]:
                    print(f"   {line.strip()}")
            
            # Show last few lines of stdout (often contains error)
            last_lines = [l.strip() for l in result.stdout.split('\n')[-10:] if l.strip()]
            if last_lines:
                print(f"\n   Last lines of output:")
                for line in last_lines:
                    print(f"   {line}")
            
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT - {source} timed out after 60s")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION - {source} raised exception: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_sources.py <domain>")
        print("Example: python test_sources.py fau.edu")
        sys.exit(1)
    
    domain = sys.argv[1]
    
    # All available sources
    sources = [
        'duckduckgo',
        'crtsh',
        'github',
        'virustotal',
        'netlas',
        'bing',
        'yahoo',
        'baidu',
        'google',
        'linkedin',
        'twitter',
        'censys',
        'dnsdumpster',
        'hackertarget',
        'hunter',
        'securitytrails',
        'shodan',
        'threatcrowd',
        'urlscan',
    ]
    
    print(f"\n{'='*70}")
    print(f"Testing theHarvester sources for domain: {domain}")
    print(f"{'='*70}")
    
    results = {}
    for source in sources:
        results[source] = test_source(domain, source)
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    working = [s for s, r in results.items() if r]
    failing = [s for s, r in results.items() if not r]
    
    print(f"\n✅ Working sources ({len(working)}):")
    for source in working:
        print(f"   - {source}")
    
    print(f"\n❌ Failing sources ({len(failing)}):")
    for source in failing:
        print(f"   - {source}")
    
    print(f"\n{'='*70}")
    print("RECOMMENDED SOURCES:")
    print(f"{'='*70}")
    if working:
        recommended = ','.join(working[:5])  # Top 5 working sources
        print(f"\nUse these in your command:")
        print(f"  -s \"{recommended}\"")
        print(f"\nFull command:")
        print(f"  python wsl_harvester.py -d {domain} -s \"{recommended}\" -l 50")
    else:
        print("No working sources found! Check your theHarvester installation.")
    
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()