"""
Test Phase 4: Collaborative Boardroom

Tests Voice Briefer Agent and Boardroom Dashboard components.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.voice_briefer import (
    create_voice_briefer_agent,
    SpeechTaskBuilder,
    generate_voice_brief
)
from langchain_groq import ChatGroq
import os


def test_1_voice_agent_creation():
    """Test Voice Briefer agent creation."""
    print("\n=== Test 1: Voice Briefer Agent Creation ===")
    
    # Create mock LLM (we won't actually call it in tests)
    try:
        llm = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY", "test-key"))
    except:
        # Fallback if Groq not available
        llm = None
        print("⚠️ Groq API not available, using mock LLM")
    
    agent = create_voice_briefer_agent(llm)
    
    assert agent is not None
    assert agent.role == "Executive Boardroom Briefer"
    assert "speech scripts" in agent.goal.lower()
    assert "short sentences" in agent.backstory.lower()
    assert "strategic question" in agent.backstory.lower()
    
    print(f"✓ Voice Briefer agent created")
    print(f"  Role: {agent.role}")
    print(f"  Goal: {agent.goal[:80]}...")
    print(f"  Backstory: {len(agent.backstory)} chars")


def test_2_speech_task_builder():
    """Test Speech Task Builder initialization."""
    print("\n=== Test 2: Speech Task Builder ===")
    
    builder = SpeechTaskBuilder(target_duration=45, words_per_second=2.5)
    
    assert builder.target_duration == 45
    assert builder.words_per_second == 2.5
    assert builder.max_words == 112  # 45 * 2.5
    
    print(f"✓ Speech Task Builder initialized")
    print(f"  Target duration: {builder.target_duration}s")
    print(f"  Max words: {builder.max_words} (~{builder.words_per_second} wps)")


def test_3_briefing_task_creation():
    """Test voice briefing task creation."""
    print("\n=== Test 3: Briefing Task Creation ===")
    
    try:
        llm = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY", "test-key"))
    except:
        llm = None
    
    agent = create_voice_briefer_agent(llm)
    builder = SpeechTaskBuilder(target_duration=45)
    
    context = {
        'query': 'What are Q3 revenue trends?',
        'sql_results': {'rows': [{'region': 'NA', 'revenue': 125000}, {'region': 'EMEA', 'revenue': 98000}]},
        'key_metrics': [125000, 98000, -15],
        'insights': 'EMEA region declined 15% due to supply chain issues'
    }
    
    task = builder.build_briefing_task(agent, context)
    
    assert task is not None
    assert "45-second" in task.description
    assert "Maximum 112 words" in task.description
    assert "Q3 revenue trends" in task.description
    assert "strategic question" in task.description.lower()
    
    print(f"✓ Briefing task created")
    print(f"  Query: {context['query']}")
    print(f"  Description length: {len(task.description)} chars")
    print(f"  Expected output defined: {len(task.expected_output) > 0}")


def test_4_multi_insight_briefing():
    """Test multi-insight briefing task."""
    print("\n=== Test 4: Multi-Insight Briefing ===")
    
    try:
        llm = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY", "test-key"))
    except:
        llm = None
    
    agent = create_voice_briefer_agent(llm)
    builder = SpeechTaskBuilder(target_duration=45)
    
    insights = [
        {'priority': 'Critical', 'title': 'Revenue decline in EMEA', 'details': 'Down 15% due to supply chain'},
        {'priority': 'High', 'title': 'Customer churn increased', 'details': 'Up 8% in enterprise segment'},
        {'priority': 'Medium', 'title': 'Product defect rate spike', 'details': '12% increase in returns'}
    ]
    
    priority_order = [0, 1, 2]  # Critical, High, Medium
    
    task = builder.build_multi_insight_briefing(agent, insights, priority_order)
    
    assert task is not None
    assert "3 prioritized insights" in task.description.lower()
    assert "Revenue decline in EMEA" in task.description
    assert "ONE strategic question" in task.description
    
    print(f"✓ Multi-insight briefing task created")
    print(f"  Insights to cover: {len(insights)}")
    print(f"  Priority order: {priority_order}")
    print(f"  Top insight: {insights[0]['title']}")


def test_5_executive_summary_task():
    """Test executive summary task."""
    print("\n=== Test 5: Executive Summary Task ===")
    
    try:
        llm = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY", "test-key"))
    except:
        llm = None
    
    agent = create_voice_briefer_agent(llm)
    builder = SpeechTaskBuilder(target_duration=45)
    
    full_analysis = """
    Comprehensive Q3 Analysis Report:
    
    Revenue Performance:
    - NA region: $125M (+8% YoY)
    - EMEA region: $98M (-15% YoY) 
    - APAC region: $110M (+12% YoY)
    
    Root Cause Analysis:
    EMEA decline attributed to:
    1. Supply chain disruptions (40% impact)
    2. Currency headwinds (30% impact)
    3. Increased competition (30% impact)
    
    Predictive Scenarios:
    - Best case: Recovery to $112M by Q4
    - Expected: Stabilization at $100M
    - Worst case: Further decline to $92M
    
    Recommended Actions:
    1. Accelerate supplier diversification
    2. Implement currency hedging strategy
    3. Increase marketing spend in EMEA by 20%
    """ * 5  # Repeat to make it long
    
    task = builder.build_executive_summary_task(agent, full_analysis, executive_focus="risk mitigation")
    
    assert task is not None
    assert "45-second" in task.description
    assert "risk mitigation" in task.description.lower()
    assert len(task.description) > 0
    
    print(f"✓ Executive summary task created")
    print(f"  Full analysis length: {len(full_analysis)} chars")
    print(f"  Executive focus: risk mitigation")
    print(f"  Task description: {len(task.description)} chars")


def test_6_context_summary_building():
    """Test context summary building."""
    print("\n=== Test 6: Context Summary Building ===")
    
    builder = SpeechTaskBuilder()
    
    context_summary = builder._build_context_summary(
        query="What are revenue trends?",
        sql_results={'rows': [{'region': 'NA', 'revenue': 125000}]},
        predictions={'baseline': 100000, 'expected': 110000, 'worst_case': 95000},
        insights="EMEA region shows concerning decline trends",
        actions=[
            {'type': 'email', 'description': 'Alert CEO about EMEA situation'},
            {'type': 'slack', 'description': 'Notify ops team'}
        ],
        key_metrics=[125000, 98000, 110000]
    )
    
    assert len(context_summary) > 0
    assert "DATA" in context_summary or "PREDICTIONS" in context_summary
    assert "Retrieved 1 records" in context_summary
    assert "Baseline scenario" in context_summary
    assert "EMEA region" in context_summary
    assert "Alert CEO" in context_summary
    assert "125000" in context_summary
    
    print(f"✓ Context summary built")
    print(f"  Summary length: {len(context_summary)} chars")
    print(f"  Contains DATA section: {'DATA' in context_summary}")
    print(f"  Contains PREDICTIONS section: {'PREDICTIONS' in context_summary}")
    print(f"  Contains INSIGHTS section: {'INSIGHTS' in context_summary}")


def test_7_voice_workflow_creation():
    """Test complete voice workflow creation."""
    print("\n=== Test 7: Voice Workflow Creation ===")
    
    try:
        llm = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY", "test-key"))
    except:
        llm = None
    
    agent = create_voice_briefer_agent(llm)
    builder = SpeechTaskBuilder(target_duration=45)
    
    context = {
        'query': 'Analyze Q3 performance',
        'key_metrics': [125000, 98000, 110000]
    }
    
    workflow = builder.create_voice_workflow(agent, context)
    
    assert workflow is not None
    assert len(workflow.agents) == 1
    assert len(workflow.tasks) == 1
    assert workflow.agents[0].role == "Executive Boardroom Briefer"
    
    print(f"✓ Voice workflow created")
    print(f"  Agents: {len(workflow.agents)}")
    print(f"  Tasks: {len(workflow.tasks)}")
    print(f"  Workflow verbose: {workflow.verbose}")


def test_8_word_count_calculation():
    """Test word count and duration calculations."""
    print("\n=== Test 8: Word Count Calculations ===")
    
    # Test different durations
    test_cases = [
        (30, 2.5, 75),   # 30s at 2.5 wps = 75 words
        (45, 2.5, 112),  # 45s at 2.5 wps = 112 words
        (60, 2.5, 150),  # 60s at 2.5 wps = 150 words
        (45, 3.0, 135),  # 45s at 3.0 wps = 135 words (faster)
    ]
    
    for duration, wps, expected_words in test_cases:
        builder = SpeechTaskBuilder(target_duration=duration, words_per_second=wps)
        assert builder.max_words == expected_words
        print(f"  ✓ {duration}s at {wps} wps = {expected_words} words")
    
    print(f"✓ Word count calculations correct")


def test_9_tts_optimization_requirements():
    """Test TTS optimization requirements in task descriptions."""
    print("\n=== Test 9: TTS Optimization Requirements ===")
    
    try:
        llm = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY", "test-key"))
    except:
        llm = None
    
    agent = create_voice_briefer_agent(llm)
    builder = SpeechTaskBuilder()
    
    context = {'query': 'Test query', 'key_metrics': [100, 200]}
    task = builder.build_briefing_task(agent, context)
    
    # Check for TTS-specific requirements
    tts_keywords = [
        "short sentences",
        "under 15 words",
        "natural speech",
        "TTS",
        "pauses",
        "conversational"
    ]
    
    description_lower = task.description.lower()
    found_keywords = [kw for kw in tts_keywords if kw.lower() in description_lower]
    
    assert len(found_keywords) >= 3, f"Missing TTS keywords. Found: {found_keywords}"
    
    print(f"✓ TTS optimization requirements present")
    print(f"  Keywords found: {', '.join(found_keywords)}")


def test_10_strategic_question_requirement():
    """Test strategic question requirement in all tasks."""
    print("\n=== Test 10: Strategic Question Requirement ===")
    
    try:
        llm = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY", "test-key"))
    except:
        llm = None
    
    agent = create_voice_briefer_agent(llm)
    builder = SpeechTaskBuilder()
    
    # Test all task types
    context = {'query': 'Test', 'key_metrics': [100]}
    insights = [{'priority': 'High', 'title': 'Test', 'details': 'Test'}]
    
    task1 = builder.build_briefing_task(agent, context)
    task2 = builder.build_multi_insight_briefing(agent, insights, [0])
    task3 = builder.build_executive_summary_task(agent, "Test analysis", "growth")
    
    for idx, task in enumerate([task1, task2, task3], 1):
        assert "question" in task.description.lower()
        assert "strategic" in task.description.lower() or "action" in task.description.lower()
        print(f"  ✓ Task {idx}: Strategic question requirement present")
    
    print(f"✓ All tasks require strategic questions")


# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 4: COLLABORATIVE BOARDROOM TEST SUITE")
    print("=" * 60)
    
    try:
        test_1_voice_agent_creation()
        test_2_speech_task_builder()
        test_3_briefing_task_creation()
        test_4_multi_insight_briefing()
        test_5_executive_summary_task()
        test_6_context_summary_building()
        test_7_voice_workflow_creation()
        test_8_word_count_calculation()
        test_9_tts_optimization_requirements()
        test_10_strategic_question_requirement()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Phase 4 Voice Briefer Ready!")
        print("=" * 60)
        print("\nVoice Briefer Agent Features:")
        print("✓ Executive-optimized speech scripts")
        print("✓ 45-second target briefings (~112 words)")
        print("✓ TTS-optimized (short sentences, natural pauses)")
        print("✓ Multi-insight prioritization")
        print("✓ Strategic question endings")
        print("✓ Context integration (Phase 1-3 outputs)")
        print("\nNext: Launch boardroom dashboard with:")
        print("  streamlit run src/ui/boardroom_app.py")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
