# GitHub Secrets Setup for OpenHands Resolver

This guide shows you how to set up GitHub secrets so the OpenHands resolver uses **YOUR** GPT-4 API key instead of OpenHands platform credits.

## 🔑 Required Secrets

You need to add these secrets to your GitHub repository:

### 1. `LLM_API_KEY` (Required)
- **What**: Your OpenAI or Anthropic API key
- **For OpenAI**: Get from https://platform.openai.com/api-keys
- **For Anthropic**: Get from https://console.anthropic.com/
- **Example**: `sk-proj-abc123...` (OpenAI) or `sk-ant-api03-...` (Anthropic)

### 2. `LLM_MODEL` (Required)
- **What**: The model name you want to use
- **OpenAI examples**:
  - `gpt-4` (GPT-4)
  - `gpt-4-turbo` (GPT-4 Turbo)
  - `gpt-3.5-turbo` (GPT-3.5 Turbo)
- **Anthropic examples**:
  - `claude-3-5-sonnet-20241022` (Claude 3.5 Sonnet)
  - `claude-3-opus-20240229` (Claude 3 Opus)
  - `claude-3-haiku-20240307` (Claude 3 Haiku)

### 3. `LLM_BASE_URL` (Optional)
- **What**: Custom API endpoint URL
- **Default**: Uses standard OpenAI/Anthropic endpoints
- **When to use**: If you're using a proxy, custom deployment, or alternative provider
- **Example**: `https://api.openai.com/v1` (default for OpenAI)

## 📝 How to Add Secrets

### Step 1: Go to Repository Settings
1. Navigate to your repository: https://github.com/qinx18/compiler-mcp-server
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**

### Step 2: Add Each Secret
1. Click **New repository secret**
2. Enter the secret name (e.g., `LLM_API_KEY`)
3. Enter the secret value (your API key)
4. Click **Add secret**
5. Repeat for each required secret

### Step 3: Verify Setup
After adding secrets, you should see:
- ✅ `LLM_API_KEY`
- ✅ `LLM_MODEL`
- ✅ `LLM_BASE_URL` (optional)

## 🧪 Testing the Setup

### Method 1: Create a Test Issue
1. Create a new issue in your repository
2. Add the `fix-me` label to the issue
3. The workflow should trigger automatically
4. Check the Actions tab for workflow execution

### Method 2: Comment on Existing Issue
1. Go to any existing issue
2. Comment: `@openhands-agent please help`
3. The workflow should trigger
4. Check the Actions tab for workflow execution

## 🔍 Troubleshooting

### Check Workflow Logs
1. Go to **Actions** tab in your repository
2. Click on the latest "OpenHands Resolver" workflow run
3. Expand the logs to see detailed execution information

### Common Issues

#### ❌ "Required secrets missing"
- **Solution**: Make sure you've added `LLM_API_KEY` and `LLM_MODEL` secrets
- **Check**: Repository Settings → Secrets and variables → Actions

#### ❌ "Invalid API key"
- **Solution**: Verify your API key is correct and has sufficient credits
- **OpenAI**: Check https://platform.openai.com/usage
- **Anthropic**: Check https://console.anthropic.com/

#### ❌ "Model not found"
- **Solution**: Check that your `LLM_MODEL` value is correct
- **OpenAI**: Use exact model names like `gpt-4`, not `openai/gpt-4`
- **Anthropic**: Use full model names like `claude-3-5-sonnet-20241022`

#### ❌ "Dependency conflicts"
- **Solution**: The new workflow has 4 fallback strategies, including a simple resolver
- **Check**: Look for "Strategy 4" in the workflow logs - this should always work

## 💰 Cost Implications

### Before (OpenHands Platform):
- Uses OpenHands platform credits
- You pay OpenHands for usage

### After (Your API Key):
- Uses your OpenAI/Anthropic credits directly
- You pay OpenAI/Anthropic directly
- Potentially more cost-effective for heavy usage

## 🔄 Workflow Trigger Conditions

The resolver triggers when:
1. **New issue** with `fix-me` label
2. **Comment** containing `@openhands-agent` on any issue

## 📊 Expected Behavior

### Successful Run:
1. Workflow installs resolver (tries 4 strategies)
2. Reads issue content via GitHub API
3. Calls your LLM (GPT-4/Claude) with issue analysis prompt
4. Posts AI-generated response as comment
5. Uses YOUR API credits, not OpenHands credits

### Workflow Output:
```
🔧 Installing OpenHands Resolver with dependency conflict resolution...
✅ Strategy 1 succeeded
✅ OpenHands Resolver installed successfully
✅ Import test passed
✅ Running resolver for issue #X
🤖 Calling gpt-4 for issue analysis...
✅ Posted AI analysis to issue
```

## 🎯 Benefits

✅ **Uses your API key** instead of OpenHands platform credits
✅ **Robust installation** with 4 fallback strategies
✅ **Automatic issue resolution** when labeled or mentioned
✅ **Direct cost control** - you pay your LLM provider directly
✅ **Multiple LLM support** - OpenAI, Anthropic, or custom endpoints
✅ **Guaranteed functionality** - simple resolver always works as fallback

## 🆘 Need Help?

If you encounter issues:
1. Check the [workflow logs](https://github.com/qinx18/compiler-mcp-server/actions)
2. Verify your secrets are set correctly
3. Test with a simple issue first
4. Check your API key has sufficient credits

The new multi-strategy approach should resolve all previous dependency conflicts and ensure your GPT-4 API key is used instead of OpenHands platform credits!
