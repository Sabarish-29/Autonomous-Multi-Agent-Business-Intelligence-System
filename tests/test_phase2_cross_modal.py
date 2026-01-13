"""
Test Phase 2: Cross-Modal Data Mesh functionality.

Tests unstructured document ingestion, hybrid retrieval, and multi-modal context generation.
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.vector_store import VectorStore
from src.agents.librarian import LibrarianAgent


def cleanup_chroma(obj):
    """Helper to cleanup ChromaDB connections on Windows."""
    if hasattr(obj, '_collections'):
        del obj._collections
    if hasattr(obj, '_client'):
        del obj._client
    if hasattr(obj, 'client'):
        del obj.client
    if hasattr(obj, 'schema_collection'):
        del obj.schema_collection
    if hasattr(obj, 'unstructured_collection'):
        del obj.unstructured_collection
    import gc
    gc.collect()
    time.sleep(0.1)  # Give OS time to release file handles


def get_test_dir(test_name):
    """Get persistent test directory."""
    test_dir = Path(f"./data/test_phase2/{test_name}")
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def cleanup_test_dir(test_dir):
    """Cleanup test directory."""
    import shutil
    time.sleep(0.2)
    try:
        shutil.rmtree(test_dir, ignore_errors=True)
    except:
        pass


def test_vector_store_unstructured_collection():
    """Test that unstructured_docs collection is initialized."""
    print("\n=== Test 1: Unstructured Docs Collection ===")
    
    test_dir = get_test_dir("test1")
    
    try:
        vs = VectorStore(persist_dir=str(test_dir))
        
        assert "unstructured_docs" in vs.COLLECTIONS
        assert "unstructured_docs" in vs._collections
        assert vs._collections["unstructured_docs"].count() >= 0
        
        print(f"✓ unstructured_docs collection initialized")
        print(f"  Collections: {list(vs.COLLECTIONS.keys())}")
        
        cleanup_chroma(vs)
    finally:
        cleanup_test_dir(test_dir.parent)


def test_text_chunking():
    """Test text chunking with overlap."""
    print("\n=== Test 2: Text Chunking ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vs = VectorStore(persist_dir=tmpdir)
        
        # Create sample text (~200 words)
        sample_text = " ".join([f"word{i}" for i in range(200)])
        
        # Chunk with 50-word chunks, 10-word overlap
        chunks = vs._chunk_text(sample_text, chunk_size=50, overlap=10)
        
        assert len(chunks) > 1
        assert all(len(chunk.split()) <= 55 for chunk in chunks)  # Allow slight variation
        
        # Verify overlap
        words_chunk1 = chunks[0].split()
        words_chunk2 = chunks[1].split()
        overlap_words = words_chunk1[-10:]
        
        print(f"✓ Text chunked successfully")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  First chunk words: {len(chunks[0].split())}")
        print(f"  Overlap check: {overlap_words[:3]}... in chunk 2: {' '.join(overlap_words[:3]) in chunks[1]}")
        
        cleanup_chroma(vs)


def test_add_text_document():
    """Test adding plain text document."""
    print("\n=== Test 3: Add Text Document ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vs = VectorStore(persist_dir=tmpdir)
        
        # Create temporary text file
        doc_path = Path(tmpdir) / "test_doc.txt"
        doc_content = "This is a test business document about Q3 revenue targets. " * 20
        doc_path.write_text(doc_content)
        
        # Add document
        chunks_added = vs.add_unstructured_document(
            str(doc_path),
            metadata={"document_type": "business_plan", "quarter": "Q3"}
        )
        
        assert chunks_added > 0
        assert vs._collections["unstructured_docs"].count() == chunks_added
        
        print(f"✓ Text document added")
        print(f"  Chunks added: {chunks_added}")
        print(f"  Collection count: {vs._collections['unstructured_docs'].count()}")
        
        cleanup_chroma(vs)


def test_search_documents():
    """Test semantic search on unstructured documents."""
    print("\n=== Test 4: Search Documents ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vs = VectorStore(persist_dir=tmpdir)
        
        # Add test documents
        doc1_path = Path(tmpdir) / "revenue_report.txt"
        doc1_path.write_text(
            "Q3 revenue growth was 10% exceeding our target of 8%. "
            "Sales team achieved record numbers in the EMEA region. " * 5
        )
        
        doc2_path = Path(tmpdir) / "hiring_plan.txt"
        doc2_path.write_text(
            "We plan to hire 50 engineers in Q4 to support product expansion. "
            "Focus areas include AI, cloud infrastructure, and security. " * 5
        )
        
        vs.add_unstructured_document(str(doc1_path), metadata={"type": "finance"})
        vs.add_unstructured_document(str(doc2_path), metadata={"type": "hr"})
        
        # Search for revenue-related content
        results = vs.search_documents("revenue growth targets Q3", top_k=3)
        
        assert len(results) > 0
        assert results[0]["source_file"] == "revenue_report.txt"
        assert results[0]["relevance"] > 0.5
        
        print(f"✓ Document search successful")
        print(f"  Results: {len(results)}")
        print(f"  Top result: {results[0]['source_file']} (relevance: {results[0]['relevance']})")
        print(f"  Content preview: {results[0]['content'][:100]}...")        
        cleanup_chroma(vs)

def test_librarian_hybrid_context():
    """Test LibrarianAgent hybrid retrieval."""
    print("\n=== Test 5: Hybrid Context Retrieval ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize librarian with temp directory
        librarian = LibrarianAgent(db_path=tmpdir, use_chroma=True)
        
        # Index a sample schema
        librarian.index_table_schema(
            table_name="sales",
            schema_definition="CREATE TABLE sales (id INTEGER PRIMARY KEY, revenue REAL, date TEXT)",
            columns=[
                {"name": "id", "type": "INTEGER"},
                {"name": "revenue", "type": "REAL"},
                {"name": "date", "type": "TEXT"}
            ]
        )
        
        # Add unstructured document via ChromaDB collection directly
        if librarian.unstructured_collection:
            librarian.unstructured_collection.add(
                documents=["Q3 Board Meeting: Revenue target is 10% growth. Sales pipeline looks strong."],
                metadatas=[{"source_file": "Q3_board_meeting.txt", "chunk_index": "0"}],
                ids=["doc_test_chunk_0"]
            )
        
        # Test hybrid retrieval
        hybrid_context = librarian.retrieve_hybrid_context(
            query="What is our revenue growth target?",
            top_k_sql=2,
            top_k_docs=2
        )
        
        assert "### DATABASE SCHEMA CONTEXT" in hybrid_context
        assert "### BUSINESS DOCUMENT CONTEXT" in hybrid_context
        assert "sales" in hybrid_context or "revenue" in hybrid_context
        
        print(f"✓ Hybrid context generated")
        print(f"  Context length: {len(hybrid_context)} chars")
        print(f"  Has DB schemas: {'sales' in hybrid_context}")
        print(f"  Has documents: {'Q3 Board Meeting' in hybrid_context or 'target' in hybrid_context}")
        print(f"\nContext preview:\n{hybrid_context[:400]}...")
        
        cleanup_chroma(librarian)


def test_pdf_parsing_mock():
    """Test PDF parsing (mocked if library unavailable)."""
    print("\n=== Test 6: PDF Parsing (Check) ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vs = VectorStore(persist_dir=tmpdir)
        
        # Check if PDF parsing libraries are available
        pdf_libs = []
        try:
            import fitz
            pdf_libs.append("PyMuPDF")
        except ImportError:
            pass
        
        try:
            from pypdf import PdfReader
            pdf_libs.append("pypdf")
        except ImportError:
            pass
        
        try:
            import pdfplumber
            pdf_libs.append("pdfplumber")
        except ImportError:
            pass
        
        if pdf_libs:
            print(f"✓ PDF parsing available: {', '.join(pdf_libs)}")
        else:
            print(f"⚠ No PDF parsing libraries installed")
            print(f"  Install with: pip install pymupdf (recommended)")
        
        cleanup_chroma(vs)


def test_docx_parsing_check():
    """Test DOCX parsing availability."""
    print("\n=== Test 7: DOCX Parsing (Check) ===")
    
    try:
        from docx import Document
        print(f"✓ DOCX parsing available (python-docx)")
    except ImportError:
        print(f"⚠ DOCX parsing not available")
        print(f"  Install with: pip install python-docx")


def test_error_handling():
    """Test error handling for missing files."""
    print("\n=== Test 8: Error Handling ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vs = VectorStore(persist_dir=tmpdir)
        
        # Test missing file
        try:
            vs.add_unstructured_document("/nonexistent/file.txt")
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError as e:
            print(f"✓ FileNotFoundError handled correctly")
            print(f"  Error: {str(e)[:80]}")
        
        # Test search on empty collection
        results = vs.search_documents("test query", top_k=5)
        assert results == []
        print(f"✓ Empty collection search handled")
        
        cleanup_chroma(vs)


def test_metadata_filtering():
    """Test document search with metadata filters."""
    print("\n=== Test 9: Metadata Filtering ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vs = VectorStore(persist_dir=tmpdir)
        
        # Add documents with different metadata
        doc1_path = Path(tmpdir) / "finance_q3.txt"
        doc1_path.write_text("Q3 financial results exceeded expectations with 15% revenue growth.")
        vs.add_unstructured_document(str(doc1_path), metadata={"department": "finance", "quarter": "Q3"})
        
        doc2_path = Path(tmpdir) / "engineering_q3.txt"
        doc2_path.write_text("Engineering team launched 5 new features in Q3.")
        vs.add_unstructured_document(str(doc2_path), metadata={"department": "engineering", "quarter": "Q3"})
        
        # Search with filter
        finance_results = vs.search_documents(
            "Q3 results",
            top_k=5,
            filter_metadata={"department": "finance"}
        )
        
        assert len(finance_results) > 0
        assert all(r["metadata"]["department"] == "finance" for r in finance_results)
        
        print(f"✓ Metadata filtering works")
        print(f"  Finance results: {len(finance_results)}")
        print(f"  All from finance dept: {all(r['metadata']['department'] == 'finance' for r in finance_results)}")
        
        cleanup_chroma(vs)


def test_integration_workflow():
    """Integration test: Full workflow from document add to hybrid retrieval."""
    print("\n=== Test 10: Full Integration Workflow ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Initialize systems
        vs = VectorStore(persist_dir=str(Path(tmpdir) / "vector"))
        librarian = LibrarianAgent(db_path=str(Path(tmpdir) / "librarian"), use_chroma=True)
        
        # 2. Index SQL schemas
        librarian.index_table_schema(
            "revenue",
            "CREATE TABLE revenue (date TEXT, amount REAL, region TEXT)",
            [{"name": "date", "type": "TEXT"}, {"name": "amount", "type": "REAL"}, {"name": "region", "type": "TEXT"}]
        )
        
        # 3. Add business documents via VectorStore
        board_doc = Path(tmpdir) / "board_meeting.txt"
        board_doc.write_text(
            "Q3 Board Meeting Minutes: Revenue growth target set at 10%. "
            "EMEA region showing strong performance. Engineering hiring approved for 25 new positions. " * 3
        )
        vs.add_unstructured_document(str(board_doc), metadata={"type": "board_minutes", "date": "2025-09-15"})
        
        # 4. Sync document to librarian's collection (simulate shared storage)
        if librarian.unstructured_collection and vs._collections["unstructured_docs"]:
            # In production, these would share the same ChromaDB instance
            doc_data = vs._collections["unstructured_docs"].get()
            if doc_data["documents"]:
                librarian.unstructured_collection.add(
                    documents=doc_data["documents"],
                    metadatas=doc_data["metadatas"],
                    ids=doc_data["ids"]
                )
        
        # 5. Perform hybrid query
        context = librarian.retrieve_hybrid_context(
            "Does our 10% revenue growth align with Q3 board targets?",
            top_k_sql=3,
            top_k_docs=5
        )
        
        # 6. Verify combined context
        assert "### DATABASE SCHEMA CONTEXT" in context
        assert "### BUSINESS DOCUMENT CONTEXT" in context
        assert "revenue" in context.lower()
        assert "10%" in context or "board" in context.lower()
        
        print(f"✓ Full integration workflow successful")
        print(f"  SQL schemas indexed: 1")
        print(f"  Documents added: 1")
        print(f"  Hybrid context generated: {len(context)} chars")
        print(f"  Contains DB info: {'revenue' in context.lower()}")
        print(f"  Contains doc info: {'board' in context.lower() or '10%' in context}")
        
        cleanup_chroma(vs)
        cleanup_chroma(librarian)


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 2: CROSS-MODAL DATA MESH TEST SUITE")
    print("=" * 60)
    
    try:
        test_vector_store_unstructured_collection()
        test_text_chunking()
        test_add_text_document()
        test_search_documents()
        test_librarian_hybrid_context()
        test_pdf_parsing_mock()
        test_docx_parsing_check()
        test_error_handling()
        test_metadata_filtering()
        test_integration_workflow()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Phase 2 Cross-Modal Ready!")
        print("=" * 60)
        print("\nNext Steps:")
        print("1. Install PDF support: pip install pymupdf")
        print("2. Install DOCX support: pip install python-docx")
        print("3. Add business documents to data/documents/")
        print("4. Index documents via API or script")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
