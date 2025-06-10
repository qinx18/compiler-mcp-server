#!/usr/bin/env python3
"""
Simple OpenHands-compatible resolver that uses your API key directly.
This bypasses dependency conflicts by implementing core functionality only.
"""
import os
import sys
import json
import requests
from typing import Optional

def get_issue_content(repo: str, issue_number: str, github_token: str) -> dict:
    """Get issue content from GitHub API"""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def call_llm(prompt: str, api_key: str, model: str, base_url: Optional[str] = None) -> str:
    """Call LLM API directly"""
    try:
        print(f"🔍 Debug: Calling LLM with model='{model}', base_url='{base_url}'")
        print(f"🔍 Debug: API key starts with: {api_key[:10]}..." if api_key else "🔍 Debug: No API key provided")
        
        # Normalize model name
        clean_model = model.replace("openai/", "").replace("anthropic/", "")
        
        # Fix common model name issues
        if clean_model == "gpt-4.1":
            clean_model = "gpt-4"
            print(f"🔧 Fixed model name: gpt-4.1 -> gpt-4")
        elif clean_model == "gpt-4o":
            clean_model = "gpt-4o"
        elif clean_model == "gpt-3.5-turbo":
            clean_model = "gpt-3.5-turbo"
        
        if "gpt" in model.lower() or "openai" in model.lower() or not ("claude" in model.lower() or "anthropic" in model.lower()):
            # OpenAI API (default)
            print(f"🤖 Using OpenAI API with model: {clean_model}")
            import openai
            client = openai.OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=clean_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7
            )
            return response.choices[0].message.content
        elif "claude" in model.lower() or "anthropic" in model.lower():
            # Anthropic API
            print(f"🤖 Using Anthropic API with model: {clean_model}")
            import anthropic
            client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
            response = client.messages.create(
                model=clean_model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        else:
            # Generic API using requests
            print(f"🤖 Using generic API with model: {clean_model}")
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {
                "model": clean_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000
            }
            url = base_url or "https://api.openai.com/v1/chat/completions"
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        error_msg = f"Error calling LLM: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg

def post_comment(repo: str, issue_number: str, comment: str, github_token: str):
    """Post comment to GitHub issue"""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": comment}
    requests.post(url, headers=headers, json=data)

def main():
    repo = os.environ.get("REPO_NAME")
    issue_number = os.environ.get("ISSUE_NUMBER")
    github_token = os.environ.get("GITHUB_TOKEN")
    llm_api_key = os.environ.get("LLM_API_KEY")
    llm_model = os.environ.get("LLM_MODEL", "gpt-4")
    llm_base_url = os.environ.get("LLM_BASE_URL")
    
    print(f"🔍 Environment variables:")
    print(f"  REPO_NAME: {repo}")
    print(f"  ISSUE_NUMBER: {issue_number}")
    print(f"  GITHUB_TOKEN: {'✅ Set' if github_token else '❌ Missing'}")
    print(f"  LLM_API_KEY: {'✅ Set' if llm_api_key else '❌ Missing'}")
    print(f"  LLM_MODEL: {llm_model}")
    print(f"  LLM_BASE_URL: {llm_base_url or 'Not set (using default)'}")
    
    if not all([repo, issue_number, github_token, llm_api_key]):
        print("❌ Missing required environment variables")
        sys.exit(1)
    
    print(f"🔄 Resolving issue #{issue_number} in {repo}")
    
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