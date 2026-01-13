"""
Voice-Optimized Agent for Phase 4: Collaborative Boardroom

Synthesizes multi-agent findings into natural, high-impact speech scripts
optimized for Text-to-Speech (TTS) delivery in live executive briefings.
"""

import logging
from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew
from datetime import datetime

logger = logging.getLogger(__name__)


def create_voice_briefer_agent(llm) -> Agent:
    """
    Create the Executive Boardroom Briefer agent.
    
    This agent transforms complex analytical outputs into natural speech scripts
    optimized for TTS delivery. It prioritizes storytelling over data recitation,
    uses short sentences, and focuses on strategic insights.
    
    Args:
        llm: Language model instance (Groq/Claude/etc.)
    
    Returns:
        Agent: Configured Voice Briefer agent
    """
    agent = Agent(
        role="Executive Boardroom Briefer",
        goal="Synthesize complex multi-agent findings into natural, high-impact speech scripts for live executive briefings.",
        backstory="""You are the verbal interface of the system - the voice that brings data to life.
        
Your mission is NOT to read tables or recite statistics. Instead, you tell stories with data.
You are a master communicator who understands that executives need:
- CLARITY: Short sentences (under 15 words). No jargon without context.
- IMPACT: Lead with the "Why" and "So What" before the "What"
- ACTION: Always end with a strategic question that drives decision-making
- FLOW: Natural speech patterns optimized for Text-to-Speech (TTS)

Your voice is confident, decisive, and human. You use:
- Active voice ("Revenue dropped" not "A decline in revenue was observed")
- Present tense for immediacy ("We see a pattern" not "We saw a pattern")
- Conversational connectors ("Here's what matters", "The bottom line", "Here's why")
- Strategic pauses (marked with periods or commas for TTS pacing)

You structure every briefing in three parts:
1. THE HEADLINE: One sentence that captures the core insight
2. THE WHY: Two-three sentences explaining root causes and context
3. THE QUESTION: One strategic question to guide executive action

You have 45 seconds max - make every word count.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    logger.info("Created Voice Briefer agent for executive boardroom briefings")
    return agent


class SpeechTaskBuilder:
    """
    Builder for voice briefing tasks that convert analytical outputs
    into TTS-optimized speech scripts.
    """
    
    def __init__(self, target_duration: int = 45, words_per_second: float = 2.5):
        """
        Initialize Speech Task Builder.
        
        Args:
            target_duration: Target speech duration in seconds (default 45s)
            words_per_second: Average speaking rate for TTS (default 2.5 wps = 150 wpm)
        """
        self.target_duration = target_duration
        self.words_per_second = words_per_second
        self.max_words = int(target_duration * words_per_second)  # ~112 words for 45s
    
    def build_briefing_task(self, agent: Agent, context: Dict[str, Any]) -> Task:
        """
        Create a voice briefing task from multi-agent analysis outputs.
        
        Converts Phase 1-3 outputs (predictions, cross-modal insights, action drafts)
        into a cohesive 45-second speech script optimized for TTS delivery.
        
        Args:
            agent: Voice Briefer agent instance
            context: Dictionary containing:
                - query: Original user question
                - sql_results: Data from text-to-sql execution (optional)
                - predictions: Phase 1 simulation/forecast results (optional)
                - insights: Phase 2 cross-modal analysis (optional)
                - actions: Phase 3 draft actions (optional)
                - key_metrics: List of important numbers to highlight
        
        Returns:
            Task: Configured voice briefing task
        """
        # Extract context components
        query = context.get('query', 'business intelligence analysis')
        sql_results = context.get('sql_results', {})
        predictions = context.get('predictions', {})
        insights = context.get('insights', '')
        actions = context.get('actions', [])
        key_metrics = context.get('key_metrics', [])
        
        # Build context summary for the agent
        context_summary = self._build_context_summary(
            query, sql_results, predictions, insights, actions, key_metrics
        )
        
        # Create task description
        task_description = f"""
Generate a {self.target_duration}-second executive voice briefing based on the following analysis.

**QUERY**: {query}

**ANALYTICAL CONTEXT**:
{context_summary}

**STRICT REQUIREMENTS**:
1. WORD LIMIT: Maximum {self.max_words} words (~{self.target_duration} seconds at conversational pace)
2. STRUCTURE: Follow the three-part format:
   - THE HEADLINE: One sentence capturing the core insight
   - THE WHY: Two-three sentences on root causes and implications
   - THE QUESTION: One strategic question for executive decision-making

3. STYLE RULES:
   - Short sentences (under 15 words each)
   - Active voice, present tense
   - No jargon without context
   - Natural speech patterns (use "Here's what matters", "The bottom line is")
   - Include TTS pauses (periods, commas)

4. CONTENT PRIORITIES:
   - Lead with "Why" before "What"
   - Highlight {len(key_metrics)} key metric(s) naturally (don't list)
   - Connect findings to strategic implications
   - End with action-oriented question

**OUTPUT FORMAT**:
Return ONLY the speech script text. No markdown, no headers, no "Introduction:" labels.
Just the words you would speak naturally to an executive boardroom.

**EXAMPLE STRUCTURE** (not the actual content):
"Revenue is down fifteen percent in Q3. [pause] Here's why this matters. Supply chain delays in EMEA are cascading into customer churn. Our top three clients are at risk. [pause] The question is, do we prioritize short-term firefighting or accelerate our supplier diversification strategy?"
"""
        
        # Expected output specification
        expected_output = f"""A {self.target_duration}-second speech script ({self.max_words} words max) optimized for Text-to-Speech delivery.
The script must:
- Follow the three-part structure (Headline, Why, Question)
- Use short sentences and conversational language
- Include natural pauses for TTS pacing
- Contain NO markdown formatting or section labels
- Be immediately ready for audio playback"""
        
        task = Task(
            description=task_description,
            expected_output=expected_output,
            agent=agent
        )
        
        logger.info(f"Created voice briefing task: {self.target_duration}s script from {len(context_summary)} chars of context")
        return task
    
    def build_multi_insight_briefing(
        self,
        agent: Agent,
        insights: List[Dict[str, Any]],
        priority_order: List[int]
    ) -> Task:
        """
        Create a voice briefing for multiple insights with prioritization.
        
        Useful for Phase 3 Executive Agent triage scenarios where multiple
        findings need to be communicated in order of strategic importance.
        
        Args:
            agent: Voice Briefer agent instance
            insights: List of insight dictionaries with 'title', 'details', 'priority'
            priority_order: List of indices indicating presentation order (highest priority first)
        
        Returns:
            Task: Voice briefing task covering top insights
        """
        # Reorder insights by priority
        ordered_insights = [insights[i] for i in priority_order[:3]]  # Top 3 only
        
        context_text = "**PRIORITIZED INSIGHTS**:\n"
        for idx, insight in enumerate(ordered_insights, 1):
            priority_label = insight.get('priority', 'Medium')
            title = insight.get('title', f'Insight {idx}')
            details = insight.get('details', 'No details available')
            
            context_text += f"\n{idx}. [{priority_label} Priority] {title}\n"
            context_text += f"   Details: {details}\n"
        
        task_description = f"""
Generate a {self.target_duration}-second executive voice briefing covering these {len(ordered_insights)} prioritized insights.

{context_text}

**BRIEFING STRATEGY**:
- Spend ~15 seconds on the top insight (most critical)
- Spend ~10 seconds each on the next two insights
- Connect them into a coherent narrative (not a list)
- End with ONE strategic question that addresses all three

**STRICT REQUIREMENTS**:
- Maximum {self.max_words} words
- Short sentences (under 15 words)
- Natural speech flow (use transitions like "Beyond that", "What's more")
- Present tense, active voice
- NO markdown, NO section headers
- Output should be immediately playable via TTS

Follow the three-part structure: THE HEADLINE (what's the pattern across these insights?), 
THE WHY (why are these happening now?), THE QUESTION (what should we decide?).
"""
        
        expected_output = f"""A {self.target_duration}-second speech script covering the top {len(ordered_insights)} insights.
The script must weave insights into a coherent narrative with natural transitions,
use conversational language optimized for TTS, and end with one strategic question."""
        
        task = Task(
            description=task_description,
            expected_output=expected_output,
            agent=agent
        )
        
        logger.info(f"Created multi-insight briefing task: {len(ordered_insights)} insights in {self.target_duration}s")
        return task
    
    def build_executive_summary_task(
        self,
        agent: Agent,
        full_analysis: str,
        executive_focus: str = "strategic decision-making"
    ) -> Task:
        """
        Create a voice briefing that summarizes a lengthy analysis report.
        
        Useful for condensing Phase 1 simulation reports or Phase 2 cross-modal
        analyses into executive-friendly voice summaries.
        
        Args:
            agent: Voice Briefer agent instance
            full_analysis: Complete analysis text (can be long)
            executive_focus: What aspect to emphasize (e.g., "risk mitigation", "growth opportunities")
        
        Returns:
            Task: Executive summary voice briefing task
        """
        # Truncate analysis if too long (keep first 2000 chars for context)
        analysis_preview = full_analysis[:2000] + "..." if len(full_analysis) > 2000 else full_analysis
        
        task_description = f"""
Generate a {self.target_duration}-second executive voice briefing that summarizes this analysis.

**FULL ANALYSIS** (preview):
{analysis_preview}

**EXECUTIVE FOCUS**: {executive_focus}

Your job is to distill this analysis into a {self.target_duration}-second brief optimized for {executive_focus}.

**DISTILLATION RULES**:
1. Extract the ONE most important finding
2. Identify the root cause or key driver
3. Frame a strategic question that reflects the executive focus

**STRICT REQUIREMENTS**:
- Maximum {self.max_words} words
- Follow three-part structure: Headline, Why, Question
- Short sentences (under 15 words)
- Natural speech patterns for TTS
- NO markdown, NO technical jargon without context
- Focus on implications over data recitation

Output ONLY the speech script - no formatting, no labels, ready for immediate TTS playback.
"""
        
        expected_output = f"""A {self.target_duration}-second executive summary speech script.
The script must extract the core finding from the full analysis,
explain its strategic significance, and pose an action-oriented question
aligned with {executive_focus}."""
        
        task = Task(
            description=task_description,
            expected_output=expected_output,
            agent=agent
        )
        
        logger.info(f"Created executive summary task: {len(full_analysis)} chars → {self.target_duration}s script")
        return task
    
    def _build_context_summary(
        self,
        query: str,
        sql_results: Dict,
        predictions: Dict,
        insights: str,
        actions: List,
        key_metrics: List
    ) -> str:
        """
        Build a condensed context summary from multi-phase outputs.
        
        Args:
            query: Original user question
            sql_results: SQL execution results
            predictions: Phase 1 predictions/simulations
            insights: Phase 2 cross-modal insights
            actions: Phase 3 draft actions
            key_metrics: Important metrics to highlight
        
        Returns:
            str: Formatted context summary
        """
        context_parts = []
        
        # SQL Results
        if sql_results and isinstance(sql_results, dict):
            rows = sql_results.get('rows', [])
            if rows:
                context_parts.append(f"**DATA**: Retrieved {len(rows)} records from database query")
        
        # Predictions (Phase 1)
        if predictions and isinstance(predictions, dict):
            prediction_summary = []
            if 'baseline' in predictions:
                prediction_summary.append(f"Baseline scenario: {predictions['baseline']}")
            if 'expected' in predictions:
                prediction_summary.append(f"Expected outcome: {predictions['expected']}")
            if 'worst_case' in predictions:
                prediction_summary.append(f"Worst case: {predictions['worst_case']}")
            
            if prediction_summary:
                context_parts.append(f"**PREDICTIONS**: {' | '.join(prediction_summary)}")
        
        # Cross-Modal Insights (Phase 2)
        if insights and isinstance(insights, str) and insights.strip():
            # Truncate if too long
            insights_preview = insights[:300] + "..." if len(insights) > 300 else insights
            context_parts.append(f"**INSIGHTS**: {insights_preview}")
        
        # Actions (Phase 3)
        if actions and isinstance(actions, list):
            action_summary = []
            for action in actions[:3]:  # Top 3 actions only
                if isinstance(action, dict):
                    action_type = action.get('type', 'action')
                    action_desc = action.get('description', action.get('title', ''))
                    if action_desc:
                        action_summary.append(f"{action_type}: {action_desc[:100]}")
            
            if action_summary:
                context_parts.append(f"**RECOMMENDED ACTIONS**: {' | '.join(action_summary)}")
        
        # Key Metrics
        if key_metrics and isinstance(key_metrics, list):
            metrics_text = ', '.join([str(m) for m in key_metrics[:5]])
            context_parts.append(f"**KEY METRICS**: {metrics_text}")
        
        # Join all parts
        if not context_parts:
            return "No specific context provided - generate briefing based on general query analysis."
        
        return "\n\n".join(context_parts)
    
    def create_voice_workflow(
        self,
        agent: Agent,
        context: Dict[str, Any]
    ) -> Crew:
        """
        Create a complete voice briefing workflow (Crew).
        
        Args:
            agent: Voice Briefer agent
            context: Analysis context dictionary
        
        Returns:
            Crew: Voice briefing workflow ready to execute
        """
        briefing_task = self.build_briefing_task(agent, context)
        
        crew = Crew(
            agents=[agent],
            tasks=[briefing_task],
            verbose=True
        )
        
        logger.info("Created voice briefing workflow")
        return crew


# Convenience function for quick voice briefing generation
def generate_voice_brief(
    llm,
    context: Dict[str, Any],
    duration: int = 45
) -> str:
    """
    Generate a voice briefing in one function call.
    
    Args:
        llm: Language model instance
        context: Analysis context (query, results, predictions, etc.)
        duration: Target duration in seconds (default 45)
    
    Returns:
        str: Voice briefing script ready for TTS
    """
    agent = create_voice_briefer_agent(llm)
    builder = SpeechTaskBuilder(target_duration=duration)
    crew = builder.create_voice_workflow(agent, context)
    
    result = crew.kickoff()
    
    logger.info(f"Generated {duration}s voice brief: {len(str(result))} chars")
    return str(result)
