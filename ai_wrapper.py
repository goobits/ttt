#!/usr/bin/env python3
"""Wrapper script that filters out async cleanup warnings."""

import sys
import subprocess
import re

def filter_output(line):
    """Filter out unwanted warnings while keeping real errors."""
    unwanted_patterns = [
        r"Task was destroyed but it is pending",
        r"sys\.meta_path is None",
        r"coroutine.*was never awaited",
        r"Exception ignored in:.*ClientSession\.__del__",
        r"Exception ignored in:.*BaseConnector\.__del__",
        r"ImportError: sys\.meta_path is None",
        r"RuntimeWarning: Enable tracemalloc",
        r"RuntimeWarning: coroutine",
        r"LiteLLM completion",
        r"selected model name for cost",
        r"cost_calculator\.py",
        r"utils\.py:\d+",
        r"INFO\s+.*\s+utils\.py",
        r"INFO\s+.*\s+cost_calculator\.py",
        r"^\s*calculation:\s*$",
        r"openrouter/google/gemini-flash-1\.5",
        r"google/gemini-flash-1\.5.*provider.*openrouter",
        r"google/gemini-flash-1\.5\s*$"
    ]
    
    for pattern in unwanted_patterns:
        if re.search(pattern, line):
            return False
    
    return True

def main():
    """Run the AI CLI with filtered output."""
    # Run the actual CLI
    cmd = [sys.executable, "-m", "ai.cli"] + sys.argv[1:]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Filter and print stdout
        for line in process.stdout:
            if filter_output(line.strip()):
                print(line, end='')
        
        # Filter stderr
        stderr_lines = []
        for line in process.stderr:
            if filter_output(line.strip()):
                stderr_lines.append(line)
        
        # Print filtered stderr if any
        if stderr_lines:
            for line in stderr_lines:
                print(line, end='', file=sys.stderr)
        
        process.wait()
        sys.exit(process.returncode)
        
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()