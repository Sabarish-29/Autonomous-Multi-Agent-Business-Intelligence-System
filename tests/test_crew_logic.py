"""
Integration Test: Hierarchical Flow & Self-Healing Logic
Autonomous Multi-Agent Business Intelligence System - Sequential Handoff Test Suite

Tests the complete agent orchestration and error correction cycle:
1. SQL Architect generates invalid SQL
2. Critic Agent detects error and provides correction plan
3. Manager routes back to Architect
4. Architect generates corrected SQL
5. Critic validates the correction

This is the most critical test for an agentic system - it validates the 
"intelligence" of the self-healing loop.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.crewai_manager import DataOpsManager, BusinessGlossary
from src.agents.librarian import LibrarianAgent


class TestHierarchicalSelfHealing(unittest.TestCase):
    """
    Test Suite for Self-Healing SQL Loop
    
    This suite validates that the hierarchical CrewAI system can:
    - Detect SQL errors via Critic Agent
    - Route corrections back to SQL Architect
    - Successfully fix errors within max retry limit
    - Properly log the self-healing cycle
    """
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        os.environ['GROQ_API_KEY'] = 'test_groq_key'
        os.environ['OPENAI_API_KEY'] = 'test_openai_key'
        os.environ['TAVILY_API_KEY'] = 'test_tavily_key'
        
        # Create mock librarian
        self.mock_librarian = Mock(spec=LibrarianAgent)
        self.mock_librarian.build_focused_context.return_value = (
            "CREATE TABLE orders (order_id INT, customer_id INT, order_date DATE, amount DECIMAL);\n"
            "CREATE TABLE customers (customer_id INT, name VARCHAR, email VARCHAR);"
        )
        
        # Create mock business glossary
        self.mock_glossary = Mock(spec=BusinessGlossary)
        self.mock_glossary.enrich_query_context.return_value = (
            "Original Query: Show total revenue\n"
            "Business Term: revenue = SUM(amount)"
        )
        
        # Initialize DataOps Manager with mocks
        with patch('src.agents.crewai_manager.ChatGroq'), \
             patch('src.agents.crewai_manager.ChatOpenAI'), \
             patch('src.agents.crewai_manager.create_critic_agent'), \
             patch('src.agents.crewai_manager.create_data_scientist_agent'), \
             patch('src.agents.crewai_manager.create_visualization_agent'), \
             patch('src.agents.crewai_manager.create_researcher_agent'), \
             patch('src.agents.crewai_manager.create_research_tool'), \
             patch('src.agents.crewai_manager.SQLQueryResultTool'), \
             patch('src.agents.crewai_manager.CodeInterpreterTool'):
            
            self.manager = DataOpsManager(
                librarian_agent=self.mock_librarian,
                business_glossary=self.mock_glossary,
                llm_api_key='test_groq_key',
                model_name='llama-3.3-70b-versatile',
                reasoning_model='o1'
            )
    
    @patch('src.agents.crewai_manager.Crew')
    @patch('src.agents.crewai_manager.Task')
    def test_self_healing_cycle_success(self, mock_task_class, mock_crew_class):
        """
        Test Case 1: Successful Self-Healing Cycle
        
        Scenario:
        1. Architect generates SQL with syntax error (missing FROM)
        2. Critic detects error and provides correction plan
        3. Architect generates corrected SQL on second attempt
        4. Critic validates correction
        5. Final SQL is returned successfully
        
        Expected:
        - Architect called twice
        - Critic called twice
        - Final result contains corrected SQL
        - Trace shows 2 attempts
        """
        
        # Mock crew instances and their kickoff results
        mock_analyst_crew = MagicMock()
        mock_architect_crew = MagicMock()
        mock_critic_crew = MagicMock()
        mock_validator_crew = MagicMock()
        
        # Setup crew creation to return different mocks
        crew_instances = [
            mock_analyst_crew,      # Query Analyst
            mock_architect_crew,    # First Architect attempt
            mock_critic_crew,       # First Critic check
            mock_architect_crew,    # Second Architect attempt (correction)
            mock_critic_crew,       # Second Critic check
            mock_validator_crew     # Final validation
        ]
        mock_crew_class.side_effect = crew_instances
        
        # Query Analyst: Analyzes user intent
        mock_analyst_crew.kickoff.return_value = (
            "Metrics: total revenue\n"
            "Dimensions: None\n"
            "Filters: None\n"
            "Joins: orders table"
        )
        
        # First SQL Architect attempt: INVALID SQL (missing FROM clause)
        invalid_sql = "SELECT SUM(amount) AS total_revenue WHERE order_date >= '2025-01-01'"
        
        # Mock architect crew to return invalid SQL first time
        architect_results = [
            invalid_sql,  # First attempt - invalid
            "SELECT SUM(amount) AS total_revenue FROM orders WHERE order_date >= '2025-01-01'"  # Second attempt - corrected
        ]
        mock_architect_crew.kickoff.side_effect = architect_results
        
        # First Critic check: DETECTS ERROR
        first_critic_response = (
            "Status: error\n"
            "Error Type: syntax_error\n"
            "Error Message: Missing FROM clause - SQL cannot execute without specifying a table\n"
            "Correction Plan: Add 'FROM orders' after SELECT statement and before WHERE clause\n"
            "Confidence: 0.95"
        )
        
        # Second Critic check: VALIDATES CORRECTION
        second_critic_response = (
            "Status: success\n"
            "Error Type: none\n"
            "Error Message: none\n"
            "Correction Plan: none\n"
            "Confidence: 0.98"
        )
        
        # Mock critic crew to return error first, then success
        critic_results = [first_critic_response, second_critic_response]
        mock_critic_crew.kickoff.side_effect = critic_results
        
        # Validator: Final approval
        mock_validator_crew.kickoff.return_value = "valid - query is safe and correct"
        
        # Execute the hierarchical flow
        result = self.manager.generate_sql_hierarchical(
            user_query="Show total revenue for 2025",
            database="test_db"
        )
        
        # ============================================================================
        # ASSERTIONS: Verify Self-Healing Behavior
        # ============================================================================
        
        # Assertion 1: No error in final result
        self.assertIsNone(result.get('error'), "Self-healing failed - error in final result")
        
        # Assertion 2: Final SQL is the CORRECTED version
        self.assertIn('FROM orders', result['sql'], "Final SQL missing corrected FROM clause")
        self.assertEqual(
            result['sql'],
            "SELECT SUM(amount) AS total_revenue FROM orders WHERE order_date >= '2025-01-01'",
            "Final SQL does not match expected corrected query"
        )
        
        # Assertion 3: Architect was called TWICE (original + correction)
        self.assertEqual(
            mock_architect_crew.kickoff.call_count, 
            2,
            f"SQL Architect should be called twice, but was called {mock_architect_crew.kickoff.call_count} times"
        )
        
        # Assertion 4: Critic was called TWICE (detect error + validate fix)
        self.assertEqual(
            mock_critic_crew.kickoff.call_count,
            2,
            f"Critic Agent should be called twice, but was called {mock_critic_crew.kickoff.call_count} times"
        )
        
        # Assertion 5: Result contains attempt count
        self.assertEqual(
            result.get('attempts'),
            2,
            "Self-healing cycle should show 2 attempts"
        )
        
        # Assertion 6: Critic feedback is captured
        self.assertIn('critic_feedback', result, "Result missing critic feedback")
        self.assertIn('error_message', result['critic_feedback'], "Critic feedback missing error message")
        
        # Assertion 7: Confidence is appropriate for corrected query
        self.assertGreaterEqual(
            result.get('confidence', 0),
            0.85,
            "Confidence should be >= 0.85 for corrected query"
        )
        
        # Assertion 8: Method is labeled as self-healing
        self.assertEqual(
            result.get('method'),
            'crewai_hierarchical_self_healing',
            "Method should indicate self-healing capability"
        )
        
        print("\n✅ TEST PASSED: Self-Healing Cycle Success")
        print(f"   - Attempts: {result['attempts']}")
        print(f"   - Final SQL: {result['sql'][:80]}...")
        print(f"   - Confidence: {result['confidence']}")
    
    @patch('src.agents.crewai_manager.Crew')
    @patch('src.agents.crewai_manager.Task')
    def test_self_healing_max_retries_exceeded(self, mock_task_class, mock_crew_class):
        """
        Test Case 2: Max Retries Exceeded
        
        Scenario:
        1. Architect generates invalid SQL (attempt 1)
        2. Critic detects error
        3. Architect generates invalid SQL again (attempt 2)
        4. Critic detects error again
        5. Architect generates invalid SQL third time (attempt 3)
        6. Critic detects error again
        7. Max retries (3) reached - system returns error
        
        Expected:
        - Architect called 3 times
        - Critic called 3 times
        - Final result contains error
        - Attempts = 3
        """
        
        # Mock crew instances
        mock_analyst_crew = MagicMock()
        mock_architect_crew = MagicMock()
        mock_critic_crew = MagicMock()
        
        # Setup crew creation
        crew_instances = [
            mock_analyst_crew,      # Query Analyst
            mock_architect_crew,    # Attempt 1
            mock_critic_crew,       # Check 1
            mock_architect_crew,    # Attempt 2
            mock_critic_crew,       # Check 2
            mock_architect_crew,    # Attempt 3
            mock_critic_crew,       # Check 3
        ]
        mock_crew_class.side_effect = crew_instances
        
        # Query Analyst
        mock_analyst_crew.kickoff.return_value = "Metrics: revenue"
        
        # Architect: Returns INVALID SQL all 3 times
        invalid_sql_attempts = [
            "SELECT SUM(amount) WHERE order_date >= '2025-01-01'",  # Missing FROM
            "SELECT SUM(amount) orders WHERE order_date >= '2025-01-01'",  # Missing FROM keyword
            "SELECT SUM(amount) AS revenue orders WHERE order_date >= '2025-01-01'"  # Still wrong
        ]
        mock_architect_crew.kickoff.side_effect = invalid_sql_attempts
        
        # Critic: Returns ERROR all 3 times
        error_responses = [
            "Status: error\nError Message: Missing FROM clause\nCorrection Plan: Add FROM orders",
            "Status: error\nError Message: Invalid FROM syntax\nCorrection Plan: Use 'FROM orders' not just 'orders'",
            "Status: error\nError Message: Still missing FROM keyword\nCorrection Plan: Correct syntax is 'FROM orders'"
        ]
        mock_critic_crew.kickoff.side_effect = error_responses
        
        # Execute the hierarchical flow
        result = self.manager.generate_sql_hierarchical(
            user_query="Show revenue",
            database="test_db"
        )
        
        # ============================================================================
        # ASSERTIONS: Verify Max Retry Handling
        # ============================================================================
        
        # Assertion 1: Result contains error
        self.assertIsNotNone(result.get('error'), "Expected error after max retries exceeded")
        
        # Assertion 2: SQL is None (no valid SQL produced)
        self.assertIsNone(result['sql'], "SQL should be None when all attempts fail")
        
        # Assertion 3: Architect was called exactly 3 times
        self.assertEqual(
            mock_architect_crew.kickoff.call_count,
            3,
            f"Architect should be called 3 times (max retries), but was called {mock_architect_crew.kickoff.call_count} times"
        )
        
        # Assertion 4: Critic was called exactly 3 times
        self.assertEqual(
            mock_critic_crew.kickoff.call_count,
            3,
            f"Critic should be called 3 times, but was called {mock_critic_crew.kickoff.call_count} times"
        )
        
        # Assertion 5: Attempts logged correctly
        self.assertEqual(
            result.get('attempts'),
            3,
            "Should show 3 attempts when max retries reached"
        )
        
        # Assertion 6: Confidence is zero
        self.assertEqual(
            result.get('confidence'),
            0.0,
            "Confidence should be 0.0 when query fails"
        )
        
        print("\n✅ TEST PASSED: Max Retries Exceeded")
        print(f"   - Attempts: {result['attempts']}")
        print(f"   - Error: {result.get('error', 'N/A')[:80]}...")
    
    @patch('src.agents.crewai_manager.Crew')
    @patch('src.agents.crewai_manager.Task')
    def test_first_attempt_success(self, mock_task_class, mock_crew_class):
        """
        Test Case 3: First Attempt Success (No Self-Healing Needed)
        
        Scenario:
        1. Architect generates VALID SQL on first attempt
        2. Critic validates - no errors detected
        3. Validator approves
        4. Query succeeds without any corrections
        
        Expected:
        - Architect called once
        - Critic called once
        - Attempts = 1
        - Confidence = 0.95 (highest for first-attempt success)
        """
        
        # Mock crew instances
        mock_analyst_crew = MagicMock()
        mock_architect_crew = MagicMock()
        mock_critic_crew = MagicMock()
        mock_validator_crew = MagicMock()
        
        crew_instances = [
            mock_analyst_crew,
            mock_architect_crew,
            mock_critic_crew,
            mock_validator_crew
        ]
        mock_crew_class.side_effect = crew_instances
        
        # Query Analyst
        mock_analyst_crew.kickoff.return_value = "Metrics: total orders"
        
        # Architect: VALID SQL on first attempt
        valid_sql = "SELECT COUNT(*) AS total_orders FROM orders WHERE order_date >= '2025-01-01'"
        mock_architect_crew.kickoff.return_value = valid_sql
        
        # Critic: NO ERRORS detected
        critic_success = (
            "Status: success\n"
            "Error Type: none\n"
            "Error Message: none\n"
            "Correction Plan: none\n"
            "Confidence: 0.98"
        )
        mock_critic_crew.kickoff.return_value = critic_success
        
        # Validator: Approves
        mock_validator_crew.kickoff.return_value = "valid"
        
        # Execute
        result = self.manager.generate_sql_hierarchical(
            user_query="Count total orders in 2025",
            database="test_db"
        )
        
        # ============================================================================
        # ASSERTIONS: Verify First-Attempt Success
        # ============================================================================
        
        # Assertion 1: No error
        self.assertIsNone(result.get('error'))
        
        # Assertion 2: SQL matches the valid query
        self.assertEqual(result['sql'], valid_sql)
        
        # Assertion 3: Architect called only ONCE
        self.assertEqual(
            mock_architect_crew.kickoff.call_count,
            1,
            "Architect should only be called once for first-attempt success"
        )
        
        # Assertion 4: Critic called only ONCE
        self.assertEqual(
            mock_critic_crew.kickoff.call_count,
            1,
            "Critic should only be called once for first-attempt success"
        )
        
        # Assertion 5: Attempts = 1
        self.assertEqual(result['attempts'], 1)
        
        # Assertion 6: Confidence is highest (0.95 for first attempt)
        self.assertEqual(
            result['confidence'],
            0.95,
            "First-attempt success should have 0.95 confidence"
        )
        
        print("\n✅ TEST PASSED: First Attempt Success")
        print(f"   - Attempts: {result['attempts']}")
        print(f"   - SQL: {result['sql'][:80]}...")
        print(f"   - Confidence: {result['confidence']}")
    
    @patch('src.agents.crewai_manager.Crew')
    @patch('src.agents.crewai_manager.Task')
    def test_trace_log_accuracy(self, mock_task_class, mock_crew_class):
        """
        Test Case 4: Trace Log Accuracy
        
        Validates that the self-healing cycle is properly logged and traceable.
        
        Expected:
        - Result contains critic_feedback from each attempt
        - Agents_involved list is complete
        - Enriched context and schema context are included
        - All metadata is accurate
        """
        
        # Setup mocks
        mock_analyst_crew = MagicMock()
        mock_architect_crew = MagicMock()
        mock_critic_crew = MagicMock()
        mock_validator_crew = MagicMock()
        
        crew_instances = [
            mock_analyst_crew,
            mock_architect_crew,
            mock_critic_crew,
            mock_architect_crew,
            mock_critic_crew,
            mock_validator_crew
        ]
        mock_crew_class.side_effect = crew_instances
        
        # Setup responses
        mock_analyst_crew.kickoff.return_value = "Analyzed query"
        mock_architect_crew.kickoff.side_effect = [
            "SELECT * WHERE id = 1",  # Invalid
            "SELECT * FROM users WHERE id = 1"  # Corrected
        ]
        mock_critic_crew.kickoff.side_effect = [
            "Status: error\nError Message: Missing FROM clause\nCorrection Plan: Add FROM users",
            "Status: success\nError Message: none\nCorrection Plan: none"
        ]
        mock_validator_crew.kickoff.return_value = "valid"
        
        # Execute
        result = self.manager.generate_sql_hierarchical(
            user_query="Get user with id 1",
            database="test_db"
        )
        
        # ============================================================================
        # ASSERTIONS: Verify Trace Accuracy
        # ============================================================================
        
        # Assertion 1: Result has all required metadata fields
        required_fields = [
            'sql', 'confidence', 'method', 'agents_involved',
            'enriched_context', 'schema_context', 'attempts',
            'critic_feedback', 'validation'
        ]
        for field in required_fields:
            self.assertIn(field, result, f"Trace missing required field: {field}")
        
        # Assertion 2: Agents involved list is accurate
        expected_agents = ['manager', 'query_analyst', 'sql_architect', 'critic', 'validator']
        self.assertEqual(
            result['agents_involved'],
            expected_agents,
            "Agents involved list is incorrect"
        )
        
        # Assertion 3: Method identifies self-healing
        self.assertEqual(result['method'], 'crewai_hierarchical_self_healing')
        
        # Assertion 4: Critic feedback contains error details
        critic_feedback = result['critic_feedback']
        self.assertIn('error_message', critic_feedback, "Critic feedback missing error_message")
        self.assertIn('correction_plan', critic_feedback, "Critic feedback missing correction_plan")
        
        # Assertion 5: Enriched context is populated
        self.assertIsNotNone(result['enriched_context'])
        self.assertIn('Original Query', result['enriched_context'])
        
        # Assertion 6: Schema context is populated
        self.assertIsNotNone(result['schema_context'])
        self.assertIn('CREATE TABLE', result['schema_context'])
        
        # Assertion 7: Validation result is captured
        self.assertEqual(result['validation'], "valid")
        
        print("\n✅ TEST PASSED: Trace Log Accuracy")
        print(f"   - Metadata fields: {len(result)} items")
        print(f"   - Agents involved: {', '.join(result['agents_involved'])}")
    
    @patch('src.agents.crewai_manager.Crew')
    @patch('src.agents.crewai_manager.Task')
    def test_pii_detection_in_workflow(self, mock_task_class, mock_crew_class):
        """
        Test Case 5: PII Detection Integration (Phase 6)
        
        Validates that PII scanning is properly integrated into the workflow.
        
        Expected:
        - Queries with CRITICAL PII are blocked
        - Result contains PII detection metadata
        - Non-critical PII allows query to proceed with warning
        """
        
        # Test 1: Critical PII blocks query
        result_blocked = self.manager.generate_sql_hierarchical(
            user_query="Show customer where ssn = '123-45-6789'",
            database="test_db"
        )
        
        self.assertIsNotNone(result_blocked.get('error'), "Critical PII should block query")
        self.assertIn('PII', result_blocked.get('error', ''), "Error should mention PII")
        self.assertEqual(result_blocked.get('risk_level'), 'CRITICAL')
        
        # Test 2: Medium PII allows query with metadata
        # Setup mocks for successful query
        mock_analyst_crew = MagicMock()
        mock_architect_crew = MagicMock()
        mock_critic_crew = MagicMock()
        mock_validator_crew = MagicMock()
        
        crew_instances = [
            mock_analyst_crew,
            mock_architect_crew,
            mock_critic_crew,
            mock_validator_crew
        ]
        mock_crew_class.side_effect = crew_instances
        
        mock_analyst_crew.kickoff.return_value = "Query analyzed"
        mock_architect_crew.kickoff.return_value = "SELECT * FROM orders WHERE customer_email = 'john@example.com'"
        mock_critic_crew.kickoff.return_value = "Status: success"
        mock_validator_crew.kickoff.return_value = "valid"
        
        result_allowed = self.manager.generate_sql_hierarchical(
            user_query="Show orders for john@example.com",
            database="test_db"
        )
        
        self.assertIsNone(result_allowed.get('error'), "Medium PII should allow query")
        self.assertTrue(result_allowed.get('pii_detected', False), "PII should be detected")
        self.assertEqual(result_allowed.get('pii_risk_level'), 'MEDIUM')
        
        print("\n✅ TEST PASSED: PII Detection Integration")
        print(f"   - Critical PII blocked: {result_blocked.get('error') is not None}")
        print(f"   - Medium PII allowed with warning: {result_allowed.get('pii_detected')}")


class TestAgentCoordination(unittest.TestCase):
    """
    Test Suite for Agent Coordination
    
    Validates that agents properly communicate and hand off tasks
    in the hierarchical workflow.
    """
    
    @patch('src.agents.crewai_manager.Crew')
    @patch('src.agents.crewai_manager.Task')
    def test_query_analyst_to_architect_handoff(self, mock_task_class, mock_crew_class):
        """
        Test that Query Analyst output is properly used by SQL Architect
        """
        # Setup will be similar to previous tests
        pass  # Placeholder for additional coordination tests
    
    @patch('src.agents.crewai_manager.Crew')
    @patch('src.agents.crewai_manager.Task')
    def test_critic_to_architect_feedback_loop(self, mock_task_class, mock_crew_class):
        """
        Test that Critic's correction plan is incorporated by Architect
        """
        pass  # Placeholder for feedback loop test


def run_integration_tests():
    """
    Run all integration tests and generate report
    """
    print("=" * 80)
    print("Autonomous Multi-Agent Business Intelligence System - Hierarchical Self-Healing Integration Tests")
    print("=" * 80)
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Self-Healing Logic Verified!")
    else:
        print("❌ SOME TESTS FAILED - Review Output Above")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Run integration tests
    success = run_integration_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
