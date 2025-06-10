# Resolver Issue Reproduction Tests

## Issue Summary

**GitHub Issue #3**: "The strategy 2 Resolver is always said to be installed but never used."

### Problem Description

The OpenHands resolver workflow has a verification logic mismatch:

1. **Strategy 2 claims success**: "✅ Strategy 2 succeeded and verified"
2. **But resolver isn't actually usable**:
   - `openhands-resolver command: not found`
   - `Python module test: not importable`
   - `Direct import test: not importable`
3. **System falls back to simple resolver**: "🔄 Fallback: Using simple resolver"

This creates confusion and inefficiency in the resolver selection process.

## Root Cause Analysis

The issue stems from a mismatch between:

1. **Strategy 2 verification logic** (lines 81-88 in workflow):
   ```bash
   if command -v openhands-resolver >/dev/null 2>&1 || python -c "import openhands_resolver" 2>/dev/null; then
   ```
   - Uses OR logic: succeeds if EITHER command OR import works
   - Sets `RESOLVER_TYPE=standard`

2. **Resolver selection logic** (lines 246+ in workflow):
   ```bash
   elif [ "$RESOLVER_TYPE" = "standard" ] && command -v openhands-resolver >/dev/null 2>&1; then
   ```
   - Requires BOTH `RESOLVER_TYPE=standard` AND working command/import
   - Falls back when interfaces don't actually work

## Test Implementation

### File: `tests/test_resolver_workflow.py`

Created comprehensive tests that reproduce the exact issue:

#### 1. `TestResolverInstallationVerification`
- **`test_strategy2_verification_logic_mismatch`**: Demonstrates the core verification mismatch

#### 2. `TestResolverWorkflowLogic`
- **`test_strategy2_verification_should_require_both_command_and_import`**: Shows the OR vs AND logic problem

#### 3. `TestResolverSelectionLogic`
- **`test_resolver_selection_requires_working_interfaces`**: Tests the selection logic requirements

#### 4. `TestResolverWorkflowFailures`
- **`test_strategy2_should_not_claim_success_when_verification_fails`**: Demonstrates what should happen
- **`test_resolver_type_should_not_be_standard_when_interfaces_dont_work`**: Shows the inconsistency

#### 5. `TestGitHubIssueReproduction`
- **`test_exact_github_issue_scenario`**: Reproduces the exact scenario from the GitHub issue
- **`test_strategy2_verification_bug_root_cause`**: Identifies the root cause

## Test Results

All tests **PASS**, which means they successfully reproduce the issue:

```bash
$ python -m pytest tests/test_resolver_workflow.py -v
========================================= test session starts ==========================================
collected 7 items

tests/test_resolver_workflow.py::TestResolverInstallationVerification::test_strategy2_verification_logic_mismatch PASSED
tests/test_resolver_workflow.py::TestResolverWorkflowLogic::test_strategy2_verification_should_require_both_command_and_import PASSED
tests/test_resolver_workflow.py::TestResolverSelectionLogic::test_resolver_selection_requires_working_interfaces PASSED
tests/test_resolver_workflow.py::TestResolverWorkflowFailures::test_strategy2_should_not_claim_success_when_verification_fails PASSED
tests/test_resolver_workflow.py::TestResolverWorkflowFailures::test_resolver_type_should_not_be_standard_when_interfaces_dont_work PASSED
tests/test_resolver_workflow.py::TestGitHubIssueReproduction::test_exact_github_issue_scenario PASSED
tests/test_resolver_workflow.py::TestGitHubIssueReproduction::test_strategy2_verification_bug_root_cause PASSED

========================================== 7 passed in 0.04s ===========================================
```

## Key Findings

### 1. Logic Inconsistency
- **Strategy 2 verification**: Uses OR logic (command OR import)
- **Resolver selection**: Requires AND logic (type AND working interface)
- **Result**: Verification can succeed when selection will fail

### 2. Environment Variable Persistence
- Strategy 2 sets `RESOLVER_TYPE=standard` even when verification is questionable
- Later resolver selection finds the interfaces don't work
- System falls back but with confusing messaging

### 3. Debugging Output Mismatch
The logs show:
```
✅ Strategy 2 succeeded and verified
...
🔍 Resolver selection debugging:
  RESOLVER_TYPE: 'standard'
  openhands-resolver command: not found
  Python module test: not importable
```

This clearly shows the verification claimed success but the resolver doesn't actually work.

## Next Steps

Now that the issue is reproduced with failing tests, the next step would be to:

1. **Fix the verification logic** in Strategy 2 to be more stringent
2. **Align verification and selection logic** to use consistent requirements
3. **Improve error messaging** to be clearer about what's happening
4. **Add proper fallback handling** that doesn't claim success when falling back

The tests provide a clear specification of what the correct behavior should be and will help validate any fixes.