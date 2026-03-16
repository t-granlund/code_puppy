#!/usr/bin/env python3
"""
Generate git commit commands for staging changes.

Groups files by risk level and generates appropriate git commands.
Makes it easy to commit changes in safe stages.

Author: Richard the Code Puppy 🐶
"""

import subprocess
from pathlib import Path
from typing import List, Dict


def get_git_status() -> Dict[str, List[str]]:
    """Get modified and untracked files from git."""
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True,
        check=True
    )
    
    modified = []
    created = []
    
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        
        status_code = line[:2].strip()
        file_path = line[3:].strip().strip('"')
        
        if status_code == 'M':
            modified.append(file_path)
        elif status_code == '??':
            path = Path(file_path)
            if path.is_file():
                created.append(file_path)
            elif path.is_dir():
                # Add all files in untracked directory
                for subfile in path.rglob('*'):
                    if subfile.is_file() and not '__pycache__' in str(subfile):
                        created.append(str(subfile))
    
    return {'modified': modified, 'created': created}


def categorize_files(files: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Categorize files by commit stage."""
    stages = {
        'stage1_docs': [],
        'stage2_plugins': [],
        'stage3_tests': [],
        'stage4_core_new': [],
        'stage5_core_modified': [],
        'ignore': [],
    }
    
    all_files = files['modified'] + files['created']
    
    for f in all_files:
        # Ignore files
        if any(x in f for x in ['Log at ', '.csv', '.html', 'audit_report.txt', '__pycache__']):
            stages['ignore'].append(f)
        
        # Stage 1: Documentation
        elif (f.startswith('research/') or 
              f.endswith('.md') and '/' not in f or
              f.startswith('examples/') and f.endswith('.md')):
            stages['stage1_docs'].append(f)
        
        # Stage 2: Plugins
        elif 'plugins/' in f and not f.endswith('.pyc'):
            stages['stage2_plugins'].append(f)
        
        # Stage 3: Tests
        elif f.startswith('tests/') and 'test_' in f:
            stages['stage3_tests'].append(f)
        
        # Stage 4: New core files
        elif (f.startswith('code_puppy/') and 
              f in files['created'] and
              not 'plugins/' in f):
            stages['stage4_core_new'].append(f)
        
        # Stage 5: Modified core files
        elif (f.startswith('code_puppy/') and 
              f in files['modified'] and
              not 'plugins/' in f):
            stages['stage5_core_modified'].append(f)
        
        # Stage 1: Other docs/examples
        elif f.startswith('examples/'):
            stages['stage1_docs'].append(f)
    
    return stages


def generate_commands(stages: Dict[str, List[str]]):
    """Generate git commit commands."""
    
    print("🐶 Code Puppy Commit Helper")
    print("=" * 80)
    print()
    print("Copy-paste these commands to commit your changes in safe stages:")
    print()
    
    # Stage 1: Documentation
    if stages['stage1_docs']:
        print("# ═══════════════════════════════════════════════════════════")
        print("# STAGE 1: Documentation (SAFE) ✅")
        print("# ═══════════════════════════════════════════════════════════")
        print()
        
        for f in sorted(stages['stage1_docs']):
            print(f'git add "{f}"')
        
        print()
        print('git commit -m "docs: Add research, optimization plan, and examples"')
        print()
        print(f"# Files: {len(stages['stage1_docs'])}")
        print()
    
    # Stage 2: Plugins
    if stages['stage2_plugins']:
        print("# ═══════════════════════════════════════════════════════════")
        print("# STAGE 2: New Plugins (SAFE) ✅")
        print("# ═══════════════════════════════════════════════════════════")
        print()
        
        # Group by plugin
        plugins = {}
        for f in stages['stage2_plugins']:
            if 'plugins/' in f:
                parts = f.split('plugins/')[1].split('/')
                if parts:
                    plugin_name = parts[0]
                    if plugin_name not in plugins:
                        plugins[plugin_name] = []
                    plugins[plugin_name].append(f)
        
        for plugin_name, plugin_files in sorted(plugins.items()):
            print(f"# Plugin: {plugin_name}")
            for f in sorted(plugin_files):
                print(f'git add "{f}"')
            print()
        
        print('git commit -m "feat: Add new plugins (agent_registry, behavioral_tests, context_monitor, mcp_progressive, skill_browser)"')
        print()
        print(f"# Files: {len(stages['stage2_plugins'])}")
        print()
    
    # Stage 3: Tests
    if stages['stage3_tests']:
        print("# ═══════════════════════════════════════════════════════════")
        print("# STAGE 3: Test Files (SAFE) ✅")
        print("# ═══════════════════════════════════════════════════════════")
        print()
        
        for f in sorted(stages['stage3_tests']):
            print(f'git add "{f}"')
        
        print()
        print('git commit -m "test: Add comprehensive test coverage for new features"')
        print()
        print(f"# Files: {len(stages['stage3_tests'])}")
        print()
    
    # Stage 4: New core files
    if stages['stage4_core_new']:
        print("# ═══════════════════════════════════════════════════════════")
        print("# STAGE 4: New Core Features (MEDIUM RISK) ⚠️")
        print("# ═══════════════════════════════════════════════════════════")
        print("# Review each file before committing!")
        print()
        
        for f in sorted(stages['stage4_core_new']):
            print(f'git add "{f}"')
        
        print()
        print('git commit -m "feat: Add OPT-000, OPT-004-B, OPT-006 implementations"')
        print()
        print(f"# Files: {len(stages['stage4_core_new'])}")
        print()
    
    # Stage 5: Modified core files
    if stages['stage5_core_modified']:
        print("# ═══════════════════════════════════════════════════════════")
        print("# STAGE 5: Core Modifications (HIGH RISK) 🔴")
        print("# ═══════════════════════════════════════════════════════════")
        print("# ⚠️  REVIEW EACH FILE CAREFULLY BEFORE COMMITTING! ⚠️")
        print("# These files are likely to conflict with upstream updates.")
        print()
        
        for f in sorted(stages['stage5_core_modified']):
            print(f'# Review: {f}')
            print(f'git add "{f}"')
            print()
        
        print('git commit -m "refactor: Integrate prompt assembler, capabilities, and fallbacks into core"')
        print()
        print(f"# Files: {len(stages['stage5_core_modified'])}")
        print()
    
    # Files to ignore
    if stages['ignore']:
        print("# ═══════════════════════════════════════════════════════════")
        print("# FILES TO IGNORE (Add to .gitignore)")
        print("# ═══════════════════════════════════════════════════════════")
        print()
        print("# Add these patterns to .gitignore:")
        print()
        
        ignore_patterns = set()
        for f in stages['ignore']:
            if 'Log at ' in f:
                ignore_patterns.add('Log at *.txt')
            elif f.endswith('.csv'):
                ignore_patterns.add('*.csv')
            elif f.endswith('.html') and 'self-optimization' in f:
                ignore_patterns.add('self-optimization-dashboard.html')
            elif f == 'audit_report.txt':
                ignore_patterns.add('audit_report.txt')
            elif '__pycache__' in f:
                ignore_patterns.add('__pycache__/')
        
        for pattern in sorted(ignore_patterns):
            print(f'echo "{pattern}" >> .gitignore')
        
        print()
        print(f"# Files to ignore: {len(stages['ignore'])}")
        print()
    
    # Summary
    print()
    print("# ═══════════════════════════════════════════════════════════")
    print("# SUMMARY")
    print("# ═══════════════════════════════════════════════════════════")
    print(f"# Stage 1 (Docs):          {len(stages['stage1_docs']):3d} files")
    print(f"# Stage 2 (Plugins):       {len(stages['stage2_plugins']):3d} files")
    print(f"# Stage 3 (Tests):         {len(stages['stage3_tests']):3d} files")
    print(f"# Stage 4 (New Core):      {len(stages['stage4_core_new']):3d} files")
    print(f"# Stage 5 (Modified Core): {len(stages['stage5_core_modified']):3d} files")
    print(f"# To Ignore:               {len(stages['ignore']):3d} files")
    print("#")
    print(f"# Total files:             {sum(len(v) for v in stages.values()):3d}")
    print()


def main():
    """Main entry point."""
    try:
        files = get_git_status()
        stages = categorize_files(files)
        generate_commands(stages)
        
        print()
        print("=" * 80)
        print("Commands generated! 🐶")
        print()
        print("Tip: Run this script again after each stage to see remaining files.")
        print()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure you're in a git repository.")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
