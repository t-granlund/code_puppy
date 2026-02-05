"""Skills Metadata Parser - YAML Frontmatter Support.

Parses skill markdown files with YAML frontmatter for rich metadata,
following the PAI Agent SDK and pydantic-deepagents patterns.

Example SKILL.md format:
```markdown
---
name: code-review
version: 1.0.0
description: Python code quality review
author: Code Puppy Team
triggers:
  - "review"
  - "check code"
  - "analyze quality"
tags:
  - python
  - quality
  - security
requires:
  - ruff
  - mypy
priority: high
---

# Code Review Skill

Your instructions here...
```
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """Metadata parsed from SKILL.md YAML frontmatter."""

    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    triggers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)  # Required packages/tools
    priority: str = "medium"  # low, medium, high
    enabled: bool = True
    
    # Runtime info
    path: Optional[Path] = None
    content: str = ""  # Full markdown content (without frontmatter)
    
    @classmethod
    def from_yaml(cls, data: Dict[str, Any], path: Optional[Path] = None) -> "SkillMetadata":
        """Create SkillMetadata from parsed YAML dict."""
        return cls(
            name=data.get("name", path.stem if path else "unknown"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            triggers=data.get("triggers", []),
            tags=data.get("tags", []),
            requires=data.get("requires", []),
            priority=data.get("priority", "medium"),
            enabled=data.get("enabled", True),
            path=path,
        )


# Regex to match YAML frontmatter
FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n",
    re.DOTALL | re.MULTILINE,
)


def parse_skill_file(file_path: Path) -> Optional[SkillMetadata]:
    """Parse a skill markdown file with optional YAML frontmatter.
    
    Args:
        file_path: Path to the SKILL.md file
        
    Returns:
        SkillMetadata if parsing succeeds, None otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read skill file {file_path}: {e}")
        return None
    
    # Try to extract frontmatter
    match = FRONTMATTER_PATTERN.match(content)
    
    if match:
        # Has YAML frontmatter
        yaml_content = match.group(1)
        markdown_content = content[match.end():]
        
        try:
            data = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML in {file_path}: {e}")
            data = {}
        
        metadata = SkillMetadata.from_yaml(data, file_path)
        metadata.content = markdown_content.strip()
    else:
        # No frontmatter - extract info from content
        metadata = _parse_legacy_skill(content, file_path)
    
    return metadata


def _parse_legacy_skill(content: str, file_path: Path) -> SkillMetadata:
    """Parse a skill file without YAML frontmatter.
    
    Extracts name from first heading, description from first paragraph.
    """
    lines = content.split("\n")
    name = file_path.stem
    description = ""
    
    # Try to find first heading
    for i, line in enumerate(lines):
        if line.startswith("# "):
            name = line[2:].strip()
            # Look for description in following paragraph
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip() and not lines[j].startswith("#"):
                    description = lines[j].strip()
                    break
            break
    
    return SkillMetadata(
        name=name,
        description=description,
        path=file_path,
        content=content,
    )


class SkillRegistry:
    """Registry for discovered skills with hot-reload support."""

    def __init__(self, skill_dirs: Optional[List[Path]] = None):
        self._skills: Dict[str, SkillMetadata] = {}
        self._skill_dirs: List[Path] = skill_dirs or []
        self._trigger_index: Dict[str, Set[str]] = {}  # trigger -> skill names
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> skill names
        self._last_scan_time: float = 0.0
    
    def add_skill_directory(self, path: Path) -> None:
        """Add a directory to scan for skills."""
        if path not in self._skill_dirs:
            self._skill_dirs.append(path)
    
    def scan_skills(self) -> int:
        """Scan all skill directories and load skills.
        
        Returns:
            Number of skills discovered
        """
        import time
        
        self._skills.clear()
        self._trigger_index.clear()
        self._tag_index.clear()
        
        for skill_dir in self._skill_dirs:
            if not skill_dir.exists():
                logger.debug(f"Skill directory does not exist: {skill_dir}")
                continue
            
            # Find all SKILL.md files
            for skill_file in skill_dir.rglob("SKILL.md"):
                metadata = parse_skill_file(skill_file)
                if metadata and metadata.enabled:
                    self._register_skill(metadata)
        
        self._last_scan_time = time.time()
        logger.info(f"Discovered {len(self._skills)} skills")
        return len(self._skills)
    
    def _register_skill(self, metadata: SkillMetadata) -> None:
        """Register a skill and update indexes."""
        self._skills[metadata.name] = metadata
        
        # Update trigger index
        for trigger in metadata.triggers:
            trigger_lower = trigger.lower()
            if trigger_lower not in self._trigger_index:
                self._trigger_index[trigger_lower] = set()
            self._trigger_index[trigger_lower].add(metadata.name)
        
        # Update tag index
        for tag in metadata.tags:
            tag_lower = tag.lower()
            if tag_lower not in self._tag_index:
                self._tag_index[tag_lower] = set()
            self._tag_index[tag_lower].add(metadata.name)
    
    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def list_skills(self) -> List[SkillMetadata]:
        """List all registered skills."""
        return list(self._skills.values())
    
    def find_by_trigger(self, text: str) -> List[SkillMetadata]:
        """Find skills matching a trigger phrase.
        
        Args:
            text: User input text to match against triggers
            
        Returns:
            List of matching skills, sorted by priority
        """
        text_lower = text.lower()
        matches = set()
        
        for trigger, skill_names in self._trigger_index.items():
            if trigger in text_lower:
                matches.update(skill_names)
        
        # Get skills and sort by priority
        result = [self._skills[name] for name in matches if name in self._skills]
        priority_order = {"high": 0, "medium": 1, "low": 2}
        result.sort(key=lambda s: priority_order.get(s.priority, 1))
        
        return result
    
    def find_by_tags(self, tags: List[str]) -> List[SkillMetadata]:
        """Find skills with matching tags."""
        matches = set()
        
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in self._tag_index:
                matches.update(self._tag_index[tag_lower])
        
        return [self._skills[name] for name in matches if name in self._skills]
    
    def search(self, query: str) -> List[SkillMetadata]:
        """Search skills by name, description, triggers, or tags."""
        query_lower = query.lower()
        results = []
        
        for skill in self._skills.values():
            # Check name
            if query_lower in skill.name.lower():
                results.append(skill)
                continue
            
            # Check description
            if query_lower in skill.description.lower():
                results.append(skill)
                continue
            
            # Check triggers
            if any(query_lower in t.lower() for t in skill.triggers):
                results.append(skill)
                continue
            
            # Check tags
            if any(query_lower in t.lower() for t in skill.tags):
                results.append(skill)
                continue
        
        return results
    
    def get_skill_content(self, name: str) -> Optional[str]:
        """Get the full content of a skill."""
        skill = self._skills.get(name)
        if skill:
            return skill.content
        return None
    
    def reload(self) -> int:
        """Hot-reload all skills."""
        return self.scan_skills()


# Global registry instance
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Get or create the global skill registry."""
    global _skill_registry
    if _skill_registry is None:
        from code_puppy.config import get_value
        from pathlib import Path
        
        # Get skill directories from config
        skill_dirs_str = get_value("skill_directories") or ""
        skill_dirs = [
            Path(d.strip()) 
            for d in skill_dirs_str.split(",") 
            if d.strip()
        ]
        
        # Add default skill directory
        default_skill_dir = Path.home() / ".code_puppy" / "skills"
        if default_skill_dir not in skill_dirs:
            skill_dirs.append(default_skill_dir)
        
        # Add workspace skills if available
        try:
            import os
            workspace = os.getcwd()
            workspace_skills = Path(workspace) / ".copilot" / "skills"
            if workspace_skills.exists():
                skill_dirs.append(workspace_skills)
        except Exception:
            pass
        
        _skill_registry = SkillRegistry(skill_dirs)
        _skill_registry.scan_skills()
    
    return _skill_registry


def reload_skills() -> int:
    """Reload all skills from directories."""
    registry = get_skill_registry()
    return registry.reload()


def create_skill_template(
    skill_dir: Path,
    name: str,
    description: str = "",
    triggers: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> Path:
    """Create a new skill from template.
    
    Args:
        skill_dir: Directory to create skill in
        name: Skill name
        description: Skill description
        triggers: Trigger phrases
        tags: Tags for categorization
        
    Returns:
        Path to created SKILL.md file
    """
    skill_path = skill_dir / name
    skill_path.mkdir(parents=True, exist_ok=True)
    
    skill_file = skill_path / "SKILL.md"
    
    triggers = triggers or [name.replace("-", " ")]
    tags = tags or []
    
    content = f"""---
name: {name}
version: 1.0.0
description: {description or f"Skill for {name}"}
author: Code Puppy User
triggers:
{chr(10).join(f'  - "{t}"' for t in triggers)}
tags:
{chr(10).join(f'  - {t}' for t in tags) if tags else '  - general'}
priority: medium
---

# {name.replace("-", " ").title()}

{description or "Add your skill instructions here."}

## Usage

Describe how to use this skill.

## Examples

Provide example prompts and expected behavior.
"""
    
    skill_file.write_text(content, encoding="utf-8")
    logger.info(f"Created skill template: {skill_file}")
    
    return skill_file
