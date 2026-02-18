#!/usr/bin/env python3
"""
Quick test to verify theHarvester integration works end-to-end.
Run this after fixing the import issue.
"""

import sys
from pathlib import Path

def test_import():
    """Test that we can import the module"""
    print("Testing import...")
    try:
        import wsl_harvester
        print("✅ wsl_harvester imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_functions():
    """Test that all required functions exist"""
    print("\nTesting functions...")
    import wsl_harvester
    
    required = ['build_theharvester_command', 'parse_theharvester_output', 'run_harvest_job']
    all_ok = True
    
    for func_name in required:
        if hasattr(wsl_harvester, func_name):
            print(f"✅ {func_name} exists")
        else:
            print(f"❌ {func_name} missing")
            all_ok = False
    
    return all_ok


def test_command_builder():
    """Test command builder"""
    print("\nTesting command builder...")
    import wsl_harvester
    
    cmd = wsl_harvester.build_theharvester_command(
        domain="test.com",
        sources=["duckduckgo", "crtsh"],
        limit=10
    )
    
    expected = ["theHarvester", "-d", "test.com", "-b", "duckduckgo,crtsh", "-l", "10"]
    
    if cmd == expected:
        print(f"✅ Command builder works correctly")
        print(f"   Command: {' '.join(cmd)}")
        return True
    else:
        print(f"❌ Command builder returned unexpected result")
        print(f"   Expected: {expected}")
        print(f"   Got: {cmd}")
        return False


def test_parser():
    """Test output parser"""
    print("\nTesting parser...")
    import wsl_harvester
    
    sample = """
[*] Emails found: 3
------------------
test1@example.com
admin@example.com
contact@example.com

[*] Hosts found: 2
------------------
www.example.com:1.2.3.4
mail.example.com

[*] IPs found: 1
------------------
1.2.3.4
"""
    
    parsed = wsl_harvester.parse_theharvester_output(sample)
    
    print(f"   Emails: {parsed.get('emails', [])}")
    print(f"   Hosts: {parsed.get('hosts', [])}")
    print(f"   IPs: {parsed.get('ips', [])}")
    
    email_count = len(parsed.get('emails', []))
    host_count = len(parsed.get('hosts', []))
    
    if email_count == 3 and host_count == 2:
        print(f"✅ Parser works correctly")
        return True
    else:
        print(f"❌ Parser returned unexpected results")
        print(f"   Expected: 3 emails, 2 hosts")
        print(f"   Got: {email_count} emails, {host_count} hosts")
        return False


def test_real_scan():
    """Test with a real domain scan"""
    print("\nTesting real scan (this may take 30-60 seconds)...")
    import wsl_harvester
    
    result = wsl_harvester.run_harvest_job(
        domain="example.com",
        sources=["duckduckgo"],
        limit=10,
        output_base=Path("test_output")
    )
    
    print(f"   Status: {result.status}")
    print(f"   Domain: {result.domain}")
    print(f"   Duration: {(result.finished_at - result.started_at).total_seconds():.1f}s")
    
    if result.status == "success":
        emails = result.parsed_data.get('emails', [])
        hosts = result.parsed_data.get('hosts', [])
        
        print(f"   Emails found: {len(emails)}")
        print(f"   Hosts found: {len(hosts)}")
        
        if emails:
            print(f"   Sample email: {emails[0]}")
        if hosts:
            print(f"   Sample host: {hosts[0]}")
        
        print(f"✅ Real scan completed successfully")
        return True
    else:
        print(f"❌ Scan failed: {result.error_message}")
        if result.stderr:
            print(f"   Stderr: {result.stderr[:200]}")
        return False


def test_error_handling():
    """Test error handling with invalid domain"""
    print("\nTesting error handling...")
    import wsl_harvester
    
    result = wsl_harvester.run_harvest_job(
        domain="this-is-not-a-real-domain-12345.invalid",
        sources=["duckduckgo"],
        limit=5,
        output_base=Path("test_output")
    )
    
    # This should still return a result object, but might have no data
    print(f"   Status: {result.status}")
    
    if result.status in ["success", "error"]:
        print(f"✅ Error handling works (status is valid)")
        return True
    else:
        print(f"❌ Unexpected status: {result.status}")
        return False


def main():
    """Run all tests"""
    print("="*70)
    print("  theHarvester Integration Quick Test")
    print("="*70)
    
    tests = [
        ("Import", test_import),
        ("Functions", test_functions),
        ("Command Builder", test_command_builder),
        ("Parser", test_parser),
        ("Real Scan", test_real_scan),
        ("Error Handling", test_error_handling),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    print("\n" + "="*70)
    print("  Summary")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED - Ready for production!")
    else:
        print("❌ SOME TESTS FAILED - Fix issues above")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())