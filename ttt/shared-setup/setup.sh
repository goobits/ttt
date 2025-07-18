#!/bin/bash
# Generic Setup Framework for Python Projects
# This script provides a robust, performant setup system with extensive validation

set -e

# Enable performance optimizations
export LC_ALL=C
export LANG=C

# Core configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"  # Go up two levels: shared-setup -> ttt -> project root
readonly CONFIG_FILE="$PROJECT_DIR/setup-config.yaml"
readonly CACHE_DIR="$HOME/.cache/setup-framework"
readonly CACHE_FILE="$CACHE_DIR/system-info.cache"
readonly CACHE_TTL=3600  # 1 hour in seconds

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Create cache directory if it doesn't exist
mkdir -p "$CACHE_DIR"

# Function to get cached system information
get_cached_value() {
    local key="$1"
    local current_time=$(date +%s)
    
    if [[ -f "$CACHE_FILE" ]]; then
        local cache_time=$(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)
        local age=$((current_time - cache_time))
        
        if [[ $age -lt $CACHE_TTL ]]; then
            grep "^$key=" "$CACHE_FILE" 2>/dev/null | cut -d'=' -f2- || true
        fi
    fi
}

# Function to set cached value
set_cached_value() {
    local key="$1"
    local value="$2"
    
    # Remove old value if exists
    if [[ -f "$CACHE_FILE" ]]; then
        grep -v "^$key=" "$CACHE_FILE" > "$CACHE_FILE.tmp" 2>/dev/null || true
        mv "$CACHE_FILE.tmp" "$CACHE_FILE"
    fi
    
    # Add new value
    echo "$key=$value" >> "$CACHE_FILE"
}

# Parse YAML configuration
parse_yaml() {
    local yaml_file="$1"
    local prefix="${2:-}"
    
    # Use a simple grep/sed approach for basic YAML parsing
    # This avoids complex Python escaping issues
    
    # Parse top-level key-value pairs
    while IFS= read -r line; do
        if [[ "$line" =~ ^([a-zA-Z_][a-zA-Z0-9_]*):\ *\"?([^\"]*)\"?$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            value="${value%\"}"  # Remove trailing quote if present
            value="${value#\"}"  # Remove leading quote if present
            
            if [[ -n "$value" && ! "$value" =~ ^[[:space:]]*$ ]]; then
                if [[ -n "$prefix" ]]; then
                    export "${prefix}_${key}=${value}"
                else
                    export "${key}=${value}"
                fi
            fi
        fi
    done < "$yaml_file"
    
    # Parse nested values (one level deep) - specifically for python section
    local in_section=""
    while IFS= read -r line; do
        # Check for section headers
        if [[ "$line" =~ ^([a-zA-Z_][a-zA-Z0-9_]*):$ ]]; then
            in_section="${BASH_REMATCH[1]}"
        # Check for indented key-value pairs
        elif [[ -n "$in_section" && "$line" =~ ^[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*):\ *\"?([^\"]*)\"?$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            value="${value%\"}"  # Remove trailing quote if present
            value="${value#\"}"  # Remove leading quote if present
            
            if [[ -n "$value" && ! "$value" =~ ^[[:space:]]*$ ]]; then
                if [[ -n "$prefix" ]]; then
                    export "${prefix}_${in_section}_${key}=${value}"
                else
                    export "${in_section}_${key}=${value}"
                fi
            fi
        # Reset section if we hit a non-indented line
        elif [[ ! "$line" =~ ^[[:space:]] ]]; then
            in_section=""
        fi
    done < "$yaml_file"
}

# Load configuration
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    
    log_info "Loading configuration from $CONFIG_FILE"
    
    # Parse YAML and export variables
    parse_yaml "$CONFIG_FILE" "CONFIG"
    
    # Validate required configuration
    if [[ -z "${CONFIG_package_name:-}" ]]; then
        log_error "Missing required configuration: package_name"
        exit 1
    fi
}

# System requirement checks
check_python_version() {
    local required_version="${CONFIG_python_minimum_version:-3.8}"
    
    log_info "Checking Python version (required: >= $required_version)"
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        return 1
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= tuple(map(int, '$required_version'.split('.'))) else 1)"; then
        log_error "Python $python_version is installed, but >= $required_version is required"
        return 1
    fi
    
    log_success "Python $python_version meets requirements"
    return 0
}

check_pipx() {
    log_info "Checking for pipx installation"
    
    if ! command -v pipx &> /dev/null; then
        log_error "pipx is not installed"
        echo
        echo "pipx is required for clean, isolated installations."
        echo
        echo "To install pipx:"
        echo "  Option 1 (recommended):"
        echo "    python3 -m pip install --user pipx"
        echo "    python3 -m pipx ensurepath"
        echo
        echo "  Option 2 (Ubuntu/Debian):"
        echo "    sudo apt update"
        echo "    sudo apt install pipx"
        echo "    pipx ensurepath"
        echo
        echo "  Option 3 (macOS with Homebrew):"
        echo "    brew install pipx"
        echo "    pipx ensurepath"
        echo
        echo "After installation, restart your terminal or run:"
        echo "    source ~/.bashrc  # or ~/.zshrc"
        return 1
    fi
    
    # Check if pipx is in PATH
    if ! pipx --version &> /dev/null; then
        log_warning "pipx is installed but may not be in PATH"
        echo "Run: pipx ensurepath"
        echo "Then restart your terminal"
        return 1
    fi
    
    log_success "pipx is installed"
    return 0
}

check_git() {
    log_info "Checking for git"
    
    if ! command -v git &> /dev/null; then
        log_error "git is not installed"
        return 1
    fi
    
    log_success "git is installed"
    return 0
}

# Installation functions
install_with_pipx() {
    local dev_mode="${1:-false}"
    
    log_info "Installing ${CONFIG_package_name} with pipx"
    
    if ! check_pipx; then
        return 1
    fi
    
    # Check if already installed
    if pipx list | grep -q "${CONFIG_package_name}"; then
        log_warning "${CONFIG_package_name} is already installed with pipx"
        log_info "Use '$0 upgrade' to upgrade or '$0 uninstall' first"
        return 1
    fi
    
    # Install based on mode
    if [[ "$dev_mode" == "true" ]]; then
        log_info "Installing in development mode (editable)"
        # For development mode, check if we need to use parent directory
        local install_dir="$PROJECT_DIR"
        if [[ ! -f "$PROJECT_DIR/pyproject.toml" && ! -f "$PROJECT_DIR/setup.py" ]]; then
            # Check parent directory
            local parent_dir="$(dirname "$PROJECT_DIR")"
            if [[ -f "$parent_dir/pyproject.toml" || -f "$parent_dir/setup.py" ]]; then
                install_dir="$parent_dir"
                log_info "Using parent directory for installation: $install_dir"
            fi
        fi
        
        if ! pipx install --editable "$install_dir" 2>&1 | tee /tmp/pipx_install_dev.log; then
            log_error "Failed to install ${CONFIG_package_name} in development mode"
            
            # Check for common development installation errors
            if grep -q "does not appear to be a Python project" /tmp/pipx_install_dev.log; then
                echo
                log_error "Not a valid Python project"
                echo "Make sure the directory contains one of:"
                echo "  - pyproject.toml"
                echo "  - setup.py"
                echo "  - setup.cfg"
                echo
                echo "Current directory: $install_dir"
                if [[ -f "$install_dir/pyproject.toml" ]]; then
                    log_success "Found pyproject.toml"
                else
                    log_warning "No pyproject.toml found"
                fi
            elif grep -q "ModuleNotFoundError\|ImportError" /tmp/pipx_install_dev.log; then
                echo
                log_error "Missing dependencies detected"
                echo "Try installing dependencies first:"
                echo "  cd $install_dir"
                echo "  pip install -e ."
            fi
            
            rm -f /tmp/pipx_install_dev.log
            return 1
        fi
        rm -f /tmp/pipx_install_dev.log
    else
        log_info "Installing from PyPI"
        
        # First check if package exists on PyPI
        log_info "Checking if '${CONFIG_package_name}' is available on PyPI..."
        
        # Use pip index to check if package exists
        if ! pip index versions "${CONFIG_package_name}" &>/dev/null; then
            log_warning "Package '${CONFIG_package_name}' not found on PyPI"
            echo
            echo "This package hasn't been published to PyPI yet."
            echo "For local development, use:"
            echo
            echo "    ./setup.sh install --dev"
            echo
            echo "This will install from your local source code in editable mode."
            return 1
        fi
        
        log_success "Package found on PyPI"
        
        # Run pipx and capture both output and exit code
        pipx_output_file="/tmp/pipx_install_$$.log"
        pipx install "${CONFIG_package_name}" 2>&1 | tee "$pipx_output_file"
        pipx_exit_code=${PIPESTATUS[0]}
        
        if [[ $pipx_exit_code -ne 0 ]]; then
            log_error "Failed to install ${CONFIG_package_name} from PyPI"
            
            # Read the output for error checking
            pipx_output=$(cat "$pipx_output_file")
            
            # Check for common errors and provide helpful suggestions
            if echo "$pipx_output" | grep -q "No matching distribution found\|Could not find a version"; then
                echo
                log_warning "Package '${CONFIG_package_name}' not found on PyPI"
                echo
                echo "This usually means one of the following:"
                echo "  1. The package hasn't been published to PyPI yet"
                echo "  2. The package name is different on PyPI"
                echo "  3. You're developing locally"
                echo
                log_info "💡 For local development, use:"
                echo "     ./setup.sh install --dev"
                echo
                log_info "💡 To check if a package exists on PyPI:"
                echo "     pip index versions ${CONFIG_package_name}"
            elif echo "$pipx_output" | grep -q "pip is configured with locations that require TLS/SSL"; then
                echo
                log_error "SSL/TLS error detected"
                echo "Try updating certificates:"
                echo "  pip install --upgrade certifi"
            elif echo "$pipx_output" | grep -q "Permission denied"; then
                echo
                log_error "Permission error detected"
                echo "Try running pipx ensurepath first:"
                echo "  pipx ensurepath"
            fi
            
            rm -f "$pipx_output_file"
            return 1
        fi
        
        rm -f "$pipx_output_file"
        log_success "${CONFIG_package_name} installed successfully!"
    fi
    
    # Setup shell integration if configured
    if [[ "${CONFIG_shell_integration_enabled:-true}" == "true" ]]; then
        setup_shell_integration
    fi
    
    return 0
}

upgrade_with_pipx() {
    log_info "Upgrading ${CONFIG_package_name} with pipx"
    
    if ! check_pipx; then
        return 1
    fi
    
    # Check if installed
    if ! pipx list | grep -q "${CONFIG_package_name}"; then
        log_error "${CONFIG_package_name} is not installed with pipx"
        log_info "Use '$0 install' to install it first"
        return 1
    fi
    
    # Upgrade
    if ! pipx upgrade "${CONFIG_package_name}"; then
        log_error "Failed to upgrade ${CONFIG_package_name}"
        return 1
    fi
    
    log_success "${CONFIG_package_name} upgraded successfully!"
    return 0
}

uninstall_with_pipx() {
    log_info "Uninstalling ${CONFIG_package_name}"
    
    if ! check_pipx; then
        return 1
    fi
    
    # Check if installed
    if ! pipx list | grep -q "${CONFIG_package_name}"; then
        log_warning "${CONFIG_package_name} is not installed with pipx"
        return 0
    fi
    
    # Uninstall
    if ! pipx uninstall "${CONFIG_package_name}"; then
        log_error "Failed to uninstall ${CONFIG_package_name}"
        return 1
    fi
    
    log_success "${CONFIG_package_name} uninstalled successfully!"
    
    # Remove shell integration if configured
    if [[ "${CONFIG_shell_integration_enabled:-true}" == "true" ]]; then
        remove_shell_integration
    fi
    
    return 0
}

# Shell integration functions
get_shell_config_file() {
    local shell_name="${SHELL##*/}"
    
    case "$shell_name" in
        bash)
            if [[ -f "$HOME/.bashrc" ]]; then
                echo "$HOME/.bashrc"
            elif [[ -f "$HOME/.bash_profile" ]]; then
                echo "$HOME/.bash_profile"
            fi
            ;;
        zsh)
            if [[ -f "$HOME/.zshrc" ]]; then
                echo "$HOME/.zshrc"
            fi
            ;;
        fish)
            if [[ -d "$HOME/.config/fish" ]]; then
                echo "$HOME/.config/fish/config.fish"
            fi
            ;;
        *)
            log_warning "Unknown shell: $shell_name"
            ;;
    esac
}

setup_shell_integration() {
    log_info "Setting up shell integration"
    
    local shell_config=$(get_shell_config_file)
    
    if [[ -z "$shell_config" ]]; then
        log_warning "Could not determine shell configuration file"
        return 0
    fi
    
    local integration_marker="# ${CONFIG_package_name} shell integration"
    
    # Check if already configured
    if grep -q "$integration_marker" "$shell_config" 2>/dev/null; then
        log_info "Shell integration already configured"
        return 0
    fi
    
    # Add integration based on configuration
    if [[ -n "${CONFIG_shell_integration_alias:-}" ]]; then
        echo "" >> "$shell_config"
        echo "$integration_marker" >> "$shell_config"
        echo "alias ${CONFIG_shell_integration_alias}='${CONFIG_package_name}'" >> "$shell_config"
        echo "$integration_marker end" >> "$shell_config"
        
        log_success "Added shell alias: ${CONFIG_shell_integration_alias}"
        log_info "Run 'source $shell_config' or start a new shell to use the alias"
    fi
}

remove_shell_integration() {
    log_info "Removing shell integration"
    
    local shell_config=$(get_shell_config_file)
    
    if [[ -z "$shell_config" ]] || [[ ! -f "$shell_config" ]]; then
        return 0
    fi
    
    local integration_marker="# ${CONFIG_package_name} shell integration"
    
    # Remove integration block
    if grep -q "$integration_marker" "$shell_config" 2>/dev/null; then
        # Create backup
        cp "$shell_config" "$shell_config.backup"
        
        # Remove the integration block
        awk "
            /$integration_marker\$/ { skip = 1 }
            /$integration_marker end/ { skip = 0; next }
            !skip { print }
        " "$shell_config.backup" > "$shell_config"
        
        log_success "Removed shell integration"
    fi
}

# Command handlers
cmd_install() {
    local dev_mode=false
    
    # Parse install options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dev)
                dev_mode=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Run system checks
    check_python_version || exit 1
    check_git || exit 1
    
    # Perform installation
    install_with_pipx "$dev_mode"
}

cmd_upgrade() {
    upgrade_with_pipx
}

cmd_uninstall() {
    uninstall_with_pipx
}

cmd_status() {
    log_info "Checking ${CONFIG_package_name} installation status"
    
    # Check pipx installation
    if pipx list 2>/dev/null | grep -q "${CONFIG_package_name}"; then
        log_success "${CONFIG_package_name} is installed via pipx"
        
        # Get version if available
        if command -v "${CONFIG_package_name}" &> /dev/null; then
            local version=$("${CONFIG_package_name}" --version 2>/dev/null || echo "unknown")
            log_info "Version: $version"
        fi
    else
        log_info "${CONFIG_package_name} is not installed via pipx"
    fi
    
    # Check command availability
    if command -v "${CONFIG_package_name}" &> /dev/null; then
        log_success "Command '${CONFIG_package_name}' is available in PATH"
    else
        log_warning "Command '${CONFIG_package_name}' is not in PATH"
    fi
}

# Show usage information
show_usage() {
    cat << EOF
Usage: ./setup.sh [COMMAND] [OPTIONS]

Commands:
    install       Install ${CONFIG_package_name:-the package} with pipx
    install --dev Install in development mode (editable)
    upgrade       Upgrade to the latest version
    uninstall     Remove the installation
    status        Check installation status
    help          Show this help message

Examples:
    ./setup.sh install              # Install from PyPI
    ./setup.sh install --dev        # Install in development mode
    ./setup.sh upgrade              # Upgrade to latest version
    ./setup.sh uninstall            # Remove installation
    ./setup.sh status               # Check if installed

EOF
}

# Main execution
main() {
    # Load configuration first
    load_config
    
    # Default to showing usage if no command given
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 0
    fi
    
    # Parse command
    case "$1" in
        install)
            shift
            cmd_install "$@"
            ;;
        upgrade)
            shift
            cmd_upgrade "$@"
            ;;
        uninstall)
            shift
            cmd_uninstall "$@"
            ;;
        status)
            shift
            cmd_status "$@"
            ;;
        help|--help|-h)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"