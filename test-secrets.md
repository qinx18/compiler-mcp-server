# 🔍 OpenHands Resolver Setup Verification

## Quick Setup Checklist

### ✅ Step 1: Repository Secrets
Go to your repository: **Settings > Secrets and variables > Actions**

Add these secrets:
- [ ] `PAT_TOKEN` - GitHub Personal Access Token ([create here](https://github.com/settings/tokens))
- [ ] `LLM_API_KEY` - API key from [Claude](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/api-keys)  
- [ ] `LLM_MODEL` - Model name (e.g., `anthropic/claude-3-5-sonnet-20241022`)

### ✅ Step 2: Workflow Permissions  
Go to: **Settings > Actions > General > Workflow permissions**
- [ ] Select "Read and write permissions"
- [ ] Enable "Allow GitHub Actions to create and approve pull requests"

### ✅ Step 3: Test the Setup
1. Create a test issue in your repository
2. Add the `fix-me` label to the issue
3. Check if the workflow runs in the **Actions** tab

## 🚨 Common Issues

**If you see "dependency conflicts" error:**
- This is expected - the workflow will post helpful instructions
- The secrets setup is the main thing to fix

**If you see "missing secrets" error:**
- Double-check that all three secrets are set correctly
- Make sure there are no extra spaces in secret values

**If the workflow doesn't trigger:**
- Make sure the `fix-me` label exists in your repository
- Check that workflow permissions are enabled

## 🎯 Expected Behavior

Once properly configured:
1. Add `fix-me` label to any issue
2. Workflow runs automatically  
3. OpenHands resolver attempts to fix the issue
4. Creates a pull request with the solution

---

**Note**: You do NOT need to configure secrets in OpenHands itself - only in GitHub repository settings.