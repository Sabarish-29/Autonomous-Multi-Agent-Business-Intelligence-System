"""
Test Phase 1 Predictive Simulation functionality in scientist.py

Tests Monte Carlo simulation with hypothetical scenarios.
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.scientist import (
    create_scenario_architect_agent,
    DataScienceTaskBuilder,
    generate_analysis_code,
    generate_plotly_visualization_code
)
from langchain_groq import ChatGroq


def test_scenario_architect_creation():
    """Test that scenario architect agent is created properly."""
    print("\n=== Test 1: Create Scenario Architect Agent ===")
    
    # Mock LLM
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY", "test-key")
    )
    
    business_glossary = {
        'business_terms': {
            'price': {'sensitivity': 'high-revenue'},
            'shipping_days': {'sensitivity': 'demand'},
            'revenue': {'sensitivity': 'revenue'}
        },
        'column_aliases': {
            'price': ['unit_price', 'product_price'],
            'revenue': ['total_revenue', 'sales']
        }
    }
    
    agent = create_scenario_architect_agent(llm, business_glossary)
    
    assert agent.role == "Predictive Scenario Architect"
    assert "Monte Carlo" in agent.goal
    assert "stochastic modeling" in agent.backstory
    print(f"✓ Agent created: {agent.role}")
    print(f"  Goal: {agent.goal[:80]}...")
    print(f"  Backstory snippet: {agent.backstory[:100]}...")


def test_simulation_task_builder():
    """Test simulation task creation."""
    print("\n=== Test 2: Build Simulation Task ===")
    
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, api_key="test")
    agent = create_scenario_architect_agent(llm)
    
    hypothetical_vars = [
        {'column': 'price', 'change_pct': 10, 'change_type': 'increase'},
        {'column': 'shipping_days', 'change_pct': -20, 'change_type': 'decrease'}
    ]
    
    task = DataScienceTaskBuilder.build_simulation_task(
        agent=agent,
        dataframe_name="df",
        hypothetical_variables=hypothetical_vars,
        target_column="revenue",
        num_iterations=1000
    )
    
    assert "Monte Carlo simulation" in task.description
    assert "price increase by 10%" in task.description
    assert "shipping_days decrease by 20%" in task.description
    assert "baseline" in task.expected_output
    assert "scenarios" in task.expected_output
    assert "P10" in task.expected_output and "P50" in task.expected_output and "P90" in task.expected_output
    
    print(f"✓ Task created: {task.description[:100]}...")
    print(f"  Expected output keys: baseline, scenarios, distribution, confidence_interval")


def test_simulation_code_generation():
    """Test Monte Carlo simulation code generation."""
    print("\n=== Test 3: Generate Simulation Code ===")
    
    hypothetical_vars = [
        {'column': 'price', 'change_pct': 10, 'change_type': 'increase'},
        {'column': 'discount', 'change_pct': -5, 'change_type': 'decrease'}
    ]
    
    code = generate_analysis_code(
        analysis_type="simulation",
        dataframe_name="df",
        target_column="revenue",
        hypothetical_variables=hypothetical_vars,
        num_iterations=500
    )
    
    assert "import numpy as np" in code
    assert "import pandas as pd" in code
    assert "Monte Carlo simulation with 500 iterations" in code
    assert "price_change = np.random.normal" in code
    assert "discount_change = np.random.normal" in code
    assert "np.percentile(simulation_array, 10)" in code  # P10
    assert "np.percentile(simulation_array, 50)" in code  # P50
    assert "np.percentile(simulation_array, 90)" in code  # P90
    assert "'sensitivity_analysis'" in code
    
    print("✓ Simulation code generated successfully")
    print(f"  Code length: {len(code)} characters")
    print(f"  Includes: numpy distributions, percentiles, sensitivity analysis")


def test_simulation_code_execution():
    """Test that generated simulation code actually runs."""
    print("\n=== Test 4: Execute Simulation Code ===")
    
    # Create sample dataframe
    np.random.seed(42)
    df = pd.DataFrame({
        'price': np.random.normal(100, 10, 100),
        'discount': np.random.normal(5, 1, 100),
        'units': np.random.randint(10, 50, 100),
        'revenue': np.random.normal(5000, 500, 100)
    })
    
    hypothetical_vars = [
        {'column': 'price', 'change_pct': 15, 'change_type': 'increase'}
    ]
    
    code = generate_analysis_code(
        analysis_type="simulation",
        dataframe_name="df",
        target_column="revenue",
        hypothetical_variables=hypothetical_vars,
        num_iterations=100
    )
    
    # Execute the generated code
    local_vars = {'df': df}
    exec(code, globals(), local_vars)
    result = local_vars['result']
    
    assert 'baseline' in result
    assert 'scenarios' in result
    assert 'low' in result['scenarios']
    assert 'expected' in result['scenarios']
    assert 'high' in result['scenarios']
    assert 'distribution' in result
    assert 'confidence_interval' in result
    assert len(result['distribution']) == 100
    
    print(f"✓ Simulation executed successfully")
    print(f"  Baseline: {result['baseline']:.2f}")
    print(f"  Scenarios - Low: {result['scenarios']['low']:.2f}, Expected: {result['scenarios']['expected']:.2f}, High: {result['scenarios']['high']:.2f}")
    print(f"  95% CI: [{result['confidence_interval'][0]:.2f}, {result['confidence_interval'][1]:.2f}]")
    print(f"  Interpretation: {result['interpretation']}")


def test_simulation_visualization_code():
    """Test simulation visualization code generation."""
    print("\n=== Test 5: Generate Simulation Visualization ===")
    
    # Test distribution histogram
    dist_code = generate_plotly_visualization_code(
        chart_type="simulation_distribution",
        x_col="",
        y_col="",
        title="Revenue Simulation Results",
        distribution_var="result['distribution']",
        baseline_var="result['baseline']",
        scenarios_var="result['scenarios']"
    )
    
    assert "import plotly.graph_objects as go" in dist_code
    assert "go.Histogram" in dist_code
    assert "add_vline" in dist_code
    assert "Baseline" in dist_code
    assert "P10 (Low)" in dist_code
    assert "P50 (Expected)" in dist_code
    assert "P90 (High)" in dist_code
    
    print("✓ Distribution histogram code generated")
    
    # Test scenario comparison
    comp_code = generate_plotly_visualization_code(
        chart_type="scenario_comparison",
        x_col="",
        y_col="",
        title="Scenario Comparison",
        scenarios_var="result['scenarios']",
        baseline_var="result['baseline']"
    )
    
    assert "go.Bar" in comp_code
    assert "Baseline" in comp_code
    assert "Low (P10)" in comp_code
    assert "Expected (P50)" in comp_code
    assert "High (P90)" in comp_code
    
    print("✓ Scenario comparison code generated")


def test_full_simulation_with_visualization():
    """Integration test: run simulation and generate visualization."""
    print("\n=== Test 6: Full Simulation + Visualization ===")
    
    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame({
        'price': np.random.normal(50, 5, 200),
        'quantity': np.random.randint(10, 100, 200),
        'revenue': np.random.normal(3000, 300, 200)
    })
    
    # Run simulation
    hypothetical_vars = [
        {'column': 'price', 'change_pct': 20, 'change_type': 'increase'},
        {'column': 'quantity', 'change_pct': -10, 'change_type': 'decrease'}
    ]
    
    sim_code = generate_analysis_code(
        analysis_type="simulation",
        dataframe_name="df",
        target_column="revenue",
        hypothetical_variables=hypothetical_vars,
        num_iterations=500
    )
    
    local_vars = {'df': df}
    exec(sim_code, globals(), local_vars)
    result = local_vars['result']
    
    # Generate visualization
    viz_code = generate_plotly_visualization_code(
        chart_type="simulation_distribution",
        x_col="",
        y_col="",
        title="Revenue Impact: +20% Price, -10% Quantity",
        distribution_var="result['distribution']",
        baseline_var="result['baseline']",
        scenarios_var="result['scenarios']"
    )
    
    exec(viz_code, globals(), local_vars)
    visualization = local_vars['visualization']
    
    assert visualization is not None
    assert isinstance(visualization, str)
    assert len(visualization) > 100  # Should be JSON
    
    print(f"✓ Full pipeline executed successfully")
    print(f"  Simulation: {len(result['distribution'])} iterations")
    print(f"  Visualization: {len(visualization)} characters of Plotly JSON")
    print(f"  Expected impact: {result['interpretation']}")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 1: PREDICTIVE SIMULATION TEST SUITE")
    print("=" * 60)
    
    try:
        test_scenario_architect_creation()
        test_simulation_task_builder()
        test_simulation_code_generation()
        test_simulation_code_execution()
        test_simulation_visualization_code()
        test_full_simulation_with_visualization()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Phase 1 Simulation Ready!")
        print("=" * 60)
        
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
