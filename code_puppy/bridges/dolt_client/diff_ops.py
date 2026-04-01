"""Diff operations for Dolt client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from .models import DoltDiffLine, DoltTableDiff

if TYPE_CHECKING:
    from .client import DoltClient


class DiffOperations:
    """Handles diff-related operations for DoltClient."""

    def __init__(self, client: "DoltClient"):
        self._client = client

    async def diff(
        self,
        from_branch: Optional[str] = None,
        to_branch: Optional[str] = None,
        table: Optional[str] = None,
        staged: bool = False,
        summary: bool = False,
    ) -> Union[List[DoltTableDiff], Dict[str, Any]]:
        """Get differences between commits or branches.

        Args:
            from_branch: Source branch/commit
            to_branch: Target branch/commit
            table: Specific table to diff
            staged: Show staged changes
            summary: Return summary only

        Returns:
            List of table diffs or summary dict
        """
        args = ["diff"]

        if summary:
            args.append("--stat")
        if staged:
            args.append("--staged")
        if table:
            args.append(table)
        if from_branch and to_branch:
            args.extend([from_branch, to_branch])
        elif from_branch:
            args.append(from_branch)

        result = await self._client._run_cmd(args, json_output=False)

        if summary:
            # Parse summary format
            summary_data = {"tables": {}, "total_changes": 0}
            for line in result.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        table_name = parts[0].strip()
                        changes = parts[1].strip()
                        summary_data["tables"][table_name] = changes
            return summary_data

        # Parse diff output
        diffs = []
        current_table = None
        current_lines = []

        for line in result.strip().split("\n"):
            if line.startswith("diff --dolt"):
                if current_table:
                    diffs.append(current_table)
                current_table = DoltTableDiff(
                    table_name=line.split()[-1] if len(line.split()) > 2 else "unknown",
                    diff_type="data",
                    lines=[],
                )
            elif line.startswith("+") and not line.startswith("+++"):
                current_lines.append(DoltDiffLine(
                    type="added",
                    content=line[1:],
                ))
            elif line.startswith("-") and not line.startswith("---"):
                current_lines.append(DoltDiffLine(
                    type="removed",
                    content=line[1:],
                ))

        if current_table:
            current_table.lines = current_lines
            diffs.append(current_table)

        return diffs

    async def schema_diff(
        self,
        from_branch: Optional[str] = None,
        to_branch: Optional[str] = None,
        table: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get schema differences.

        Args:
            from_branch: Source branch/commit
            to_branch: Target branch/commit
            table: Specific table

        Returns:
            Schema diff information
        """
        args = ["diff", "--schema"]
        if table:
            args.append(table)
        if from_branch and to_branch:
            args.extend([from_branch, to_branch])
        elif from_branch:
            args.append(from_branch)

        result = await self._client._run_cmd(args, json_output=False)
        return {"diff": result.strip()}
