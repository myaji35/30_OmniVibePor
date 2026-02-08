#!/bin/bash

# OmniVibe Pro - Test Runner Script
# Usage: ./run_tests.sh [test_type]
# Examples:
#   ./run_tests.sh all       # Run all tests
#   ./run_tests.sh e2e       # Run E2E tests only
#   ./run_tests.sh unit      # Run unit tests only
#   ./run_tests.sh fast      # Run fast tests only (skip slow)

set -e

TEST_TYPE=${1:-all}

echo "🧪 OmniVibe Pro - Test Runner"
echo "Test Type: $TEST_TYPE"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ Error: pytest not found${NC}"
    echo "Please install: pip install pytest pytest-asyncio pytest-cov httpx"
    exit 1
fi

# Run tests based on type
case $TEST_TYPE in
    all)
        echo -e "${GREEN}🚀 Running all tests...${NC}"
        pytest tests/
        ;;

    e2e)
        echo -e "${GREEN}🚀 Running E2E tests...${NC}"
        pytest tests/e2e/ -m e2e
        ;;

    unit)
        echo -e "${GREEN}🚀 Running unit tests...${NC}"
        pytest tests/ -m "not e2e and not slow"
        ;;

    integration)
        echo -e "${GREEN}🚀 Running integration tests...${NC}"
        pytest tests/e2e/ -m integration
        ;;

    performance)
        echo -e "${GREEN}🚀 Running performance tests...${NC}"
        pytest tests/e2e/ -m performance
        ;;

    fast)
        echo -e "${GREEN}🚀 Running fast tests (skip slow)...${NC}"
        pytest tests/ -m "not slow"
        ;;

    pipeline)
        echo -e "${GREEN}🚀 Running full pipeline test...${NC}"
        pytest tests/e2e/test_full_pipeline.py::TestFullPipeline -v
        ;;

    writer)
        echo -e "${GREEN}🚀 Running Writer Agent tests...${NC}"
        pytest tests/e2e/test_writer_agent.py -v
        ;;

    remotion)
        echo -e "${GREEN}🚀 Running Remotion tests...${NC}"
        pytest tests/e2e/test_remotion_rendering.py -v
        ;;

    coverage)
        echo -e "${GREEN}🚀 Running tests with coverage report...${NC}"
        pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${GREEN}✅ Coverage report generated: htmlcov/index.html${NC}"
        ;;

    watch)
        echo -e "${GREEN}🚀 Running tests in watch mode...${NC}"
        pytest-watch tests/ -c
        ;;

    *)
        echo -e "${RED}❌ Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Available test types:"
        echo "  all         - Run all tests"
        echo "  e2e         - Run E2E tests only"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests"
        echo "  performance - Run performance benchmarks"
        echo "  fast        - Run fast tests (skip slow)"
        echo "  pipeline    - Run full pipeline test"
        echo "  writer      - Run Writer Agent tests"
        echo "  remotion    - Run Remotion tests"
        echo "  coverage    - Run with coverage report"
        echo "  watch       - Run in watch mode"
        exit 1
        ;;
esac

EXIT_CODE=$?

echo ""
echo "=================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
fi
echo "=================================="

exit $EXIT_CODE
