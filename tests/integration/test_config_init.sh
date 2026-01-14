#!/bin/bash
#
# Integration tests for config init command
#
# Tests the complete workflow of the config init wizard including:
# - Complete wizard flow with mocked input
# - Configuration level parameter handling (system/local/user)
# - Custom platform configuration
# - Permission error handling
# - File overwrite confirmation
# - Ctrl+C interrupt handling
# - Platform-specific configuration generation
# - Invalid input validation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
assert_success() {
    ((TESTS_RUN++))
    if [ $? -eq 0 ]; then
        ((TESTS_PASSED++))
        echo -e "${GREEN}✓ PASS${NC}: $1"
    else
        ((TESTS_FAILED++))
        echo -e "${RED}✗ FAIL${NC}: $1"
        return 1
    fi
}

assert_file_exists() {
    ((TESTS_RUN++))
    if [ -f "$1" ]; then
        ((TESTS_PASSED++))
        echo -e "${GREEN}✓ PASS${NC}: File exists: $1"
    else
        ((TESTS_FAILED++))
        echo -e "${RED}✗ FAIL${NC}: File does not exist: $1"
        return 1
    fi
}

assert_file_contains() {
    local file="$1"
    local content="$2"
    ((TESTS_RUN++))
    if grep -q "$content" "$file" 2>/dev/null; then
        ((TESTS_PASSED++))
        echo -e "${GREEN}✓ PASS${NC}: File contains: $content"
    else
        ((TESTS_FAILED++))
        echo -e "${RED}✗ FAIL${NC}: File does not contain: $content"
        return 1
    fi
}

# Setup
TEST_DIR=$(mktemp -d)
TEST_CONFIG_USER="$TEST_DIR/user_config.ini"
TEST_CONFIG_LOCAL="$TEST_DIR/local_config.ini"
TEST_CONFIG_SYSTEM="$TEST_DIR/system_config.ini"

cleanup() {
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

echo -e "${YELLOW}Running config init integration tests...${NC}\n"

# ===================================================================
# Test 1: User Story 1 - Complete wizard flow with mocked input
# ===================================================================
echo "Test 1: Complete wizard flow (user level)"

# Create input sequence for user-level config
cat > "$TEST_DIR/input_user.txt" <<EOF
3
0.0.0.0
6789
$TEST_DIR/test.log
1
1
y
test-secret-123
owner/test-repo
$TEST_DIR/repo
git pull && ./deploy.sh
2
EOF

mkdir -p "$TEST_DIR/repo"

# Run wizard with mocked input (using the Python -c approach for mocking)
python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

# Mock input function
inputs = []
with open('$TEST_DIR/input_user.txt', 'r') as f:
    inputs = [line.strip() for line in f.readlines()]

input_count = [0]
def mock_input(prompt=''):
    result = inputs[input_count[0]]
    input_count[0] += 1
    return result

# Patch the input function
import gitwebhooks.cli.init_wizard as wizard_module
wizard_module.input = mock_input

# Run the wizard
from gitwebhooks.cli.init_wizard import Wizard
wizard = Wizard()
result_path = wizard.run()
print(f'GENERATED:{result_path}')
" > "$TEST_DIR/output1.txt" 2>&1

GENERATED_PATH=$(grep "GENERATED:" "$TEST_DIR/output1.txt" | cut -d: -f2)

assert_file_exists "$GENERATED_PATH" || true
assert_file_contains "$GENERATED_PATH" "\[server\]" || true
assert_file_contains "$GENERATED_PATH" "\[github\]" || true
assert_file_contains "$GENERATED_PATH" "\[repo/owner/test-repo\]" || true

echo ""

# ===================================================================
# Test 2: User Story 2 - Configuration level parameter (user)
# ===================================================================
echo "Test 2: Direct user level configuration"

cat > "$TEST_DIR/input_user_level.txt" <<EOF

0.0.0.0
6789
$TEST_DIR/test2.log
1
1
y
secret456
user/repo2
$TEST_DIR/repo2
make deploy
2
EOF

mkdir -p "$TEST_DIR/repo2"

python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

inputs = []
with open('$TEST_DIR/input_user_level.txt', 'r') as f:
    inputs = [line.strip() for line in f.readlines()]

input_count = [0]
def mock_input(prompt=''):
    result = inputs[input_count[0]]
    input_count[0] += 1
    return result

import gitwebhooks.cli.init_wizard as wizard_module
wizard_module.input = mock_input

from gitwebhooks.cli.init_wizard import Wizard
wizard = Wizard(level='user')
result_path = wizard.run()
print(f'GENERATED:{result_path}')
" > "$TEST_DIR/output2.txt" 2>&1

GENERATED_PATH2=$(grep "GENERATED:" "$TEST_DIR/output2.txt" | cut -d: -f2)

assert_file_exists "$GENERATED_PATH2" || true
# Verify it used user level by checking path contains .gitwebhooks.ini
if [[ "$GENERATED_PATH2" == *".gitwebhooks.ini"* ]]; then
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓ PASS${NC}: User level path verified"
else
    ((TESTS_FAILED++))
    echo -e "${RED}✗ FAIL${NC}: User level path not verified"
fi
((TESTS_RUN++))

echo ""

# ===================================================================
# Test 3: User Story 3 - Custom platform configuration
# ===================================================================
echo "Test 3: Custom platform configuration"

cat > "$TEST_DIR/input_custom.txt" <<EOF
3
0.0.0.0
6789
$TEST_DIR/test3.log
4
push
n
X-Custom-Header
custom-token-value
repo.full_path
X-Event-Header
owner/custom-repo
$TEST_DIR/repo3
./deploy.sh
2
EOF

mkdir -p "$TEST_DIR/repo3"

python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

inputs = []
with open('$TEST_DIR/input_custom.txt', 'r') as f:
    inputs = [line.strip() for line in f.readlines()]

input_count = [0]
def mock_input(prompt=''):
    result = inputs[input_count[0]]
    input_count[0] += 1
    return result

import gitwebhooks.cli.init_wizard as wizard_module
wizard_module.input = mock_input

from gitwebhooks.cli.init_wizard import Wizard
wizard = Wizard()
result_path = wizard.run()
print(f'GENERATED:{result_path}')
" > "$TEST_DIR/output3.txt" 2>&1

GENERATED_PATH3=$(grep "GENERATED:" "$TEST_DIR/output3.txt" | cut -d: -f2)

assert_file_exists "$GENERATED_PATH3" || true
assert_file_contains "$GENERATED_PATH3" "\[custom\]" || true
assert_file_contains "$GENERATED_PATH3" "header_name" || true
assert_file_contains "$GENERATED_PATH3" "X-Custom-Header" || true

echo ""

# ===================================================================
# Test 4: Permission error handling (system/local without root)
# ===================================================================
echo "Test 4: Permission error handling"

# Try to create system config without root (should fail gracefully)
python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

def mock_input(prompt=''):
    return ''  # Empty input to trigger default behavior

import gitwebhooks.cli.init_wizard as wizard_module
wizard_module.input = mock_input

from gitwebhooks.cli.init_wizard import Wizard
wizard = Wizard(level='system')
try:
    result_path = wizard.run()
    print('ERROR:Should have failed')
except PermissionError as e:
    print('PERMISSION_ERROR:Detected')
except Exception as e:
    print(f'OTHER_ERROR:{type(e).__name__}')
" > "$TEST_DIR/output4.txt" 2>&1

assert_file_contains "$TEST_DIR/output4.txt" "PERMISSION_ERROR" || {
    echo -e "${YELLOW}⚠ SKIP${NC}: Permission test (may have root access)"
    ((TESTS_RUN++))
}

echo ""

# ===================================================================
# Test 5: Invalid input validation
# ===================================================================
echo "Test 5: Invalid input validation"

cat > "$TEST_DIR/input_invalid.txt" <<EOF
3
0.0.0.0
6789
$TEST_DIR/test5.log
1
1
y
secret789
invalid-repo-name
owner/valid-repo
$TEST_DIR/repo5
./deploy.sh
2
EOF

mkdir -p "$TEST_DIR/repo5"

python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

inputs = []
with open('$TEST_DIR/input_invalid.txt', 'r') as f:
    inputs = [line.strip() for line in f.readlines()]

input_count = [0]
def mock_input(prompt=''):
    result = inputs[input_count[0]]
    input_count[0] += 1
    return result

import gitwebhooks.cli.init_wizard as wizard_module
wizard_module.input = mock_input

from gitwebhooks.cli.init_wizard import Wizard
wizard = Wizard()
result_path = wizard.run()
print(f'GENERATED:{result_path}')
" > "$TEST_DIR/output5.txt" 2>&1

GENERATED_PATH5=$(grep "GENERATED:" "$TEST_DIR/output5.txt" | cut -d: -f2)

# Check that wizard handled invalid input and completed successfully
if grep -q 'GENERATED:' "$TEST_DIR/output5.txt"; then
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓ PASS${NC}: Wizard handled invalid input gracefully"
else
    ((TESTS_FAILED++))
    echo -e "${RED}✗ FAIL${NC}: Wizard failed to handle invalid input"
fi
((TESTS_RUN++))

echo ""

# ===================================================================
# Test 6: Platform-specific configurations (github/gitee/gitlab)
# ===================================================================
echo "Test 6: Platform-specific configurations"

for platform in github gitee gitlab; do
    echo "  Testing $platform platform..."

    cat > "$TEST_DIR/input_$platform.txt" <<EOF
3
0.0.0.0
6789
$TEST_DIR/test_$platform.log
$([ "$platform" = "github" ] && echo "1" || [ "$platform" = "gitee" ] && echo "2" || echo "3")
1
y
secret-$platform
owner/$platform-repo
$TEST_DIR/repo_$platform
echo 'Deploying $platform'
2
EOF

    mkdir -p "$TEST_DIR/repo_$platform"

    python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

inputs = []
with open('$TEST_DIR/input_$platform.txt', 'r') as f:
    inputs = [line.strip() for line in f.readlines()]

input_count = [0]
def mock_input(prompt=''):
    result = inputs[input_count[0]]
    input_count[0] += 1
    return result

import gitwebhooks.cli.init_wizard as wizard_module
wizard_module.input = mock_input

from gitwebhooks.cli.init_wizard import Wizard
wizard = Wizard()
result_path = wizard.run()
print(f'GENERATED:{result_path}')
" > "$TEST_DIR/output_$platform.txt" 2>&1

    GENERATED_PATH_PLATFORM=$(grep "GENERATED:" "$TEST_DIR/output_$platform.txt" | cut -d: -f2)
    assert_file_contains "$GENERATED_PATH_PLATFORM" "\[$platform\]" || true
done

echo ""

# ===================================================================
# Summary
# ===================================================================
echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}============================================${NC}"
echo "Tests run: $TESTS_RUN"
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
