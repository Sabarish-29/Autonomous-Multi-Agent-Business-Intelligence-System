"""
Librarian Agent - Schema Metadata Manager

This agent manages database schema metadata using ChromaDB for semantic retrieval.
Instead of passing the entire schema to the LLM, it retrieves only relevant tables
based on the user's query intent.
"""

import logging
import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LibrarianAgent:
    """
    Agent responsible for semantic schema retrieval and management.
    
    Uses ChromaDB to store table schemas with embeddings, enabling
    semantic search to retrieve only relevant tables for a given query.
    """
    
    def __init__(self, db_path: str = "./data/schema_library", use_chroma: Optional[bool] = None):
        """
        Initialize the Librarian Agent with ChromaDB.
        
        Args:
            db_path: Path to ChromaDB persistent storage
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        if use_chroma is None:
            use_chroma = os.getenv("DATAGENIE_TEST_MODE") != "1"

        self.use_chroma = bool(use_chroma)
        
        if not self.use_chroma:
            self.client = None
            self.schema_collection = None
            logger.info("Librarian Agent initialized in lightweight mode (Chroma disabled)")
            return

        try:
            # Defer importing chromadb (and any heavy embedding deps) until needed.
            import chromadb
            from chromadb.config import Settings

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create schema collection
            self.schema_collection = self.client.get_or_create_collection(
                name="database_schemas",
                metadata={"description": "Database table schemas with metadata"}
            )
            
            # Phase 2: Initialize unstructured documents collection
            self.unstructured_collection = self.client.get_or_create_collection(
                name="unstructured_docs",
                metadata={"description": "Internal business documents and unstructured knowledge"}
            )

            logger.info(
                f"Librarian Agent initialized with {self.schema_collection.count()} schemas "
                f"and {self.unstructured_collection.count()} document chunks"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Librarian Agent: {e}")
            self.client = None
            self.schema_collection = None

    def _fallback_db_path(self) -> Optional[Path]:
        """Best-effort SQLite path for lightweight schema introspection."""
        # Prefer the sample DB used across the repo/tests.
        candidate = Path("./data/sample/sample.db")
        if candidate.exists():
            return candidate
        return None

    def _fallback_retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        db_path = self._fallback_db_path()
        if not db_path:
            return []

        try:
            conn = sqlite3.connect(str(db_path))
            try:
                tables = [
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                ]

                query_lower = (query or "").lower()
                scored: List[tuple[int, str, List[str]]] = []
                for table in tables:
                    cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]
                    score = 0
                    if table.lower() in query_lower:
                        score += 3
                    for col in cols:
                        if col.lower() in query_lower:
                            score += 1
                    scored.append((score, table, cols))

                scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
                picked = scored[: max(1, top_k)]

                results: List[Dict[str, Any]] = []
                for score, table, cols in picked:
                    doc = f"Table: {table}\nColumns: {', '.join(cols)}"
                    results.append(
                        {
                            "document": doc,
                            "metadata": {"table_name": table, "column_names": cols, "score": score},
                            "distance": None,
                            "id": f"table_{table}",
                        }
                    )

                return results
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Fallback schema retrieval failed: {e}")
            return []
    
    def index_table_schema(
        self,
        table_name: str,
        schema_definition: str,
        columns: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Index a table schema into ChromaDB for semantic retrieval.
        
        Args:
            table_name: Name of the database table
            schema_definition: Full CREATE TABLE statement or schema description
            columns: List of column definitions with name, type, description
            metadata: Additional metadata (database name, relationships, etc.)
            
        Returns:
            bool: True if indexing successful
        """
        if not self.schema_collection:
            logger.error("Schema collection not initialized")
            return False
        
        try:
            # Build comprehensive document for embedding
            column_descriptions = []
            for col in columns:
                col_desc = f"{col.get('name', 'unknown')}: {col.get('type', 'unknown')}"
                if col.get('description'):
                    col_desc += f" - {col['description']}"
                column_descriptions.append(col_desc)
            
            # Create rich text for semantic search
            document_text = f"""
            Table: {table_name}
            Schema: {schema_definition}
            Columns: {', '.join([c.get('name', '') for c in columns])}
            Details: {' | '.join(column_descriptions)}
            """
            
            # Prepare metadata
            meta = metadata or {}
            meta.update({
                "table_name": table_name,
                "column_count": len(columns),
                # ChromaDB metadata values must be scalar types (no lists/dicts).
                "column_names": ", ".join([c.get('name', '') for c in columns])
            })
            
            # Add to ChromaDB
            self.schema_collection.add(
                documents=[document_text],
                metadatas=[meta],
                ids=[f"table_{table_name}"]
            )
            
            logger.info(f"Indexed schema for table: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index schema for {table_name}: {e}")
            return False
    
    def retrieve_relevant_schemas(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant table schemas based on query semantics.
        
        Args:
            query: User's natural language query
            top_k: Number of relevant schemas to retrieve
            filter_metadata: Optional metadata filters (e.g., specific database)
            
        Returns:
            List of relevant schema documents with metadata
        """
        if not self.schema_collection:
            # Lightweight mode: attempt SQLite introspection instead of semantic search.
            return self._fallback_retrieve(query=query, top_k=top_k)
        
        try:
            collection_count = self.schema_collection.count()
            if collection_count <= 0:
                return []

            # Query ChromaDB for semantically similar schemas
            results = self.schema_collection.query(
                query_texts=[query],
                n_results=max(1, min(top_k, collection_count)),
                where=filter_metadata
            )
            
            # Format results
            relevant_schemas = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    schema_info = {
                        'document': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results.get('distances') else None,
                        'id': results['ids'][0][i] if results['ids'] else None
                    }
                    relevant_schemas.append(schema_info)
            
            logger.info(f"Retrieved {len(relevant_schemas)} relevant schemas for query")
            return relevant_schemas
            
        except Exception as e:
            logger.error(f"Failed to retrieve schemas: {e}")
            return []
    
    def get_schema_by_table_name(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get specific schema by exact table name.
        
        Args:
            table_name: Exact table name
            
        Returns:
            Schema document with metadata or None
        """
        if not self.schema_collection:
            return None
        
        try:
            result = self.schema_collection.get(
                ids=[f"table_{table_name}"]
            )
            
            if result['documents']:
                return {
                    'document': result['documents'][0],
                    'metadata': result['metadatas'][0] if result['metadatas'] else {},
                    'id': result['ids'][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {e}")
            return None
    
    def list_all_tables(self) -> List[str]:
        """
        Get list of all indexed table names.
        
        Returns:
            List of table names
        """
        if not self.schema_collection:
            return []
        
        try:
            results = self.schema_collection.get()
            table_names = [
                meta.get('table_name', 'unknown')
                for meta in results.get('metadatas', [])
            ]
            return table_names
            
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []
    
    def build_focused_context(
        self,
        query: str,
        max_tables: int = 3
    ) -> str:
        """
        Build a focused schema context for LLM based on query.
        
        This is the main method to use - it retrieves relevant schemas
        and formats them into a concise context string for the LLM.
        
        Args:
            query: User's natural language query
            max_tables: Maximum number of tables to include in context
            
        Returns:
            Formatted schema context string
        """
        relevant_schemas = self.retrieve_relevant_schemas(query, top_k=max_tables)
        
        if not relevant_schemas:
            logger.warning("No relevant schemas found, returning empty context")
            return "No relevant database schemas available."
        
        # Build focused context
        context_parts = ["=== RELEVANT DATABASE SCHEMAS ===\n"]
        
        for schema in relevant_schemas:
            meta = schema.get('metadata', {})
            table_name = meta.get('table_name', 'unknown')
            columns = meta.get('column_names', [])
            if isinstance(columns, str):
                columns = [c.strip() for c in columns.split(',') if c.strip()]
            
            context_parts.append(f"\nTable: {table_name}")
            context_parts.append(f"Columns: {', '.join(columns)}")
            
            # Extract schema definition from document
            doc = schema.get('document', '')
            if 'Schema:' in doc:
                schema_def = doc.split('Schema:')[1].split('Columns:')[0].strip()
                context_parts.append(f"Definition: {schema_def[:200]}...")  # Truncate if too long
            
            context_parts.append("")  # Blank line between tables
        
        context_parts.append("=== END SCHEMAS ===")
        
        return "\n".join(context_parts)
    
    def retrieve_hybrid_context(
        self,
        query: str,
        top_k_sql: int = 3,
        top_k_docs: int = 5
    ) -> str:
        """
        Phase 2: Hybrid retrieval combining SQL schemas and business documents.
        
        Performs semantic search across both database schemas and unstructured
        documents, returning a unified context string for LLM consumption.
        
        Args:
            query: User's natural language query
            top_k_sql: Number of relevant SQL table schemas to retrieve
            top_k_docs: Number of relevant document snippets to retrieve
            
        Returns:
            Formatted hybrid context string with database and document sections
        """
        context_parts = []
        
        # Section 1: Database Schema Context
        try:
            sql_schemas = self.retrieve_relevant_schemas(query, top_k=top_k_sql)
            
            if sql_schemas:
                context_parts.append("### DATABASE SCHEMA CONTEXT\n")
                
                for idx, schema in enumerate(sql_schemas, 1):
                    meta = schema.get('metadata', {})
                    table_name = meta.get('table_name', 'unknown')
                    columns = meta.get('column_names', [])
                    
                    if isinstance(columns, str):
                        columns = [c.strip() for c in columns.split(',') if c.strip()]
                    
                    context_parts.append(f"{idx}. Table: {table_name}")
                    context_parts.append(f"   Columns: {', '.join(columns) if columns else 'N/A'}")
                    
                    # Add schema definition snippet
                    doc = schema.get('document', '')
                    if 'Schema:' in doc:
                        schema_def = doc.split('Schema:')[1].split('Columns:')[0].strip()
                        # Truncate long definitions
                        if len(schema_def) > 150:
                            schema_def = schema_def[:150] + "..."
                        context_parts.append(f"   Definition: {schema_def}")
                    
                    context_parts.append("")  # Blank line
            else:
                context_parts.append("### DATABASE SCHEMA CONTEXT\n")
                context_parts.append("No relevant database schemas found.\n")
                
        except Exception as e:
            logger.error(f"Failed to retrieve SQL schemas: {e}")
            context_parts.append("### DATABASE SCHEMA CONTEXT\n")
            context_parts.append(f"Error retrieving schemas: {str(e)}\n")
        
        # Section 2: Business Document Context
        try:
            if not self.unstructured_collection:
                context_parts.append("### BUSINESS DOCUMENT CONTEXT\n")
                context_parts.append("Unstructured document collection not initialized.\n")
            else:
                doc_count = self.unstructured_collection.count()
                
                if doc_count == 0:
                    context_parts.append("### BUSINESS DOCUMENT CONTEXT\n")
                    context_parts.append("No business documents indexed.\n")
                else:
                    # Query unstructured documents
                    doc_results = self.unstructured_collection.query(
                        query_texts=[query],
                        n_results=min(top_k_docs, doc_count)
                    )
                    
                    if doc_results['documents'] and doc_results['documents'][0]:
                        context_parts.append("### BUSINESS DOCUMENT CONTEXT\n")
                        
                        for idx, doc_text in enumerate(doc_results['documents'][0], 1):
                            metadata = doc_results['metadatas'][0][idx - 1] if doc_results['metadatas'] else {}
                            distance = doc_results['distances'][0][idx - 1] if doc_results.get('distances') else 0
                            relevance = round(1 - distance, 3)
                            
                            source_file = metadata.get('source_file', 'unknown')
                            chunk_idx = metadata.get('chunk_index', '0')
                            
                            context_parts.append(f"{idx}. Source: {source_file} (chunk {chunk_idx})")
                            context_parts.append(f"   Relevance: {relevance}")
                            
                            # Truncate long snippets
                            snippet = doc_text.strip()
                            if len(snippet) > 300:
                                snippet = snippet[:300] + "..."
                            context_parts.append(f"   Content: {snippet}")
                            context_parts.append("")  # Blank line
                    else:
                        context_parts.append("### BUSINESS DOCUMENT CONTEXT\n")
                        context_parts.append("No relevant documents found.\n")
                        
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            context_parts.append("### BUSINESS DOCUMENT CONTEXT\n")
            context_parts.append(f"Error retrieving documents: {str(e)}\n")
        
        # Combine all sections
        hybrid_context = "\n".join(context_parts)
        
        logger.info(
            f"Generated hybrid context: {len(sql_schemas) if 'sql_schemas' in locals() else 0} schemas, "
            f"{len(doc_results['documents'][0]) if 'doc_results' in locals() and doc_results['documents'] else 0} documents"
        )
        
        return hybrid_context
    
    def reset_collection(self) -> bool:
        """
        Reset the schema collection (use with caution).
        
        Returns:
            bool: True if reset successful
        """
        try:
            if self.client:
                self.client.delete_collection(name="database_schemas")
                self.schema_collection = self.client.get_or_create_collection(
                    name="database_schemas",
                    metadata={"description": "Database table schemas with metadata"}
                )
                logger.info("Schema collection reset successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False
