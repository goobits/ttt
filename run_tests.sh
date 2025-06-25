#!/bin/bash
# Unit Test Runner
# Runs fast, mocked unit tests for development

set -e

echo "🧪 AI Library Unit Test Runner"
echo "=============================="
echo

# Check if we're in a virtual environment (recommended but not required)
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "✅ Virtual environment detected: $(basename $VIRTUAL_ENV)"
elif [[ -d ".venv" ]]; then
    echo "💡 Virtual environment available but not activated"
    echo "   Consider running: source .venv/bin/activate"
elif [[ -d "venv" ]]; then
    echo "💡 Virtual environment available but not activated"
    echo "   Consider running: source venv/bin/activate"
fi

echo

# Check for required dependencies
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "❌ pytest not found!"
    echo "Install with: pip install pytest pytest-asyncio pytest-cov"
    exit 1
fi

echo "🚀 Running unit tests..."
echo

# Parse command line arguments
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""
MARKERS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --test|-t)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --markers|-m)
            MARKERS="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --coverage, -c     Run with coverage report"
            echo "  --verbose, -v      Run with verbose output"
            echo "  --test, -t TEST    Run specific test file or pattern"
            echo "  --markers, -m EXPR Run tests matching marker expression"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                              # Run all unit tests"
            echo "  $0 --coverage                  # Run with coverage"
            echo "  $0 --test test_cloud_backend   # Run specific test file"
            echo "  $0 --markers 'not slow'        # Skip slow tests"
            echo "  $0 --verbose --coverage        # Verbose with coverage"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="python3 -m pytest"

# Add test path or specific test
if [[ -n "$SPECIFIC_TEST" ]]; then
    if [[ "$SPECIFIC_TEST" == *"test_"* ]]; then
        # Specific test file - add .py extension if not present
        if [[ "$SPECIFIC_TEST" != *".py" ]]; then
            SPECIFIC_TEST="${SPECIFIC_TEST}.py"
        fi
        PYTEST_CMD="$PYTEST_CMD tests/$SPECIFIC_TEST"
    else
        # Assume it's a test name pattern
        PYTEST_CMD="$PYTEST_CMD tests/ -k $SPECIFIC_TEST"
    fi
else
    # Run all unit tests (exclude integration tests)
    PYTEST_CMD="$PYTEST_CMD tests/ -m 'not integration'"
fi

# Add markers if specified
if [[ -n "$MARKERS" ]]; then
    PYTEST_CMD="$PYTEST_CMD -m '$MARKERS'"
fi

# Add verbose flag
if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage if requested
if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=ai --cov-report=term-missing --cov-report=html"
    echo "📊 Coverage report will be generated in htmlcov/"
    echo
fi

echo "Running: $PYTEST_CMD"
echo

# Execute the tests
eval $PYTEST_CMD
TEST_EXIT_CODE=$?

echo
if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    echo "✅ All tests passed!"
    
    if [[ "$COVERAGE" == true ]]; then
        echo "📊 Coverage report generated in htmlcov/index.html"
    fi
    
    echo
    echo "💡 Tips:"
    echo "  • Run integration tests: ./run_integration_tests.sh"
    echo "  • Run with coverage: $0 --coverage"
    echo "  • Run specific test: $0 --test test_cloud_backend"
    echo "  • Skip slow tests: $0 --markers 'not slow'"
else
    echo "❌ Some tests failed (exit code: $TEST_EXIT_CODE)"
    echo
    echo "🔍 Debugging tips:"
    echo "  • Run with verbose output: $0 --verbose"
    echo "  • Run specific failing test: $0 --test <test_name>"
    echo "  • Check test output above for details"
fi

echo
echo "🧪 Unit test run complete"
exit $TEST_EXIT_CODE