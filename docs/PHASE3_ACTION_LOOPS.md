# Phase 3: Autonomous Action Loops

**Status**: ✅ Complete  
**Tests**: 12/12 Passing  
**Commit**: Pending

## Overview

Phase 3 introduces the **Executive COO Agent** - an autonomous agent that converts business intelligence insights into actionable operational plans. Unlike previous agents that only analyze and report, the Executive Agent **takes immediate action** by drafting concrete artifacts using its enterprise action tools.

## Key Components

### 1. Enterprise Action Tools (`src/tools/enterprise_actions.py`)

Three CrewAI tools for drafting business actions:

#### **DraftExecutiveEmailTool**
- **Purpose**: Generate professionally formatted executive email DRAFTS
- **Inputs**:
  - `recipient`: Email address (e.g., "CEO@company.com")
  - `subject`: Email subject line
  - `key_points`: Bullet points (comma or newline separated)
- **Output**: Formatted email with To/Subject/Date/Body/Signature + DRAFT disclaimer
- **Important**: Creates DRAFT only - human must review and send

**Example**:
```python
from src.tools.enterprise_actions import DraftExecutiveEmailTool

tool = DraftExecutiveEmailTool()
email = tool._run(
    recipient="CEO@company.com",
    subject="Q3 Revenue Decline - Immediate Action Required",
    key_points="Revenue down 15% vs target, EMEA region underperforming by 20%, Recommend emergency marketing budget review"
)

print(email)
# Output:
# To: CEO@company.com
# Subject: Q3 Revenue Decline - Immediate Action Required
# Date: 2026-01-13 19:58
# ---
# Dear CEO,
# I hope this message finds you well. I am writing to bring to your attention critical insights from our recent business intelligence analysis:
# 1. Revenue down 15% vs target
# 2. EMEA region underperforming by 20%
# 3. Recommend emergency marketing budget review
# ...
# [DRAFT - REQUIRES HUMAN REVIEW AND APPROVAL BEFORE SENDING]
```

#### **PostSlackAlertTool**
- **Purpose**: Generate Slack alert DRAFTS (MOCK - does not actually post)
- **Inputs**:
  - `channel`: Slack channel name (e.g., "#ops-alerts")
  - `message`: Alert message content
  - `priority`: "low", "medium", "high", or "critical"
- **Output**: Formatted Slack alert with emojis + MOCK disclaimer
- **Important**: Simulated only - human must manually post to Slack

**Example**:
```python
tool = PostSlackAlertTool()
alert = tool._run(
    channel="ops-alerts",
    message="Revenue drop detected in EMEA region: -15% vs target. Requires immediate investigation.",
    priority="high"
)

print(alert)
# Output:
# ════════════════════════════════════════
# SLACK ALERT DRAFT (MOCK)
# ════════════════════════════════════════
# Channel: #ops-alerts
# Priority: HIGH
# Timestamp: 2026-01-13 19:58:43
# 
# 🚨 **HIGH PRIORITY ALERT** 🚨
# Revenue drop detected in EMEA region: -15% vs target. Requires immediate investigation.
# [MOCK ALERT - NOT ACTUALLY POSTED TO SLACK]
```

#### **CreateERPTicketTool**
- **Purpose**: Generate ERP/ticketing system entry DRAFTS (Jira, SAP, ServiceNow)
- **Inputs**:
  - `issue_type`: "Bug", "Task", "Incident", "Change Request"
  - `priority`: "P1", "P2", "P3", "P4" or "Critical", "High", "Medium", "Low"
  - `description`: Detailed description
- **Output**: Formatted ticket with ID/Type/Priority/Description + MOCK disclaimer
- **Important**: Simulated only - human must create ticket in actual system

**Example**:
```python
tool = CreateERPTicketTool()
ticket = tool._run(
    issue_type="Incident",
    priority="P1",
    description="Revenue tracking system showing -15% discrepancy in EMEA region. Requires immediate investigation by finance and sales teams."
)

print(ticket)
# Output:
# ╔════════════════════════════════════════╗
# ║   ERP TICKET DRAFT (MOCK)              ║
# ╚════════════════════════════════════════╝
# Ticket ID: DRAFT-20260113-195843
# Issue Type: Incident
# Priority: P1
# Status: [DRAFT - NOT CREATED]
# Created: 2026-01-13 19:58:43
# Reporter: AI Operations Assistant
# ...
# [MOCK TICKET - NOT CREATED IN ACTUAL ERP SYSTEM]
```

### 2. Executive COO Agent (`src/agents/executive.py`)

#### **Agent Configuration**
- **Role**: Chief Operating Officer (AI Delegate)
- **Personality**: Decisive operational leader with 15+ years of executive experience
- **Backstory**: EXTREMELY ACTION-ORIENTED - immediately uses tools to draft artifacts, doesn't just describe actions
- **Tools**: All three enterprise action tools

**Creating the Agent**:
```python
from src.agents.executive import create_executive_agent
from langchain_groq import ChatGroq

llm = ChatGroq(model_name="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"))
agent = create_executive_agent(llm)

# Agent automatically has access to:
# - draft_executive_email
# - post_slack_alert
# - create_erp_ticket
```

#### **ActionTaskBuilder**

Helper class to create tasks for the Executive Agent:

**1. Action Plan Task** (`build_action_plan_task`):
```python
from src.agents.executive import ActionTaskBuilder

builder = ActionTaskBuilder()
task = builder.build_action_plan_task(
    insight="Revenue dropped 15% in Q3 EMEA region - root cause: supply chain delays",
    action_type="email"  # or "slack", "ticket", "comprehensive"
)
```

**2. Insight Triage Task** (`build_insight_triage_task`):
```python
insights = [
    "Revenue down 15% in EMEA",
    "Customer churn increased 8%",
    "Product defect rate spiked 12%"
]
task = builder.build_insight_triage_task(insights, top_n=2)
```

**3. Escalation Task** (`build_escalation_task`):
```python
task = builder.build_escalation_task(
    alert="Data warehouse outage - 45 minutes downtime",
    stakeholders=["CTO", "VP Engineering", "COO"],
    priority="P1"
)
```

### 3. Action Workflow (`create_action_workflow`)

Complete workflow to analyze insights and draft actions:

```python
from src.agents.executive import create_action_workflow

agent = create_executive_agent(llm)
workflow = create_action_workflow(
    agent=agent,
    insight="Revenue dropped 18% in Q3 EMEA region - root cause analysis shows supply chain disruptions",
    action_type="comprehensive"  # Will use ALL tools
)

# Workflow includes:
# - Agent: Executive COO
# - Tasks: Action planning with tool usage
# - Process: Sequential (agent reviews insight, drafts artifacts)
```

## Integration with Main System

### Extending the CrewAI Workflow

Add Executive Agent to existing crew in `src/agents/crewai_manager.py`:

```python
from src.agents.executive import create_executive_agent, ActionTaskBuilder

# In DataOpsManager.__init__:
self.executive_agent = create_executive_agent(self.llm)
self.action_builder = ActionTaskBuilder()

# In DataOpsManager.execute_query:
# After getting insights from scientist/reporter...
action_task = self.action_builder.build_action_plan_task(
    insight=final_insights,
    action_type="comprehensive"
)

action_crew = Crew(
    agents=[self.executive_agent],
    tasks=[action_task],
    verbose=True
)

action_results = action_crew.kickoff()
```

## Testing

### Running Tests

```bash
# All Phase 3 tests
python tests/test_phase3_action_loops.py

# Should see:
# ✓ Test 1: Enterprise Tools Available
# ✓ Test 2: Draft Executive Email
# ✓ Test 3: Post Slack Alert
# ✓ Test 4: Create ERP Ticket
# ✓ Test 5: Executive Agent Creation
# ✓ Test 6: Action Task Builder
# ✓ Test 7: Insight Triage Task
# ✓ Test 8: Escalation Task
# ✓ Test 9: Action Workflow
# ✓ Test 10: Tool Error Handling
# ✓ Test 11: Draft Disclaimers
# ✓ Test 12: Professional Formatting
# 
# ✓ ALL TESTS PASSED - Phase 3 Action Loops Ready!
```

### Test Coverage

| Test | Description | Validation |
|------|-------------|------------|
| 1 | Tools Available | Verifies 3 tools returned by `get_enterprise_tools()` |
| 2 | Email Drafting | Email contains recipient, subject, key points, DRAFT disclaimer |
| 3 | Slack Alert | Alert contains channel, priority emoji, message, MOCK disclaimer |
| 4 | ERP Ticket | Ticket contains type, priority, description, MOCK disclaimer |
| 5 | Agent Creation | Executive Agent created with role, tools, goal |
| 6 | Action Task | Task created with tool execution instructions |
| 7 | Insight Triage | Multiple insights triaged, top N prioritized for action |
| 8 | Escalation | Critical alert drafted with stakeholder list |
| 9 | Workflow | Full workflow created with agent and task |
| 10 | Error Handling | String/list input handling, missing prefixes, invalid priorities |
| 11 | Disclaimers | All tools include DRAFT/MOCK/HUMAN REVIEW disclaimers |
| 12 | Formatting | Email has To/Subject/Date/Greeting/Signature |

## Architecture Decisions

### Why CrewAI BaseTool, Not LangChain @tool?

**Initial Attempt**: Used `langchain.tools.tool` decorator
```python
from langchain.tools import tool

@tool
def draft_executive_email(recipient: str, subject: str, key_points: str) -> str:
    ...
```

**Problem**: CrewAI Agent expects `crewai.tools.BaseTool`, not `langchain.tools.BaseTool`
```
ValidationError: 3 validation errors for Agent
tools.0
  Input should be a valid dictionary or instance of BaseTool [type=model_type]
```

**Solution**: Inherit from CrewAI's BaseTool with `_run()` method
```python
from crewai.tools import BaseTool

class DraftExecutiveEmailTool(BaseTool):
    name: str = "draft_executive_email"
    description: str = "..."
    
    def _run(self, recipient: str, subject: str, key_points: str) -> str:
        ...
```

**Lesson**: Always use framework-specific tool base classes for compatibility.

### Why DRAFT/MOCK Disclaimers?

**Critical Safety Feature**: All tools generate DRAFTS, not real actions:
1. **Email Tool**: Generates formatted email text, does NOT send via SMTP
2. **Slack Tool**: Generates alert message, does NOT post to Slack API
3. **ERP Tool**: Generates ticket content, does NOT create in Jira/SAP/ServiceNow

**Reason**: AI should **propose** actions, not **execute** them autonomously. Human-in-the-loop approval required for:
- Executive communications (legal/compliance risk)
- Alert fatigue (avoid Slack spam)
- Ticket noise (avoid overwhelming engineering teams)

**Future**: Could add approval API endpoints for human review UI.

## Performance

- **Tool Execution**: < 50ms per tool (string formatting only)
- **Agent Planning**: 2-5 seconds (LLM reasoning with Groq llama-3.3-70b)
- **Full Workflow**: 5-10 seconds (insight analysis + multi-tool drafting)

## Security Considerations

1. **No External API Calls**: Tools do NOT connect to email/Slack/ERP services
2. **Input Validation**: All tools validate input types and formats
3. **Error Handling**: Exceptions caught, logged, returned as error messages
4. **Audit Trail**: Logger records all tool usage (`logger.info(f"Generated email draft for {recipient}...")`)

## Future Enhancements

### Phase 4 Ideas

1. **Human Approval Workflow**:
   ```python
   # API endpoint for draft review
   @app.post("/api/review_draft")
   def review_draft(draft_id: str, action: Literal["approve", "reject", "edit"]):
       if action == "approve":
           send_email(draft_content)  # Now actually send
   ```

2. **Multi-Modal Actions**:
   - Generate PowerPoint decks from insights
   - Create Excel reports with visualizations
   - Draft SQL migration scripts

3. **Action Chaining**:
   - If email sent → Create follow-up calendar invite
   - If ticket created → Notify assignee via Slack
   - If alert posted → Escalate if no response in 1 hour

4. **Learning from Feedback**:
   - Track human approval/rejection rates
   - Fine-tune action prioritization
   - Personalize communication style per executive

## Troubleshooting

### Import Errors

**Problem**: `ImportError: cannot import name 'tool' from 'crewai_tools'`

**Solution**: Use `crewai.tools.BaseTool`, not `crewai_tools.tool`
```python
from crewai.tools import BaseTool  # ✓ Correct
from crewai_tools import tool       # ✗ Does not exist
```

### Agent Tool Validation Errors

**Problem**: `ValidationError: tools.0 Input should be a valid dictionary or instance of BaseTool`

**Solution**: Ensure tools inherit from `crewai.tools.BaseTool`
```python
# ✓ Correct
class MyTool(BaseTool):
    def _run(self, input: str) -> str:
        ...

# ✗ Wrong
@tool
def my_tool(input: str) -> str:
    ...
```

## References

- **Enterprise Actions**: `src/tools/enterprise_actions.py` (250 lines)
- **Executive Agent**: `src/agents/executive.py` (295 lines)
- **Tests**: `tests/test_phase3_action_loops.py` (352 lines, 12 tests)
- **CrewAI Docs**: https://docs.crewai.com/core-concepts/Tools/
- **Tool Design Pattern**: `src/agents/crewai_manager.py` (SchemaRetrievalTool, BusinessTermTool examples)

---

**Phase 3 Complete**: Executive COO Agent ready for autonomous action planning! 🚀

All tools generate DRAFTS for human approval - safety first! ✅
