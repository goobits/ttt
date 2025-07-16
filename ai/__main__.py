#!/usr/bin/env python3
"""Make the ai module executable with python -m ai."""

import sys
from .cli import main

if __name__ == "__main__":
    # Preprocess sys.argv to inject 'ask' command when needed
    # This allows 'ai "prompt"' to work without explicit 'ask'
    known_commands = ['ask', 'chat', 'status', 'models', 'tools', 'config']
    
    # Check if we have args and first arg is not a known command or flag
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        # If first arg is not a flag (--something) and not a known command
        if not first_arg.startswith('-') and first_arg not in known_commands:
            # Inject 'ask' command
            sys.argv.insert(1, 'ask')
    
    main()
