#!/bin/bash
# Quick-start test runner for Character Perturbation Robustness Test Suite
# 
# This script provides convenient shortcuts for running common test configurations
# 
# Usage:
#   ./run_tests.sh                          # Run full test suite
#   ./run_tests.sh --languages ami pwn      # Run specific languages
#   ./run_tests.sh --quick                  # Quick test with subset
#   ./run_tests.sh --analyze results_dir    # Analyze existing results

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEST_SCRIPT="$SCRIPT_DIR/test_character_perturbation_robustness.py"
RUNNER_SCRIPT="$SCRIPT_DIR/test_runner.py"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEFAULT_OUTPUT_DIR="test_results/robustness_$TIMESTAMP"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

show_help() {
    cat << EOF
Character Perturbation Robustness Test Suite - Quick Start

USAGE:
    ./run_tests.sh [OPTION]

OPTIONS:
    --full              Run complete test suite for all languages (default)
    --quick             Quick test with only Amis and Paiwan
    --languages L1 L2   Test specific languages (e.g., ami tay pwn)
    --sources S1 S2     Test specific sources (e.g., ePark ILRDF_Dicts)
    --analyze DIR       Analyze results from a previous test run
    --compare D1 D2 D3  Compare results from multiple test runs
    --help              Show this message

EXAMPLES:
    # Full test suite
    ./run_tests.sh --full

    # Quick test for faster iteration
    ./run_tests.sh --quick

    # Test specific languages
    ./run_tests.sh --languages ami tay bnn pwn

    # Test specific sources
    ./run_tests.sh --sources ePark ILRDF_Dicts

    # Analyze existing results
    ./run_tests.sh --analyze test_results/robustness_20260629_150000

    # Compare multiple runs
    ./run_tests.sh --compare run1_results run2_results run3_results

OUTPUT:
    Results are saved to: test_results/robustness_YYYYMMDD_HHMMSS/
    
    Generated files:
    - all_results.json       : Aggregated results from all tests
    - summary_report.txt     : Human-readable summary
    - {lang}_{dialect}_results.json : Individual test results
    - test_run_YYYYMMDD_HHMMSS.log  : Detailed execution log

PERFORMANCE NOTES:
    - Full suite: ~10-30 minutes (all 7 languages × multiple dialects)
    - Quick test: ~2-3 minutes (2 languages)
    - Each test requires loading and processing corpus text

EOF
}

run_full_test() {
    print_header "Running Full Character Perturbation Robustness Test Suite"
    
    print_info "Target directory: $DEFAULT_OUTPUT_DIR"
    print_info "Testing all languages: ami tay bnn pwn pyu dru trv"
    print_info "Testing all sources: ePark ILRDF_Dicts Paiwan_Stories NTUFormosanCorpus"
    
    python "$TEST_SCRIPT" \
        --output-dir "$DEFAULT_OUTPUT_DIR" \
        --languages ami tay bnn pwn pyu dru trv \
        --sources ePark ILRDF_Dicts Paiwan_Stories NTUFormosanCorpus
    
    print_success "Test suite completed!"
    print_info "Results saved to: $DEFAULT_OUTPUT_DIR"
    
    # Auto-generate report
    generate_report "$DEFAULT_OUTPUT_DIR"
}

run_quick_test() {
    print_header "Running Quick Character Perturbation Robustness Test"
    
    print_info "Target directory: $DEFAULT_OUTPUT_DIR"
    print_info "Testing languages: ami pwn"
    print_info "Testing sources: ePark ILRDF_Dicts"
    
    python "$TEST_SCRIPT" \
        --output-dir "$DEFAULT_OUTPUT_DIR" \
        --languages ami pwn \
        --sources ePark ILRDF_Dicts
    
    print_success "Quick test completed!"
    print_info "Results saved to: $DEFAULT_OUTPUT_DIR"
    
    # Auto-generate report
    generate_report "$DEFAULT_OUTPUT_DIR"
}

run_custom_test() {
    local output_dir="$DEFAULT_OUTPUT_DIR"
    local cmd="python \"$TEST_SCRIPT\" --output-dir \"$output_dir\""
    
    # Add languages if provided
    if [ ${#LANGUAGES[@]} -gt 0 ]; then
        cmd="$cmd --languages ${LANGUAGES[@]}"
    fi
    
    # Add sources if provided
    if [ ${#SOURCES[@]} -gt 0 ]; then
        cmd="$cmd --sources ${SOURCES[@]}"
    fi
    
    print_header "Running Custom Character Perturbation Robustness Test"
    print_info "Command: $cmd"
    
    eval "$cmd"
    
    print_success "Custom test completed!"
    print_info "Results saved to: $output_dir"
    
    # Auto-generate report
    generate_report "$output_dir"
}

generate_report() {
    local results_dir="$1"
    
    if [ ! -d "$results_dir" ]; then
        print_error "Results directory not found: $results_dir"
        return 1
    fi
    
    print_info "Generating comparative analysis report..."
    
    local report_file="$results_dir/comparative_analysis.txt"
    local csv_file="$results_dir/results.csv"
    
    python "$RUNNER_SCRIPT" \
        --load-results "$results_dir" \
        --output-report "$report_file" \
        --export-csv "$csv_file"
    
    print_success "Reports generated:"
    print_info "  - $report_file"
    print_info "  - $csv_file"
}

analyze_results() {
    local results_dir="$1"
    
    if [ ! -d "$results_dir" ]; then
        print_error "Results directory not found: $results_dir"
        return 1
    fi
    
    print_header "Analyzing Results"
    print_info "Results directory: $results_dir"
    
    generate_report "$results_dir"
    
    # Display summary if exists
    if [ -f "$results_dir/summary_report.txt" ]; then
        print_info "Summary Report:"
        head -100 "$results_dir/summary_report.txt"
        print_info "[... full report in $results_dir/summary_report.txt]"
    fi
}

compare_multiple_runs() {
    print_header "Comparing Multiple Test Runs"
    
    if [ ${#COMPARE_DIRS[@]} -lt 2 ]; then
        print_error "At least 2 directories required for comparison"
        return 1
    fi
    
    local output_file="test_results/cross_run_comparison_$TIMESTAMP.txt"
    
    print_info "Comparing ${#COMPARE_DIRS[@]} test runs"
    print_info "Output: $output_file"
    
    python "$RUNNER_SCRIPT" \
        --compare-runs "${COMPARE_DIRS[@]}" \
        --output-comparison "$output_file"
    
    print_success "Comparison complete!"
    print_info "Results saved to: $output_file"
}

# Main script logic
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# Parse arguments
declare -a LANGUAGES
declare -a SOURCES
declare -a COMPARE_DIRS
COMMAND="full"

while [ $# -gt 0 ]; do
    case "$1" in
        --full)
            COMMAND="full"
            shift
            ;;
        --quick)
            COMMAND="quick"
            shift
            ;;
        --languages)
            COMMAND="custom"
            shift
            while [ $# -gt 0 ] && [[ ! "$1" =~ ^-- ]]; do
                LANGUAGES+=("$1")
                shift
            done
            ;;
        --sources)
            shift
            while [ $# -gt 0 ] && [[ ! "$1" =~ ^-- ]]; do
                SOURCES+=("$1")
                shift
            done
            ;;
        --analyze)
            COMMAND="analyze"
            shift
            if [ $# -eq 0 ]; then
                print_error "Missing directory argument for --analyze"
                exit 1
            fi
            RESULTS_DIR="$1"
            shift
            ;;
        --compare)
            COMMAND="compare"
            shift
            while [ $# -gt 0 ] && [[ ! "$1" =~ ^-- ]]; do
                COMPARE_DIRS+=("$1")
                shift
            done
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Execute command
case "$COMMAND" in
    full)
        run_full_test
        ;;
    quick)
        run_quick_test
        ;;
    custom)
        run_custom_test
        ;;
    analyze)
        analyze_results "$RESULTS_DIR"
        ;;
    compare)
        compare_multiple_runs
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        exit 1
        ;;
esac

print_success "Done!"
