#!/usr/bin/env python3
"""Entry point wrapper that handles JSON mode environment setup."""

import sys
import os

def main():
    """Main entry point that handles JSON mode properly."""
    # For JSON mode, aggressively suppress all output
    if '--json' in sys.argv:
        import io
        import os
        import logging
        
        # Set environment variable for any code that checks it
        os.environ['TTT_JSON_MODE'] = 'true'
        
        # Completely disable all logging
        logging.disable(logging.CRITICAL)
        
        # Suppress only stderr (preserve stdout for JSON output)
        original_stderr = sys.stderr
        devnull = open(os.devnull, 'w')
        sys.stderr = devnull
        
        try:
            # Import and run CLI with stderr suppressed but stdout preserved
            from ttt.cli_fire import main as cli_main
            cli_main()
        finally:
            # Always restore streams and logging
            devnull.close()
            sys.stderr = original_stderr
            logging.disable(logging.NOTSET)
    else:
        # Normal mode - no suppression
        from ttt.cli_fire import main as cli_main
        cli_main()

if __name__ == '__main__':
    main()