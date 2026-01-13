"""
Test Phase 3: Autonomous Action Loops

Tests Executive COO Agent and Enterprise Action Tools.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.enterprise_actions import (
    DraftExecutiveEmailTool,
    PostSlackAlertTool,
    CreateERPTicketTool,
    get_enterprise_tools
)
from src.agents.executive import (
    create_executive_agent,
    ActionTaskBuilder,
    create_action_workflow
)
from langchain_groq import ChatGroq
import os


def test_1_enterprise_tools_available():
    """Test that all enterprise tools are available."""
    print("\n=== Test 1: Enterprise Tools Available ===")
    
    tools = get_enterprise_tools()
    
    assert len(tools) == 3
    print(f"✓ Found {len(tools)} enterprise tools")
    print(f"  Tools: {[t.name for t in tools]}")


def test_2_draft_email():
    """Test email drafting tool."""
    print("\n=== Test 2: Draft Executive Email ===")
    
    # Convert list to comma-separated string
    key_points_str = "Revenue down 15% vs target, EMEA region underperforming by 20%, Recommend emergency marketing budget review"
    
    tool = DraftExecutiveEmailTool()
    email = tool._run(
        recipient="CEO@company.com",
        subject="Q3 Revenue Decline - Immediate Action Required",
        key_points=key_points_str
    )
    
    assert "CEO@company.com" in email
    assert "Q3 Revenue Decline" in email
    assert "Revenue down 15%" in email
    assert "[DRAFT - REQUIRES HUMAN REVIEW" in email
    
    print(f"✓ Email draft generated ({len(email)} chars)")
    print(f"  Subject line: Q3 Revenue Decline")
    print(f"  Key points: 3")
    print(f"\nEmail preview:\n{email[:300]}...")


def test_3_slack_alert():
    """Test Slack alert tool."""
    print("\n=== Test 3: Post Slack Alert ===")
    
    tool = PostSlackAlertTool()
    alert = tool._run(
        channel="ops-alerts",
        message="Revenue drop detected in EMEA region: -15% vs target. Requires immediate investigation.",
        priority="high"
    )
    
    assert "#ops-alerts" in alert
    assert "Revenue drop" in alert
    assert "HIGH PRIORITY" in alert
    assert "[MOCK ALERT - NOT ACTUALLY POSTED" in alert
    
    print(f"✓ Slack alert generated ({len(alert)} chars)")
    print(f"  Channel: #ops-alerts")
    print(f"  Priority: HIGH")
    print(f"\nAlert preview:\n{alert[:200]}...")


def test_4_erp_ticket():
    """Test ERP ticket creation tool."""
    print("\n=== Test 4: Create ERP Ticket ===")
    
    tool = CreateERPTicketTool()
    ticket = tool._run(
        issue_type="Incident",
        priority="P1",
        description="Revenue tracking system showing -15% discrepancy in EMEA region. Requires immediate investigation by finance and sales teams."
    )
    
    assert "Incident" in ticket
    assert "P1" in ticket
    assert "Revenue tracking" in ticket
    assert "[MOCK TICKET - NOT CREATED IN ACTUAL ERP" in ticket
    
    print(f"✓ ERP ticket generated ({len(ticket)} chars)")
    print(f"  Issue Type: Incident")
    print(f"  Priority: P1")
    print(f"\nTicket preview:\n{ticket[:250]}...")


def test_5_executive_agent_creation():
    """Test Executive Agent creation."""
    print("\n=== Test 5: Executive Agent Creation ===")
    
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY", "test-key")
    )
    
    agent = create_executive_agent(llm)
    
    assert agent.role == "Chief Operating Officer (AI Delegate)"
    assert len(agent.tools) == 3
    assert "ACTION-ORIENTED" in agent.backstory
    
    print(f"✓ Executive Agent created")
    print(f"  Role: {agent.role}")
    print(f"  Tools: {len(agent.tools)}")
    print(f"  Goal: {agent.goal[:80]}...")


def test_6_action_task_builder():
    """Test ActionTaskBuilder."""
    print("\n=== Test 6: Action Task Builder ===")
    
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, api_key="test")
    agent = create_executive_agent(llm)
    
    # Build action plan task
    task = ActionTaskBuilder.build_action_plan_task(
        agent=agent,
        insight_context="Revenue dropped 15% in EMEA region, primarily in Germany and France. Sales velocity decreased 22%.",
        recommended_action="email"
    )
    
    assert "Revenue dropped 15%" in task.description
    assert "draft_executive_email" in task.description
    assert "MUST actually execute the tools" in task.description
    
    print(f"✓ Action task created")
    print(f"  Task type: Action Plan (email)")
    print(f"  Description length: {len(task.description)} chars")
    print(f"  Expected output defined: {len(task.expected_output) > 0}")


def test_7_triage_task():
    """Test insight triage task."""
    print("\n=== Test 7: Insight Triage Task ===")
    
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, api_key="test")
    agent = create_executive_agent(llm)
    
    insights = [
        {"description": "Revenue down 15% in EMEA", "severity": "critical"},
        {"description": "Customer churn increased 5%", "severity": "high"},
        {"description": "Server response time +20ms", "severity": "medium"}
    ]
    
    task = ActionTaskBuilder.build_insight_triage_task(
        agent=agent,
        insights=insights
    )
    
    assert "triage" in task.description.lower()
    assert "Revenue down 15%" in task.description
    assert "Customer churn" in task.description
    assert "TOP 2 most critical" in task.description
    
    print(f"✓ Triage task created")
    print(f"  Insights to triage: {len(insights)}")
    print(f"  Requires tools for: Top 2 critical")


def test_8_escalation_task():
    """Test critical escalation task."""
    print("\n=== Test 8: Escalation Task ===")
    
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, api_key="test")
    agent = create_executive_agent(llm)
    
    task = ActionTaskBuilder.build_escalation_task(
        agent=agent,
        critical_alert="System outage affecting revenue tracking",
        affected_metrics=["daily_revenue", "transaction_count", "user_sessions"],
        stakeholders=["CEO", "CTO", "CFO"]
    )
    
    assert "CRITICAL ESCALATION" in task.description
    assert "System outage" in task.description
    assert "CEO" in task.description
    assert "P1" in task.description
    assert "Execute ALL THREE tools" in task.description
    
    print(f"✓ Escalation task created")
    print(f"  Alert: System outage")
    print(f"  Stakeholders: 3 executives")
    print(f"  Priority: P1 (Critical)")


def test_9_action_workflow():
    """Test complete action workflow."""
    print("\n=== Test 9: Action Workflow ===")
    
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, api_key="test")
    
    workflow = create_action_workflow(
        llm=llm,
        insight="Revenue dropped 18% in Q3 EMEA region",
        action_type="comprehensive"
    )
    
    assert "agent" in workflow
    assert "task" in workflow
    assert "insight" in workflow
    assert workflow["action_type"] == "comprehensive"
    assert workflow["agent"].role == "Chief Operating Officer (AI Delegate)"
    
    print(f"✓ Action workflow created")
    print(f"  Agent: {workflow['agent'].role}")
    print(f"  Action type: {workflow['action_type']}")
    print(f"  Insight: {workflow['insight'][:50]}...")


def test_10_tool_error_handling():
    """Test error handling in tools."""
    print("\n=== Test 10: Tool Error Handling ===")
    
    # Test with various input types
    email_tool = DraftExecutiveEmailTool()
    email1 = email_tool._run(
        recipient="test@test.com",
        subject="Test",
        key_points="Single string point"  # Should handle string instead of list
    )
    
    assert "test@test.com" in email1
    assert "Single string point" in email1
    
    # Test alert with missing # prefix
    alert_tool = PostSlackAlertTool()
    alert = alert_tool._run(
        channel="ops-alerts",  # No # prefix
        message="Test message",
        priority="invalid_priority"  # Invalid priority
    )
    
    assert "#ops-alerts" in alert  # Should add # prefix
    assert "Test message" in alert
    
    print(f"✓ Error handling works")
    print(f"  String key_points handled: ✓")
    print(f"  Missing # prefix added: ✓")
    print(f"  Invalid priority handled: ✓")


def test_11_draft_disclaimers():
    """Test that all tools include draft disclaimers."""
    print("\n=== Test 11: Draft Disclaimers ===")
    
    email_tool = DraftExecutiveEmailTool()
    alert_tool = PostSlackAlertTool()
    ticket_tool = CreateERPTicketTool()
    
    email = email_tool._run(
        "test@test.com", "Test", "Point 1"
    )
    alert = alert_tool._run(
        "ops", "Test alert", "high"
    )
    ticket = ticket_tool._run(
        "Bug", "P2", "Test ticket"
    )
    
    assert "DRAFT" in email.upper()
    assert "HUMAN" in email.upper()
    assert "MOCK" in alert.upper()
    assert "NOT ACTUALLY POSTED" in alert
    assert "MOCK" in ticket.upper()
    assert "NOT CREATED IN ACTUAL" in ticket
    
    print(f"✓ All tools include disclaimers")
    print(f"  Email: DRAFT + HUMAN REVIEW")
    print(f"  Alert: MOCK + NOT POSTED")
    print(f"  Ticket: MOCK + NOT CREATED")


def test_12_professional_formatting():
    """Test professional formatting of outputs."""
    print("\n=== Test 12: Professional Formatting ===")
    
    tool = DraftExecutiveEmailTool()
    email = tool._run(
        "CEO@company.com",
        "Critical Revenue Alert",
        "Revenue down 15%, Immediate action needed"
    )
    
    # Check professional email elements
    assert "To:" in email
    assert "Subject:" in email
    assert "Date:" in email
    assert "Dear" in email
    assert "Best regards" in email
    
    print(f"✓ Professional formatting verified")
    print(f"  Email has: To, Subject, Date, Greeting, Signature")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3: AUTONOMOUS ACTION LOOPS TEST SUITE")
    print("=" * 60)
    
    try:
        test_1_enterprise_tools_available()
        test_2_draft_email()
        test_3_slack_alert()
        test_4_erp_ticket()
        test_5_executive_agent_creation()
        test_6_action_task_builder()
        test_7_triage_task()
        test_8_escalation_task()
        test_9_action_workflow()
        test_10_tool_error_handling()
        test_11_draft_disclaimers()
        test_12_professional_formatting()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Phase 3 Action Loops Ready!")
        print("=" * 60)
        print("\nExecutive COO Agent Features:")
        print("✓ Draft executive emails")
        print("✓ Generate Slack alerts")
        print("✓ Create ERP tickets")
        print("✓ Triage multiple insights")
        print("✓ Escalate critical issues")
        print("\nAll tools generate DRAFTS for human approval!")
        
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
