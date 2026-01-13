"""
Autonomous Multi-Agent Business Intelligence System - Vector Store

ChromaDB-based vector store for RAG (Retrieval Augmented Generation).
Stores query examples, schema documentation, and business insights.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB vector store for RAG.
    
    Collections:
    - query_examples: Similar query retrieval
    - database_schemas: Schema documentation
    - business_insights: Domain knowledge
    """

    COLLECTIONS = {
        "query_examples": "Natural language to SQL query examples",
        "database_schemas": "Database schema documentation",
        "business_insights": "Business domain knowledge",
        "unstructured_docs": "Internal business documents and unstructured knowledge",
    }

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        """
        Initialize vector store.
        
        Args:
            persist_dir: Directory for ChromaDB persistence
            embedding_model: Sentence transformer model name
        """
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.embedding_model = embedding_model or settings.embedding_model
        
        self._client = None
        self._embedding_fn = None
        self._collections = {}
        
        self._initialize()

    def _initialize(self):
        """Initialize ChromaDB client and collections."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            # Create persist directory if needed
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

            # Initialize client
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Initialize embedding function
            self._embedding_fn = self._get_embedding_function()

            # Initialize collections
            for name, description in self.COLLECTIONS.items():
                self._collections[name] = self._get_or_create_collection(name)

            logger.info(f"Vector store initialized at {self.persist_dir}")

        except ImportError as e:
            logger.error(f"ChromaDB not installed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise

    def _get_embedding_function(self):
        """Get sentence transformer embedding function."""
        try:
            from chromadb.utils import embedding_functions
            
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )
        except Exception as e:
            logger.warning(f"Failed to load embedding function: {e}")
            return None

    def _get_or_create_collection(self, name: str):
        """Get or create a collection."""
        try:
            return self._client.get_or_create_collection(
                name=name,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            raise

    # -------------------------------------------------------------------------
    # Query Examples
    # -------------------------------------------------------------------------

    def add_query_examples(self, examples: List[Dict[str, Any]]) -> int:
        """
        Add query examples to vector store.
        
        Args:
            examples: List of {natural_query, sql_query, metadata}
            
        Returns:
            Number of examples added
        """
        collection = self._collections["query_examples"]
        
        documents = []
        metadatas = []
        ids = []
        
        existing_count = collection.count()

        for i, example in enumerate(examples):
            doc_id = f"query_{existing_count + i}"
            
            documents.append(example["natural_query"])
            metadatas.append({
                "sql_query": example["sql_query"],
                "complexity": example.get("complexity", "medium"),
                "accuracy": str(example.get("accuracy", 0.9)),
                "database": example.get("database", "default"),
            })
            ids.append(doc_id)

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Added {len(examples)} query examples")
        return len(examples)

    def search_similar_queries(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar queries.
        
        Args:
            query: Natural language query
            top_k: Number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar queries with SQL and metadata
        """
        collection = self._collections["query_examples"]

        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count())
        )

        similar_queries = []
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i]
            similarity = 1 - distance  # Convert distance to similarity

            if similarity >= min_similarity:
                similar_queries.append({
                    "natural_query": doc,
                    "sql_query": results["metadatas"][0][i]["sql_query"],
                    "similarity": round(similarity, 3),
                    "complexity": results["metadatas"][0][i]["complexity"],
                    "id": results["ids"][0][i]
                })

        return similar_queries

    # -------------------------------------------------------------------------
    # Schema Documentation
    # -------------------------------------------------------------------------

    def add_schema_documentation(self, schemas: List[Dict[str, Any]]) -> int:
        """
        Add database schema documentation.
        
        Args:
            schemas: List of {table_name, description, columns, relationships}
            
        Returns:
            Number of schemas added
        """
        collection = self._collections["database_schemas"]

        documents = []
        metadatas = []
        ids = []

        for schema in schemas:
            # Create searchable description
            description = f"{schema['table_name']}: {schema['description']}"
            if schema.get("columns"):
                cols = ", ".join(schema["columns"])
                description += f". Columns: {cols}"

            documents.append(description)
            metadatas.append({
                "table_name": schema["table_name"],
                "columns": str(schema.get("columns", [])),
                "relationships": str(schema.get("relationships", [])),
                "database": schema.get("database", "default"),
            })
            ids.append(f"schema_{schema['table_name']}")

        # Upsert to handle duplicates
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Added {len(schemas)} schema documents")
        return len(schemas)

    def search_relevant_schemas(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find relevant database schemas for a query.
        
        Args:
            query: Natural language query
            top_k: Number of results
            
        Returns:
            List of relevant schemas
        """
        collection = self._collections["database_schemas"]

        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count())
        )

        schemas = []
        for i in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][i]
            schemas.append({
                "table_name": metadata["table_name"],
                "description": results["documents"][0][i],
                "columns": eval(metadata["columns"]) if metadata["columns"] != "[]" else [],
                "relevance": round(1 - results["distances"][0][i], 3)
            })

        return schemas

    # -------------------------------------------------------------------------
    # Business Insights
    # -------------------------------------------------------------------------

    def add_business_insights(self, insights: List[Dict[str, Any]]) -> int:
        """
        Add business domain knowledge.
        
        Args:
            insights: List of {content, category, keywords}
            
        Returns:
            Number of insights added
        """
        collection = self._collections["business_insights"]

        documents = []
        metadatas = []
        ids = []
        
        existing_count = collection.count()

        for i, insight in enumerate(insights):
            documents.append(insight["content"])
            metadatas.append({
                "category": insight.get("category", "general"),
                "keywords": str(insight.get("keywords", [])),
                "source": insight.get("source", "manual"),
            })
            ids.append(f"insight_{existing_count + i}")

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Added {len(insights)} business insights")
        return len(insights)

    def search_insights(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant business insights.
        
        Args:
            query: Search query
            category: Optional category filter
            top_k: Number of results
            
        Returns:
            List of relevant insights
        """
        collection = self._collections["business_insights"]

        if collection.count() == 0:
            return []

        where_filter = {"category": category} if category else None

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count()),
            where=where_filter
        )

        insights = []
        for i, doc in enumerate(results["documents"][0]):
            insights.append({
                "content": doc,
                "category": results["metadatas"][0][i]["category"],
                "relevance": round(1 - results["distances"][0][i], 3)
            })

        return insights

    # -------------------------------------------------------------------------
    # Unstructured Documents (Phase 2: Cross-Modal Data Mesh)
    # -------------------------------------------------------------------------

    def add_unstructured_document(
        self,
        file_path: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add unstructured document (PDF, Docx, etc.) to vector store.
        
        Parses document, chunks into ~500-word segments with 50-word overlap,
        and stores in unstructured_docs collection.
        
        Args:
            file_path: Path to document file
            metadata: Optional metadata (document_type, date, author, etc.)
            
        Returns:
            Number of chunks added
        """
        collection = self._collections["unstructured_docs"]
        
        try:
            from pathlib import Path
            import hashlib
            
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Document not found: {file_path}")
            
            # Parse document based on file type
            text_content = self._parse_document(file_path)
            
            if not text_content or len(text_content.strip()) == 0:
                logger.warning(f"No text extracted from {file_path}")
                return 0
            
            # Chunk text into segments (~500 words with 50-word overlap)
            chunks = self._chunk_text(text_content, chunk_size=500, overlap=50)
            
            # Generate unique document ID
            doc_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
            
            # Prepare documents for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            base_metadata = metadata or {}
            base_metadata.update({
                "source_file": str(file_path.name),
                "file_type": file_path.suffix[1:],  # Remove leading dot
                "total_chunks": len(chunks),
            })
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                chunk_metadata = base_metadata.copy()
                chunk_metadata["chunk_index"] = str(i)
                chunk_metadata["word_count"] = str(len(chunk.split()))
                metadatas.append(chunk_metadata)
                ids.append(f"doc_{doc_hash}_chunk_{i}")
            
            # Add to ChromaDB
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks from {file_path.name}")
            return len(chunks)
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to add document {file_path}: {e}")
            raise
    
    def _parse_document(self, file_path: Path) -> str:
        """
        Parse document content based on file type.
        
        Args:
            file_path: Path to document
            
        Returns:
            Extracted text content
        """
        file_ext = file_path.suffix.lower()
        
        try:
            # PDF parsing
            if file_ext == ".pdf":
                return self._parse_pdf(file_path)
            
            # DOCX parsing
            elif file_ext in [".docx", ".doc"]:
                return self._parse_docx(file_path)
            
            # Plain text files
            elif file_ext in [".txt", ".md", ".csv"]:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return ""
    
    def _parse_pdf(self, file_path: Path) -> str:
        """
        Parse PDF using PyMuPDF (fitz).
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            import fitz  # PyMuPDF
            
            text_parts = []
            with fitz.open(file_path) as doc:
                for page in doc:
                    text_parts.append(page.get_text())
            
            return "\n".join(text_parts)
            
        except ImportError:
            logger.warning("PyMuPDF not installed, trying fallback PDF parser")
            return self._parse_pdf_fallback(file_path)
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            return ""
    
    def _parse_pdf_fallback(self, file_path: Path) -> str:
        """
        Fallback PDF parser using pypdf or pdfplumber.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            # Try pypdf first
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(file_path))
                text_parts = [page.extract_text() for page in reader.pages]
                return "\n".join(text_parts)
            except ImportError:
                pass
            
            # Try pdfplumber
            try:
                import pdfplumber
                text_parts = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                return "\n".join(text_parts)
            except ImportError:
                pass
            
            logger.error("No PDF parsing library available (install pymupdf, pypdf, or pdfplumber)")
            return ""
            
        except Exception as e:
            logger.error(f"Fallback PDF parsing failed: {e}")
            return ""
    
    def _parse_docx(self, file_path: Path) -> str:
        """
        Parse DOCX using python-docx.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        try:
            from docx import Document
            
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(paragraphs)
            
        except ImportError:
            logger.error("python-docx not installed (pip install python-docx)")
            return ""
        except Exception as e:
            logger.error(f"DOCX parsing failed: {e}")
            return ""
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Chunk text into segments with word-based overlap.
        
        Args:
            text: Text to chunk
            chunk_size: Target number of words per chunk
            overlap: Number of overlapping words between chunks
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            # Get chunk
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Only add non-empty chunks
            if chunk_text.strip():
                chunks.append(chunk_text)
            
            # Move forward by (chunk_size - overlap)
            i += max(1, chunk_size - overlap)
        
        return chunks
    
    def search_documents(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search unstructured documents for relevant snippets.
        
        Args:
            query: Search query
            top_k: Number of results
            filter_metadata: Optional metadata filters (e.g., document_type)
            
        Returns:
            List of relevant document snippets with metadata
        """
        collection = self._collections["unstructured_docs"]
        
        try:
            if collection.count() == 0:
                logger.warning("No documents in collection")
                return []
            
            # Query ChromaDB
            results = collection.query(
                query_texts=[query],
                n_results=min(top_k, collection.count()),
                where=filter_metadata
            )
            
            # Format results
            documents = []
            for i in range(len(results["documents"][0])):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                
                documents.append({
                    "content": results["documents"][0][i],
                    "source_file": metadata.get("source_file", "unknown"),
                    "file_type": metadata.get("file_type", "unknown"),
                    "chunk_index": metadata.get("chunk_index", "0"),
                    "relevance": round(1 - distance, 3),
                    "metadata": metadata,
                    "id": results["ids"][0][i]
                })
            
            logger.info(f"Found {len(documents)} relevant document snippets")
            return documents
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        stats = {
            "persist_dir": self.persist_dir,
            "embedding_model": self.embedding_model,
            "collections": {}
        }

        for name, collection in self._collections.items():
            stats["collections"][name] = {
                "count": collection.count(),
                "metadata": collection.metadata
            }

        return stats

    def clear_collection(self, collection_name: str) -> bool:
        """
        Clear a collection.
        
        Args:
            collection_name: Name of collection to clear
            
        Returns:
            True if successful
        """
        if collection_name not in self._collections:
            logger.warning(f"Collection {collection_name} not found")
            return False

        try:
            self._client.delete_collection(collection_name)
            self._collections[collection_name] = self._get_or_create_collection(
                collection_name
            )
            logger.info(f"Cleared collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False

    def reset_all(self) -> bool:
        """Reset all collections."""
        try:
            self._client.reset()
            for name in self.COLLECTIONS:
                self._collections[name] = self._get_or_create_collection(name)
            logger.info("Reset all collections")
            return True
        except Exception as e:
            logger.error(f"Failed to reset: {e}")
            return False
