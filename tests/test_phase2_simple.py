"""
Test Phase 2: Cross-Modal Data Mesh functionality.

Simplified tests using persistent test directory (./data/test_phase2_temp).
"""

import sys
import os
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.vector_store import VectorStore
from src.agents.librarian import LibrarianAgent

# Use persistent test directory
TEST_DIR = Path("./data/test_phase2_temp")


def setup_test_env():
    """Setup test environment."""
    if TEST_DIR.exists():
        try:
            shutil.rmtree(TEST_DIR)
        except:
            pass
    TEST_DIR.mkdir(parents=True, exist_ok=True)


def test_1_unstructured_collection():
    """Test unstructured_docs collection initialization."""
    print("\n=== Test 1: Unstructured Docs Collection ===")
    
    vs = VectorStore(persist_dir=str(TEST_DIR / "test1"))
    
    assert "unstructured_docs" in vs.COLLECTIONS
    print(f"✓ Collections: {list(vs.COLLECTIONS.keys())}")


def test_2_text_chunking():
    """Test text chunking."""
    print("\n=== Test 2: Text Chunking ===")
    
    vs = VectorStore(persist_dir=str(TEST_DIR / "test2"))
    text = " ".join([f"word{i}" for i in range(200)])
    chunks = vs._chunk_text(text, chunk_size=50, overlap=10)
    
    assert len(chunks) > 1
    print(f"✓ Chunked {len(chunks)} segments")


def test_3_add_document():
    """Test adding text document."""
    print("\n=== Test 3: Add Document ===")
    
    vs = VectorStore(persist_dir=str(TEST_DIR / "test3"))
    
    doc_path = TEST_DIR / "test_doc.txt"
    doc_path.write_text("Q3 revenue growth exceeded targets. " * 30)
    
    chunks = vs.add_unstructured_document(str(doc_path), metadata={"type": "finance"})
    assert chunks > 0
    print(f"✓ Added {chunks} chunks")


def test_4_search_documents():
    """Test document search."""
    print("\n=== Test 4: Search Documents ===")
    
    vs = VectorStore(persist_dir=str(TEST_DIR / "test4"))
    
    doc1 = TEST_DIR / "revenue.txt"
    doc1.write_text("Q3 revenue growth was 10% exceeding target of 8%. " * 5)
    vs.add_unstructured_document(str(doc1), metadata={"dept": "finance"})
    
    results = vs.search_documents("revenue growth targets", top_k=3)
    assert len(results) > 0
    print(f"✓ Found {len(results)} results, relevance: {results[0]['relevance']}")


def test_5_librarian_hybrid():
    """Test hybrid retrieval."""
    print("\n=== Test 5: Hybrid Retrieval ===")
    
    lib = LibrarianAgent(db_path=str(TEST_DIR / "test5"), use_chroma=True)
    
    # Index schema
    lib.index_table_schema(
        "sales",
        "CREATE TABLE sales (id INT, revenue REAL, date TEXT)",
        [{"name": "id", "type": "INT"}, {"name": "revenue", "type": "REAL"}]
    )
    
    # Add document
    if lib.unstructured_collection:
        lib.unstructured_collection.add(
            documents=["Q3 target: 10% revenue growth."],
            metadatas=[{"source_file": "board_meeting.txt", "chunk_index": "0"}],
            ids=["doc1"]
        )
    
    # Hybrid retrieval
    context = lib.retrieve_hybrid_context("revenue growth target", top_k_sql=2, top_k_docs=2)
    
    assert "### DATABASE SCHEMA CONTEXT" in context
    assert "### BUSINESS DOCUMENT CONTEXT" in context
    print(f"✓ Hybrid context: {len(context)} chars")
    print(f"  Has schemas: {'sales' in context}")
    print(f"  Has docs: {'target' in context or 'revenue' in context}")


def test_6_metadata_filter():
    """Test metadata filtering."""
    print("\n=== Test 6: Metadata Filtering ===")
    
    vs = VectorStore(persist_dir=str(TEST_DIR / "test6"))
    
    doc1 = TEST_DIR / "finance.txt"
    doc1.write_text("Q3 financial results exceeded expectations.")
    vs.add_unstructured_document(str(doc1), metadata={"dept": "finance"})
    
    doc2 = TEST_DIR / "eng.txt"
    doc2.write_text("Engineering launched 5 features in Q3.")
    vs.add_unstructured_document(str(doc2), metadata={"dept": "engineering"})
    
    results = vs.search_documents("Q3 results", top_k=5, filter_metadata={"dept": "finance"})
    
    assert len(results) > 0
    assert all(r["metadata"]["dept"] == "finance" for r in results)
    print(f"✓ Filtered to {len(results)} finance docs")


def test_7_parsing_libraries():
    """Check parsing library availability."""
    print("\n=== Test 7: Parsing Libraries ===")
    
    libs = []
    try:
        import fitz
        libs.append("PyMuPDF")
    except:
        pass
    try:
        from docx import Document
        libs.append("python-docx")
    except:
        pass
    
    if libs:
        print(f"✓ Available: {', '.join(libs)}")
    else:
        print(f"⚠ Install: pip install pymupdf python-docx")


def test_8_error_handling():
    """Test error handling."""
    print("\n=== Test 8: Error Handling ===")
    
    vs = VectorStore(persist_dir=str(TEST_DIR / "test8"))
    
    try:
        vs.add_unstructured_document("/nonexistent/file.txt")
        assert False
    except FileNotFoundError:
        print(f"✓ FileNotFoundError handled")
    
    results = vs.search_documents("test", top_k=5)
    assert results == []
    print(f"✓ Empty search handled")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 2: CROSS-MODAL DATA MESH TEST SUITE")
    print("=" * 60)
    
    try:
        setup_test_env()
        
        test_1_unstructured_collection()
        test_2_text_chunking()
        test_3_add_document()
        test_4_search_documents()
        test_5_librarian_hybrid()
        test_6_metadata_filter()
        test_7_parsing_libraries()
        test_8_error_handling()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Phase 2 Cross-Modal Ready!")
        print("=" * 60)
        print("\nNext Steps:")
        print("1. Install: pip install pymupdf python-docx")
        print("2. Add documents to data/documents/")
        print("3. Use VectorStore.add_unstructured_document()")
        print("4. Use LibrarianAgent.retrieve_hybrid_context()")
        
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
    finally:
        # Final cleanup
        print("\nCleaning up test directory...")
        try:
            shutil.rmtree(TEST_DIR, ignore_errors=True)
        except:
            pass
