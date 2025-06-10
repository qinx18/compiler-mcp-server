#!/usr/bin/env python3
"""
Simple OpenHands-compatible resolver that uses your API key directly.
This bypasses dependency conflicts by implementing core functionality only.
"""

import os
import sys
from typing import Any, Optional

import requests


def get_issue_content(repo: str, issue_number: str, github_token: str) -> dict:
    """Get issue content from GitHub API"""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(url, headers=headers, timeout=30)
    return response.json()  # type: ignore[no-any-return]


def call_llm(
    prompt: str, api_key: str, model: str, base_url: Optional[str] = None
) -> str:
    """Call LLM API directly"""
    try:
        print(f"🔍 Debug: Calling LLM with model='{model}', base_url='{base_url}'")
        print(
            f"🔍 Debug: API key starts with: {api_key[:10]}..."
            if api_key
            else "🔍 Debug: No API key provided"
        )

        if not base_url or not base_url.strip():
            print("🔍 Debug: Empty base_url detected, will use default API endpoint")

        # Normalize model name
        clean_model = model.replace("openai/", "").replace("anthropic/", "")

        # Validate and normalize model names (keep valid models as-is)
        valid_models = [
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
        ]

        if clean_model in valid_models:
            print(f"✅ Using valid model: {clean_model}")
        else:
            print(f"⚠️ Unknown model '{clean_model}', proceeding anyway")

        client: Any
        if (
            "gpt" in model.lower()
            or "openai" in model.lower()
            or not ("claude" in model.lower() or "anthropic" in model.lower())
        ):
            # OpenAI API (default)
            print(f"🤖 Using OpenAI API with model: {clean_model}")
            import openai

            # Only pass base_url if it's not empty
            if base_url and base_url.strip():
                client = openai.OpenAI(api_key=api_key, base_url=base_url)
            else:
                client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=clean_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        elif "claude" in model.lower() or "anthropic" in model.lower():
            # Anthropic API
            print(f"🤖 Using Anthropic API with model: {clean_model}")
            import anthropic

            # Only pass base_url if it's not empty
            if base_url and base_url.strip():
                client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
            else:
                client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=clean_model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text  # type: ignore[no-any-return]
        else:
            # Generic API using requests
            print(f"🤖 Using generic API with model: {clean_model}")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": clean_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000,
            }
            url = base_url or "https://api.openai.com/v1/chat/completions"
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]  # type: ignore[no-any-return]
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        error_msg = f"Error calling LLM: {e!s}"
        print(f"❌ {error_msg}")
        print(f"🔍 Full error details:\n{error_details}")

        # Check for specific error types
        if "Connection" in str(e) or "connection" in str(e).lower():
            print("🌐 This appears to be a network connectivity issue")
        elif "401" in str(e) or "unauthorized" in str(e).lower():
            print("🔑 This appears to be an API key authentication issue")
        elif "404" in str(e) or "not found" in str(e).lower():
            print("🎯 This appears to be a model or endpoint not found issue")
        elif "429" in str(e) or "rate limit" in str(e).lower():
            print("⏱️ This appears to be a rate limiting issue")

        return error_msg


def post_comment(repo: str, issue_number: str, comment: str, github_token: str) -> None:
    """Post comment to GitHub issue"""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"body": comment}
    requests.post(url, headers=headers, json=data, timeout=30)


def main() -> None:
    repo = os.environ.get("REPO_NAME")
    issue_number = os.environ.get("ISSUE_NUMBER")
    github_token = os.environ.get("GITHUB_TOKEN")
    llm_api_key = os.environ.get("LLM_API_KEY")
    llm_model = os.environ.get("LLM_MODEL", "gpt-4")
    llm_base_url = os.environ.get("LLM_BASE_URL")

    print("🔍 Environment variables:")
    print(f"  REPO_NAME: {repo}")
    print(f"  ISSUE_NUMBER: {issue_number}")
    print(f"  GITHUB_TOKEN: {'✅ Set' if github_token else '❌ Missing'}")
    print(f"  LLM_API_KEY: {'✅ Set' if llm_api_key else '❌ Missing'}")
    print(f"  LLM_MODEL: {llm_model}")
    print(f"  LLM_BASE_URL: {llm_base_url or 'Not set (using default)'}")

    if not all([repo, issue_number, github_token, llm_api_key]):
        print("❌ Missing required environment variables")
        sys.exit(1)

    # Type narrowing - after this point, these variables are guaranteed to be non-None
    assert repo is not None
    assert issue_number is not None
    assert github_token is not None
    assert llm_api_key is not None

    print(f"🔄 Resolving issue #{issue_number} in {repo}")

    # Test dependencies and network connectivity
    print("🔍 Testing dependencies...")
    try:
        import importlib.util

        if importlib.util.find_spec("openai") is not None:
            print("✅ OpenAI package is available")
    except ImportError as e:
        print(f"❌ OpenAI package not available: {e}")

    print("🌐 Testing network connectivity...")

    # Test basic internet connectivity first
    try:
        basic_test = requests.get("https://httpbin.org/ip", timeout=5)
        print(f"✅ Basic internet connectivity: {basic_test.status_code}")
    except Exception as e:
        print(f"❌ No basic internet connectivity: {e}")

    # Test OpenAI API connectivity
    try:
        test_response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {llm_api_key}"},
            timeout=15,
        )
        if test_response.status_code == 200:
            print("✅ OpenAI API is reachable and API key is valid")
            # Show available models
            models = test_response.json().get("data", [])
            gpt_models = [m["id"] for m in models if "gpt" in m["id"].lower()][:5]
            print(f"📋 Available GPT models: {', '.join(gpt_models)}")
        elif test_response.status_code == 401:
            print("❌ OpenAI API key is invalid or expired")
        else:
            print(f"⚠️ OpenAI API returned status {test_response.status_code}")
            print(f"Response: {test_response.text[:200]}")
    except requests.exceptions.ConnectTimeout:
        print(
            "❌ Connection timeout to OpenAI API - GitHub Actions may have network restrictions"
        )
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error to OpenAI API: {e}")
        print("💡 This might be due to GitHub Actions network restrictions")
    except Exception as e:
        print(f"❌ Network connectivity test failed: {e}")
        import traceback

        print(f"Full error: {traceback.format_exc()}")

    # Get issue content
    issue = get_issue_content(repo, issue_number, github_token)
    issue_title = issue.get("title", "")
    issue_body = issue.get("body", "")

    # Create prompt for LLM
    prompt = f"""You are an AI assistant helping to resolve GitHub issues. Please analyze this issue and provide a helpful response.

Issue Title: {issue_title}
Issue Body: {issue_body}

Please provide:
1. Analysis of the issue
2. Suggested solution or next steps
3. Any code examples if relevant

Keep your response concise and actionable."""

    # Call LLM
    print(f"🤖 Calling {llm_model} for issue analysis...")
    response = call_llm(prompt, llm_api_key, llm_model, llm_base_url)

    # Format response
    comment = f"""🤖 **AI Analysis & Suggestions**

{response}

---
*This response was generated using {llm_model} via the OpenHands resolver.*"""

    # Post comment
    post_comment(repo, issue_number, comment, github_token)
    print("✅ Posted AI analysis to issue")


if __name__ == "__main__":
    main()
