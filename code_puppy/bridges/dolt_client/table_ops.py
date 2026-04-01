"""Table operations for Dolt client."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from .models import DoltSchemaColumn, DoltSQLResult, DoltTableSchema

if TYPE_CHECKING:
    from .client import DoltClient


class TableOperations:
    """Handles table-related operations for DoltClient."""

    def __init__(self, client: "DoltClient"):
        self._client = client

    async def create(
        self,
        name: str,
        schema: Union[str, List[DoltSchemaColumn]],
        as_select: Optional[str] = None,
    ) -> DoltSQLResult:
        """Create a table.

        Args:
            name: Table name
            schema: SQL schema definition or list of columns
            as_select: Create from SELECT query

        Returns:
            DoltSQLResult
        """
        if isinstance(schema, list):
            # Build CREATE TABLE from columns
            columns_sql = ", ".join(
                f"{col.name} {col.type}"
                + (" NOT NULL" if not col.nullable else "")
                + (f" DEFAULT {col.default}" if col.default else "")
                + (" PRIMARY KEY" if col.primary_key else "")
                for col in schema
            )
            query = f"CREATE TABLE {name} ({columns_sql})"
        else:
            query = f"CREATE TABLE {name} ({schema})"

        if as_select:
            query += f" AS {as_select}"

        return await self._client.sql(query)

    async def drop(self, name: str, if_exists: bool = True) -> DoltSQLResult:
        """Drop a table.

        Args:
            name: Table name
            if_exists: Only drop if exists

        Returns:
            DoltSQLResult
        """
        query = "DROP TABLE "
        if if_exists:
            query += "IF EXISTS "
        query += name
        return await self._client.sql(query)

    async def import_data(
        self,
        table: str,
        file_path: Union[str, Path],
        file_format: str = "csv",
        continue_on_error: bool = False,
    ) -> str:
        """Import data into a table.

        Args:
            table: Target table name
            file_path: Path to import file
            file_format: File format (csv, json, parquet)
            continue_on_error: Continue on import errors

        Returns:
            Import result
        """
        args = ["table", "import", "-u", table, str(file_path)]

        if file_format == "json":
            args.append("--json")
        elif file_format == "parquet":
            args.append("--parquet")
        if continue_on_error:
            args.append("--continue")

        result = await self._client._run_cmd(args, json_output=False)
        return result.strip()

    async def export_data(
        self,
        table: str,
        file_path: Union[str, Path],
        file_format: str = "csv",
    ) -> str:
        """Export table data.

        Args:
            table: Table name to export
            file_path: Output file path
            file_format: Export format (csv, json, parquet, sql)

        Returns:
            Export result
        """
        args = ["table", "export", table, str(file_path)]

        if file_format == "json":
            args.append("--json")
        elif file_format == "parquet":
            args.append("--parquet")
        elif file_format == "sql":
            args.append("--sql")

        result = await self._client._run_cmd(args, json_output=False)
        return result.strip()

    async def list_tables(self) -> List[str]:
        """List all tables.

        Returns:
            List of table names
        """
        result = await self._client._run_cmd(["table", "ls"], json_output=False)
        tables = []
        for line in result.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("Tables"):
                tables.append(line)
        return tables

    async def show_schema(
        self,
        table: Optional[str] = None,
    ) -> Union[DoltTableSchema, Dict[str, DoltTableSchema]]:
        """Show table schema.

        Args:
            table: Specific table, or None for all tables

        Returns:
            Single schema or dict of all schemas
        """
        args = ["schema", "show"]
        if table:
            args.append(table)

        result = await self._client._run_cmd(args, json_output=False)

        # Parse schema output
        schemas = {}
        current_table = None
        columns = []
        primary_keys = []

        for line in result.strip().split("\n"):
            line = line.strip()
            if line.startswith("CREATE TABLE"):
                if current_table:
                    schemas[current_table] = DoltTableSchema(
                        table_name=current_table,
                        columns=columns,
                        primary_key=primary_keys,
                    )
                current_table = line.split()[-1].rstrip("(")
                columns = []
                primary_keys = []
            elif line and current_table:
                # Parse column definition
                parts = line.rstrip(",").split()
                if len(parts) >= 2:
                    col_name = parts[0]
                    col_type = " ".join(parts[1:]).upper()
                    nullable = "NOT NULL" not in col_type
                    default = None
                    is_pk = "PRIMARY KEY" in col_type

                    col_type = (
                        col_type.replace("NOT NULL", "")
                        .replace("PRIMARY KEY", "")
                        .strip()
                    )

                    if "DEFAULT" in col_type:
                        type_parts = col_type.split("DEFAULT")
                        col_type = type_parts[0].strip()
                        default = type_parts[1].strip() if len(type_parts) > 1 else None

                    columns.append(
                        DoltSchemaColumn(
                            name=col_name,
                            type=col_type,
                            nullable=nullable,
                            default=default,
                            primary_key=is_pk,
                        )
                    )

        if current_table:
            schemas[current_table] = DoltTableSchema(
                table_name=current_table,
                columns=columns,
                primary_key=primary_keys,
            )

        if table:
            return schemas.get(table, DoltTableSchema(table_name=table, columns=[]))
        return schemas
