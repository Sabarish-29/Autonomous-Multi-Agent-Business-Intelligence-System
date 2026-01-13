"""
Enterprise Action Tools for Phase 3: Autonomous Action Loops

Tools for the Executive COO Agent to draft business actions including:
- Executive emails
- Slack alerts
- ERP/ticketing system entries

IMPORTANT: All tools generate DRAFTS for human approval. No actions are automatically executed.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from crewai.tools import BaseTool
from pydantic import Field

logger = logging.getLogger(__name__)


class DraftExecutiveEmailTool(BaseTool):
    """Tool to generate professionally formatted executive email DRAFTS."""
    
    name: str = "draft_executive_email"
    description: str = (
        "Generate a professionally formatted executive email DRAFT. "
        "**IMPORTANT**: This creates a DRAFT email for human review. "
        "It does NOT send the email. Requires: recipient (email address), "
        "subject (email subject line), key_points (comma or newline separated bullet points)."
    )
    
    def _run(self, recipient: str, subject: str, key_points: str) -> str:
        """
        Generate email draft.
        
        Args:
            recipient: Email recipient (name or email address)
            subject: Email subject line
            key_points: Key points/bullet points (comma or newline separated)
        
        Returns:
            str: Formatted email draft
        """
        try:
            # Parse key_points - handle string input (comma or newline separated)
            if isinstance(key_points, str):
                # Try splitting by newline first, then by comma
                if '\n' in key_points:
                    points_list = [p.strip() for p in key_points.split('\n') if p.strip()]
                else:
                    points_list = [p.strip() for p in key_points.split(',') if p.strip()]
            else:
                points_list = [str(key_points)]
            
            # Build email body
            body_parts = []
            body_parts.append(f"To: {recipient}")
            body_parts.append(f"Subject: {subject}")
            body_parts.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            body_parts.append("\n---\n")
            body_parts.append(f"Dear {recipient.split('@')[0]},\n")
            body_parts.append("I hope this message finds you well. I am writing to bring to your attention critical insights from our recent business intelligence analysis:\n")
            
            # Add key points
            for i, point in enumerate(points_list, 1):
                body_parts.append(f"{i}. {point}")
            
            body_parts.append("\nBased on this analysis, I recommend we schedule a meeting to discuss immediate action items and resource allocation.\n")
            body_parts.append("Please let me know your availability for this week.\n")
            body_parts.append("\nBest regards,")
            body_parts.append("AI Operations Assistant")
            body_parts.append("\n---")
            body_parts.append("[DRAFT - REQUIRES HUMAN REVIEW AND APPROVAL BEFORE SENDING]")
            
            email_draft = "\n".join(body_parts)
            
            logger.info(f"Generated email draft for {recipient}: {subject}")
            return email_draft
            
        except Exception as e:
            logger.error(f"Failed to generate email draft: {e}")
            return f"ERROR: Failed to generate email draft - {str(e)}"


class PostSlackAlertTool(BaseTool):
    """Tool to generate Slack alert message DRAFTS (simulated posting)."""
    
    name: str = "post_slack_alert"
    description: str = (
        "Generate a Slack alert message DRAFT (simulated posting). "
        "**IMPORTANT**: This is a MOCK tool. It does NOT actually post to Slack. "
        "Requires: channel (Slack channel name like #ops-alerts), "
        "message (alert message content), priority (low/medium/high/critical)."
    )
    
    def _run(self, channel: str, message: str, priority: str = "medium") -> str:
        """
        Generate Slack alert draft.
        
        Args:
            channel: Slack channel name (e.g., "#ops-alerts")
            message: Alert message content
            priority: Priority level ("low", "medium", "high", "critical")
        
        Returns:
            str: Draft alert content
        """
        try:
            # Normalize channel name
            if not channel.startswith("#"):
                channel = f"#{channel}"
            
            # Priority emoji mapping
            priority_emoji = {
                "low": "ℹ️",
                "medium": "⚠️",
                "high": "🚨",
                "critical": "🔴"
            }
            
            emoji = priority_emoji.get(priority.lower(), "ℹ️")
            
            # Build Slack message format
            slack_draft = f"""
════════════════════════════════════════
SLACK ALERT DRAFT (MOCK)
════════════════════════════════════════
Channel: {channel}
Priority: {priority.upper()}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{emoji} **{priority.upper()} PRIORITY ALERT** {emoji}

{message}

────────────────────────────────────────
[MOCK ALERT - NOT ACTUALLY POSTED TO SLACK]
[Human must manually post to Slack after review]
════════════════════════════════════════
"""
            
            logger.info(f"Generated Slack alert draft for {channel} (priority: {priority})")
            return slack_draft
            
        except Exception as e:
            logger.error(f"Failed to generate Slack alert: {e}")
            return f"ERROR: Failed to generate Slack alert - {str(e)}"


class CreateERPTicketTool(BaseTool):
    """Tool to generate ERP/ticketing system entry DRAFTS."""
    
    name: str = "create_erp_ticket"
    description: str = (
        "Generate an ERP/ticketing system entry DRAFT (Jira, SAP, ServiceNow, etc.). "
        "**IMPORTANT**: This is a MOCK tool. It does NOT actually create a ticket. "
        "Requires: issue_type (Bug/Task/Incident/Change Request), "
        "priority (P1/P2/P3/P4 or Critical/High/Medium/Low), description (detailed description)."
    )
    
    def _run(self, issue_type: str, priority: str, description: str) -> str:
        """
        Generate ERP ticket draft.
        
        Args:
            issue_type: Type of issue (e.g., "Bug", "Task", "Incident")
            priority: Priority level ("P1", "P2", "P3", "P4" or "Critical", "High", "Medium", "Low")
            description: Detailed description of the issue/task
        
        Returns:
            str: Draft ticket content
        """
        try:
            # Normalize priority
            priority_map = {
                "critical": "P1",
                "high": "P2",
                "medium": "P3",
                "low": "P4"
            }
            priority = priority_map.get(priority.lower(), priority.upper())
            
            # Generate ticket ID (mock)
            ticket_id = f"DRAFT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Build ticket format
            ticket_draft = f"""
╔════════════════════════════════════════╗
║   ERP TICKET DRAFT (MOCK)              ║
╚════════════════════════════════════════╝

Ticket ID: {ticket_id}
Issue Type: {issue_type}
Priority: {priority}
Status: [DRAFT - NOT CREATED]
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reporter: AI Operations Assistant

────────────────────────────────────────
DESCRIPTION:
────────────────────────────────────────
{description}

────────────────────────────────────────
RECOMMENDED ACTIONS:
────────────────────────────────────────
1. Review the reported issue/insight
2. Assign to appropriate team/individual
3. Set target resolution date
4. Establish escalation path if needed

────────────────────────────────────────
[MOCK TICKET - NOT CREATED IN ACTUAL ERP SYSTEM]
[Human must manually create this ticket in Jira/SAP/ServiceNow]
╚════════════════════════════════════════╝
"""
            
            logger.info(f"Generated ERP ticket draft: {issue_type} ({priority})")
            return ticket_draft
            
        except Exception as e:
            logger.error(f"Failed to generate ERP ticket: {e}")
            return f"ERROR: Failed to generate ERP ticket - {str(e)}"


# Convenience function to get all tools as a list
def get_enterprise_tools() -> List[BaseTool]:
    """
    Get list of all enterprise action tools.
    
    Returns:
        List of tool instances for use with CrewAI agents
    """
    return [
        DraftExecutiveEmailTool(),
        PostSlackAlertTool(),
        CreateERPTicketTool()
    ]
