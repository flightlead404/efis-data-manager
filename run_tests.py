#!/usr/bin/env python3
"""
Test runner for EFIS Data Manager project.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_unit_tests():
    """Run unit tests."""
    print("🧪 Running Unit Tests...")
    print("=" * 50)
    
    unit_test_files = [
        "tests/shared/test_config_manager.py",
        "tests/shared/test_data_models.py",
        "tests/windows/test_imdisk_wrapper.py",
        "tests/windows/test_sync_engine.py",
        "tests/macos/test_grt_scraper_unit.py",
        "tests/macos/test_usb_drive_processor_unit.py"
    ]
    
    success_count = 0
    total_count = len(unit_test_files)
    
    for test_file in unit_test_files:
        if Path(test_file).exists():
            print(f"\n📋 Running {test_file}...")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", test_file, "-v"
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                    success_count += 1
                else:
                    print(f"❌ {test_file} - FAILED")
                    print(result.stdout)
                    print(result.stderr)
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {test_file} - TIMEOUT")
            except Exception as e:
                print(f"💥 {test_file} - ERROR: {e}")
        else:
            print(f"⚠️  {test_file} - NOT FOUND")
    
    print(f"\n📊 Unit Tests Summary: {success_count}/{total_count} passed")
    return success_count == total_count


def run_integration_tests():
    """Run integration tests."""
    print("\n🔗 Running Integration Tests...")
    print("=" * 50)
    
    integration_test_files = [
        "tests/integration/test_end_to_end_workflow.py",
        "tests/integration/test_network_failure_simulation.py",
        "tests/integration/test_usb_drive_lifecycle.py",
        "tests/integration/test_performance_load.py"
    ]
    
    success_count = 0
    total_count = len(integration_test_files)
    
    for test_file in integration_test_files:
        if Path(test_file).exists():
            print(f"\n📋 Running {test_file}...")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", test_file, "-v", "-s"
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                    success_count += 1
                else:
                    print(f"❌ {test_file} - FAILED")
                    print(result.stdout)
                    print(result.stderr)
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {test_file} - TIMEOUT")
            except Exception as e:
                print(f"💥 {test_file} - ERROR: {e}")
        else:
            print(f"⚠️  {test_file} - NOT FOUND")
    
    print(f"\n📊 Integration Tests Summary: {success_count}/{total_count} passed")
    return success_count == total_count


def run_existing_tests():
    """Run existing macOS tests."""
    print("\n🍎 Running Existing macOS Tests...")
    print("=" * 50)
    
    existing_test_files = [
        "macos/test_complete_system.py",
        "macos/test_grt_scraper.py",
        "macos/test_download_manager.py",
        "macos/test_usb_drive_updater.py"
    ]
    
    success_count = 0
    total_count = len(existing_test_files)
    
    for test_file in existing_test_files:
        if Path(test_file).exists():
            print(f"\n📋 Running {test_file}...")
            try:
                result = subprocess.run([
                    sys.executable, test_file
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                    success_count += 1
                    # Show some output for successful tests
                    lines = result.stdout.split('\n')
                    for line in lines[-10:]:  # Last 10 lines
                        if line.strip():
                            print(f"  {line}")
                else:
                    print(f"❌ {test_file} - FAILED")
                    print(result.stdout)
                    print(result.stderr)
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {test_file} - TIMEOUT")
            except Exception as e:
                print(f"💥 {test_file} - ERROR: {e}")
        else:
            print(f"⚠️  {test_file} - NOT FOUND")
    
    print(f"\n📊 Existing Tests Summary: {success_count}/{total_count} passed")
    return success_count == total_count


def run_setup_test():
    """Run project setup test."""
    print("\n🔧 Running Project Setup Test...")
    print("=" * 50)
    
    setup_test = "tests/test_setup.py"
    
    if Path(setup_test).exists():
        try:
            result = subprocess.run([
                sys.executable, setup_test
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Project setup test - PASSED")
                print(result.stdout)
                return True
            else:
                print("❌ Project setup test - FAILED")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Project setup test - TIMEOUT")
            return False
        except Exception as e:
            print(f"💥 Project setup test - ERROR: {e}")
            return False
    else:
        print("⚠️  Project setup test - NOT FOUND")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="EFIS Data Manager Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--existing", action="store_true", help="Run existing tests only")
    parser.add_argument("--setup", action="store_true", help="Run setup test only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    if not any([args.unit, args.integration, args.existing, args.setup, args.all]):
        args.all = True  # Default to all tests
    
    print("🚀 EFIS Data Manager Test Suite")
    print("=" * 60)
    
    results = []
    
    if args.setup or args.all:
        results.append(("Setup", run_setup_test()))
    
    if args.unit or args.all:
        results.append(("Unit", run_unit_tests()))
    
    if args.integration or args.all:
        results.append(("Integration", run_integration_tests()))
    
    if args.existing or args.all:
        results.append(("Existing", run_existing_tests()))
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST SUMMARY")
    print("=" * 60)
    
    total_suites = len(results)
    passed_suites = sum(1 for _, passed in results if passed)
    
    for suite_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{suite_name:12} Tests: {status}")
    
    print(f"\nOverall: {passed_suites}/{total_suites} test suites passed")
    
    if passed_suites == total_suites:
        print("\n🎉 All tests passed! The EFIS Data Manager testing framework is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_suites - passed_suites} test suite(s) failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())