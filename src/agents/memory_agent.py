"""
Memory Agent for Autonomous Multi-Agent Business Intelligence System

Responsibilities:
- Store successful query → SQL pairs
- Retrieve similar past queries
- Improve accuracy over time
- Use existing VectorStore as backend
- Remain lightweight and deterministic

This agent does NOT generate SQL.
This agent does NOT call LLMs.
"""

class MemoryAgent:
    def __init__(self):
        self.memory = {}  # In-memory store for now
    
    def remember(self, query: str, sql: str) -> None:
        """
        Store a successful query-SQL pair.
        """
        # Simple string matching key
        key = query.lower().strip()
        self.memory[key] = sql
    
    def recall(self, query: str, top_k: int = 3) -> list:
        """
        Retrieve similar past queries using simple string matching.
        Returns list of (query, sql) tuples.
        """
        query_lower = query.lower().strip()
        similar = []
        
        # Extract key terms from query
        query_terms = set(word for word in query_lower.split() if len(word) > 3)
        
        # Find matches
        for stored_query, stored_sql in self.memory.items():
            stored_terms = set(word for word in stored_query.split() if len(word) > 3)
            
            # Calculate similarity (Jaccard index)
            if query_terms and stored_terms:
                intersection = len(query_terms & stored_terms)
                union = len(query_terms | stored_terms)
                similarity = intersection / union if union > 0 else 0
                
                if similarity > 0.3:  # 30% similarity threshold
                    similar.append({
                        "query": stored_query,
                        "sql": stored_sql,
                        "similarity": similarity
                    })
        
        # Sort by similarity and return top_k
        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar[:top_k]
