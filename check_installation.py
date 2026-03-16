#!/usr/bin/env python3
"""Check which code-puppy installation is being used."""

import sys
import os
from pathlib import Path

def check_installation():
    print("🔍 Code Puppy Installation Check\n")
    print("=" * 60)
    
    # Check if code_puppy module exists
    try:
        import code_puppy
        module_path = Path(code_puppy.__file__).parent.parent
        print(f"✅ code_puppy module found")
        print(f"📁 Location: {module_path}")
        
        # Check if it's the local version
        current_dir = Path.cwd()
        is_local = module_path.resolve() == current_dir.resolve()
        
        if is_local:
            print("🏠 Running from: LOCAL VERSION (your changes active!)")
        else:
            print("📦 Running from: INSTALLED PACKAGE (PyPI, no local changes)")
            print(f"\n⚠️  Your local changes at {current_dir} are NOT being used")
            print("\n💡 To use your local changes, run:")
            print(f"   cd {current_dir}")
            print("   pip install -e .")
            print("   code-puppy")
        
        # Check if OAuth client exists (our new file)
        oauth_client_path = module_path / "code_puppy" / "claude_oauth_client.py"
        if oauth_client_path.exists():
            print("\n✅ OAuth client found (OAuth fix applied)")
        else:
            print("\n❌ OAuth client NOT found (OAuth fix NOT applied)")
            print("   This means you're running the upstream version without your fixes")
        
        # Show version
        try:
            version = code_puppy.__version__
            print(f"\n📌 Version: {version}")
        except AttributeError:
            print("\n⚠️  Version info not available")
            
    except ImportError:
        print("❌ code_puppy module not found")
        print("   Install with: pip install code-puppy")
        print("   Or run from local: python -m code_puppy.main")
    
    print("=" * 60)

if __name__ == "__main__":
    check_installation()
