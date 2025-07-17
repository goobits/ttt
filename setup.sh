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

# Print friendly output
print_status() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Spinner for long operations
with_spinner() {
    local pid=$!
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local temp
    printf "${BLUE}%s${NC}" "$1"
    while ps -p $pid > /dev/null 2>&1; do
        temp=${spinstr#?}
        printf " [%c]" "$spinstr"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b"
    done
    printf "    \b\b\b\b"
    wait $pid
    return $?
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Clean shell RC file of AI Library entries
clean_shell_rc() {
    if [[ -f "$SHELL_RC" ]]; then
        grep -v "# AI Library Integration" "$SHELL_RC" > "${SHELL_RC}.tmp" || true
        grep -v "function ai()" "${SHELL_RC}.tmp" > "${SHELL_RC}.tmp2" || true
        grep -v "$VENV_DIR/bin" "${SHELL_RC}.tmp2" > "$SHELL_RC" || true
        rm -f "${SHELL_RC}.tmp" "${SHELL_RC}.tmp2"
    fi
}

# Check for active API keys
has_active_api_keys() {
    [[ -f "$API_KEY_FILE" ]] && grep -q "^[^#]*API_KEY=" "$API_KEY_FILE" 2>/dev/null
}

# Create virtual environment
create_venv() {
    printf "${BLUE}🔄 Setting up Python environment${NC}"
    if ! command_exists python3; then
        printf "\n"
        print_error "Python3 is required but not installed"
        exit 1
    fi
    
    (python3 -m venv "$VENV_DIR" && source "$VENV_DIR/bin/activate" && pip install --upgrade pip --quiet) >/dev/null 2>&1 &
    with_spinner "Setting up Python environment"
    printf "\n"
    print_success "Python environment ready"
}

# Install AI library
install_ai() {
    printf "${BLUE}🔄 Installing AI library${NC}"
    source "$VENV_DIR/bin/activate"
    
    # Install dependencies from pyproject.toml
    if command_exists poetry; then
        poetry install >/dev/null 2>&1 &
    else
        # Install core dependencies
        (pip install --quiet pydantic "litellm>=1.0.0" "rich>=13.0.0" "click>=8.0.0" "python-dotenv>=1.0.0" "pyyaml>=6.0" "bleach>=6.0.0" "validators>=0.22.0" "httpx" && pip install --quiet -e .) >/dev/null 2>&1 &
    fi
    
    with_spinner "Installing AI library"
    printf "\n"
    print_success "AI library installed"
}

# Setup shell integration (fallback only)
setup_shell() {
    print_status "Configuring shell integration"
    detect_shell
    
    # Create function with subshell to avoid persistent venv activation
    local ai_function="function ai() { (cd $AI_DIR && source .venv/bin/activate && python -m ai \"\$@\"); }"
    local ai_path_export="export PATH=\"$VENV_DIR/bin:\$PATH\""
    local ai_comment="# AI Library Integration"
    
    # Remove existing entries
    clean_shell_rc
    
    # Add new entries
    echo "" >> "$SHELL_RC"
    echo "$ai_comment" >> "$SHELL_RC"
    echo "$ai_path_export" >> "$SHELL_RC"
    echo "$ai_function" >> "$SHELL_RC"
    
    print_success "Shell integration configured"
}

# Setup environment variables
setup_env() {
    print_status "Setting up API configuration"
    
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
        print_warning "Created $API_KEY_FILE - add your API keys here"
    else
        if has_active_api_keys; then
            print_success "Found existing API keys"
        else
            print_warning "No active API keys found"
        fi
    fi
    
    # Add env file sourcing to shell
    local env_source="source $API_KEY_FILE 2>/dev/null || true"
    
    if ! grep -q "$API_KEY_FILE" "$SHELL_RC" 2>/dev/null; then
        echo "$env_source" >> "$SHELL_RC"
    fi
}

# Install function
install() {
    local dev_mode=${1:-false}
    
    echo
    if [[ "$dev_mode" == "true" ]]; then
        echo -e "${BLUE}🚀 AI Library Installer (Development Mode)${NC}"
    else
        echo -e "${BLUE}🚀 AI Library Installer${NC}"
    fi
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    
    # Check for pipx (recommended)
    if command_exists pipx; then
        print_status "Using pipx for clean installation"
        
        # Check if already installed via pipx
        if pipx list | grep -q "^  package ai "; then
            if [[ "$dev_mode" == "true" ]]; then
                print_warning "AI library already installed. Development mode requires clean reinstall."
                pipx uninstall ai 2>/dev/null || true
            else
                print_warning "AI library already installed via pipx"
                echo -n "Reinstall? [y/N]: "
                read -r response
                if [[ ! "$response" =~ ^[Yy]$ ]]; then
                    echo "Installation cancelled"
                    exit 0
                fi
                pipx uninstall ai 2>/dev/null || true
            fi
        fi
        
        # Install with pipx
        if [[ "$dev_mode" == "true" ]]; then
            print_status "Installing with pipx in editable mode..."
            pipx install --editable . || {
                print_error "pipx development installation failed"
                exit 1
            }
        else
            print_status "Installing with pipx..."
            pipx install . || {
                print_error "pipx installation failed"
                exit 1
            }
        fi
        
        echo
        echo -e "${GREEN}🎉 Installation Complete!${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo
        echo -e "${YELLOW}Next Steps:${NC}"
        echo -e "1. 🔑 Set your API key: ${YELLOW}export OPENROUTER_API_KEY=your-key-here${NC}"
        echo -e "2. 🧪 Test it out: ${YELLOW}ai 'What is 2+2?'${NC}"
        echo
        if [[ "$dev_mode" == "true" ]]; then
            echo -e "${GREEN}Development mode:${NC}"
            echo "  ✅ Live file editing (changes reflect immediately)"
            echo "  ✅ No need to reinstall after code changes"
        else
            echo -e "${GREEN}pipx provides:${NC}"
            echo "  ✅ Isolated virtual environment"
        fi
        echo "  ✅ Global 'ai' command"
        echo "  ✅ Easy updates with 'pipx upgrade ai'"
        echo "  ✅ Clean uninstall with 'pipx uninstall ai'"
        
    else
        print_error "pipx is required for installation"
        echo "Install pipx first:"
        echo "  sudo apt install pipx"
        echo "  pipx ensurepath"
        exit 1
    fi
    
    echo
    echo -e "${BLUE}Quick Examples:${NC}"
    echo -e "  ${YELLOW}ai${NC} 'Explain quantum computing'"
    echo -e "  ${YELLOW}echo 'Hello world' | ai${NC}"
    echo -e "  ${YELLOW}git diff | ai 'Explain changes'${NC}"
    echo -e "  ${YELLOW}ai${NC} status"
    echo
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Ready to chat with AI! 🤖${NC}"
    
}

# Uninstall function
uninstall() {
    echo
    echo -e "${YELLOW}🗑️  Uninstalling AI Library${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    
    # Check if installed via pipx
    if command_exists pipx && pipx list | grep -q "^  package ai "; then
        print_status "Removing pipx installation..."
        pipx uninstall ai
        print_success "Removed pipx installation"
    else
        # Legacy removal - virtual environment and shell integration
        if [[ -d "$VENV_DIR" ]]; then
            rm -rf "$VENV_DIR"
            print_success "Removed virtual environment"
        fi
        
        # Remove shell integration
        detect_shell
        if [[ -f "$SHELL_RC" ]]; then
            clean_shell_rc
            print_success "Removed shell integration"
        fi
        
        # Remove global binary
        if [[ -f "$HOME/.local/bin/ai" ]]; then
            rm -f "$HOME/.local/bin/ai"
            print_success "Removed global binary"
        fi
    fi
    
    # Ask about .env file
    if [[ -f "$API_KEY_FILE" ]]; then
        # Check if there are active API keys
        if has_active_api_keys; then
            print_warning "Found active API keys in $API_KEY_FILE"
            echo -n "Remove API key file with ACTIVE KEYS? [y/N]: "
        else
            echo -n "Remove API key file ($API_KEY_FILE)? [y/N]: "
        fi
        
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            # Create backup first
            backup_file="${API_KEY_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
            cp "$API_KEY_FILE" "$backup_file"
            echo "💾 Created backup at $backup_file"
            
            rm -f "$API_KEY_FILE"
            print_success "Removed API key file (backup saved)"
        else
            echo "📁 Kept API key file"
        fi
    fi
    
    echo
    print_success "Uninstallation complete!"
}


# Fallback pip installation
install_with_pip() {
    # Check if already installed
    if [[ -d "$VENV_DIR" ]]; then
        print_warning "AI library appears to be already installed"
        
        # Check for existing .env file with keys
        if has_active_api_keys; then
            print_success "Your API keys will be preserved"
        fi
        
        echo -n "Continue with reinstall? [y/N]: "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Installation cancelled"
            exit 0
        fi
        
        # Only remove venv, not config files
        rm -rf "$VENV_DIR"
        echo "🗑️  Removed old environment"
    fi
    
    create_venv
    install_ai
    setup_shell
    setup_env
    
    echo
    echo -e "${GREEN}🎉 Installation Complete!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "1. 🔄 Restart your terminal or run: ${YELLOW}source $SHELL_RC${NC}"
    echo -e "2. 🔑 Add your API keys to: ${YELLOW}$API_KEY_FILE${NC}"
    echo -e "3. 🧪 Test it out: ${YELLOW}ai 'What is 2+2?'${NC}"
}

# Test installation
test_installation() {
    print_status "Testing AI installation..."
    
    if [[ -f "$API_KEY_FILE" ]]; then
        source "$API_KEY_FILE" 2>/dev/null || true
    fi
    
    echo "Running: ai status"
    ai status || {
        print_warning "CLI test failed - make sure to add API keys to $API_KEY_FILE"
    }
}


# Usage function
usage() {
    echo "AI Library Setup Script"
    echo
    echo "Usage: $0 {install|install --dev|uninstall|help}"
    echo
    echo "Commands:"
    echo "  install        Install the AI library and CLI"
    echo "  install --dev  Install in development mode (editable)"
    echo "  uninstall      Remove the AI library and CLI"
    echo "  help           Show this help message"
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
        if [[ "${2:-}" == "--dev" ]]; then
            install true
        else
            install false
        fi
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