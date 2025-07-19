#!/bin/bash
# Syncs the shared-setup framework to all designated projects.
#
# This script works in multiple scenarios:
# 1. When run from the project containing the framework (default)
# 2. When run from a central framework repository
# 3. When given explicit project paths
#
# Usage:
#   ./sync-framework.sh                    # Sync to current project
#   ./sync-framework.sh /path/to/project   # Sync to specific project
#   ./sync-framework.sh proj1 proj2 proj3  # Sync to multiple projects
#
# The framework source is determined by:
# 1. SETUP_FRAMEWORK_SOURCE environment variable (if set)
# 2. Default: ./ttt/shared-setup/ (relative to this script)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The source directory of the framework (relative to this script)
# By default, assumes the framework is in ttt/shared-setup/
FRAMEWORK_SOURCE_DIR="$SCRIPT_DIR/ttt/shared-setup"

# Allow overriding the source directory via environment variable
if [[ -n "${SETUP_FRAMEWORK_SOURCE}" ]]; then
    FRAMEWORK_SOURCE_DIR="${SETUP_FRAMEWORK_SOURCE}"
fi

# Project directories to sync to
# Can be specified as command line arguments, or defaults to current directory
if [[ $# -gt 0 ]]; then
    # Use command line arguments as project paths
    PROJECTS=("$@")
else
    # Default projects list - using relative paths from script location
    # You can customize this array for your specific setup
    PROJECTS=(
        "."           # TTT (current)
        "../tts"      # TTS project
        "../stt"      # STT project
    )
    
    # Convert relative paths to absolute paths
    ABSOLUTE_PROJECTS=()
    for project in "${PROJECTS[@]}"; do
        if [[ "$project" == "." ]]; then
            ABSOLUTE_PROJECTS+=("$SCRIPT_DIR")
        else
            # Resolve relative path from script directory
            ABSOLUTE_PROJECTS+=("$(cd "$SCRIPT_DIR" && cd "$project" 2>/dev/null && pwd || echo "")")
        fi
    done
    PROJECTS=("${ABSOLUTE_PROJECTS[@]}")
fi

# Show usage if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [project_path1] [project_path2] ..."
    echo
    echo "Syncs the shared-setup framework to one or more projects."
    echo
    echo "Options:"
    echo "  No arguments     - Syncs to current project (containing this script)"
    echo "  project_path...  - Syncs to specified project directories"
    echo "  --help, -h      - Show this help message"
    echo
    echo "Environment variables:"
    echo "  SETUP_FRAMEWORK_SOURCE - Override the framework source directory"
    echo
    echo "Examples:"
    echo "  $0                          # Sync to current project"
    echo "  $0 ../another-project       # Sync to a relative path"
    echo "  $0 /path/to/project1 /path/to/project2  # Sync to multiple projects"
    echo
    exit 0
fi

echo -e "\033[0;34m🚀 Starting framework synchronization...\033[0m"
echo "  Source: $FRAMEWORK_SOURCE_DIR"
echo

if [ ! -d "$FRAMEWORK_SOURCE_DIR" ]; then
    echo -e "\033[0;31m❌ Framework source not found at: $FRAMEWORK_SOURCE_DIR\033[0m"
    echo "  Make sure the framework exists at the expected location."
    echo "  You can override the source with SETUP_FRAMEWORK_SOURCE environment variable."
    exit 1
fi

# Track success/failure
success_count=0
skip_count=0

for project_path in "${PROJECTS[@]}"; do
    if [[ -z "$project_path" || ! -d "$project_path" ]]; then
        echo -e "  - \033[1;33m⚠️  Skipping: Invalid or missing path: $project_path\033[0m"
        ((skip_count++))
        continue
    fi
    
    echo "  - 📋 Syncing to: $project_path"
    
    # Auto-detect target directory structure
    # Check for existing shared-setup in different locations
    if [[ -d "$project_path/ttt/shared-setup" ]]; then
        target_dir="$project_path/ttt/shared-setup"
    elif [[ -d "$project_path/src/shared-setup" ]]; then
        target_dir="$project_path/src/shared-setup"
    else
        # Default to ttt/shared-setup for new projects
        target_dir="$project_path/ttt/shared-setup"
    fi
    
    # Create the target directory if it doesn't exist
    mkdir -p "$(dirname "$target_dir")"
    
    # Use rsync to efficiently copy, updating only changed files and removing deleted ones.
    if rsync -av --delete --exclude='.git/' "$FRAMEWORK_SOURCE_DIR/" "$target_dir/"; then
        echo -e "    \033[0;32m✓ Success\033[0m"
        ((success_count++))
    else
        echo -e "    \033[0;31m✗ Failed\033[0m"
        ((skip_count++))
    fi
done

echo
if [[ $skip_count -eq 0 ]]; then
    echo -e "\033[0;32m✅ Synchronization complete! ($success_count projects updated)\033[0m"
else
    echo -e "\033[1;33m⚠️  Synchronization finished with warnings:\033[0m"
    echo "  - Successful: $success_count projects"
    echo "  - Skipped/Failed: $skip_count projects"
fi