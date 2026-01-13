"""
Autonomous Multi-Agent Business Intelligence System - Schema Manager

Manages database schema information for SQL generation.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from ..config import settings

logger = logging.getLogger(__name__)


class SchemaManager:
    """
    Database schema management.
    
    Features:
    - Load schemas from files
    - Format schemas for LLM prompts
    - Schema validation
    """

    # Default sample schema
    DEFAULT_SCHEMA = {
        "default": {
            "tables": {
                "customers": {
                    "description": "Customer information",
                    "columns": {
                        "customer_id": "INTEGER PRIMARY KEY",
                        "customer_name": "TEXT",
                        "region": "TEXT",
                        "country": "TEXT",
                        "segment": "TEXT (Enterprise/SMB/Consumer)"
                    }
                },
                "products": {
                    "description": "Product catalog",
                    "columns": {
                        "product_id": "INTEGER PRIMARY KEY",
                        "product_name": "TEXT",
                        "category": "TEXT (Software/Hardware/Services)",
                        "unit_price": "REAL"
                    }
                },
                "sales": {
                    "description": "Sales transactions",
                    "columns": {
                        "sale_id": "INTEGER PRIMARY KEY",
                        "customer_id": "INTEGER (FK to customers)",
                        "product_id": "INTEGER (FK to products)",
                        "sale_date": "DATE",
                        "quantity": "INTEGER",
                        "revenue": "REAL",
                        "profit": "REAL"
                    },
                    "relationships": [
                        "customers.customer_id -> sales.customer_id",
                        "products.product_id -> sales.product_id"
                    ]
                }
            }
        }
    }

    def __init__(self, schema_dir: Optional[str] = None):
        """
        Initialize schema manager.
        
        Args:
            schema_dir: Directory containing schema JSON files
        """
        self.schema_dir = Path(schema_dir) if schema_dir else Path("data/schemas")
        self._schemas = self.DEFAULT_SCHEMA.copy()
        self._load_schemas()
        logger.info("Schema Manager initialized")

    def _load_schemas(self):
        """Load schemas from schema directory."""
        if not self.schema_dir.exists():
            self.schema_dir.mkdir(parents=True, exist_ok=True)
            # Save default schema
            self._save_default_schema()
            return

        for schema_file in self.schema_dir.glob("*.json"):
            try:
                with open(schema_file, 'r') as f:
                    schema_data = json.load(f)
                    db_name = schema_file.stem
                    self._schemas[db_name] = schema_data
                    logger.info(f"Loaded schema: {db_name}")
            except Exception as e:
                logger.warning(f"Failed to load schema {schema_file}: {e}")

    def _save_default_schema(self):
        """Save default schema to file."""
        default_file = self.schema_dir / "default.json"
        with open(default_file, 'w') as f:
            json.dump(self.DEFAULT_SCHEMA["default"], f, indent=2)
        logger.info("Saved default schema")

    def get_schema(self, database: str = "default") -> Dict[str, Any]:
        """
        Get schema for a database.
        
        Args:
            database: Database name
            
        Returns:
            Schema dictionary
        """
        return self._schemas.get(database, self._schemas.get("default", {}))

    def get_schema_for_prompt(self, database: str = "default") -> str:
        """
        Format schema for LLM prompt.
        
        Args:
            database: Database name
            
        Returns:
            Formatted schema string
        """
        schema = self.get_schema(database)
        if not schema:
            return "No schema available."

        lines = ["Database Schema:"]
        
        tables = schema.get("tables", {})
        for table_name, table_info in tables.items():
            lines.append(f"\nTable: {table_name}")
            
            if "description" in table_info:
                lines.append(f"  Description: {table_info['description']}")
            
            if "columns" in table_info:
                lines.append("  Columns:")
                for col_name, col_type in table_info["columns"].items():
                    lines.append(f"    - {col_name}: {col_type}")
            
            if "relationships" in table_info:
                lines.append("  Relationships:")
                for rel in table_info["relationships"]:
                    lines.append(f"    - {rel}")

        return "\n".join(lines)

    def get_table_names(self, database: str = "default") -> List[str]:
        """Get list of table names."""
        schema = self.get_schema(database)
        return list(schema.get("tables", {}).keys())

    def get_column_names(
        self,
        database: str = "default",
        table: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Get column names for tables.
        
        Args:
            database: Database name
            table: Specific table (None for all)
            
        Returns:
            Dict mapping table names to column lists
        """
        schema = self.get_schema(database)
        tables = schema.get("tables", {})
        
        result = {}
        for table_name, table_info in tables.items():
            if table is None or table_name == table:
                columns = table_info.get("columns", {})
                result[table_name] = list(columns.keys())
        
        return result

    def add_schema(
        self,
        database: str,
        schema: Dict[str, Any],
        save: bool = True
    ):
        """
        Add or update a schema.
        
        Args:
            database: Database name
            schema: Schema dictionary
            save: Whether to persist to file
        """
        self._schemas[database] = schema
        
        if save:
            schema_file = self.schema_dir / f"{database}.json"
            with open(schema_file, 'w') as f:
                json.dump(schema, f, indent=2)
            logger.info(f"Saved schema: {database}")

    def infer_schema_from_db(self, connection_string: str) -> Dict[str, Any]:
        """
        Infer schema from database connection.
        
        Args:
            connection_string: SQLAlchemy connection string
            
        Returns:
            Inferred schema dictionary
        """
        try:
            from sqlalchemy import create_engine, inspect
            
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            
            schema = {"tables": {}}
            
            for table_name in inspector.get_table_names():
                columns = {}
                for column in inspector.get_columns(table_name):
                    col_type = str(column["type"])
                    columns[column["name"]] = col_type
                
                # Get foreign keys
                fks = inspector.get_foreign_keys(table_name)
                relationships = []
                for fk in fks:
                    ref_table = fk["referred_table"]
                    ref_cols = fk["referred_columns"]
                    local_cols = fk["constrained_columns"]
                    rel = f"{ref_table}.{ref_cols[0]} -> {table_name}.{local_cols[0]}"
                    relationships.append(rel)
                
                schema["tables"][table_name] = {
                    "columns": columns,
                    "relationships": relationships
                }
            
            return schema
            
        except Exception as e:
            logger.error(f"Failed to infer schema: {e}")
            return {}

    def validate_query_tables(
        self,
        sql: str,
        database: str = "default"
    ) -> tuple:
        """
        Validate that SQL references valid tables.
        
        Args:
            sql: SQL query
            database: Database name
            
        Returns:
            (is_valid, list of invalid table references)
        """
        import re
        
        valid_tables = set(self.get_table_names(database))
        
        # Extract table names from SQL (simplified)
        sql_upper = sql.upper()
        
        # Find FROM and JOIN clauses
        from_pattern = r"FROM\s+(\w+)"
        join_pattern = r"JOIN\s+(\w+)"
        
        found_tables = set()
        for match in re.finditer(from_pattern, sql_upper):
            found_tables.add(match.group(1).lower())
        for match in re.finditer(join_pattern, sql_upper):
            found_tables.add(match.group(1).lower())
        
        invalid = found_tables - valid_tables
        
        return len(invalid) == 0, list(invalid)
