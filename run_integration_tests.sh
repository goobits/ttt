#!/bin/bash
# Integration Test Runner
# Runs tests with real API keys - USE SPARINGLY to avoid costs

set -e

echo "🧪 AI Library Integration Test Runner"
echo "======================================"
echo

# Check for API keys
API_KEYS_FOUND=0

if [[ -n "$OPENAI_API_KEY" ]]; then
    echo "✅ OpenAI API key found"
    API_KEYS_FOUND=1
fi

if [[ -n "$ANTHROPIC_API_KEY" ]]; then
    echo "✅ Anthropic API key found"  
    API_KEYS_FOUND=1
fi

if [[ -n "$OPENROUTER_API_KEY" ]]; then
    echo "✅ OpenRouter API key found"
    API_KEYS_FOUND=1
fi

if [[ $API_KEYS_FOUND -eq 0 ]]; then
    echo "❌ No API keys found!"
    echo "Set one or more of these environment variables:"
    echo "  - OPENAI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"  
    echo "  - OPENROUTER_API_KEY"
    echo
    echo "Example:"
    echo "  export OPENROUTER_API_KEY='your-key-here'"
    echo "  ./run_integration_tests.sh"
    exit 1
fi

echo
echo "⚠️  WARNING: These tests will make real API calls and consume credits!"
echo "💰 Estimated cost: $0.01 - $0.10 depending on models used"
echo

# Ask for confirmation
read -p "Continue with integration tests? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Integration tests cancelled."
    exit 0
fi

echo
echo "🚀 Running integration tests..."
echo

# Run different test categories
echo "📋 Basic Integration Tests:"
python -m pytest tests/test_integration.py::TestRealAPIIntegration -v -m integration

echo
echo "🏷️  Provider-Specific Tests:"
python -m pytest tests/test_integration.py::TestProviderSpecificIntegration -v -m integration

echo  
echo "⚡ Error Handling Tests:"
python -m pytest tests/test_integration.py::TestErrorHandlingIntegration -v -m integration

# Optional: Run benchmarks (uncomment if needed)
# echo
# echo "📊 Performance Benchmarks (optional):"
# read -p "Run performance benchmarks? [y/N]: " -n 1 -r
# echo
# if [[ $REPLY =~ ^[Yy]$ ]]; then
#     python -m pytest tests/test_integration.py::TestPerformanceBenchmarks -v -m benchmark
# fi

echo
echo "✅ Integration tests complete!"
echo "💡 Tip: Run unit tests with 'python -m pytest' for development"