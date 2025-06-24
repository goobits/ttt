#!/usr/bin/env python3
"""
Command-line interface for Agents.py
"""

import sys
import os
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Import agents early to ensure env vars are loaded for model registration
    from agents import ai, chat, stream, get_default_configuration, ModelInfo
    
    parser = argparse.ArgumentParser(
        description="Agents.py - AI that just works",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agents "What is Python?"                    # Simple query
  agents "Calculate 15% of 120" --math        # Force math model
  agents "Explain this code" --code file.py   # Analyze code file
  agents --chat                               # Interactive chat mode
  agents --model gpt-4o "Complex question"    # Use specific model
        """
    )
    
    parser.add_argument("prompt", nargs="*", help="The prompt to send to AI")
    parser.add_argument("-m", "--model", help="Specific model to use")
    parser.add_argument("--math", action="store_true", help="Use math-optimized model")
    parser.add_argument("--code", metavar="FILE", help="Include code from file")
    parser.add_argument("--fast", action="store_true", help="Prefer fast models")
    parser.add_argument("--quality", action="store_true", help="Prefer quality models")
    parser.add_argument("--chat", action="store_true", help="Interactive chat mode")
    parser.add_argument("--stream", action="store_true", help="Stream the response")
    parser.add_argument("--mock", action="store_true", help="Use mock backend for testing")
    
    args = parser.parse_args()
    
    # Configure mock mode if requested
    if args.mock:
        config = get_default_configuration()
        config.add_model(ModelInfo(
            name="mock",
            provider="mock", 
            provider_name="mock"
        ))
        # Override default models to use mock
        for model_name in config.list_models():
            model = config.get_model(model_name)
            model.provider = "mock"
            model.provider_name = "mock"
    
    # Interactive chat mode
    if args.chat:
        print("🤖 Agents.py Interactive Chat (type 'exit' to quit)\n")
        try:
            with chat(model=args.model) as assistant:
                while True:
                    try:
                        user_input = input("You: ")
                        if user_input.lower() in ["exit", "quit", "bye"]:
                            print("\nGoodbye! 👋")
                            break
                        
                        response = assistant(user_input)
                        print(f"\nAI: {response}\n")
                        
                    except KeyboardInterrupt:
                        print("\n\nGoodbye! 👋")
                        break
                        
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    # Regular query mode
    else:
        if not args.prompt:
            parser.print_help()
            sys.exit(1)
        
        prompt = " ".join(args.prompt)
        
        # Handle code input
        kwargs = {}
        if args.code:
            try:
                with open(args.code, 'r') as f:
                    kwargs['code'] = f.read()
            except FileNotFoundError:
                print(f"Error: File '{args.code}' not found")
                sys.exit(1)
        
        # Handle model selection
        if args.model:
            kwargs['model'] = args.model
        elif args.math:
            prompt = f"[Math] {prompt}"  # Hint for router
        
        if args.fast:
            kwargs['fast'] = True
        if args.quality:
            kwargs['quality'] = True
        
        try:
            # Stream or regular response
            if args.stream:
                for chunk in stream(prompt, **kwargs):
                    print(chunk, end="", flush=True)
                print()  # Final newline
            else:
                response = ai(prompt, **kwargs)
                print(response)
                
                # Show metadata in verbose mode
                if os.getenv("AGENTS_VERBOSE"):
                    print(f"\n[Model: {response.model}, Time: {response.time:.2f}s]")
                    
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()