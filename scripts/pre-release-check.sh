#!/usr/bin/env bash
# Pre-release validation script for gitwebhooks
# This script MUST be run before publishing to PyPI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Pre-release Validation ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check step function
check_step() {
    local name="$1"
    local command="$2"

    echo -n "Checking $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        return 1
    fi
}

# 1. Check if package builds successfully
echo "Step 1: Building package..."
cd "$PROJECT_ROOT"
if ! python3 -m build --outdir /tmp/gitwebhooks-build . > /dev/null 2>&1; then
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi
echo -e "${GREEN}Build successful${NC}"
echo ""

# 2. Create temporary venv for testing
echo "Step 2: Creating test environment..."
TEMP_VENV=$(mktemp -d)
python3 -m venv "$TEMP_VENV"
source "$TEMP_VENV/bin/activate"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}Test environment created${NC}"
echo ""

# 3. Install the built package
echo "Step 3: Installing built package..."
pip install /tmp/gitwebhooks-build/gitwebhooks-*.tar.gz > /dev/null 2>&1
echo -e "${GREEN}Package installed${NC}"
echo ""

# 4. Critical tests
echo "Step 4: Running critical tests..."

# Test CLI entry point
if ! check_step "CLI entry point (gitwebhooks-cli)" "gitwebhooks-cli --help"; then
    echo -e "${RED}ERROR: CLI entry point not working!${NC}"
    deactivate
    rm -rf "$TEMP_VENV"
    rm -rf /tmp/gitwebhooks-build
    exit 1
fi

# Test subcommands
if ! check_step "CLI service subcommand" "gitwebhooks-cli service --help"; then
    echo -e "${RED}ERROR: service subcommand not working!${NC}"
    deactivate
    rm -rf "$TEMP_VENV"
    rm -rf /tmp/gitwebhooks-build
    exit 1
fi

if ! check_step "CLI config subcommand" "gitwebhooks-cli config --help"; then
    echo -e "${RED}ERROR: config subcommand not working!${NC}"
    deactivate
    rm -rf "$TEMP_VENV"
    rm -rf /tmp/gitwebhooks-build
    exit 1
fi

# Test module import
if ! check_step "Module import (gitwebhooks.main)" "python3 -c 'from gitwebhooks.main import main'"; then
    echo -e "${RED}ERROR: Module import failed!${NC}"
    deactivate
    rm -rf "$TEMP_VENV"
    rm -rf /tmp/gitwebhooks-build
    exit 1
fi

# Test server import
if ! check_step "Server import" "python3 -c 'from gitwebhooks.server import WebhookServer'"; then
    echo -e "${RED}ERROR: Server import failed!${NC}"
    deactivate
    rm -rf "$TEMP_VENV"
    rm -rf /tmp/gitwebhooks-build
    exit 1
fi

echo ""
echo "Step 5: Cleanup..."
deactivate
rm -rf "$TEMP_VENV"
rm -rf /tmp/gitwebhooks-build
echo -e "${GREEN}Cleanup complete${NC}"
echo ""

echo -e "${GREEN}=== All validation checks passed! ===${NC}"
echo ""
echo -e "${YELLOW}You can now publish to PyPI with:${NC}"
echo "  python3 -m twine upload dist/*"
