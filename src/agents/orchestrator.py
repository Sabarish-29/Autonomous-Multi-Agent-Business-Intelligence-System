"""
Agent Orchestrator for Autonomous Multi-Agent Business Intelligence System.

This class coordinates the agentic BI pipeline.
It must:
- Call PlannerAgent to create a plan
- Call TextToSQLGenerator.generate() to create SQL
- Track agent execution order in agent_trace
- Call InsightAgent to generate insights
- Return a dictionary safe for JSON serialization

It must NOT:
- Execute SQL
- Modify existing services
- Use FastAPI
"""

from .planner_agent import PlannerAgent
from .validator_agent import ValidatorAgent
from .correction_agent import CorrectionAgent
from .insight_agent import InsightAgent
from .memory_agent import MemoryAgent

class AgentOrchestrator:
    def __init__(self, sql_generator):
        self.sql_generator = sql_generator
        self.planner = PlannerAgent()
        self.validator = ValidatorAgent()
        self.corrector = CorrectionAgent()
        self.insight = InsightAgent()
        self.memory = MemoryAgent()
    
    def run(self, query: str, database: str = "default") -> dict:
        """
        Orchestrate the full agentic pipeline.
        Returns a dict with both agent-specific fields and core query fields.
        """
        agent_trace = []
        attempts = []
        
        try:
            # Step 1: Check memory for similar past queries
            agent_trace.append("memory_recall")
            similar_queries = self.memory.recall(query, top_k=3)
            
            # Step 2: Create analytical plan
            agent_trace.append("planner")
            plan = self.planner.plan(query)
            
            # Step 3: Generate SQL (get full response from generator)
            agent_trace.append("generator")
            core_result = self.sql_generator.generate(query, database=database)
            sql = core_result.sql if hasattr(core_result, 'sql') else core_result.get("sql", "")
            
            # Step 4: Validate SQL
            agent_trace.append("validator")
            validation = self.validator.validate(sql)
            attempts.append({"sql": sql, "valid": validation["is_valid"], "errors": validation["errors"]})
            
            # Step 5: Correct if needed
            if not validation["is_valid"] and validation["errors"]:
                agent_trace.append("corrector")
                sql = self.corrector.fix(sql, validation["errors"])
                
                # Re-validate corrected SQL
                validation = self.validator.validate(sql)
                attempts.append({"sql": sql, "valid": validation["is_valid"], "errors": validation["errors"]})
            
            # Step 6: Generate insights
            agent_trace.append("insight")
            insights = self.insight.analyze(sql, plan)
            
            # Step 7: Remember for future
            agent_trace.append("memory_remember")
            if validation["is_valid"]:
                self.memory.remember(query, sql)
            
            # Build response: merge core fields with agent-specific fields
            response = {
                # Core fields from generator
                "sql": sql,
                "confidence": core_result.confidence if hasattr(core_result, 'confidence') else core_result.get("confidence", 0.8),
                "explanation": core_result.explanation if hasattr(core_result, 'explanation') else core_result.get("explanation", ""),
                "complexity": core_result.complexity if hasattr(core_result, 'complexity') else core_result.get("complexity", "medium"),
                "entities": core_result.entities if hasattr(core_result, 'entities') else core_result.get("entities", []),
                "intent": core_result.intent if hasattr(core_result, 'intent') else core_result.get("intent", {}),
                "cost_estimate": core_result.cost_estimate if hasattr(core_result, 'cost_estimate') else core_result.get("cost_estimate", 0.0),
                "provider": core_result.provider if hasattr(core_result, 'provider') else core_result.get("provider", "unknown"),
                "validation_status": "valid" if validation["is_valid"] else "invalid",
                "validation_errors": validation["errors"],
                # Agent-specific fields
                "plan": plan,
                "insights": insights,
                "agent_trace": agent_trace,
                "attempts": len(attempts),
            }
            
            return response
        
        except Exception as e:
            return {
                "sql": "",
                "confidence": 0.0,
                "explanation": f"Error: {str(e)}",
                "complexity": "unknown",
                "entities": [],
                "intent": {},
                "cost_estimate": 0.0,
                "provider": "error",
                "validation_status": "error",
                "validation_errors": [str(e)],
                "plan": {},
                "insights": {},
                "agent_trace": agent_trace,
                "attempts": len(attempts),
            }
