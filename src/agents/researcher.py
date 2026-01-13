"""
Researcher Agent for Autonomous Multi-Agent Business Intelligence System Phase 4
===========================================

External knowledge retrieval agent that uses Tavily Search API to fetch
real-time market data, industry trends, and contextual information to enrich
internal database insights.

Features:
- Tavily Search API integration
- CrewAI tool wrapper
- Search result summarization
- Context-aware query formulation
- Rate limiting and error handling
- Multiple search modes (news, general, academic)

Author: Sabarish-29
Version: 2.0.4
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from crewai import Agent, Task, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchMode(Enum):
    """Search mode types"""
    GENERAL = "general"
    NEWS = "news"
    ACADEMIC = "academic"


class TavilySearchInput(BaseModel):
    """Input schema for Tavily Search Tool"""
    query: str = Field(..., description="The search query to execute")
    search_mode: str = Field(
        default="general",
        description="Search mode: 'general', 'news', or 'academic'"
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of results to return (1-10)"
    )


class TavilySearchTool(BaseTool):
    """
    CrewAI-compatible tool for Tavily Search API.

    Allows agents to search the web for real-time information,
    market data, news articles, and research papers.
    """

    name: str = "tavily_search"
    description: str = """
    Search the web for real-time information using Tavily Search API.

    Use this tool to:
    - Fetch market trends and industry data
    - Find news articles about companies or sectors
    - Research economic indicators and forecasts
    - Get competitor analysis and benchmarks
    - Discover external factors affecting business metrics

    Input Parameters:
    - query: The search query (be specific and contextual)
    - search_mode: 'general' for broad search, 'news' for recent news, 'academic' for research
    - max_results: Number of results to return (1-10, default 5)

    Returns:
    - Formatted search results with titles, snippets, URLs, and publication dates
    """

    args_schema: type[BaseModel] = TavilySearchInput

    api_key: Optional[str] = Field(
        default=None,
        description="Tavily API key (optional; defaults to TAVILY_API_KEY env var)",
    )
    _client: Any = PrivateAttr(default=None)

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily Search Tool.

        Args:
            api_key: Tavily API key (or set TAVILY_API_KEY env var)
        """
        resolved_key = api_key or os.getenv("TAVILY_API_KEY")
        super().__init__(api_key=resolved_key)

        if not self.api_key:
            logger.warning("⚠️ TAVILY_API_KEY not set. Web search will be unavailable.")
            self._client = None
        else:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
                logger.info("✅ Tavily Search Tool initialized successfully")
            except ImportError:
                logger.error("❌ tavily-python not installed. Run: pip install tavily-python")
                self._client = None
            except Exception as e:
                logger.error(f"❌ Error initializing Tavily client: {e}")
                self._client = None

    def _run(
        self,
        query: str,
        search_mode: str = "general",
        max_results: int = 5
    ) -> str:
        """
        Execute a web search using Tavily API.

        Args:
            query: Search query
            search_mode: Type of search (general, news, academic)
            max_results: Number of results to return

        Returns:
            Formatted search results as a string
        """
        if not self._client:
            return "❌ Tavily Search is not available. Please set TAVILY_API_KEY environment variable."

        try:
            logger.info(f"🔍 Executing Tavily search: '{query}' (mode: {search_mode})")

            # Validate parameters
            max_results = max(1, min(10, max_results))

            # Execute search
            search_params = {
                "query": query,
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False
            }

            # Add search depth for news mode
            if search_mode == "news":
                search_params["search_depth"] = "basic"
                search_params["days"] = 7  # Last 7 days for news

            response = self._client.search(**search_params)

            # Format results
            formatted_results = self._format_search_results(response, query, search_mode)

            logger.info(f"✅ Tavily search completed: {len(response.get('results', []))} results")

            return formatted_results

        except Exception as e:
            logger.error(f"❌ Tavily search failed: {e}")
            return f"❌ Search failed: {str(e)}"

    def _format_search_results(self, response: Dict[str, Any], query: str, mode: str) -> str:
        """
        Format Tavily search results for agent consumption.

        Args:
            response: Raw Tavily API response
            query: Original search query
            mode: Search mode used

        Returns:
            Formatted string with search results
        """
        output = []

        # Header
        output.append(f"# Web Search Results for: '{query}'")
        output.append(f"**Search Mode:** {mode.upper()}")
        output.append(f"**Search Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")

        # AI-generated answer (if available)
        if response.get("answer"):
            output.append("## AI Summary")
            output.append(response["answer"])
            output.append("")

        # Individual results
        results = response.get("results", [])

        if not results:
            output.append("*No results found.*")
            return "\n".join(output)

        output.append(f"## Top {len(results)} Results")
        output.append("")

        for idx, result in enumerate(results, 1):
            title = result.get("title", "No Title")
            url = result.get("url", "")
            content = result.get("content", "No content available")
            score = result.get("score", 0)

            output.append(f"### {idx}. {title}")
            output.append(f"**URL:** {url}")
            output.append(f"**Relevance Score:** {score:.2f}")
            output.append("")
            output.append(f"**Summary:** {content}")
            output.append("")
            output.append("---")
            output.append("")

        return "\n".join(output)


class ResearcherAgent:
    """
    Wrapper class for the Researcher Agent with helper methods.
    """

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        llm_model: str = "llama-3.3-70b-versatile"
    ):
        """
        Initialize the Researcher Agent.

        Args:
            tavily_api_key: Tavily API key
            llm_model: LLM model to use for the agent
        """
        self.tavily_tool = TavilySearchTool(api_key=tavily_api_key)

        # Initialize LLM
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        max_tokens_env = os.getenv("DATAGENIE_LLM_MAX_TOKENS")
        try:
            max_tokens = int(max_tokens_env) if max_tokens_env else None
        except ValueError:
            max_tokens = None
        llm_kwargs = {"temperature": 0.3}
        if max_tokens and max_tokens > 0:
            llm_kwargs["max_tokens"] = max_tokens

        self.llm = LLM(
            model=f"groq/{llm_model}",
            is_litellm=True,
            api_key=groq_api_key,
            **llm_kwargs,
        )

        # Create the agent
        self.agent = self._create_agent()

        logger.info("🔬 Researcher Agent initialized")

    def _create_agent(self) -> Agent:
        """Create the Researcher CrewAI agent"""
        test_mode = os.getenv("DATAGENIE_TEST_MODE") == "1"
        backstory = (
            "Use Tavily to fetch a few relevant sources and summarize briefly."
            if test_mode
            else """
            You are an expert Market Research Analyst with deep knowledge of business intelligence
            and data-driven decision making. Your specialty is finding relevant external context
            (market trends, industry benchmarks, economic indicators, competitor analysis) that
            helps explain internal business metrics.

            You use the Tavily Search API to find:
            - Recent news articles about the industry
            - Market research reports and forecasts
            - Economic indicators and trends
            - Competitor performance data
            - External factors affecting business (regulations, technology shifts, consumer behavior)

            You synthesize search results into concise, actionable insights that directly
            relate to the internal data analysis being performed.
            """
        )
        return Agent(
            role="Market Research Analyst",
            goal="Fetch external market data, industry trends, and contextual information to enrich internal database insights",
            backstory=backstory,
            tools=[self.tavily_tool],
            llm=self.llm,
            verbose=not test_mode,
            allow_delegation=False
        )

    def create_research_task(
        self,
        context: str,
        internal_findings: str,
        research_focus: Optional[str] = None
    ) -> Task:
        """
        Create a research task for the agent.

        Args:
            context: The original user query or business question
            internal_findings: Summary of internal database analysis
            research_focus: Specific aspect to research (optional)

        Returns:
            CrewAI Task for the researcher
        """
        if research_focus:
            description = f"""
            Based on this internal analysis:
            {internal_findings}

            Research the following external aspect:
            {research_focus}

            Original business question: {context}

            Use Tavily Search to find:
            1. Recent market trends related to this topic
            2. Industry benchmarks and forecasts
            3. External factors that might explain the internal findings
            4. Competitor or market comparison data

            Synthesize your findings to provide context for the internal analysis.
            """
        else:
            description = f"""
            Based on this internal analysis:
            {internal_findings}

            Original business question: {context}

            Use Tavily Search to find relevant external context that helps explain or
            validate these internal findings. Focus on:
            1. Market trends in the relevant industry/sector
            2. Economic indicators that might correlate
            3. Recent news or events that could impact these metrics
            4. Industry benchmarks for comparison

            Your goal is to provide external validation or alternative explanations
            for the internal data patterns.
            """

        expected_output = """
        A comprehensive research report including:
        1. **Key External Findings**: 2-3 most relevant external data points
        2. **Market Context**: How external trends relate to internal metrics
        3. **Validation/Contrast**: Do external sources confirm or contradict internal findings?
        4. **Actionable Insights**: What do the combined internal + external data suggest?
        5. **Sources**: List of URLs and publication dates for all cited information
        """

        return Task(
            description=description,
            expected_output=expected_output,
            agent=self.agent
        )

    def quick_search(self, query: str, mode: str = "general") -> str:
        """
        Perform a quick search without full agent orchestration.

        Args:
            query: Search query
            mode: Search mode (general, news, academic)

        Returns:
            Formatted search results
        """
        return self.tavily_tool._run(query=query, search_mode=mode, max_results=5)


# ============================================================================
# Helper Functions for CrewAI Integration
# ============================================================================

def create_researcher_agent(
    tavily_api_key: Optional[str] = None,
    llm_model: str = "llama-3.3-70b-versatile"
) -> Agent:
    """
    Factory function to create a Researcher Agent for CrewAI Manager.

    Args:
        tavily_api_key: Tavily API key
        llm_model: LLM model to use

    Returns:
        Configured CrewAI Agent
    """
    researcher = ResearcherAgent(tavily_api_key=tavily_api_key, llm_model=llm_model)
    return researcher.agent


def create_research_tool(tavily_api_key: Optional[str] = None) -> TavilySearchTool:
    """
    Factory function to create a Tavily Search Tool for agents.

    Args:
        tavily_api_key: Tavily API key

    Returns:
        Configured TavilySearchTool
    """
    return TavilySearchTool(api_key=tavily_api_key)


def detect_research_need(query: str, sql_results: Optional[Dict] = None) -> bool:
    """
    Heuristic to detect if external research would enhance the answer.

    Args:
        query: User's original question
        sql_results: Results from SQL query (optional)

    Returns:
        True if research is recommended
    """
    research_keywords = [
        "market", "industry", "trend", "forecast", "compare", "benchmark",
        "competitor", "average", "typical", "normal", "expected",
        "why", "reason", "cause", "explain", "context", "external"
    ]

    query_lower = query.lower()

    # Check for research keywords
    for keyword in research_keywords:
        if keyword in query_lower:
            return True

    # Check for comparison queries
    if any(word in query_lower for word in ["vs", "versus", "compared to"]):
        return True

    return False


# ============================================================================
# Example Usage
# ============================================================================

def example_usage():
    """Example of using the Researcher Agent"""

    # Initialize researcher
    researcher = ResearcherAgent(
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        llm_model="llama-3.3-70b-versatile"
    )

    # Quick search example
    print("\n=== Quick Search Example ===")
    results = researcher.quick_search(
        query="e-commerce market growth 2024",
        mode="news"
    )
    print(results)

    # Create research task (would be used in CrewAI workflow)
    print("\n=== Research Task Example ===")
    task = researcher.create_research_task(
        context="User asked: 'Is our 10% revenue growth good?'",
        internal_findings="Internal analysis shows 10% revenue growth over last quarter.",
        research_focus="E-commerce industry growth benchmarks for Q4 2024"
    )
    print(f"Task Description: {task.description}")


if __name__ == "__main__":
    example_usage()
