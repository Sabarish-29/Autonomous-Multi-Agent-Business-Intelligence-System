"""
Autonomous Multi-Agent Business Intelligence System - Initialize Vector Store

Initializes ChromaDB with sample query examples and schema documentation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.vector_store import VectorStore


# Sample query examples for few-shot learning
QUERY_EXAMPLES = [
    {
        "natural_query": "Show me total revenue",
        "sql_query": "SELECT SUM(revenue) as total_revenue FROM sales;",
        "complexity": "low",
        "accuracy": 0.95
    },
    {
        "natural_query": "What is the total revenue for last quarter?",
        "sql_query": """SELECT SUM(revenue) as total_revenue 
FROM sales 
WHERE sale_date >= date('now', '-3 months');""",
        "complexity": "medium",
        "accuracy": 0.92
    },
    {
        "natural_query": "Show revenue by region",
        "sql_query": """SELECT c.region, SUM(s.revenue) as total_revenue 
FROM sales s 
JOIN customers c ON s.customer_id = c.customer_id 
GROUP BY c.region 
ORDER BY total_revenue DESC;""",
        "complexity": "medium",
        "accuracy": 0.90
    },
    {
        "natural_query": "Top 10 products by sales",
        "sql_query": """SELECT p.product_name, SUM(s.revenue) as total_sales 
FROM sales s 
JOIN products p ON s.product_id = p.product_id 
GROUP BY p.product_id, p.product_name 
ORDER BY total_sales DESC 
LIMIT 10;""",
        "complexity": "medium",
        "accuracy": 0.93
    },
    {
        "natural_query": "Compare Q1 and Q2 revenue",
        "sql_query": """SELECT 
    CASE 
        WHEN strftime('%m', sale_date) BETWEEN '01' AND '03' THEN 'Q1'
        WHEN strftime('%m', sale_date) BETWEEN '04' AND '06' THEN 'Q2'
    END as quarter,
    SUM(revenue) as total_revenue
FROM sales
WHERE strftime('%m', sale_date) BETWEEN '01' AND '06'
GROUP BY quarter;""",
        "complexity": "high",
        "accuracy": 0.88
    },
    {
        "natural_query": "Customer count by segment",
        "sql_query": """SELECT segment, COUNT(*) as customer_count 
FROM customers 
GROUP BY segment 
ORDER BY customer_count DESC;""",
        "complexity": "low",
        "accuracy": 0.95
    },
    {
        "natural_query": "Average order value",
        "sql_query": "SELECT AVG(revenue) as avg_order_value FROM sales;",
        "complexity": "low",
        "accuracy": 0.96
    },
    {
        "natural_query": "Monthly revenue trend",
        "sql_query": """SELECT 
    strftime('%Y-%m', sale_date) as month,
    SUM(revenue) as monthly_revenue
FROM sales
GROUP BY month
ORDER BY month;""",
        "complexity": "medium",
        "accuracy": 0.91
    },
    {
        "natural_query": "Revenue by product category",
        "sql_query": """SELECT p.category, SUM(s.revenue) as total_revenue 
FROM sales s 
JOIN products p ON s.product_id = p.product_id 
GROUP BY p.category 
ORDER BY total_revenue DESC;""",
        "complexity": "medium",
        "accuracy": 0.92
    },
    {
        "natural_query": "Top 5 customers by revenue",
        "sql_query": """SELECT c.customer_name, SUM(s.revenue) as total_revenue 
FROM sales s 
JOIN customers c ON s.customer_id = c.customer_id 
GROUP BY c.customer_id, c.customer_name 
ORDER BY total_revenue DESC 
LIMIT 5;""",
        "complexity": "medium",
        "accuracy": 0.93
    },
    {
        "natural_query": "Sales in the North region",
        "sql_query": """SELECT SUM(s.revenue) as north_revenue 
FROM sales s 
JOIN customers c ON s.customer_id = c.customer_id 
WHERE c.region = 'North';""",
        "complexity": "medium",
        "accuracy": 0.94
    },
    {
        "natural_query": "Profit margin by category",
        "sql_query": """SELECT 
    p.category,
    SUM(s.profit) as total_profit,
    SUM(s.revenue) as total_revenue,
    ROUND(SUM(s.profit) * 100.0 / SUM(s.revenue), 2) as profit_margin_pct
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY profit_margin_pct DESC;""",
        "complexity": "high",
        "accuracy": 0.87
    },
    {
        "natural_query": "Enterprise customers revenue",
        "sql_query": """SELECT SUM(s.revenue) as enterprise_revenue 
FROM sales s 
JOIN customers c ON s.customer_id = c.customer_id 
WHERE c.segment = 'Enterprise';""",
        "complexity": "medium",
        "accuracy": 0.94
    },
    {
        "natural_query": "Number of orders per month",
        "sql_query": """SELECT 
    strftime('%Y-%m', sale_date) as month,
    COUNT(*) as order_count
FROM sales
GROUP BY month
ORDER BY month;""",
        "complexity": "medium",
        "accuracy": 0.93
    },
    {
        "natural_query": "Year over year revenue growth",
        "sql_query": """SELECT 
    strftime('%Y', sale_date) as year,
    SUM(revenue) as annual_revenue
FROM sales
GROUP BY year
ORDER BY year;""",
        "complexity": "medium",
        "accuracy": 0.91
    }
]

# Schema documentation
SCHEMA_DOCS = [
    {
        "table_name": "customers",
        "description": "Customer master data including demographics and segmentation",
        "columns": ["customer_id", "customer_name", "region", "country", "segment", "created_date"],
        "relationships": ["customers.customer_id -> sales.customer_id"]
    },
    {
        "table_name": "products",
        "description": "Product catalog with pricing and categorization",
        "columns": ["product_id", "product_name", "category", "subcategory", "unit_price"],
        "relationships": ["products.product_id -> sales.product_id"]
    },
    {
        "table_name": "sales",
        "description": "Sales transactions with revenue, quantity, and profit data",
        "columns": ["sale_id", "customer_id", "product_id", "sale_date", "quantity", "revenue", "profit", "discount"],
        "relationships": ["sales.customer_id -> customers.customer_id", "sales.product_id -> products.product_id"]
    }
]

# Business insights
BUSINESS_INSIGHTS = [
    {
        "content": "Revenue is typically highest in Q4 due to year-end budget spending",
        "category": "seasonality",
        "keywords": ["revenue", "Q4", "seasonal"]
    },
    {
        "content": "Enterprise customers typically have higher order values but longer sales cycles",
        "category": "customer_segments",
        "keywords": ["enterprise", "order value", "segment"]
    },
    {
        "content": "Software products have the highest profit margins at around 35-40%",
        "category": "profitability",
        "keywords": ["software", "profit", "margin"]
    },
    {
        "content": "The North and West regions account for 60% of total revenue",
        "category": "geography",
        "keywords": ["region", "north", "west", "revenue"]
    },
    {
        "content": "Average discount rates are 8-12% with Enterprise customers receiving higher discounts",
        "category": "pricing",
        "keywords": ["discount", "pricing", "enterprise"]
    }
]


def initialize_vector_store():
    """Initialize vector store with sample data."""
    
    print("="*50)
    print("Initializing Vector Store")
    print("="*50)
    
    # Create vector store
    print("\n📁 Creating ChromaDB instance...")
    vector_store = VectorStore()
    
    # Add query examples
    print("\n📝 Adding query examples...")
    count = vector_store.add_query_examples(QUERY_EXAMPLES)
    print(f"   Added {count} query examples")
    
    # Add schema documentation
    print("\n📊 Adding schema documentation...")
    count = vector_store.add_schema_documentation(SCHEMA_DOCS)
    print(f"   Added {count} schema documents")
    
    # Add business insights
    print("\n💡 Adding business insights...")
    count = vector_store.add_business_insights(BUSINESS_INSIGHTS)
    print(f"   Added {count} business insights")
    
    # Print stats
    stats = vector_store.get_stats()
    
    print("\n" + "="*50)
    print("✅ Vector Store Initialized!")
    print("="*50)
    print(f"📁 Persist Directory: {stats['persist_dir']}")
    print(f"🧠 Embedding Model: {stats['embedding_model']}")
    print("\n📊 Collection Stats:")
    for name, info in stats['collections'].items():
        print(f"   - {name}: {info['count']} documents")
    print("="*50)
    
    # Test search
    print("\n🔍 Testing search...")
    test_query = "total revenue by region"
    results = vector_store.search_similar_queries(test_query, top_k=2)
    print(f"   Query: '{test_query}'")
    for r in results:
        print(f"   → {r['natural_query']} (similarity: {r['similarity']:.2f})")


if __name__ == "__main__":
    initialize_vector_store()
