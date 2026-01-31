#!/usr/bin/env python3
"""Fix account storage by creating from existing OAuth tokens."""

import json
import time
from pathlib import Path

def main():
    # Load existing OAuth tokens
    oauth_path = Path.home() / ".code_puppy" / "antigravity_oauth.json"
    
    if not oauth_path.exists():
        print("❌ No Antigravity OAuth tokens found")
        return
    
    with open(oauth_path) as f:
        tokens = json.load(f)
    
    project_id = tokens.get("project_id", "")
    refresh_token = tokens.get("refresh_token", "")
    
    if not refresh_token:
        print("❌ No refresh token found in OAuth file")
        return
    
    # Create proper account storage - email not needed, project_id is the identifier
    accounts_path = Path.home() / ".code_puppy" / "antigravity_accounts.json"
    now_ms = time.time() * 1000
    
    account_data = {
        "version": 3,
        "accounts": [
            {
                "refreshToken": refresh_token,
                "addedAt": now_ms,
                "lastUsed": now_ms,
                "email": None,  # Not needed - project_id is the identifier
                "projectId": project_id,
                "managedProjectId": None,
                "rateLimitResetTimes": {
                    "claude": None,
                    "geminiAntigravity": None,
                    "geminiCli": None
                },
                "lastSwitchReason": "initial"
            }
        ],
        "activeIndex": 0,
        "activeIndexByFamily": {
            "claude": 0,
            "gemini": 0
        }
    }
    
    with open(accounts_path, 'w') as f:
        json.dump(account_data, f, indent=2)
    
    print(f"✅ Created Antigravity account entry")
    print(f"   Project: {project_id}")
    print(f"   No rate limits set")

if __name__ == "__main__":
    main()
