"""
Autonomous Multi-Agent Business Intelligence System - Create Sample Database

Creates a sample SQLite database with sales data for testing.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path


def create_sample_database(db_path: str = "data/sample/sales_db.sqlite"):
    """Create sample sales database."""
    
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS sales")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS customers")
    
    # Create customers table
    cursor.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name TEXT NOT NULL,
        region TEXT NOT NULL,
        country TEXT NOT NULL,
        segment TEXT NOT NULL,
        created_date DATE
    )
    """)
    
    # Create products table
    cursor.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT,
        unit_price REAL NOT NULL
    )
    """)
    
    # Create sales table
    cursor.execute("""
    CREATE TABLE sales (
        sale_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        sale_date DATE NOT NULL,
        quantity INTEGER NOT NULL,
        revenue REAL NOT NULL,
        profit REAL NOT NULL,
        discount REAL DEFAULT 0,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)
    
    # Sample data
    regions = ["North", "South", "East", "West", "Central"]
    countries = ["USA", "Canada", "UK", "Germany", "France"]
    segments = ["Enterprise", "SMB", "Consumer", "Government"]
    categories = ["Software", "Hardware", "Services", "Support"]
    
    # Generate customers
    print("Generating customers...")
    customers = []
    for i in range(1, 201):
        customers.append((
            i,
            f"Customer {i}",
            random.choice(regions),
            random.choice(countries),
            random.choice(segments),
            (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d")
        ))
    
    cursor.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)",
        customers
    )
    
    # Generate products
    print("Generating products...")
    products = []
    product_names = [
        "Enterprise Suite", "Data Analytics Pro", "Cloud Platform", "Security Shield",
        "Desktop Workstation", "Server Rack", "Network Switch", "Storage Array",
        "Consulting Package", "Training Bundle", "Implementation Service", "Migration Assist",
        "Premium Support", "24/7 Helpdesk", "Managed Service", "SLA Package"
    ]
    
    for i, name in enumerate(product_names, 1):
        category = categories[i % len(categories)]
        products.append((
            i,
            name,
            category,
            f"{category} - Standard",
            round(random.uniform(100, 10000), 2)
        ))
    
    cursor.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?)",
        products
    )
    
    # Generate sales (1 year of data)
    print("Generating sales transactions...")
    sales = []
    sale_id = 1
    start_date = datetime.now() - timedelta(days=365)
    
    for day in range(365):
        current_date = start_date + timedelta(days=day)
        num_sales = random.randint(10, 50)
        
        for _ in range(num_sales):
            customer_id = random.randint(1, 200)
            product_id = random.randint(1, len(products))
            quantity = random.randint(1, 20)
            
            # Get product price
            cursor.execute(
                "SELECT unit_price FROM products WHERE product_id = ?",
                (product_id,)
            )
            unit_price = cursor.fetchone()[0]
            
            discount = random.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2])
            revenue = round(quantity * unit_price * (1 - discount), 2)
            profit = round(revenue * random.uniform(0.1, 0.4), 2)
            
            sales.append((
                sale_id,
                customer_id,
                product_id,
                current_date.strftime("%Y-%m-%d"),
                quantity,
                revenue,
                profit,
                discount
            ))
            
            sale_id += 1
    
    cursor.executemany(
        "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        sales
    )
    
    conn.commit()
    
    # Print summary
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sales")
    sales_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(revenue) FROM sales")
    total_revenue = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n" + "="*50)
    print("✅ Sample database created successfully!")
    print("="*50)
    print(f"📁 Location: {db_path}")
    print(f"👥 Customers: {customer_count:,}")
    print(f"📦 Products: {product_count:,}")
    print(f"💰 Sales: {sales_count:,}")
    print(f"💵 Total Revenue: ${total_revenue:,.2f}")
    print("="*50)


if __name__ == "__main__":
    create_sample_database()
