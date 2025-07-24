#!/bin/bash
# Generic Setup Framework for Python Projects
# This script provides a robust, performant setup system with extensive validation

set -e

# Enable performance optimizations
export LC_ALL=C
export LANG=C

# Prevent Python bytecode generation during development
export PYTHONDONTWRITEBYTECODE=1

# Core configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Since this is a generated script, PROJECT_DIR is where the script lives
readonly PROJECT_DIR="$SCRIPT_DIR"
readonly CACHE_DIR="$HOME/.cache/setup-framework"
readonly CACHE_FILE="$CACHE_DIR/system-info.cache"
readonly CACHE_TTL=3600  # 3600 in seconds

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Tree view components
readonly TREE_BRANCH="├─"
readonly TREE_LAST="└─"
readonly TREE_PIPE="│ "
readonly TREE_SPACE="  "

# Tree view state
TREE_MODE="${TREE_MODE:-false}"
TREE_DEPTH=0
TREE_PREFIX=""
TREE_BUFFER=""

# Check if terminal supports colors
if [[ -t 1 ]] && [[ "$(tput colors 2>/dev/null)" -ge 8 ]]; then
    USE_COLOR=true
else
    USE_COLOR=false
fi

# Project-specific configuration
readonly PACKAGE_NAME="goobits-ttt"
readonly COMMAND_NAME="ttt"
readonly DISPLAY_NAME="TTT - Terminal Tools for Thoughts"
readonly DESCRIPTION="A powerful AI assistant for your terminal"
readonly PYPI_NAME="goobits-ttt"
readonly DEVELOPMENT_PATH="."
readonly REQUIRED_VERSION="3.8"
readonly MAXIMUM_VERSION="3.13"
readonly CHECK_API_KEYS="False"
readonly CHECK_DISK_SPACE="True"
readonly REQUIRED_MB="100"
readonly SHELL_INTEGRATION="False"
readonly SHELL_ALIAS="ttt"

# Dependencies
readonly REQUIRED_DEPS=("git" "pipx")
readonly OPTIONAL_DEPS=("curl" "wget")

# Tree view helper functions
tree_start() {
    local title="$1"
    echo "$DISPLAY_NAME Setup $(get_version)"
    echo "$TREE_LAST $title"
    TREE_DEPTH=1
    TREE_PREFIX="   "
}

tree_node() {
    local status="$1"
    local message="$2"
    local is_last="${3:-false}"
    
    local status_icon
    case "$status" in
        "success") status_icon="✓" ;;
        "warning") status_icon="⚠" ;;
        "error") status_icon="✗" ;;
        "info") status_icon="•" ;;
        *) status_icon="" ;;
    esac
    
    if [[ "$is_last" == "true" ]]; then
        echo "${TREE_PREFIX}$TREE_LAST $status_icon $message"
    else
        echo "${TREE_PREFIX}$TREE_BRANCH $status_icon $message"
    fi
}

tree_sub_node() {
    local status="$1"
    local message="$2"
    local is_last="${3:-false}"
    
    local status_icon
    case "$status" in
        "success") status_icon="✓" ;;
        "warning") status_icon="⚠" ;;
        "error") status_icon="✗" ;;
        "info") status_icon="•" ;;
        *) status_icon="" ;;
    esac
    
    local sub_prefix="${TREE_PREFIX}$TREE_PIPE "
    if [[ "$is_last" == "true" ]]; then
        echo "${sub_prefix}$TREE_LAST $status_icon $message"
    else
        echo "${sub_prefix}$TREE_BRANCH $status_icon $message"
    fi
}

tree_final_node() {
    local status="$1"
    local message="$2"
    
    local status_icon
    case "$status" in
        "success") status_icon="✓" ;;
        "warning") status_icon="⚠" ;;
        "error") status_icon="✗" ;;
        "info") status_icon="•" ;;
        *) status_icon="" ;;
    esac
    
    echo "${TREE_PREFIX}$TREE_LAST $status_icon $message"
}

get_version() {
    # Try to extract version from various sources
    local version=""
    if command -v "$COMMAND_NAME" >/dev/null 2>&1; then
        version=$("$COMMAND_NAME" --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+[^ ]*' | head -1)
    fi
    if [[ -n "$version" ]]; then
        echo "v$version"
    else
        echo ""
    fi
}

# Logging functions (original + tree mode support)
log_info() {
    if [[ "$TREE_MODE" == "true" ]]; then
        return  # Tree mode handles its own output
    fi
    if [[ "$USE_COLOR" == "true" ]]; then
        echo -e "${BLUE}[INFO]${NC} $*" >&2
    else
        echo "[INFO] $*" >&2
    fi
}

log_success() {
    if [[ "$TREE_MODE" == "true" ]]; then
        return  # Tree mode handles its own output
    fi
    if [[ "$USE_COLOR" == "true" ]]; then
        echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
    else
        echo "[SUCCESS] $*" >&2
    fi
}

log_warning() {
    if [[ "$TREE_MODE" == "true" ]]; then
        return  # Tree mode handles its own output
    fi
    if [[ "$USE_COLOR" == "true" ]]; then
        echo -e "${YELLOW}[WARNING]${NC} $*" >&2
    else
        echo "[WARNING] $*" >&2
    fi
}

log_error() {
    if [[ "$TREE_MODE" == "true" ]]; then
        return  # Tree mode handles its own output
    fi
    if [[ "$USE_COLOR" == "true" ]]; then
        echo -e "${RED}[ERROR]${NC} $*" >&2
    else
        echo "[ERROR] $*" >&2
    fi
}

# Spinner for long-running operations
show_spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while ps -p "$pid" > /dev/null 2>&1; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# System information cache
get_cached_system_info() {
    if [[ -f "$CACHE_FILE" ]]; then
        local cache_age=$(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)))
        if [[ $cache_age -lt $CACHE_TTL ]]; then
            source "$CACHE_FILE"
            return 0
        fi
    fi
    return 1
}

cache_system_info() {
    mkdir -p "$CACHE_DIR"
    cat > "$CACHE_FILE" << EOF
SYSTEM_OS="$SYSTEM_OS"
SYSTEM_ARCH="$SYSTEM_ARCH"
PYTHON_VERSION="$PYTHON_VERSION"
PYTHON_PATH="$PYTHON_PATH"
PIPX_AVAILABLE="$PIPX_AVAILABLE"
PIPX_PATH="$PIPX_PATH"
EOF
}

detect_system() {
    if ! get_cached_system_info; then
        if [[ "$TREE_MODE" != "true" ]]; then
            log_info "Detecting system configuration..."
        fi
        
        # Detect OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            SYSTEM_OS="linux"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            SYSTEM_OS="macos"
        elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
            SYSTEM_OS="windows"
        else
            SYSTEM_OS="unknown"
        fi
        
        # Detect architecture
        SYSTEM_ARCH="$(uname -m)"
        
        # Detect Python
        if command -v python3 >/dev/null 2>&1; then
            PYTHON_PATH="$(command -v python3)"
            PYTHON_VERSION="$(python3 --version 2>&1 | cut -d' ' -f2)"
        elif command -v python >/dev/null 2>&1; then
            PYTHON_PATH="$(command -v python)"
            PYTHON_VERSION="$(python --version 2>&1 | cut -d' ' -f2)"
        else
            PYTHON_PATH=""
            PYTHON_VERSION=""
        fi
        
        # Detect pipx
        if command -v pipx >/dev/null 2>&1; then
            PIPX_AVAILABLE="true"
            PIPX_PATH="$(command -v pipx)"
        else
            PIPX_AVAILABLE="false"
            PIPX_PATH=""
        fi
        
        cache_system_info
    fi
}

# Version comparison function
version_compare() {
    local version1=$1
    local version2=$2
    
    # Convert versions to arrays
    IFS='.' read -ra v1_parts <<< "$(echo "$version1" | sed 's/[^0-9.]*//g')"
    IFS='.' read -ra v2_parts <<< "$(echo "$version2" | sed 's/[^0-9.]*//g')"
    
    # Pad arrays to same length
    local max_parts=3
    for ((i=${#v1_parts[@]}; i<$max_parts; i++)); do
        v1_parts[i]=0
    done
    for ((i=${#v2_parts[@]}; i<$max_parts; i++)); do
        v2_parts[i]=0
    done
    
    # Compare each part
    for ((i=0; i<$max_parts; i++)); do
        # Force base 10 to avoid octal interpretation
        local p1=$((10#${v1_parts[i]:-0}))
        local p2=$((10#${v2_parts[i]:-0}))
        
        if [[ $p1 -lt $p2 ]]; then
            return 1  # version1 < version2
        elif [[ $p1 -gt $p2 ]]; then
            return 2  # version1 > version2
        fi
    done
    
    return 0  # version1 == version2
}

validate_python() {
    if [[ -z "$PYTHON_PATH" ]]; then
        log_error "Python is not installed or not found in PATH"
        log_error "Please install Python $REQUIRED_VERSION or later"
        return 1
    fi
    
    if [[ "$TREE_MODE" != "true" ]]; then
        log_info "Found Python $PYTHON_VERSION at $PYTHON_PATH"
    fi
    
    # Check minimum version
    version_compare "$PYTHON_VERSION" "$REQUIRED_VERSION"
    case $? in
        1)  # Current version is less than required
            log_error "Python $PYTHON_VERSION is installed, but $REQUIRED_VERSION or later is required"
            return 1
            ;;
        0|2)  # Current version is equal or greater than required
            if [[ "$TREE_MODE" != "true" ]]; then
                log_success "Python version requirement satisfied"
            fi
            ;;
    esac
    
    # Check maximum version if specified
    if [[ -n "$MAXIMUM_VERSION" ]]; then
        version_compare "$PYTHON_VERSION" "$MAXIMUM_VERSION"
        case $? in
            2)  # Current version is greater than maximum
                log_error "Python $PYTHON_VERSION is installed, but maximum supported version is $MAXIMUM_VERSION"
                return 1
                ;;
            0|1)  # Current version is equal or less than maximum
                log_success "Python maximum version requirement satisfied"
                ;;
        esac
    fi
    
    return 0
}

# Tree mode versions of validation functions
validate_python_tree() {
    if [[ -z "$PYTHON_PATH" ]]; then
        tree_sub_node "error" "Python not found in PATH" "true"
        return 1
    fi
    
    # Check minimum version
    version_compare "$PYTHON_VERSION" "$REQUIRED_VERSION"
    case $? in
        1)  # Current version is less than required
            tree_sub_node "error" "Python $PYTHON_VERSION < $REQUIRED_VERSION (required)" "true"
            return 1
            ;;
        0|2)  # Current version is equal or greater than required
            return 0
            ;;
    esac
}

validate_dependencies_tree() {
    local missing_deps=()
    local optional_missing=()
    
    # Check required dependencies
    for dep in "${REQUIRED_DEPS[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing_deps+=("$dep")
        fi
    done
    
    # Check optional dependencies
    for dep in "${OPTIONAL_DEPS[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            optional_missing+=("$dep")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        tree_sub_node "error" "Missing required: ${missing_deps[*]}" "true"
        return 1
    fi
    
    if [[ ${#optional_missing[@]} -gt 0 ]]; then
        tree_sub_node "warning" "${optional_missing[*]} (optional)" "true"
    fi
    
    return 0
}

validate_pipx() {
    if [[ "$PIPX_AVAILABLE" != "true" ]]; then
        log_warning "pipx is not installed. Installing pipx is recommended for isolated Python applications."
        log_info "You can install pipx with: python3 -m pip install --user pipx"
        log_info "Or on macOS with Homebrew: brew install pipx"
        return 1
    fi
    
    log_success "pipx is available at $PIPX_PATH"
    return 0
}

validate_disk_space() {
    if [[ "$CHECK_DISK_SPACE" != "true" ]]; then
        return 0
    fi
    
    local available_mb
    if command -v df >/dev/null 2>&1; then
        available_mb=$(df "$PROJECT_DIR" | awk 'NR==2 {print int($4/1024)}')
        
        if [[ $available_mb -lt $REQUIRED_MB ]]; then
            log_error "Insufficient disk space. Required: ${REQUIRED_MB}MB, Available: ${available_mb}MB"
            return 1
        fi
        
        log_success "Disk space check passed (${available_mb}MB available)"
    else
        log_warning "Cannot check disk space (df command not available)"
    fi
    
    return 0
}

validate_dependencies() {
    local missing_deps=()
    local optional_missing=()
    
    # Check required dependencies
    for dep in "${REQUIRED_DEPS[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing_deps+=("$dep")
        fi
    done
    
    # Check optional dependencies
    for dep in "${OPTIONAL_DEPS[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            optional_missing+=("$dep")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Please install the missing dependencies and try again"
        return 1
    fi
    
    if [[ ${#optional_missing[@]} -gt 0 ]]; then
        log_warning "Missing optional dependencies: ${optional_missing[*]}"
        log_warning "Some features may not be available"
    fi
    
    if [[ "$TREE_MODE" != "true" ]]; then
        log_success "Dependency check completed"
    fi
    return 0
}

# Installation functions
install_package() {
    local install_dev="$1"
    
    if [[ "$PIPX_AVAILABLE" == "true" ]]; then
        install_with_pipx "$install_dev"
    else
        install_with_pip "$install_dev"
    fi
}

install_with_pipx() {
    local install_dev="$1"
    
    if [[ "$install_dev" == "true" ]]; then
        log_info "Installing $DISPLAY_NAME in development mode with pipx..."
        (cd "$PROJECT_DIR" && pipx install --editable "$DEVELOPMENT_PATH" --force) &
        show_spinner $!
        wait $!
        
        if [[ $? -eq 0 ]]; then
            log_success "Development installation completed!"
            show_dev_success_message
        else
            log_error "Development installation failed"
            return 1
        fi
    else
        log_info "Installing $DISPLAY_NAME with pipx..."
        pipx install "$PYPI_NAME" --force &
        show_spinner $!
        wait $!
        
        if [[ $? -eq 0 ]]; then
            log_success "Installation completed!"
            show_install_success_message
        else
            log_error "Installation failed"
            return 1
        fi
    fi
}

install_with_pip() {
    local install_dev="$1"
    
    log_warning "Using pip instead of pipx (not recommended for applications)"
    
    if [[ "$install_dev" == "true" ]]; then
        log_info "Installing $DISPLAY_NAME in development mode with pip..."
        (cd "$PROJECT_DIR" && python3 -m pip install --editable "$DEVELOPMENT_PATH" --user) &
        show_spinner $!
        wait $!
        
        if [[ $? -eq 0 ]]; then
            log_success "Development installation completed!"
            show_dev_success_message
        else
            log_error "Development installation failed"
            return 1
        fi
    else
        log_info "Installing $DISPLAY_NAME with pip..."
        python3 -m pip install "$PYPI_NAME" --user &
        show_spinner $!
        wait $!
        
        if [[ $? -eq 0 ]]; then
            log_success "Installation completed!"
            show_install_success_message
        else
            log_error "Installation failed"
            return 1
        fi
    fi
}

upgrade_package() {
    if [[ "$PIPX_AVAILABLE" == "true" ]]; then
        # Check if package is installed via pipx
        if pipx list | grep -q "$PACKAGE_NAME"; then
            # Check if it's a local/development installation by looking at the package_or_url
            local package_info=$(pipx list --json 2>/dev/null)
            if echo "$package_info" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    pkg_data = data.get('venvs', {}).get('$PACKAGE_NAME', {})
    pkg_url = pkg_data.get('metadata', {}).get('main_package', {}).get('package_or_url', '')
    # Check if it's a local path (not from PyPI)
    if pkg_url and not pkg_url.startswith('$PACKAGE_NAME') and '/' in pkg_url:
        sys.exit(0)  # It's a local installation
    else:
        sys.exit(1)  # It's from PyPI
except:
    sys.exit(1)
" 2>/dev/null; then
                if [[ "$TREE_MODE" == "true" ]]; then
                    tree_sub_node "info" "Detected local/development installation"
                    tree_sub_node "info" "Reinstalling from local directory..."
                else
                    log_info "Detected local/development installation."
                    log_info "Reinstalling from local directory to update dependencies..."
                fi
                
                # Capture output for tree mode
                local output
                if [[ "$TREE_MODE" == "true" ]]; then
                    output=$(pipx install --force --editable "$PROJECT_DIR" 2>&1)
                    local exit_code=$?
                    
                    # Parse output for version info
                    local version_info=$(echo "$output" | grep -E '(already at latest|installed|upgraded)' | head -1)
                    if [[ -n "$version_info" ]]; then
                        tree_sub_node "success" "$version_info" "true"
                    else
                        tree_sub_node "success" "Reinstalled successfully" "true"
                    fi
                else
                    pipx install --force --editable "$PROJECT_DIR" &
                    show_spinner $!
                    wait $!
                    local exit_code=$?
                fi
            else
                # Regular PyPI installation
                if [[ "$TREE_MODE" == "true" ]]; then
                    # Capture pipx upgrade output to parse version info
                    local output
                    output=$(pipx upgrade "$PACKAGE_NAME" 2>&1)
                    local exit_code=$?
                    
                    # Parse the output to extract version information
                    local version_info=$(echo "$output" | grep -E '(already at latest version|upgraded|installed)' | head -1)
                    if [[ -n "$version_info" ]]; then
                        # Clean up the version info message and truncate if too long
                        version_info=$(echo "$version_info" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' | cut -c1-50)
                        tree_sub_node "success" "$version_info" "true"
                    else
                        tree_sub_node "success" "Upgrade completed" "true"
                    fi
                else
                    log_info "Upgrading $DISPLAY_NAME with pipx..."
                    pipx upgrade "$PACKAGE_NAME" &
                    show_spinner $!
                    wait $!
                    local exit_code=$?
                fi
            fi
        else
            if [[ "$TREE_MODE" == "true" ]]; then
                tree_sub_node "error" "Package '$PACKAGE_NAME' not found in pipx installations" "true"
            else
                log_error "Package '$PACKAGE_NAME' not found in pipx installations."
                log_error "Please install first with: $0 install"
            fi
            return 1
        fi
    else
        if [[ "$TREE_MODE" == "true" ]]; then
            local output
            output=$(python3 -m pip install --upgrade "$PYPI_NAME" --user 2>&1)
            local exit_code=$?
            
            # Parse pip output for version info
            local version_info=$(echo "$output" | grep -E '(already satisfied|successfully installed)' | head -1)
            if [[ -n "$version_info" ]]; then
                tree_sub_node "success" "$(echo "$version_info" | sed 's/^[[:space:]]*//')" "true"
            else
                tree_sub_node "success" "Upgrade completed" "true"
            fi
        else
            log_info "Upgrading $DISPLAY_NAME with pip..."
            python3 -m pip install --upgrade "$PYPI_NAME" --user &
            show_spinner $!
            wait $!
            local exit_code=$?
        fi
    fi
    
    if [[ ${exit_code:-$?} -eq 0 ]]; then
        if [[ "$TREE_MODE" != "true" ]]; then
            log_success "Upgrade completed!"
        fi
        show_upgrade_success_message
    else
        if [[ "$TREE_MODE" == "true" ]]; then
            tree_sub_node "error" "Upgrade failed" "true"
        else
            log_error "Upgrade failed"
        fi
        return 1
    fi
}

uninstall_package() {
    if [[ "$PIPX_AVAILABLE" == "true" ]]; then
        log_info "Uninstalling $DISPLAY_NAME with pipx..."
        pipx uninstall "$PYPI_NAME" &
        show_spinner $!
        wait $!
    else
        log_info "Uninstalling $DISPLAY_NAME with pip..."
        python3 -m pip uninstall "$PYPI_NAME" -y &
        show_spinner $!
        wait $!
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Uninstall completed!"
        show_uninstall_success_message
    else
        log_error "Uninstall failed"
        return 1
    fi
}

# Message display functions
show_install_success_message() {
    echo
    echo "TTT has been installed successfully!
You can now use 'ttt' or 't' (if shell integration is enabled) from your terminal.

Quick start:
  ttt "Hello, how can I help you today?"
  ttt status
  ttt models
"
    echo
}

show_dev_success_message() {
    echo
    echo "TTT has been installed in development mode!
✅ Your local changes will be reflected immediately - no reinstalling needed!

Development workflow:
  - Edit code in src/ttt/ directory
  - Test immediately with: ttt --stream "test"  
  - Run tests with: ./test.sh
  - Format code with: ruff format src/ttt/
  - Check types with: mypy src/ttt/
  
💡 No need to run ./setup.sh upgrade after code changes!
"
    echo
}

show_upgrade_success_message() {
    echo
    echo "TTT has been upgraded successfully!
Check out the latest features with: ttt --version
"
    echo
}

show_uninstall_success_message() {
    echo
    echo "TTT has been uninstalled.
Thank you for using TTT!
"
    echo
}

# Shell integration
setup_shell_integration() {
    if [[ "$SHELL_INTEGRATION" != "true" ]]; then
        return 0
    fi
    
    log_info "Setting up shell integration..."
    
    # Add alias to shell configuration files
    local shell_configs=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile")
    local alias_line="alias $SHELL_ALIAS='$COMMAND_NAME'"
    
    for config in "${shell_configs[@]}"; do
        if [[ -f "$config" ]] && ! grep -q "alias $SHELL_ALIAS=" "$config"; then
            echo "$alias_line" >> "$config"
            log_info "Added alias to $config"
        fi
    done
    
    log_success "Shell integration configured"
}

# Help and usage
show_help() {
    cat << EOF
$DISPLAY_NAME Setup Framework

DESCRIPTION:
    $DESCRIPTION

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    install                 Install $DISPLAY_NAME from PyPI
    install --dev          Install $DISPLAY_NAME in development mode
    upgrade                Upgrade $DISPLAY_NAME to the latest version
    uninstall              Uninstall $DISPLAY_NAME
    validate               Validate system requirements without installing
    help                   Show this help message

OPTIONS:
    --force                Skip confirmation prompts
    --no-deps              Skip dependency checks
    --no-cache             Skip system information caching
    --tree                 Use compact tree view output

EXAMPLES:
    $0 install             # Install from PyPI
    $0 install --dev       # Development installation
    $0 upgrade             # Upgrade to latest version
    $0 validate            # Check requirements

For more information, visit the project documentation.
EOF
}

# Main execution
main() {
    local command="${1:-install}"
    local force_flag="false"
    local no_deps="false"
    local no_cache="false"
    local install_dev="false"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            install|upgrade|uninstall|validate|help)
                command="$1"
                ;;
            --dev)
                install_dev="true"
                ;;
            --force)
                force_flag="true"
                ;;
            --no-deps)
                no_deps="true"
                ;;
            --no-cache)
                no_cache="true"
                ;;
            --tree)
                TREE_MODE="true"
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done
    
    # Handle help command
    if [[ "$command" == "help" ]]; then
        show_help
        exit 0
    fi
    
    # Header
    if [[ "$TREE_MODE" == "true" ]]; then
        tree_start "${command^} Process"
    else
        echo
        log_info "Starting $DISPLAY_NAME setup..."
        echo
    fi
    
    # System detection
    if [[ "$no_cache" != "true" ]]; then
        detect_system
    fi
    
    # Validation
    if [[ "$command" != "uninstall" ]]; then
        if [[ "$TREE_MODE" == "true" ]]; then
            tree_node "info" "System Check"
            
            # Python validation
            if validate_python_tree; then
                tree_sub_node "success" "Python $PYTHON_VERSION"
            else
                exit 1
            fi
            
            # Dependencies validation
            if [[ "$no_deps" != "true" ]]; then
                if validate_dependencies_tree; then
                    : # Already handled in function
                else
                    exit 1
                fi
            fi
            
            # Disk space validation
            validate_disk_space || exit 1
            
            # pipx validation for install
            if [[ "$command" == "install" ]]; then
                validate_pipx || log_warning "Continuing with pip installation"
            fi
        else
            log_info "Validating system requirements..."
            
            validate_python || exit 1
            
            if [[ "$no_deps" != "true" ]]; then
                validate_dependencies || exit 1
            fi
            
            validate_disk_space || exit 1
            
            if [[ "$command" == "install" ]]; then
                validate_pipx || log_warning "Continuing with pip installation"
            fi
        fi
    fi
    
    # Execute command
    case "$command" in
        install)
            install_package "$install_dev"
            if [[ $? -eq 0 ]]; then
                setup_shell_integration
            fi
            ;;
        upgrade)
            if [[ "$TREE_MODE" == "true" ]]; then
                tree_node "info" "Package Status"
                upgrade_package
                tree_final_node "success" "Complete"
                echo "        └─ Try: $COMMAND_NAME --version"
            else
                upgrade_package
            fi
            ;;
        uninstall)
            if [[ "$force_flag" != "true" ]]; then
                echo -n "Are you sure you want to uninstall $DISPLAY_NAME? [y/N]: "
                read -r response
                if [[ ! "$response" =~ ^[Yy]$ ]]; then
                    log_info "Uninstall cancelled"
                    exit 0
                fi
            fi
            uninstall_package
            ;;
        validate)
            log_success "All system requirements validated successfully!"
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
    
    if [[ "$TREE_MODE" != "true" ]]; then
        echo
        log_success "$DISPLAY_NAME setup completed!"
    fi
}

# Run main function with all arguments
main "$@"