#!/usr/bin/env python3
"""Entry point wrapper that handles JSON mode environment setup."""

import sys
import os


def main():
    """Main entry point that handles JSON mode properly."""
    # For JSON mode, aggressively suppress all output
    if "--json" in sys.argv:
        import io
        import os
        import logging

        # Set environment variable for any code that checks it
        os.environ["TTT_JSON_MODE"] = "true"

        # Completely disable all logging at the root level
        logging.disable(logging.CRITICAL)

        # Also disable all existing loggers
        logging.getLogger().disabled = True

        # More aggressive stderr redirection using file descriptor
        original_stderr_fd = os.dup(2)  # Duplicate stderr file descriptor
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, 2)  # Redirect stderr file descriptor to /dev/null

        # Also redirect sys.stderr as fallback
        original_stderr = sys.stderr
        sys.stderr = open(os.devnull, "w")

        try:
            # Import and run CLI with all output suppressed
            from ttt.cli_fire import main as cli_main

            cli_main()
        finally:
            # Always restore file descriptors and streams
            sys.stderr.close()
            sys.stderr = original_stderr
            os.dup2(original_stderr_fd, 2)  # Restore stderr file descriptor
            os.close(devnull_fd)
            os.close(original_stderr_fd)
            logging.disable(logging.NOTSET)
            logging.getLogger().disabled = False
    else:
        # Normal mode - no suppression
        from ttt.cli_fire import main as cli_main

        cli_main()


if __name__ == "__main__":
    main()
