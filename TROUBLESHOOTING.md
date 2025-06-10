# Troubleshooting OpenHands Resolver

## Common Issues and Solutions

### 1. Workflow Fails with "Install OpenHands Resolver" Step

**Problem**: The workflow fails during the installation step with dependency conflicts.

**Solution**: The workflow now includes fallback strategies:
- First tries to install the latest version
- Falls back to installing without dependencies if that fails
- Provides informative error messages

### 2. Missing Secrets

**Problem**: Workflow fails with authentication or API errors.

**Required Secrets** (set in repository Settings > Secrets and variables > Actions):
- `PAT_TOKEN`: GitHub Personal Access Token with repo permissions
- `PAT_USERNAME`: Your GitHub username (optional, defaults to github.actor)
- `LLM_API_KEY`: API key for your LLM service (Claude, OpenAI, etc.)
- `LLM_MODEL`: Model name (e.g., `anthropic/claude-3-5-sonnet-20241022`)
- `LLM_BASE_URL`: Base URL for LLM API (optional, for proxies)

### 3. Workflow Permissions

**Problem**: Workflow fails with permission errors.

**Solution**: Ensure these settings in repository Settings > Actions > General:
- Workflow permissions: "Read and write permissions"
- "Allow GitHub Actions to create and approve pull requests": Enabled

### 4. Dependency Conflicts

**Problem**: The openhands-resolver package has dependency conflicts with e2b package versions.

**Current Status**: This is a known issue with the openhands-resolver package. The workflow includes:
- Multiple installation strategies
- Graceful fallback to error reporting
- Clear error messages for debugging

### 5. Testing the Workflow

To test if the resolver is working:

1. Create a test issue
2. Add the `fix-me` label
3. Check the Actions tab for workflow runs
4. Look for comments on the issue from the bot

### 6. Manual Trigger

You can also trigger the resolver by commenting `@openhands-agent` on any issue.

## Getting Help

If you continue to have issues:

1. Check the Actions tab for detailed error logs
2. Ensure all required secrets are properly set
3. Verify repository permissions are correctly configured
4. Check if the issue has the `fix-me` label or contains `@openhands-agent` mention

## Alternative Solutions

If the automated resolver continues to fail, you can:

1. Use the manual installation method described in the README
2. Set up a local development environment
3. Use the test mode: `python solution_for_s1113.py --mode test`