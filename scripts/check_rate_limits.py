#!/usr/bin/env python3
"""Check current rate limit status for all Antigravity accounts."""

import time
from code_puppy.plugins.antigravity_oauth.accounts import AccountManager


def main():
    manager = AccountManager.load_from_disk()
    print(f"📊 Account Pool: {manager.account_count} accounts\n")

    now_ms = time.time() * 1000
    
    for acc in manager.get_accounts_snapshot():
        project = acc.parts.project_id or "Unknown"
        print(f"Account #{acc.index}: {project}")
        
        if acc.rate_limit_reset_times:
            for key, reset_time in acc.rate_limit_reset_times.items():
                remaining = (reset_time - now_ms) / 1000
                if remaining > 0:
                    mins = remaining / 60
                    print(f"  ⚠️  {key}: rate-limited for {mins:.1f} min more")
                else:
                    print(f"  ✅ {key}: expired (will be cleared on next load)")
        else:
            print("  ✅ No active rate limits")
        print()

    # Check availability
    claude_acc = manager.get_current_or_next_for_family("claude")
    gemini_acc = manager.get_current_or_next_for_family("gemini")

    print("🔍 Current Selection:")
    if claude_acc:
        print(f"  Antigravity Claude: Account #{claude_acc.index} ({claude_acc.parts.project_id})")
    else:
        print("  Antigravity Claude: ❌ NONE available (all rate-limited)")
    if gemini_acc:
        print(f"  Antigravity Gemini: Account #{gemini_acc.index} ({gemini_acc.parts.project_id})")
    else:
        print("  Antigravity Gemini: ❌ NONE available (all rate-limited)")


if __name__ == "__main__":
    main()
