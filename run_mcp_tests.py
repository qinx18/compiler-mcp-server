#!/usr/bin/env python3
"""
Comprehensive test runner for MCP protocol tests.

This script runs all MCP protocol tests with proper categorization and reporting.
It provides different test suites for different scenarios.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def run_command(cmd: List[str], description: str = "") -> bool:
    """Run a command and return success status"""
    print(f"\n{'=' * 60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)

    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MCP protocol tests")
    parser.add_argument(
        "--suite",
        choices=["all", "basic", "protocol", "integration", "performance", "claude"],
        default="all",
        help="Test suite to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--no-integration",
        action="store_true",
        help="Skip integration tests (useful if server can't start)",
    )

    args = parser.parse_args()

    # Change to project directory
    project_dir = Path(__file__).parent
    print(f"Running tests from: {project_dir}")

    # Base pytest command
    base_cmd = [sys.executable, "-m", "pytest"]

    if args.verbose:
        base_cmd.extend(["-v", "-s"])

    success_count = 0
    total_count = 0

    # Define test suites
    test_suites = {
        "basic": {
            "description": "Basic MCP server functionality tests",
            "cmd": [*base_cmd, "tests/test_mcp_connection.py"],
        },
        "protocol": {
            "description": "MCP protocol compliance tests",
            "cmd": [*base_cmd, "tests/test_mcp_protocol.py", "-m", "not integration"],
        },
        "integration": {
            "description": "Real MCP communication integration tests",
            "cmd": [*base_cmd, "tests/test_mcp_real_communication.py"],
        },
        "performance": {
            "description": "Performance and load tests",
            "cmd": [*base_cmd, "-m", "performance"],
        },
        "claude": {
            "description": "Claude Desktop specific tests",
            "cmd": [*base_cmd, "-m", "claude_desktop"],
        },
    }

    # Determine which suites to run
    if args.suite == "all":
        suites_to_run = list(test_suites.keys())
        if args.no_integration:
            suites_to_run.remove("integration")
    else:
        suites_to_run = [args.suite]
        if args.no_integration and args.suite == "integration":
            print("⚠️ Skipping integration tests as requested")
            return 0

    print("\n🚀 Running MCP Protocol Test Suite")
    print(f"Suites to run: {', '.join(suites_to_run)}")

    # Run each test suite
    for suite_name in suites_to_run:
        if suite_name not in test_suites:
            print(f"❌ Unknown test suite: {suite_name}")
            continue

        suite = test_suites[suite_name]
        total_count += 1

        if run_command(list(suite["cmd"]), str(suite["description"])):
            success_count += 1

    # Summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"Suites run: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")

    if success_count == total_count:
        print("🎉 All test suites passed!")
        return 0
    else:
        print("❌ Some test suites failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
