# Phase 1: Predictive Simulation

## Overview

Phase 1 extends the Data Scientist agent capabilities with Monte Carlo simulation for predictive "what-if" scenario analysis. This enables business stakeholders to model the probable impact of hypothetical changes to key variables.

## Features

### 1. Scenario Architect Agent

**New Function**: `create_scenario_architect_agent(llm, business_glossary)`

A specialized agent that:
- Generates Monte Carlo simulations with configurable iterations
- Creates "shadow data" by applying hypothetical variable changes
- Outputs probability distributions (P10/Low, P50/Expected, P90/High)
- Integrates business glossary to identify price/demand sensitive variables
- Uses numpy for probabilistic distributions and pandas for data projection

**Agent Profile**:
- **Role**: Predictive Scenario Architect
- **Goal**: Generate Monte Carlo simulations to predict probable outcomes under different business conditions
- **Backstory**: Expert in stochastic modeling with deep understanding of business variable interactions

### 2. Simulation Task Builder

**New Method**: `DataScienceTaskBuilder.build_simulation_task()`

**Parameters**:
- `agent`: Scenario Architect agent instance
- `dataframe_name`: Variable name of base dataframe
- `hypothetical_variables`: List of dicts specifying changes
  ```python
  [
      {'column': 'price', 'change_pct': 10, 'change_type': 'increase'},
      {'column': 'shipping_days', 'change_pct': -20, 'change_type': 'decrease'}
  ]
  ```
- `target_column`: Column to predict (e.g., 'revenue', 'sales')
- `num_iterations`: Number of Monte Carlo iterations (default: 1000)
- `context`: Previous CrewAI tasks for context

**Task Outputs**:
- `baseline`: Original mean of target column
- `scenarios`: Dict with P10 (low), P50 (expected), P90 (high) values
- `distribution`: Full array of simulated outcomes
- `confidence_interval`: 95% CI [P2.5, P97.5]
- `sensitivity_analysis`: Identifies most impactful variable
- `interpretation`: Business insights

### 3. Simulation Code Generation

**Enhanced Function**: `generate_analysis_code(analysis_type="simulation", ...)`

Generates executable Python code that:
1. Calculates baseline target column mean
2. Runs Monte Carlo loop with configurable iterations
3. Applies normal distribution sampling per hypothetical variable
   - Mean: `change_pct / 100`
   - Std: `abs(change_pct) / 300`
4. Creates shadow dataframes with modified values
5. Computes simulated target for each iteration
6. Aggregates percentiles (P10, P50, P90, P2.5, P97.5)
7. Performs sensitivity analysis

**Example Usage**:
```python
code = generate_analysis_code(
    analysis_type="simulation",
    dataframe_name="df",
    target_column="revenue",
    hypothetical_variables=[
        {'column': 'price', 'change_pct': 15, 'change_type': 'increase'},
        {'column': 'discount', 'change_pct': -10, 'change_type': 'decrease'}
    ],
    num_iterations=1000
)

# Execute code
local_vars = {'df': sales_data}
exec(code, globals(), local_vars)
result = local_vars['result']

print(f"Baseline: {result['baseline']}")
print(f"Expected: {result['scenarios']['expected']}")
print(f"95% CI: {result['confidence_interval']}")
```

### 4. Simulation Visualizations

**New Chart Types** in `generate_plotly_visualization_code()`:

#### A. Distribution Histogram (`chart_type="simulation_distribution"`)

Shows full Monte Carlo distribution with:
- Histogram of all simulated outcomes
- Vertical lines marking Baseline (red dash), P10 (orange dot), P50 (green solid), P90 (purple dot)
- Interactive hover details

**Parameters**:
- `distribution_var`: Variable containing full simulation array
- `baseline_var`: Original baseline value
- `scenarios_var`: Dict with low/expected/high

#### B. Scenario Comparison (`chart_type="scenario_comparison"`)

Bar chart comparing:
- Baseline (gray)
- Low/P10 (orange)
- Expected/P50 (green)
- High/P90 (purple)

All charts include value labels and are Plotly JSON compatible for frontend rendering.

## Integration with Business Glossary

The Scenario Architect agent automatically extracts sensitive variables from the business glossary:

```python
business_glossary = {
    'business_terms': {
        'price': {'sensitivity': 'high-revenue'},
        'shipping_days': {'sensitivity': 'demand'},
        'discount_rate': {'sensitivity': 'revenue'}
    },
    'column_aliases': {
        'price': ['unit_price', 'product_price'],
        'revenue': ['total_revenue', 'sales']
    }
}

agent = create_scenario_architect_agent(llm, business_glossary)
```

The agent's backstory will include context about which variables impact revenue/churn/KPIs, enabling smarter simulation recommendations.

## Workflow Example

### Use Case: Revenue Impact of Price Increase

**Scenario**: E-commerce team wants to understand the impact of a 10% price increase with a simultaneous 5% reduction in marketing spend.

```python
from src.agents.scientist import (
    create_scenario_architect_agent,
    DataScienceTaskBuilder,
    generate_analysis_code,
    generate_plotly_visualization_code
)
from langchain_groq import ChatGroq

# 1. Create agent
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
agent = create_scenario_architect_agent(llm, business_glossary)

# 2. Build simulation task
task = DataScienceTaskBuilder.build_simulation_task(
    agent=agent,
    dataframe_name="sales_df",
    hypothetical_variables=[
        {'column': 'price', 'change_pct': 10, 'change_type': 'increase'},
        {'column': 'marketing_spend', 'change_pct': -5, 'change_type': 'decrease'}
    ],
    target_column="monthly_revenue",
    num_iterations=5000
)

# 3. Generate and execute simulation code
sim_code = generate_analysis_code(
    analysis_type="simulation",
    dataframe_name="sales_df",
    target_column="monthly_revenue",
    hypothetical_variables=[...],
    num_iterations=5000
)

local_vars = {'sales_df': df}
exec(sim_code, globals(), local_vars)
result = local_vars['result']

# 4. Generate visualization
viz_code = generate_plotly_visualization_code(
    chart_type="simulation_distribution",
    x_col="",
    y_col="",
    title="Revenue Impact: +10% Price, -5% Marketing",
    distribution_var="result['distribution']",
    baseline_var="result['baseline']",
    scenarios_var="result['scenarios']"
)

exec(viz_code, globals(), local_vars)
viz_json = local_vars['visualization']

# 5. Interpret results
print(f"Baseline Revenue: ${result['baseline']:,.0f}")
print(f"Expected Revenue: ${result['scenarios']['expected']:,.0f}")
print(f"Low (P10): ${result['scenarios']['low']:,.0f}")
print(f"High (P90): ${result['scenarios']['high']:,.0f}")
print(f"95% Confidence: ${result['confidence_interval'][0]:,.0f} - ${result['confidence_interval'][1]:,.0f}")
print(result['interpretation'])
print(result['sensitivity_analysis'])
```

**Output**:
```
Baseline Revenue: $1,245,000
Expected Revenue: $1,370,000
Low (P10): $1,320,000
High (P90): $1,425,000
95% Confidence: $1,305,000 - $1,445,000
Expected outcome: 1370000.00 (baseline: 1245000.00, change: 10.0%)
Most sensitive variable: price
```

## Testing

Run the comprehensive test suite:

```bash
python tests/test_simulation.py
```

**Test Coverage**:
1. ✓ Scenario Architect agent creation with business glossary
2. ✓ Simulation task builder with hypothetical variables
3. ✓ Code generation for Monte Carlo simulation
4. ✓ Execution of generated code with real data
5. ✓ Visualization code generation (histogram & comparison)
6. ✓ Full end-to-end simulation + visualization pipeline

## API Integration

The simulation functionality can be integrated into the FastAPI backend:

```python
# In src/api/main_crewai.py

from src.agents.scientist import (
    create_scenario_architect_agent,
    DataScienceTaskBuilder
)

@app.post("/simulate")
async def run_simulation(request: SimulationRequest):
    """
    Run Monte Carlo simulation for what-if scenarios.
    
    Body:
    {
        "query": "What if we increase price by 10% and reduce shipping time by 2 days?",
        "hypothetical_variables": [
            {"column": "price", "change_pct": 10, "change_type": "increase"},
            {"column": "shipping_days", "change_pct": -28.5, "change_type": "decrease"}
        ],
        "target_column": "revenue",
        "num_iterations": 1000
    }
    """
    # Implementation...
    pass
```

## Limitations & Future Enhancements

### Current Limitations
1. **Linear Relationships**: Simulation assumes linear impact of variable changes on target
2. **Independent Variables**: Does not model variable interdependencies
3. **Normal Distribution**: Uses normal distribution for all variable changes
4. **Static Business Logic**: Target calculation uses simplified mean aggregation

### Phase 2 Enhancements (Planned)
- [ ] Non-linear relationship modeling (polynomial, exponential)
- [ ] Variable correlation matrices for dependent variable simulation
- [ ] Custom distribution types (uniform, beta, gamma)
- [ ] Time-series aware simulations with seasonal effects
- [ ] Multi-target simulations (revenue, churn, LTV simultaneously)
- [ ] Confidence interval visualization bands
- [ ] Automated optimal scenario finder

## Best Practices

1. **Choose Realistic Change Percentages**: Use domain knowledge to constrain changes
   ```python
   # Good: Realistic price change
   {'column': 'price', 'change_pct': 15, 'change_type': 'increase'}
   
   # Bad: Unrealistic change
   {'column': 'price', 'change_pct': 500, 'change_type': 'increase'}
   ```

2. **Balance Iterations vs Performance**: 
   - Prototyping: 100-500 iterations
   - Production: 1000-5000 iterations
   - High-stakes decisions: 10000+ iterations

3. **Validate Baseline**: Always compare simulated baseline to actual data

4. **Interpret Sensitivity Analysis**: Focus on high-impact variables

5. **Use Business Glossary**: Ensure agent understands domain-specific variable relationships

## Changelog

### v2.1.0 (2025-01-XX)
- ✨ Added `create_scenario_architect_agent()` for predictive simulations
- ✨ Added `build_simulation_task()` to DataScienceTaskBuilder
- ✨ Enhanced `generate_analysis_code()` with "simulation" analysis type
- ✨ Added `simulation_distribution` and `scenario_comparison` chart types
- 🧪 Added comprehensive test suite: `tests/test_simulation.py`
- 📚 Added Phase 1 documentation

---

**Developed by**: Dev Team Lead  
**Phase**: 1 - Predictive Simulation  
**Status**: ✅ Production Ready
