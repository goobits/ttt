#!/usr/bin/env python3
"""
CLI command examples for the AI library.

This script demonstrates the advanced CLI commands for managing
models and backends. Run these commands in your terminal.
"""

import subprocess
import sys


def run_command(cmd):
    """Run a command and print the output."""
    print(f"\n$ {cmd}")
    print("-" * 60)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}", file=sys.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Failed to run command: {e}", file=sys.stderr)
        return False


def main():
    """Demonstrate CLI commands."""
    print("AI Library CLI Commands Demo")
    print("=" * 60)

    # Check if AI is installed
    print("\nChecking if 'ai' command is available...")
    if not run_command("which ai"):
        print("\nThe 'ai' command is not found in PATH.")
        print("Install with: pip install -e .")
        return

    # Show version
    print("\n1. Version Information")
    run_command("ai version")

    # Backend status
    print("\n2. Backend Status")
    run_command("ai backend status")

    # Backend status verbose
    print("\n3. Backend Status (Verbose)")
    run_command("ai backend status --verbose")

    # List all models
    print("\n4. List All Models")
    run_command("ai models list")

    # List local models only
    print("\n5. List Local Models")
    run_command("ai models list --local")

    # List cloud models only
    print("\n6. List Cloud Models")
    run_command("ai models list --cloud")

    # List models with details
    print("\n7. List Models (Verbose)")
    run_command("ai models list --verbose")

    # Show model pull help
    print("\n8. Model Pull Help")
    run_command("ai models pull --help")

    # Basic ask example
    print("\n9. Basic Ask Example")
    run_command('ai "What is 2+2?" --verbose')

    # Help for main command
    print("\n10. Main Command Help")
    run_command("ai --help")

    print("\n" + "=" * 60)
    print("CLI Commands Demo Complete!")
    print("\nTips:")
    print("- Use 'ai backend status' to check your setup")
    print("- Use 'ai models list' to see available models")
    print("- Use 'ai models pull <model>' to download local models")
    print("- Add --verbose to any command for more details")


if __name__ == "__main__":
    main()
