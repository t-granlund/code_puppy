#!/usr/bin/env python3
"""
Comprehensive audit script for Code Puppy local changes.

Compares the local directory against what would be in the upstream public repo,
identifying all created, modified, and potentially conflicting files.

Author: Richard the Code Puppy 🐶
Created: During self-optimization session
"""

import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class FileInfo:
    """Information about a single file."""
    
    def __init__(self, path: Path, status: str):
        self.path = path
        self.status = status  # 'created', 'modified', or 'unknown'
        self.size = path.stat().st_size if path.exists() else 0
        self.category = self._categorize()
        self.purpose = self._determine_purpose()
        self.conflict_risk = self._assess_conflict_risk()
        
    def _categorize(self) -> str:
        """Categorize file by type and location."""
        path_str = str(self.path)
        
        # Documentation
        if path_str.endswith('.md') and not path_str.startswith('code_puppy/'):
            if path_str.startswith('research/'):
                return 'research_docs'
            elif path_str.startswith('docs/'):
                return 'documentation'
            else:
                return 'root_docs'
        
        # Research
        if path_str.startswith('research/'):
            return 'research'
        
        # Examples
        if path_str.startswith('examples/'):
            return 'examples'
        
        # Core code
        if path_str.startswith('code_puppy/'):
            if '/plugins/' in path_str:
                return 'plugins'
            elif '/agents/' in path_str:
                return 'agents'
            elif '/tools/' in path_str:
                return 'tools'
            elif '/command_line/' in path_str:
                return 'command_line'
            elif '/mcp' in path_str:
                return 'mcp'
            else:
                return 'core_code'
        
        # Tests
        if path_str.startswith('tests/'):
            if '/plugins/' in path_str:
                return 'test_plugins'
            elif '/agents/' in path_str:
                return 'test_agents'
            elif '/mcp' in path_str:
                return 'test_mcp'
            else:
                return 'tests'
        
        # Scripts
        if path_str.endswith('.py') and '/' not in path_str:
            return 'scripts'
        
        # Misc
        if path_str.endswith(('.txt', '.csv', '.html', '.gif', '.png')):
            return 'misc_files'
        
        return 'other'
    
    def _determine_purpose(self) -> str:
        """Determine the file's purpose from its path and content."""
        path_str = str(self.path)
        name = self.path.name
        
        # Quick purpose mapping based on filename patterns
        purposes = {
            'AGENTS.md': 'Agent catalog documentation',
            'README.md': 'Project documentation',
            'CODE_PUPPY_OPTIMIZATION_PLAN.md': 'Optimization plan and architecture decisions',
            'LOCAL_VS_PYPI.md': 'Local vs PyPI installation comparison',
            'MASTER-PROMPT-SELF-OPTIMIZATION.md': 'Self-optimization master prompt',
            'OAUTH_TEST_RESULTS.md': 'OAuth testing results documentation',
            'VERIFY_OAUTH.md': 'OAuth verification guide',
            'SONNET_46_FEATURE.md': 'Sonnet 4.6 feature documentation',
            'CEREBRAS-GLM-4.7-OPTIMIZATION-VALIDATION.md': 'Cerebras GLM optimization validation',
            'check_installation.py': 'Installation verification script',
            'test_both_models.py': 'Dual model testing script',
            'verify_oauth_fix.py': 'OAuth fix verification script',
            'self-optimization-dashboard.html': 'Self-optimization tracking dashboard',
            'code-puppy-self-optimization-prompt.md': 'Self-optimization prompt template',
            'agent_creator_agent.py': 'Agent creator implementation',
            'agent_manager.py': 'Agent management system',
            'base_agent.py': 'Base agent class',
            'json_agent.py': 'JSON agent loader',
            'prompt_assembler.py': 'Centralized prompt assembly (OPT-000)',
            'claude_oauth_client.py': 'Claude OAuth client implementation',
            'fallback_config.py': 'Model fallback configuration',
            'model_capabilities.py': 'Model capability registry',
            'progressive_discovery.py': 'Progressive MCP server discovery',
        }
        
        if name in purposes:
            return purposes[name]
        
        # Pattern-based purposes
        if 'test_' in name:
            return f'Tests for {name.replace("test_", "").replace(".py", "")}'
        
        if path_str.startswith('research/'):
            if 'README' in name:
                return 'Research project overview'
            elif 'sources' in name:
                return 'Research sources and references'
            elif 'analysis' in name:
                return 'Research analysis results'
            elif 'recommendations' in name:
                return 'Research recommendations'
            return 'Research documentation'
        
        if path_str.startswith('examples/'):
            return 'Example code/documentation'
        
        if '/plugins/' in path_str:
            plugin_name = path_str.split('/plugins/')[1].split('/')[0]
            return f'Plugin: {plugin_name}'
        
        return 'Unknown purpose - needs investigation'
    
    def _assess_conflict_risk(self) -> str:
        """Assess risk of conflicts with upstream."""
        path_str = str(self.path)
        
        # High risk: Modified core files
        if self.status == 'modified':
            if any(x in path_str for x in ['base_agent.py', 'agent_manager.py', 'config.py']):
                return 'HIGH'
            elif path_str.startswith('code_puppy/') and not '/plugins/' in path_str:
                return 'MEDIUM'
            else:
                return 'LOW'
        
        # Low risk: New files that are clearly local additions
        if self.status == 'created':
            if any(x in path_str for x in ['research/', 'examples/', 'Log at', '.csv', '.html']):
                return 'NONE'
            elif '/plugins/' in path_str:
                # New plugins are low risk
                return 'LOW'
            elif path_str.endswith('.md') and not path_str.startswith('code_puppy/'):
                return 'NONE'
            elif path_str.startswith('tests/'):
                return 'LOW'
            else:
                return 'MEDIUM'
        
        return 'UNKNOWN'
    
    def __repr__(self):
        return f"FileInfo({self.path}, {self.status}, {self.category})"


class CodePuppyAuditor:
    """Audits local Code Puppy changes against upstream."""
    
    def __init__(self):
        self.root = Path.cwd()
        self.modified_files: List[FileInfo] = []
        self.created_files: List[FileInfo] = []
        self.all_files: List[FileInfo] = []
        
    def run_audit(self):
        """Run complete audit."""
        print("🔍 Code Puppy Local Changes Audit")
        print("=" * 80)
        print()
        
        self._check_git_status()
        self._analyze_files()
        self._generate_report()
    
    def _check_git_status(self):
        """Get git status to identify modified and new files."""
        print("📊 Checking git status...")
        
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                status_code = line[:2].strip()
                file_path = line[3:].strip().strip('"')
                path = Path(file_path)
                
                if status_code == 'M':
                    # Modified file
                    info = FileInfo(path, 'modified')
                    self.modified_files.append(info)
                    self.all_files.append(info)
                elif status_code == '??':
                    # Untracked (created) file or directory
                    if path.is_file():
                        info = FileInfo(path, 'created')
                        self.created_files.append(info)
                        self.all_files.append(info)
                    elif path.is_dir():
                        # Recursively add all files in untracked directory
                        for subfile in path.rglob('*'):
                            if subfile.is_file():
                                info = FileInfo(subfile, 'created')
                                self.created_files.append(info)
                                self.all_files.append(info)
            
            print(f"✅ Found {len(self.modified_files)} modified files")
            print(f"✅ Found {len(self.created_files)} created files")
            print()
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running git: {e}")
            sys.exit(1)
    
    def _analyze_files(self):
        """Analyze all files for detailed information."""
        print("🔬 Analyzing files...")
        print()
    
    def _generate_report(self):
        """Generate comprehensive report."""
        
        # Section 1: Summary Statistics
        self._print_summary_stats()
        
        # Section 2: Modified Files
        self._print_modified_files()
        
        # Section 3: Created Files by Category
        self._print_created_files_by_category()
        
        # Section 4: Conflict Risk Analysis
        self._print_conflict_analysis()
        
        # Section 5: Recommendations
        self._print_recommendations()
    
    def _print_summary_stats(self):
        """Print summary statistics."""
        print("📈 SUMMARY STATISTICS")
        print("=" * 80)
        
        total_modified = len(self.modified_files)
        total_created = len(self.created_files)
        total_files = total_modified + total_created
        
        # Calculate total lines of new code
        total_size = sum(f.size for f in self.all_files)
        total_kb = total_size / 1024
        total_mb = total_kb / 1024
        
        # Estimate lines (rough: 50 bytes per line average)
        estimated_lines = total_size // 50
        
        print(f"Total files changed:     {total_files}")
        print(f"  • Modified files:      {total_modified}")
        print(f"  • Created files:       {total_created}")
        print()
        print(f"Total size:              {total_mb:.2f} MB ({total_kb:.1f} KB)")
        print(f"Estimated total lines:   ~{estimated_lines:,}")
        print()
        
        # Category breakdown
        categories = defaultdict(int)
        for f in self.all_files:
            categories[f.category] += 1
        
        print("Files by category:")
        for category, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  • {category:20s} {count:4d} files")
        print()
    
    def _print_modified_files(self):
        """Print detailed list of modified files."""
        print("✏️  MODIFIED FILES")
        print("=" * 80)
        
        if not self.modified_files:
            print("No modified files.")
            print()
            return
        
        for f in sorted(self.modified_files, key=lambda x: str(x.path)):
            size_str = self._format_size(f.size)
            print(f"📝 {f.path}")
            print(f"   Size: {size_str:>10s} | Category: {f.category:15s} | Risk: {f.conflict_risk}")
            print(f"   Purpose: {f.purpose}")
            print()
    
    def _print_created_files_by_category(self):
        """Print created files organized by category."""
        print("🆕 CREATED FILES BY CATEGORY")
        print("=" * 80)
        
        if not self.created_files:
            print("No created files.")
            print()
            return
        
        # Group by category
        by_category = defaultdict(list)
        for f in self.created_files:
            by_category[f.category].append(f)
        
        # Print each category
        for category in sorted(by_category.keys()):
            files = sorted(by_category[category], key=lambda x: str(x.path))
            total_size = sum(f.size for f in files)
            
            print(f"\n📂 {category.upper().replace('_', ' ')} ({len(files)} files, {self._format_size(total_size)})")
            print("-" * 80)
            
            for f in files:
                size_str = self._format_size(f.size)
                print(f"  🔹 {f.path}")
                print(f"     Size: {size_str:>10s} | Risk: {f.conflict_risk:6s} | {f.purpose}")
            print()
    
    def _print_conflict_analysis(self):
        """Print conflict risk analysis."""
        print("⚠️  CONFLICT RISK ANALYSIS")
        print("=" * 80)
        
        # Group by risk level
        by_risk = defaultdict(list)
        for f in self.all_files:
            by_risk[f.conflict_risk].append(f)
        
        risk_order = ['HIGH', 'MEDIUM', 'LOW', 'NONE', 'UNKNOWN']
        
        for risk in risk_order:
            if risk not in by_risk:
                continue
            
            files = sorted(by_risk[risk], key=lambda x: str(x.path))
            
            emoji = {
                'HIGH': '🔴',
                'MEDIUM': '🟡',
                'LOW': '🟢',
                'NONE': '⚪',
                'UNKNOWN': '❓'
            }[risk]
            
            print(f"\n{emoji} {risk} RISK ({len(files)} files)")
            print("-" * 80)
            
            for f in files:
                status_icon = "✏️" if f.status == 'modified' else "🆕"
                print(f"  {status_icon} {f.path}")
                if risk in ['HIGH', 'MEDIUM']:
                    print(f"     ⚠️  {f.purpose}")
            
            print()
    
    def _print_recommendations(self):
        """Print recommendations for safe commits."""
        print("💡 RECOMMENDATIONS")
        print("=" * 80)
        
        high_risk = [f for f in self.all_files if f.conflict_risk == 'HIGH']
        medium_risk = [f for f in self.all_files if f.conflict_risk == 'MEDIUM']
        safe_files = [f for f in self.all_files if f.conflict_risk in ['LOW', 'NONE']]
        
        print("\n✅ SAFE TO COMMIT (Low/No conflict risk):")
        print("-" * 80)
        print("These files are safe additions that won't conflict with upstream:")
        print()
        
        safe_categories = defaultdict(int)
        for f in safe_files:
            safe_categories[f.category] += 1
        
        for category, count in sorted(safe_categories.items()):
            print(f"  • {category:20s} {count:4d} files")
        
        print(f"\nTotal safe files: {len(safe_files)}")
        print()
        
        if medium_risk:
            print("\n⚠️  REVIEW BEFORE COMMIT (Medium conflict risk):")
            print("-" * 80)
            print("These files should be reviewed before committing:")
            print()
            for f in sorted(medium_risk, key=lambda x: str(x.path)):
                print(f"  • {f.path}")
                print(f"    Reason: {f.purpose}")
            print()
        
        if high_risk:
            print("\n🔴 HIGH CONFLICT RISK - CAREFUL:")
            print("-" * 80)
            print("These modified core files are likely to conflict with upstream updates:")
            print()
            for f in sorted(high_risk, key=lambda x: str(x.path)):
                print(f"  • {f.path}")
                print(f"    Purpose: {f.purpose}")
            print()
            print("Recommendation: Consider rebasing these changes or creating patches.")
            print()
        
        # Specific recommendations
        print("\n📋 SPECIFIC RECOMMENDATIONS:")
        print("-" * 80)
        
        print("\n1. COMMIT IN STAGES:")
        print("   a) First commit: Safe documentation and research files")
        print("   b) Second commit: New plugins and examples")
        print("   c) Third commit: Test files")
        print("   d) Fourth commit: Core modifications (carefully review each)")
        
        print("\n2. CREATE FEATURE BRANCHES:")
        print("   - Create a branch for each major feature/optimization")
        print("   - Makes it easier to merge upstream changes")
        
        print("\n3. DOCUMENT CORE CHANGES:")
        print("   - For each modified core file, document WHY it was changed")
        print("   - Create ADR (Architecture Decision Record) files")
        
        print("\n4. CONSIDER PLUGIN-IFICATION:")
        print("   - Some core modifications could become plugins")
        print("   - Review: prompt_assembler, model_capabilities, fallback_config")
        
        print("\n5. TRACK UPSTREAM:")
        print("   - Regularly check for upstream updates")
        print("   - Rebase your changes on top of upstream main")
        
        print()
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size for display."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / 1024 / 1024:.2f} MB"


def main():
    """Run the audit."""
    auditor = CodePuppyAuditor()
    auditor.run_audit()
    
    print()
    print("=" * 80)
    print("Audit complete! 🐶")
    print()


if __name__ == '__main__':
    main()
