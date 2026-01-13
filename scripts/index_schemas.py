"""
Schema Indexing Script for Librarian Agent

This script helps you index your existing database schemas into the Librarian Agent's
ChromaDB vector store for semantic retrieval.
"""

import logging
import sqlite3
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.librarian import LibrarianAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_sqlite_schema(db_path: str) -> list:
    """
    Extract schema information from a SQLite database.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List of table schemas
    """
    schemas = []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            # Skip SQLite internal tables
            if table_name.startswith('sqlite_'):
                continue
            
            # Get CREATE TABLE statement
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            create_stmt = cursor.fetchone()[0]
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            
            columns = []
            for col in columns_info:
                col_id, col_name, col_type, not_null, default_val, primary_key = col
                columns.append({
                    'name': col_name,
                    'type': col_type,
                    'nullable': not not_null,
                    'primary_key': bool(primary_key),
                    'description': f"{col_type} column"
                })
            
            schemas.append({
                'table_name': table_name,
                'schema_definition': create_stmt,
                'columns': columns,
                'metadata': {
                    'database': Path(db_path).stem,
                    'column_count': len(columns)
                }
            })
            
        conn.close()
        logger.info(f"Extracted {len(schemas)} tables from {db_path}")
        return schemas
        
    except Exception as e:
        logger.error(f"Failed to extract schema from {db_path}: {e}")
        return []


def index_sample_schemas():
    """
    Index example schemas for demonstration purposes.
    """
    librarian = LibrarianAgent(db_path="./data/schema_library")
    
    # Example: E-commerce database schemas
    example_schemas = [
        {
            'table_name': 'customers',
            'schema_definition': """
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                country VARCHAR(50),
                lifetime_value DECIMAL(10,2),
                first_purchase_date DATE,
                last_login_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            'columns': [
                {'name': 'customer_id', 'type': 'INTEGER', 'description': 'Unique customer identifier'},
                {'name': 'email', 'type': 'VARCHAR(255)', 'description': 'Customer email address'},
                {'name': 'first_name', 'type': 'VARCHAR(100)', 'description': 'Customer first name'},
                {'name': 'last_name', 'type': 'VARCHAR(100)', 'description': 'Customer last name'},
                {'name': 'country', 'type': 'VARCHAR(50)', 'description': 'Customer country'},
                {'name': 'lifetime_value', 'type': 'DECIMAL(10,2)', 'description': 'Total value of all purchases'},
                {'name': 'first_purchase_date', 'type': 'DATE', 'description': 'Date of first purchase'},
                {'name': 'last_login_date', 'type': 'DATE', 'description': 'Most recent login date'},
                {'name': 'created_at', 'type': 'TIMESTAMP', 'description': 'Account creation timestamp'}
            ],
            'metadata': {'database': 'ecommerce', 'category': 'customer_data'}
        },
        {
            'table_name': 'orders',
            'schema_definition': """
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                order_date DATE NOT NULL,
                order_total DECIMAL(10,2),
                status VARCHAR(50),
                shipping_address TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
            """,
            'columns': [
                {'name': 'order_id', 'type': 'INTEGER', 'description': 'Unique order identifier'},
                {'name': 'customer_id', 'type': 'INTEGER', 'description': 'Reference to customer who placed order'},
                {'name': 'order_date', 'type': 'DATE', 'description': 'Date order was placed'},
                {'name': 'order_total', 'type': 'DECIMAL(10,2)', 'description': 'Total order value'},
                {'name': 'status', 'type': 'VARCHAR(50)', 'description': 'Order status (pending, shipped, delivered, etc.)'},
                {'name': 'shipping_address', 'type': 'TEXT', 'description': 'Delivery address'}
            ],
            'metadata': {'database': 'ecommerce', 'category': 'transaction_data'}
        },
        {
            'table_name': 'products',
            'schema_definition': """
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                product_name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                unit_price DECIMAL(10,2),
                stock_quantity INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            'columns': [
                {'name': 'product_id', 'type': 'INTEGER', 'description': 'Unique product identifier'},
                {'name': 'product_name', 'type': 'VARCHAR(255)', 'description': 'Product name'},
                {'name': 'category', 'type': 'VARCHAR(100)', 'description': 'Product category'},
                {'name': 'unit_price', 'type': 'DECIMAL(10,2)', 'description': 'Price per unit'},
                {'name': 'stock_quantity', 'type': 'INTEGER', 'description': 'Current inventory level'},
                {'name': 'description', 'type': 'TEXT', 'description': 'Product description'},
                {'name': 'created_at', 'type': 'TIMESTAMP', 'description': 'Product creation timestamp'}
            ],
            'metadata': {'database': 'ecommerce', 'category': 'product_catalog'}
        },
        {
            'table_name': 'order_items',
            'schema_definition': """
            CREATE TABLE order_items (
                order_item_id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2),
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
            """,
            'columns': [
                {'name': 'order_item_id', 'type': 'INTEGER', 'description': 'Unique order item identifier'},
                {'name': 'order_id', 'type': 'INTEGER', 'description': 'Reference to parent order'},
                {'name': 'product_id', 'type': 'INTEGER', 'description': 'Reference to product'},
                {'name': 'quantity', 'type': 'INTEGER', 'description': 'Quantity ordered'},
                {'name': 'unit_price', 'type': 'DECIMAL(10,2)', 'description': 'Price at time of purchase'}
            ],
            'metadata': {'database': 'ecommerce', 'category': 'transaction_data'}
        }
    ]
    
    # Index all schemas
    success_count = 0
    for schema in example_schemas:
        if librarian.index_table_schema(
            table_name=schema['table_name'],
            schema_definition=schema['schema_definition'],
            columns=schema['columns'],
            metadata=schema.get('metadata')
        ):
            success_count += 1
    
    logger.info(f"✅ Successfully indexed {success_count}/{len(example_schemas)} schemas")
    
    # Test retrieval
    test_query = "Show me customer purchase history"
    logger.info(f"\nTesting retrieval with query: '{test_query}'")
    context = librarian.build_focused_context(test_query, max_tables=3)
    print(context)


def index_from_sqlite(db_path: str):
    """
    Index schemas from an existing SQLite database.
    
    Args:
        db_path: Path to SQLite database file
    """
    librarian = LibrarianAgent(db_path="./data/schema_library")
    
    # Extract schemas
    schemas = extract_sqlite_schema(db_path)
    
    if not schemas:
        logger.error("No schemas extracted. Aborting.")
        return
    
    # Index all schemas
    success_count = 0
    for schema in schemas:
        if librarian.index_table_schema(
            table_name=schema['table_name'],
            schema_definition=schema['schema_definition'],
            columns=schema['columns'],
            metadata=schema.get('metadata')
        ):
            success_count += 1
    
    logger.info(f"✅ Successfully indexed {success_count}/{len(schemas)} schemas from {db_path}")
    
    # List all tables
    all_tables = librarian.list_all_tables()
    logger.info(f"Total tables in library: {len(all_tables)}")
    logger.info(f"Tables: {', '.join(all_tables)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Index database schemas into Librarian Agent")
    parser.add_argument(
        '--mode',
        choices=['example', 'sqlite'],
        default='example',
        help='Indexing mode: example schemas or SQLite database'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        help='Path to SQLite database (required for sqlite mode)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'example':
        logger.info("Indexing example schemas...")
        index_sample_schemas()
    elif args.mode == 'sqlite':
        if not args.db_path:
            logger.error("--db-path required for sqlite mode")
            sys.exit(1)
        logger.info(f"Indexing schemas from {args.db_path}...")
        index_from_sqlite(args.db_path)
