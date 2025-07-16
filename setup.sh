#!/bin/bash

# AI Library Setup Script
# Manages installation and configuration of the AI CLI tool

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$SCRIPT_DIR"
VENV_DIR="$AI_DIR/.venv"
SHELL_RC=""
API_KEY_FILE="$AI_DIR/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect shell and set RC file
detect_shell() {
    if [[ -n "$ZSH_VERSION" ]]; then
        SHELL_RC="$HOME/.zshrc"
        echo "Detected: zsh"
    elif [[ -n "$BASH_VERSION" ]]; then
        SHELL_RC="$HOME/.bashrc"
        echo "Detected: bash"
    else
        echo -e "${YELLOW}Warning: Could not detect shell. Defaulting to ~/.bashrc${NC}"
        SHELL_RC="$HOME/.bashrc"
    fi
}

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Create virtual environment
create_venv() {
    print_status "Creating Python virtual environment..."
    if ! command_exists python3; then
        print_error "Python3 is required but not installed"
        exit 1
    fi
    
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    print_success "Virtual environment created"
}

# Install AI library
install_ai() {
    print_status "Installing AI library..."
    source "$VENV_DIR/bin/activate"
    
    # Install dependencies from pyproject.toml
    if command_exists poetry; then
        print_status "Using Poetry for dependency management..."
        poetry install
    else
        print_status "Installing dependencies manually..."
        # Install core dependencies
        pip install pydantic "litellm>=1.0.0" "rich>=13.0.0" "click>=8.0.0" "python-dotenv>=1.0.0" "pyyaml>=6.0" "bleach>=6.0.0" "validators>=0.22.0" "httpx"
        
        # Install the library in development mode
        pip install -e .
    fi
    
    print_success "AI library installed"
}

# Setup shell integration
setup_shell() {
    print_status "Setting up shell integration..."
    detect_shell
    
    # Create function instead of alias for better compatibility
    local ai_function="function ai() { source $VENV_DIR/bin/activate && python -m ai \"\$@\"; }"
    local ai_path_export="export PATH=\"$VENV_DIR/bin:\$PATH\""
    local ai_comment="# AI Library Integration"
    
    # Remove existing entries
    if [[ -f "$SHELL_RC" ]]; then
        grep -v "# AI Library Integration" "$SHELL_RC" > "${SHELL_RC}.tmp" || true
        grep -v "function ai()" "${SHELL_RC}.tmp" > "${SHELL_RC}.tmp2" || true
        grep -v "$VENV_DIR/bin" "${SHELL_RC}.tmp2" > "$SHELL_RC" || true
        rm -f "${SHELL_RC}.tmp" "${SHELL_RC}.tmp2"
    fi
    
    # Add new entries
    echo "" >> "$SHELL_RC"
    echo "$ai_comment" >> "$SHELL_RC"
    echo "$ai_path_export" >> "$SHELL_RC"
    echo "$ai_function" >> "$SHELL_RC"
    
    # Also create a global binary for better compatibility
    local bin_dir="$HOME/.local/bin"
    mkdir -p "$bin_dir"
    
    cat > "$bin_dir/ai" << EOF
#!/bin/bash
# AI Library Global Command

# Change to the AI library directory
cd $AI_DIR

# Activate virtual environment and run the AI CLI
source .venv/bin/activate && python -m ai "\$@"
EOF
    
    chmod +x "$bin_dir/ai"
    
    print_success "Shell integration added to $SHELL_RC"
    print_success "Global 'ai' command created in $bin_dir/ai"
}

# Setup environment variables
setup_env() {
    print_status "Setting up environment variables..."
    
    # Check for existing .env file or create template
    if [[ ! -f "$API_KEY_FILE" ]]; then
        cat > "$API_KEY_FILE" << 'EOF'
# AI Library Environment Variables
# Uncomment and set the API keys you want to use

# OpenRouter (recommended - works with multiple models)
# OPENROUTER_API_KEY=your-openrouter-key-here

# Direct provider keys (optional)
# OPENAI_API_KEY=your-openai-key-here
# ANTHROPIC_API_KEY=your-anthropic-key-here
# GOOGLE_API_KEY=your-google-key-here

# Local Ollama configuration (optional)
# OLLAMA_BASE_URL=http://localhost:11434
EOF
        print_warning "Created $API_KEY_FILE - please edit it with your API keys"
    else
        print_status "Environment file already exists at $API_KEY_FILE"
    fi
    
    # Add env file sourcing to shell
    local env_source="source $API_KEY_FILE 2>/dev/null || true"
    
    if ! grep -q "$API_KEY_FILE" "$SHELL_RC" 2>/dev/null; then
        echo "$env_source" >> "$SHELL_RC"
        print_success "Environment file sourcing added to shell"
    fi
}

# Install function
install() {
    print_status "Installing AI Library..."
    
    # Check if already installed
    if [[ -d "$VENV_DIR" ]]; then
        print_warning "AI library appears to be already installed"
        echo "Run '$0 uninstall' to remove the existing installation first"
        exit 1
    fi
    
    create_venv
    install_ai
    setup_shell
    setup_env
    
    print_success "Installation complete!"
    echo
    echo -e "${GREEN}✅ AI Library Successfully Installed${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    echo -e "${YELLOW}NEXT STEPS:${NC}"
    echo "1. ${GREEN}Restart your terminal${NC} or run: ${YELLOW}source $SHELL_RC${NC}"
    echo "2. ${GREEN}Configure API keys${NC} in: ${YELLOW}$API_KEY_FILE${NC}"
    echo "3. ${GREEN}Test installation${NC}: ${YELLOW}ai 'What is 2+2?'${NC}"
    echo
    echo -e "${BLUE}COMMANDS AVAILABLE:${NC}"
    echo "  ${YELLOW}ai${NC}                               # Show help menu"
    echo "  ${YELLOW}ai${NC} 'Your question here'           # Basic usage"
    echo "  ${YELLOW}echo 'text' | ai${NC}                 # Pipe text to AI"
    echo "  ${YELLOW}ai${NC} status                         # Check system status"
    echo "  ${YELLOW}ai${NC} models                         # List available models"
    echo "  ${YELLOW}ai${NC} --help                         # Show all options"
    echo
    echo -e "${BLUE}EXAMPLE USAGE:${NC}"
    echo "  ${YELLOW}ai${NC} 'Explain quantum computing'"
    echo "  ${YELLOW}ai${NC} 'Write Python code' --model claude-3-sonnet"
    echo "  ${YELLOW}echo 'Hello world' | ai${NC}          # NEW: Direct pipe support"
    echo "  ${YELLOW}cat file.txt | ai 'Review this'${NC}  # Pipe with additional prompt"
    echo "  ${YELLOW}git diff | ai 'Explain changes'${NC}  # Pipe git output"
    echo "  ${YELLOW}ai${NC} 'Question' --verbose           # Show metadata"
    echo
    echo -e "${GREEN}FEATURES:${NC}"
    echo "  ✅ Unified interface for multiple AI providers"
    echo "  ✅ OpenRouter integration (100+ models)"
    echo "  ✅ Direct pipe support (no dash needed!)"
    echo "  ✅ Clean output with minimal logging"
    echo "  ✅ Global command available from any directory"
    echo "  ✅ Professional error handling and diagnostics"
    echo
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Ready for professional AI assistance!${NC}"
    
    echo
    echo -e "${BLUE}TROUBLESHOOTING:${NC}"
    echo "If you see 'model not found' errors:"
    echo "  ${YELLOW}ai config backend cloud${NC}         # Switch to cloud backend"
    echo "  ${YELLOW}ai config openai_key sk-...${NC}     # Add your API key"
    echo "  ${YELLOW}ai status${NC}                       # Check configuration"
    echo
    echo "For local models (requires Ollama):"
    echo "  ${YELLOW}curl https://ollama.ai/install.sh | sh${NC}"
    echo "  ${YELLOW}ollama pull mistral${NC}             # Pull a model"
    echo "  ${YELLOW}ai config model mistral${NC}         # Set default model"
    
    # Offer to test in current session
    echo
    echo -n "Test AI in current session? [y/N]: "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        test_current_session
    fi
}

# Uninstall function
uninstall() {
    print_status "Uninstalling AI Library..."
    
    # Remove virtual environment
    if [[ -d "$VENV_DIR" ]]; then
        rm -rf "$VENV_DIR"
        print_success "Removed virtual environment"
    fi
    
    # Remove shell integration
    detect_shell
    if [[ -f "$SHELL_RC" ]]; then
        print_status "Removing shell integration..."
        grep -v "# AI Library Integration" "$SHELL_RC" > "${SHELL_RC}.tmp" || true
        grep -v "function ai()" "${SHELL_RC}.tmp" > "${SHELL_RC}.tmp2" || true
        grep -v "$AI_DIR" "${SHELL_RC}.tmp2" > "$SHELL_RC" || true
        rm -f "${SHELL_RC}.tmp" "${SHELL_RC}.tmp2"
        print_success "Removed shell integration"
    fi
    
    # Ask about .env file
    if [[ -f "$API_KEY_FILE" ]]; then
        echo -n "Remove API key file ($API_KEY_FILE)? [y/N]: "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -f "$API_KEY_FILE"
            print_success "Removed API key file"
        else
            print_status "Kept API key file"
        fi
    fi
    
    print_success "Uninstallation complete!"
    echo "Please restart your terminal to complete the removal."
}


# Test in current session
test_current_session() {
    print_status "Testing AI in current session..."
    source "$VENV_DIR/bin/activate"
    
    if [[ -f "$API_KEY_FILE" ]]; then
        source "$API_KEY_FILE" 2>/dev/null || true
    fi
    
    echo "Running: python -m ai status"
    python -m ai status || {
        print_warning "CLI test failed, trying Python API..."
        python -c "
from ai.api import ask
try:
    print('Testing basic functionality...')
    response = ask('Hello!', max_tokens=10)
    print(f'✅ Success: {str(response)[:50]}...')
except Exception as e:
    print(f'❌ Error: {e}')
    print('Make sure to add API keys to $API_KEY_FILE')
"
    }
}


# Usage function
usage() {
    echo "AI Library Setup Script"
    echo
    echo "Usage: $0 {install|uninstall|help}"
    echo
    echo "Commands:"
    echo "  install     Install the AI library and CLI"
    echo "  uninstall   Remove the AI library and CLI"
    echo "  help        Show this help message"
    echo
    echo "After installation, use:"
    echo "  ai 'Your question here'  # Clean output with minimal logging"
    echo "  ai --help               # Show available options"
    echo
    echo "Features:"
    echo "  ✅ Clean output (filtered async warnings)"
    echo "  ✅ OpenRouter integration (multiple AI models)"
    echo "  ✅ Smart defaults (cloud backend, gemini-flash model)"
    echo "  ✅ Comprehensive commands (status, models, tools)"
}

# Main script logic
case "${1:-}" in
    install)
        install
        ;;
    uninstall)
        uninstall
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}Error: Unknown command '${1:-}'${NC}"
        echo
        usage
        exit 1
        ;;
esac