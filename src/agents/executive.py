"""
Executive COO Agent for Phase 3: Autonomous Action Loops

The Executive Agent converts business insights into actionable operational plans:
- Drafts executive communications
- Creates alert notifications
- Generates ticket/task assignments

This agent USES TOOLS to create actual artifacts, not just descriptions.
"""

import logging
from typing import Optional, List, Dict, Any
from crewai import Agent, Task
from langchain_groq import ChatGroq

from ..tools.enterprise_actions import get_enterprise_tools

logger = logging.getLogger(__name__)


def create_executive_agent(llm: ChatGroq, tools: Optional[List] = None) -> Agent:
    """
    Create Executive COO Agent for autonomous action planning.
    
    This agent reviews business intelligence insights and immediately takes
    action by drafting specific artifacts (emails, alerts, tickets) using
    its enterprise tools.
    
    Args:
        llm: Language model for the agent
        tools: Optional list of tools (defaults to enterprise action tools)
    
    Returns:
        CrewAI Agent configured as Executive COO
    """
    if tools is None:
        tools = get_enterprise_tools()
    
    return Agent(
        role="Chief Operating Officer (AI Delegate)",
        goal=(
            "Review business intelligence insights and prepare actionable operational "
            "plans to mitigate risks and capitalize on opportunities. Convert insights "
            "into concrete actions: draft emails to executives, create alert notifications, "
            "and generate tickets for operational teams."
        ),
        backstory=(
            "You are a decisive operational leader with 15+ years of executive experience. "
            "When you receive a data insight (e.g., 'Revenue dropped 15% in EMEA region'), "
            "you immediately determine:\n"
            "1. Who needs to be informed (CEO, CFO, Regional VP)\n"
            "2. What specific actions need to be taken\n"
            "3. How urgent the situation is\n\n"
            "You are EXTREMELY ACTION-ORIENTED. You don't just talk about sending emails or "
            "creating tickets - you ACTUALLY USE YOUR TOOLS to draft them. When you see a "
            "critical insight, you immediately:\n"
            "- Use draft_executive_email to create the actual email text\n"
            "- Use post_slack_alert to generate the specific alert message\n"
            "- Use create_erp_ticket to draft the detailed ticket\n\n"
            "You understand these are DRAFTS for human approval, but you always generate "
            "the complete, ready-to-send artifact rather than just describing what should "
            "be done. You write clear, professional, actionable communications."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
        max_iter=5
    )


class ActionTaskBuilder:
    """
    Builder for creating CrewAI tasks for the Executive Agent.
    
    Generates tasks that instruct the agent to analyze insights and
    execute specific enterprise tools to draft actionable artifacts.
    """
    
    @staticmethod
    def build_action_plan_task(
        agent: Agent,
        insight_context: str,
        recommended_action: str,
        context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create task for Executive Agent to generate action plan.
        
        Args:
            agent: Executive COO Agent
            insight_context: Business intelligence insight or anomaly description
            recommended_action: Suggested action type ("email", "alert", "ticket", "comprehensive")
            context: Previous tasks to use as context
        
        Returns:
            CrewAI Task for action planning
        """
        # Map action types to tool usage
        tool_instructions = {
            "email": (
                "Use the draft_executive_email tool to create an email draft. "
                "Identify the appropriate recipient, write a compelling subject line, "
                "and structure key points clearly."
            ),
            "alert": (
                "Use the post_slack_alert tool to create a Slack alert. "
                "Choose the appropriate channel, write a clear message, "
                "and set the correct priority level."
            ),
            "ticket": (
                "Use the create_erp_ticket tool to generate a ticket. "
                "Determine the issue type, priority level, and write a detailed "
                "description with actionable steps."
            ),
            "comprehensive": (
                "Use ALL available tools to create a comprehensive action plan:\n"
                "1. Draft an executive email for leadership\n"
                "2. Create a Slack alert for the operations team\n"
                "3. Generate an ERP ticket for tracking and resolution\n\n"
                "Execute each tool separately to generate complete artifacts."
            )
        }
        
        action_instruction = tool_instructions.get(
            recommended_action.lower(),
            tool_instructions["comprehensive"]
        )
        
        return Task(
            description=(
                f"Analyze the following business intelligence insight and take immediate action:\n\n"
                f"INSIGHT:\n{insight_context}\n\n"
                f"RECOMMENDED ACTION TYPE: {recommended_action}\n\n"
                f"YOUR TASK:\n"
                f"{action_instruction}\n\n"
                f"IMPORTANT INSTRUCTIONS:\n"
                f"- You MUST actually execute the tools, not just describe what to do\n"
                f"- Generate complete, ready-to-use drafts with all required details\n"
                f"- Be specific: include real names, channels, subject lines\n"
                f"- Write professional, executive-level communications\n"
                f"- Remember: these are DRAFTS for human approval\n\n"
                f"Provide the generated draft artifacts in your response."
            ),
            expected_output=(
                "Complete draft artifacts generated using your tools:\n"
                "- If email: Full email draft with To/Subject/Body\n"
                "- If alert: Complete Slack message with channel and priority\n"
                "- If ticket: Full ticket draft with ID, description, and actions\n"
                "- If comprehensive: All three artifacts above\n\n"
                "Each artifact should be production-ready after human review."
            ),
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def build_insight_triage_task(
        agent: Agent,
        insights: List[Dict[str, Any]],
        context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create task for triaging multiple insights and prioritizing actions.
        
        Args:
            agent: Executive COO Agent
            insights: List of business insights with severity/context
            context: Previous tasks
        
        Returns:
            CrewAI Task for insight triage
        """
        insights_text = "\n\n".join([
            f"{i+1}. {insight.get('description', insight)}\n"
            f"   Severity: {insight.get('severity', 'unknown') if isinstance(insight, dict) else 'unknown'}"
            for i, insight in enumerate(insights)
        ])
        
        return Task(
            description=(
                f"Review the following business intelligence insights and perform triage:\n\n"
                f"INSIGHTS:\n{insights_text}\n\n"
                f"YOUR TASK:\n"
                f"1. Analyze each insight for urgency and business impact\n"
                f"2. Prioritize them (Critical, High, Medium, Low)\n"
                f"3. For the TOP 2 most critical insights, use your tools to:\n"
                f"   - Draft an executive email\n"
                f"   - Create a Slack alert\n"
                f"   - Generate an ERP ticket\n\n"
                f"4. For remaining insights, provide brief recommended actions\n\n"
                f"Focus on insights that require immediate executive attention or "
                f"operational intervention."
            ),
            expected_output=(
                "Triage report with:\n"
                "1. Prioritized list of insights with severity ratings\n"
                "2. Complete draft artifacts (email, alert, ticket) for top 2 critical insights\n"
                "3. Brief action recommendations for remaining insights\n"
                "4. Overall operational risk assessment"
            ),
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def build_escalation_task(
        agent: Agent,
        critical_alert: str,
        affected_metrics: List[str],
        stakeholders: List[str],
        context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create task for escalating critical issues to leadership.
        
        Args:
            agent: Executive COO Agent
            critical_alert: Description of critical issue
            affected_metrics: List of affected KPIs/metrics
            stakeholders: List of people who need to be notified
            context: Previous tasks
        
        Returns:
            CrewAI Task for critical escalation
        """
        metrics_text = ", ".join(affected_metrics)
        stakeholder_text = ", ".join(stakeholders)
        
        return Task(
            description=(
                f"CRITICAL ESCALATION REQUIRED\n\n"
                f"ALERT: {critical_alert}\n\n"
                f"AFFECTED METRICS: {metrics_text}\n"
                f"STAKEHOLDERS: {stakeholder_text}\n\n"
                f"YOUR IMMEDIATE ACTIONS:\n"
                f"1. Draft urgent executive email to: {stakeholder_text}\n"
                f"   - Subject line must convey urgency\n"
                f"   - Include specific metric impacts\n"
                f"   - Recommend immediate meeting/action\n\n"
                f"2. Create HIGH PRIORITY Slack alert to #executive channel\n"
                f"   - Clear, concise summary of issue\n"
                f"   - Tag critical stakeholders\n\n"
                f"3. Generate P1 (Critical) ERP ticket\n"
                f"   - Issue type: Incident\n"
                f"   - Detailed description with metrics\n"
                f"   - Escalation path defined\n\n"
                f"Execute ALL THREE tools to generate complete escalation package."
            ),
            expected_output=(
                "Complete critical escalation package:\n"
                "1. Urgent executive email draft (ready to send)\n"
                "2. High-priority Slack alert (ready to post)\n"
                "3. P1 Critical ERP ticket (ready to create)\n\n"
                "All artifacts should reflect the critical nature and require "
                "immediate human review and approval."
            ),
            agent=agent,
            context=context or []
        )


def create_action_workflow(
    llm: ChatGroq,
    insight: str,
    action_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Create a complete action workflow with agent and task.
    
    Convenience function to quickly set up Executive Agent with action task.
    
    Args:
        llm: Language model
        insight: Business intelligence insight
        action_type: Type of action ("email", "alert", "ticket", "comprehensive")
    
    Returns:
        Dict with 'agent' and 'task' keys
    """
    agent = create_executive_agent(llm)
    task = ActionTaskBuilder.build_action_plan_task(
        agent=agent,
        insight_context=insight,
        recommended_action=action_type
    )
    
    return {
        "agent": agent,
        "task": task,
        "insight": insight,
        "action_type": action_type
    }
