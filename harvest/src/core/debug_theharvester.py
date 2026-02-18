#!/usr/bin/env python3
"""
Diagnostic script to test theHarvester integration
Run this to identify exactly where the problem is
"""

import subprocess
import sys
import os
from pathlib import Path

def print_section(title):
    """Print a nice section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_environment():
    """Check system environment"""
    print_section("1. ENVIRONMENT CHECK")
    
    # Python version
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # OS info
    try:
        with open('/proc/version', 'r') as f:
            version = f.read().strip()
            print(f"OS: {version[:100]}...")
            if 'microsoft' in version.lower() or 'wsl' in version.lower():
                print("✅ Running in WSL")
            else:
                print("⚠️  Not running in WSL")
    except:
        print("OS: Cannot read /proc/version (not Linux?)")
    
    # Current directory
    print(f"Current directory: {os.getcwd()}")
    print(f"User: {os.environ.get('USER', 'unknown')}")


def check_theharvester():
    """Check if theHarvester is installed"""
    print_section("2. THEHARVESTER INSTALLATION CHECK")
    
    # Check if binary exists
    try:
        result = subprocess.run(
            ['which', 'theHarvester'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            print(f"✅ theHarvester found at: {path}")
        else:
            print("❌ theHarvester not found in PATH")
            return False
    except Exception as e:
        print(f"❌ Error checking for theHarvester: {e}")
        return False
    
    # Check version
    try:
        result = subprocess.run(
            ['theHarvester', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version info from help text
            help_text = result.stdout
            if 'theHarvester' in help_text:
                print("✅ theHarvester is executable")
                print(f"Help text length: {len(help_text)} chars")
            else:
                print("⚠️  theHarvester runs but help text looks unusual")
        else:
            print(f"⚠️  theHarvester --help returned code {result.returncode}")
    except Exception as e:
        print(f"❌ Error running theHarvester --help: {e}")
        return False
    
    return True


def test_manual_command():
    """Test theHarvester with a simple command"""
    print_section("3. MANUAL COMMAND TEST")
    
    domain = "example.com"
    sources = "duckduckgo"
    limit = 10
    
    cmd = [
        'theHarvester',
        '-d', domain,
        '-b', sources,
        '-l', str(limit)
    ]
    
    print(f"Testing command: {' '.join(cmd)}")
    print("This may take 30-60 seconds...\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)} chars")
        print(f"Stderr length: {len(result.stderr)} chars")
        
        if result.returncode == 0:
            print("✅ Command executed successfully")
            
            # Show first part of output
            if result.stdout:
                print("\nFirst 500 chars of output:")
                print("-" * 70)
                print(result.stdout[:500])
                print("-" * 70)
                
                # Check for results
                if '@' in result.stdout:
                    print("✅ Output contains emails (@)")
                else:
                    print("⚠️  No emails found in output")
                
                if 'found' in result.stdout.lower():
                    print("✅ Output contains 'found' (likely results)")
                else:
                    print("⚠️  Output doesn't contain 'found'")
            else:
                print("⚠️  Stdout is empty")
            
            if result.stderr:
                print("\nStderr output:")
                print("-" * 70)
                print(result.stderr[:500])
                print("-" * 70)
        else:
            print(f"❌ Command failed with code {result.returncode}")
            print("\nStderr:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Command timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False
    
    return True


def test_output_directory():
    """Test if we can write to output directory"""
    print_section("4. OUTPUT DIRECTORY TEST")
    
    test_dir = Path("harvester_results/raw_leads")
    
    try:
        test_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {test_dir}")
        
        # Test write
        test_file = test_dir / "test.txt"
        test_file.write_text("test")
        print(f"✅ Can write to directory")
        
        # Test read
        content = test_file.read_text()
        print(f"✅ Can read from directory")
        
        # Cleanup
        test_file.unlink()
        print(f"✅ Can delete from directory")
        
    except Exception as e:
        print(f"❌ Error with output directory: {e}")
        return False
    
    return True


def test_simplified_module():
    """Test the simplified harvester module"""
    print_section("5. SIMPLIFIED MODULE TEST")
    
    try:
        # Try to import
        import wsl_harvester
        print("✅ wsl_harvester module imported")
        
        # Check for required functions
        if hasattr(wsl_harvester, 'run_harvest_job'):
            print("✅ run_harvest_job function exists")
        else:
            print("❌ run_harvest_job function not found")
            return False
        
        if hasattr(wsl_harvester, 'build_theharvester_command'):
            print("✅ build_theharvester_command function exists")
        else:
            print("❌ build_theharvester_command function not found")
            return False
        
        if hasattr(wsl_harvester, 'parse_theharvester_output'):
            print("✅ parse_theharvester_output function exists")
        else:
            print("❌ parse_theharvester_output function not found")
            return False
        
        # Test command builder
        cmd = wsl_harvester.build_theharvester_command(
            domain="test.com",
            sources=["duckduckgo"],
            limit=10
        )
        print(f"✅ Command builder works: {cmd}")
        
        # Test parser with sample output
        sample_output = """
[*] Emails found: 2
------------------
test1@example.com
test2@example.com

[*] Hosts found: 1
------------------
www.example.com
        """
        
        parsed = wsl_harvester.parse_theharvester_output(sample_output)
        print(f"✅ Parser works: {parsed}")
        
        if len(parsed.get('emails', [])) == 2:
            print("✅ Parser extracted correct number of emails")
        else:
            print(f"⚠️  Parser extracted {len(parsed.get('emails', []))} emails, expected 2")
        
    except ImportError as e:
        print(f"❌ Cannot import wsl_harvester: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing module: {e}")
        return False
    
    return True


def test_full_integration():
    """Test full integration with actual run"""
    print_section("6. FULL INTEGRATION TEST")
    
    try:
        import wsl_harvester
        from pathlib import Path
        
        print("Running actual harvest job for example.com...")
        print("This will take 30-60 seconds...\n")
        
        result = wsl_harvester.run_harvest_job(
            domain="example.com",
            sources=["duckduckgo"],
            limit=10,
            output_base=Path("harvester_results")
        )
        
        print(f"Status: {result.status}")
        print(f"Domain: {result.domain}")
        
        if result.status == "success":
            print("✅ Job completed successfully")
            print(f"Emails found: {len(result.parsed_data.get('emails', []))}")
            print(f"Hosts found: {len(result.parsed_data.get('hosts', []))}")
            
            if result.parsed_data.get('emails'):
                print("\nSample emails:")
                for email in result.parsed_data.get('emails', [])[:3]:
                    print(f"  - {email}")
            
            if result.parsed_data.get('hosts'):
                print("\nSample hosts:")
                for host in result.parsed_data.get('hosts', [])[:3]:
                    print(f"  - {host}")
            
            if result.raw_output_path:
                print(f"\nRaw output saved to: {result.raw_output_path}")
        else:
            print(f"❌ Job failed: {result.error_message}")
            if result.stderr:
                print(f"\nStderr: {result.stderr[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all diagnostic tests"""
    print("\n" + "="*70)
    print("  theHarvester Integration Diagnostic Tool")
    print("="*70)
    
    results = {
        "Environment": check_environment(),
        "theHarvester Installation": check_theharvester(),
        "Manual Command": test_manual_command(),
        "Output Directory": test_output_directory(),
        "Simplified Module": test_simplified_module(),
        "Full Integration": test_full_integration(),
    }
    
    print_section("SUMMARY")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED - Integration is working!")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())