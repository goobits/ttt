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

# Check Python version meets minimum requirements
check_python_version() {
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
    
    if [ "$python_version" != "unknown" ]; then
        print_status "Detected Python $python_version"
    fi
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        print_error "Python 3.8+ required (found $python_version)"
        echo "Please upgrade your Python installation"
        exit 1
    fi
    
    print_success "Python version check passed"
}

# Check for dependency conflicts
check_dependency_conflicts() {
    print_status "Checking for dependency conflicts..."
    
    local conflicts_found=false
    local warning_packages=()
    
    # Check for conflicting AI/LLM packages that might cause issues
    local conflict_packages=(
        "openai==0.*"           # Old OpenAI versions
        "anthropic==0.2.*"      # Very old Anthropic versions
        "litellm==0.*"          # Old LiteLLM versions
        "langchain-core==0.0.*" # Very old LangChain versions
    )
    
    # Check for packages that might conflict with our dependencies
    for package in "${conflict_packages[@]}"; do
        local pkg_name="${package%%==*}"  # Extract package name before ==
        
        if python3 -m pip show "$pkg_name" >/dev/null 2>&1; then
            local installed_version
            installed_version=$(python3 -m pip show "$pkg_name" 2>/dev/null | grep "^Version:" | cut -d' ' -f2)
            
            # Check if this version might conflict
            case "$package" in
                "openai==0.*")
                    if [[ "$installed_version" =~ ^0\. ]]; then
                        warning_packages+=("$pkg_name ($installed_version) - recommend upgrading to 1.0+")
                        conflicts_found=true
                    fi
                    ;;
                "anthropic==0.2.*")
                    if [[ "$installed_version" =~ ^0\.2\. ]]; then
                        warning_packages+=("$pkg_name ($installed_version) - recommend upgrading to 0.3+")
                        conflicts_found=true
                    fi
                    ;;
                "litellm==0.*")
                    if [[ "$installed_version" =~ ^0\. ]]; then
                        warning_packages+=("$pkg_name ($installed_version) - recommend upgrading to 1.0+")
                        conflicts_found=true
                    fi
                    ;;
                "langchain-core==0.0.*")
                    if [[ "$installed_version" =~ ^0\.0\. ]]; then
                        warning_packages+=("$pkg_name ($installed_version) - may cause import conflicts")
                        conflicts_found=true
                    fi
                    ;;
            esac
        fi
    done
    
    # Check for virtual environment conflicts if not using pipx
    if [[ "$VIRTUAL_ENV" != "" ]] && ! command_exists pipx; then
        print_warning "Active virtual environment detected: $VIRTUAL_ENV"
        echo "Consider using pipx for global installation or deactivate venv first"
    fi
    
    if [ "$conflicts_found" = true ]; then
        print_warning "Potential dependency conflicts detected:"
        for warning in "${warning_packages[@]}"; do
            echo "  ⚠️  $warning"
        done
        echo
        echo "These packages may cause compatibility issues. Consider upgrading them:"
        for warning in "${warning_packages[@]}"; do
            local pkg_name="${warning%% (*}"  # Extract package name before space
            echo "  pip install --upgrade $pkg_name"
        done
        echo
        echo -n "Continue anyway? [y/N]: "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Installation cancelled. Please resolve conflicts first."
            exit 1
        fi
    else
        print_success "No dependency conflicts detected"
    fi
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
    local ttt_function="function ttt() { (cd $AI_DIR && source .venv/bin/activate && python -m ai \"\$@\"); }"
    local ai_path_export="export PATH=\"$VENV_DIR/bin:\$PATH\""
    local ai_comment="# AI Library Integration"
    
    # Remove existing entries
    clean_shell_rc
    
    # Add new entries
    echo "" >> "$SHELL_RC"
    echo "$ai_comment" >> "$SHELL_RC"
    echo "$ai_path_export" >> "$SHELL_RC"
    echo "$ttt_function" >> "$SHELL_RC"
    
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

# Upgrade function
upgrade() {
    echo
    echo -e "${BLUE}🔄 AI Library Upgrader${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    
    # Check Python version first
    check_python_version
    echo
    
    # Check for dependency conflicts
    check_dependency_conflicts
    echo
    
    # Check if installed via pipx
    if command_exists pipx && pipx list | grep -q "^  package ai "; then
        print_status "Upgrading pipx installation..."
        if pipx upgrade ai; then
            print_success "AI library upgraded successfully via pipx!"
        else
            print_error "pipx upgrade failed"
            exit 1
        fi
    else
        print_warning "No pipx installation found"
        echo "Upgrade is only supported for pipx installations"
        echo "For other installation methods, please uninstall and reinstall:"
        echo "  $0 uninstall"
        echo "  $0 install"
        exit 1
    fi
    
    echo
    echo -e "${GREEN}🎉 Upgrade Complete!${NC}"
    echo
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "1. 🧪 Test the upgrade: ${YELLOW}ttt 'What is 2+2?'${NC}"
    echo -e "2. 🔍 Check version: ${YELLOW}ttt --version${NC}"
    echo
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Ready to continue with AI! 🤖${NC}"
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
    
    # Check Python version first
    check_python_version
    echo
    
    # Check for dependency conflicts
    check_dependency_conflicts
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
        echo -e "2. 🧪 Test it out: ${YELLOW}ttt 'What is 2+2?'${NC}"
        echo
        if [[ "$dev_mode" == "true" ]]; then
            echo -e "${GREEN}Development mode:${NC}"
            echo "  ✅ Live file editing (changes reflect immediately)"
            echo "  ✅ No need to reinstall after code changes"
        else
            echo -e "${GREEN}pipx provides:${NC}"
            echo "  ✅ Isolated virtual environment"
        fi
        echo "  ✅ Global 'ttt' command"
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
    echo -e "  ${YELLOW}ttt${NC} 'Explain quantum computing'"
    echo -e "  ${YELLOW}echo 'Hello world' | ttt${NC}"
    echo -e "  ${YELLOW}git diff | ttt 'Explain changes'${NC}"
    echo -e "  ${YELLOW}ttt${NC} status"
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
        
        # Remove global binaries (both old 'ai' and new 'ttt')
        if [[ -f "$HOME/.local/bin/ai" ]]; then
            rm -f "$HOME/.local/bin/ai"
            print_success "Removed old 'ai' binary"
        fi
        if [[ -f "$HOME/.local/bin/ttt" ]]; then
            rm -f "$HOME/.local/bin/ttt"
            print_success "Removed 'ttt' binary"
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
    echo -e "3. 🧪 Test it out: ${YELLOW}ttt 'What is 2+2?'${NC}"
}

# Test installation
test_installation() {
    print_status "Testing AI installation..."
    
    if [[ -f "$API_KEY_FILE" ]]; then
        source "$API_KEY_FILE" 2>/dev/null || true
    fi
    
    echo "Running: ttt status"
    ttt status || {
        print_warning "CLI test failed - make sure to add API keys to $API_KEY_FILE"
    }
}


# Usage function
usage() {
    echo "AI Library Setup Script"
    echo
    echo "Usage: $0 {install|install --dev|upgrade|uninstall|help}"
    echo
    echo "Commands:"
    echo "  install        Install the AI library and CLI"
    echo "  install --dev  Install in development mode (editable)"
    echo "  upgrade        Upgrade existing installation to latest version"
    echo "  uninstall      Remove the AI library and CLI"
    echo "  help           Show this help message"
    echo
    echo "After installation, use:"
    echo "  ttt 'Your question here'  # Clean output with minimal logging"
    echo "  ttt --help               # Show available options"
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
    upgrade)
        upgrade
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