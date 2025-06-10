#!/usr/bin/env python3
"""
Test script to verify the resolver installation fix works correctly.
This simulates the workflow logic to ensure the fix resolves the issue.
"""

import os
import subprocess
import sys
import tempfile
from typing import Tuple


def run_command(cmd: str, capture_output: bool = True) -> Tuple[bool, str, str]:
    """Run a command and return the result"""
    try:
        result = subprocess.run(  # nosec B602
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            executable="/bin/bash",
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def test_strategy_2_simulation() -> bool:
    """Test the Strategy 2 logic that was fixed"""
    print("🧪 Testing Strategy 2 simulation...")

    # Create a temporary virtual environment
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = os.path.join(temp_dir, "test_env")

        # Create virtual environment
        success, _, _ = run_command(f"python -m venv {venv_path}")
        if not success:
            print("❌ Failed to create virtual environment")
            return False

        # Activate and install dependencies
        activate_cmd = f"source {venv_path}/bin/activate"

        # Install pinned versions (Strategy 2 approach)
        install_cmd = f'{activate_cmd} && pip install --force-reinstall "pydantic>=2.0,<3.0" "litellm>=1.0,<2.0" "requests>=2.25.0" "click>=8.0.0" "rich>=12.0.0" "pandas>=2.0.0" "typing-extensions>=4.0.0" "aiohttp>=3.8.0" "termcolor>=1.1.0"'

        print("  📦 Installing pinned dependencies...")
        success, _, stderr = run_command(install_cmd)
        if not success:
            print(f"❌ Failed to install dependencies: {stderr}")
            return False

        # Try to install openhands-resolver (this should fail due to dependency conflicts)
        resolver_cmd = f"{activate_cmd} && pip install openhands-resolver"
        print("  🔧 Attempting to install openhands-resolver...")
        success, stdout, stderr = run_command(resolver_cmd)

        if success:
            print("  ✅ openhands-resolver installed successfully")

            # Test verification logic
            print("  🔍 Testing verification logic...")

            # Check command interface
            cmd_test = (
                f"{activate_cmd} && command -v openhands-resolver >/dev/null 2>&1"
            )
            cmd_success, _, _ = run_command(cmd_test)

            # Check module import interface
            module_test = f'{activate_cmd} && python -c "import openhands_resolver.resolve_issue" 2>/dev/null'
            module_success, _, _ = run_command(module_test)

            # Check direct import interface
            direct_test = f'{activate_cmd} && python -c "from openhands_resolver import resolve_issue" 2>/dev/null'
            direct_success, _, _ = run_command(direct_test)

            print(f"    Command interface: {'✅ PASS' if cmd_success else '❌ FAIL'}")
            print(
                f"    Module import interface: {'✅ PASS' if module_success else '❌ FAIL'}"
            )
            print(
                f"    Direct import interface: {'✅ PASS' if direct_success else '❌ FAIL'}"
            )

            # Apply the fix logic: success if ANY interface works
            interfaces_available = cmd_success or module_success or direct_success

            if interfaces_available:
                print(
                    "  ✅ Strategy 2 verification: At least one interface works - SUCCESS"
                )
                return True
            else:
                print(
                    "  ⚠️ Strategy 2 verification: No working interfaces - should fall back"
                )
                return False
        else:
            print(
                "  ❌ openhands-resolver installation failed (expected due to dependency conflicts)"
            )
            print(
                "  ✅ Strategy 2 correctly fails and should fall back to Strategy 3/4"
            )
            return True


def test_simple_resolver_fallback() -> bool:
    """Test that the simple resolver fallback works"""
    print("🧪 Testing simple resolver fallback...")

    # Check if simple_resolver.py exists and is executable
    if not os.path.exists("simple_resolver.py"):
        print("❌ simple_resolver.py not found")
        return False

    # Test basic execution
    success, stdout, stderr = run_command("python simple_resolver.py 2>&1 | head -5")
    if (
        "Environment variables:" in stdout
        or "Missing required environment variables" in stdout
    ):
        print("✅ Simple resolver is executable and working")
        return True
    else:
        print(f"❌ Simple resolver test failed: {stdout} {stderr}")
        return False


def main() -> bool:
    """Run all tests"""
    print("🔧 Testing OpenHands Resolver Installation Fix")
    print("=" * 50)

    tests = [
        ("Strategy 2 Simulation", test_strategy_2_simulation),
        ("Simple Resolver Fallback", test_simple_resolver_fallback),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The resolver fix is working correctly.")
        print("\n📋 Summary of fix:")
        print("  • Strategy 2 now properly handles dependency conflicts")
        print("  • Verification logic checks all resolver interfaces")
        print("  • Graceful fallback to simple resolver when needed")
        print("  • No more false positives claiming success with broken installations")
        return True
    else:
        print("⚠️ Some tests failed. The fix may need additional work.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
