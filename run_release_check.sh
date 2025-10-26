#!/bin/bash
# Phase 3 Release Check - Bash Runner
# Validates production readiness for Phase 3 completion
# Exit codes: 0=ready, 1=warnings, 2=failures

# Default values
WORKSPACE_ROOT="$(pwd)"
VERBOSE=false
SKIP_PYTHON=false
SHOW_HELP=false

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace-root)
            WORKSPACE_ROOT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --skip-python)
            SKIP_PYTHON=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Show usage information
show_usage() {
    cat << 'EOF'
Phase 3 Release Check - Bash Runner

USAGE:
    ./run_release_check.sh [OPTIONS]

OPTIONS:
    --workspace-root <path>    Set workspace root directory (default: current)
    --verbose                  Enable detailed output
    --skip-python             Skip Python environment checks
    --help, -h                Show this help message

EXAMPLES:
    ./run_release_check.sh
    ./run_release_check.sh --verbose
    ./run_release_check.sh --workspace-root "/path/to/workspace"

EXIT CODES:
    0 - Production ready (all checks passed)
    1 - Warnings detected (review recommended)
    2 - Critical failures (not ready for production)

EOF
}

# Print formatted header
print_header() {
    local message="$1"
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo -e "${WHITE} $message${NC}"
    echo -e "${CYAN}============================================${NC}"
}

# Print status messages
print_status() {
    local status="$1"
    local message="$2"
    local color
    
    case "$status" in
        "PASS") color="$GREEN" ;;
        "WARN") color="$YELLOW" ;;
        "FAIL") color="$RED" ;;
        "INFO") color="$CYAN" ;;
        *) color="$WHITE" ;;
    esac
    
    echo -e "${color}[$status]${NC} $message"
}

# Test if Python is available
test_python_available() {
    if command -v python3 &> /dev/null; then
        local version=$(python3 --version 2>&1)
        print_status "PASS" "Python available: $version"
        return 0
    elif command -v python &> /dev/null; then
        local version=$(python --version 2>&1)
        print_status "PASS" "Python available: $version"
        return 0
    else
        print_status "FAIL" "Python not found in PATH"
        return 1
    fi
}

# Test virtual environment status
test_virtual_environment() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        print_status "PASS" "Virtual environment active: $VIRTUAL_ENV"
        return 0
    fi
    
    # Check for common venv directories
    local venv_paths=("venv" ".venv" "env" ".env")
    for venv_path in "${venv_paths[@]}"; do
        local full_path="$WORKSPACE_ROOT/$venv_path"
        if [[ -d "$full_path" ]]; then
            print_status "WARN" "Virtual environment found but not activated: $full_path"
            return 1
        fi
    done
    
    print_status "WARN" "No virtual environment detected"
    return 1
}

# Test required files
test_required_files() {
    local required_files=(
        "tools/phase3_release_check.py"
        "src/phase3/schemas.py"
        "src/phase3/orchestrator.py"
        "src/phase3/synthesizer.py"
        "src/phase3/gates.py"
        "scripts/stage_order_cli.py"
    )
    
    local all_found=true
    for file in "${required_files[@]}"; do
        local full_path="$WORKSPACE_ROOT/$file"
        if [[ -f "$full_path" ]]; then
            if [[ "$VERBOSE" == "true" ]]; then
                print_status "PASS" "Found: $file"
            fi
        else
            print_status "FAIL" "Missing: $file"
            all_found=false
        fi
    done
    
    if [[ "$all_found" == "true" ]]; then
        print_status "PASS" "All required Phase 3 files present"
        return 0
    else
        return 1
    fi
}

# Get Python command (prefer python3)
get_python_command() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        echo ""
    fi
}

# Main execution
main() {
    if [[ "$SHOW_HELP" == "true" ]]; then
        show_usage
        exit 0
    fi
    
    print_header "Phase 3 Release Check - Bash Runner"
    echo -e "${GRAY}Workspace: $WORKSPACE_ROOT${NC}"
    echo -e "${GRAY}Timestamp: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    
    # Change to workspace directory
    if [[ ! -d "$WORKSPACE_ROOT" ]]; then
        print_status "FAIL" "Workspace directory not found: $WORKSPACE_ROOT"
        exit 2
    fi
    
    cd "$WORKSPACE_ROOT" || {
        print_status "FAIL" "Cannot change to workspace directory: $WORKSPACE_ROOT"
        exit 2
    }
    print_status "INFO" "Changed to workspace directory"
    
    local warnings=0
    local failures=0
    
    # Pre-flight checks
    print_header "Pre-flight Checks"
    
    if [[ "$SKIP_PYTHON" != "true" ]]; then
        if ! test_python_available; then
            ((failures++))
        fi
        
        if ! test_virtual_environment; then
            ((warnings++))
        fi
    fi
    
    if ! test_required_files; then
        ((failures++))
    fi
    
    # If pre-flight failed, exit early
    if [[ $failures -gt 0 ]]; then
        print_header "Pre-flight Failed"
        print_status "FAIL" "Cannot proceed with release check ($failures failures)"
        exit 2
    fi
    
    # Run the main Python release checker
    print_header "Running Phase 3 Release Check"
    
    local python_cmd=$(get_python_command)
    if [[ -z "$python_cmd" ]]; then
        print_status "FAIL" "No Python interpreter found"
        exit 2
    fi
    
    local python_args=("tools/phase3_release_check.py")
    if [[ "$VERBOSE" == "true" ]]; then
        python_args+=("--verbose")
    fi
    
    print_status "INFO" "Executing: $python_cmd ${python_args[*]}"
    
    "$python_cmd" "${python_args[@]}"
    local exit_code=$?
    
    print_header "Release Check Complete"
    
    case $exit_code in
        0)
            print_status "PASS" "Production ready! All checks passed."
            echo ""
            echo -e "${GREEN}🚀 Phase 3 is ready for production deployment!${NC}"
            ;;
        1)
            print_status "WARN" "Warnings detected. Review recommended."
            echo ""
            echo -e "${YELLOW}⚠️  Phase 3 has warnings but may be deployable.${NC}"
            ((warnings++))
            ;;
        2)
            print_status "FAIL" "Critical failures detected. Not ready for production."
            echo ""
            echo -e "${RED}❌ Phase 3 is not ready for production deployment.${NC}"
            ((failures++))
            ;;
        *)
            print_status "FAIL" "Unexpected exit code: $exit_code"
            ((failures++))
            ;;
    esac
    
    # Summary
    echo ""
    echo -e "${GRAY}Summary: $failures failures, $warnings warnings${NC}"
    
    # Final exit code
    if [[ $failures -gt 0 ]]; then
        exit 2
    elif [[ $warnings -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"