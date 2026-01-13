# Phase 3: Python Analytics Sandbox - Implementation Guide

## Overview

Phase 3 extends Autonomous Multi-Agent Business Intelligence System with advanced analytics capabilities through a secure Python execution sandbox. The system now performs secondary analysis on SQL query results including forecasting, correlation analysis, anomaly detection, and statistical summaries.

## Architecture

```
User Query: "Show revenue by product and predict next month"
    ↓
[Manager] Detects analytics intent → "forecast"
    ↓
Phase 1+2: Generate & validate SQL
    ↓
[SQL Executor] Execute query → DataFrame/CSV
    ↓
[Data Scientist Agent] Perform time series forecast
    ↓
[Code Interpreter Tool] Execute Python code in Docker sandbox
    ↓
[Visualization Agent] Generate Plotly JSON
    ↓
Return: {sql, data, forecast, visualization}
```

## Components

### 1. Secure Code Interpreter (`src/tools/code_interpreter.py`)

**Purpose**: Execute Python analytics code in a secure, isolated environment.

**Security Layers**:
- **Docker Mode (Preferred)**:
  - Isolated container with no network access
  - Memory limit: 512MB (configurable)
  - CPU constraints enforced
  - Timeout: 30 seconds
  - Clean teardown after execution

- **RestrictedPython Mode (Fallback)**:
  - Blocks `os`, `sys`, `subprocess`, `eval`, `exec`
  - Guarded imports and iteration
  - Safe globals only

**Pre-installed Packages**:
- pandas, numpy, scipy
- matplotlib, seaborn, plotly
- statsmodels, scikit-learn

**Usage**:
```python
from src.tools.code_interpreter import CodeInterpreterTool

interpreter = CodeInterpreterTool(
    mode="auto",  # Docker preferred, RestrictedPython fallback
    timeout=30,
    memory_limit="512m"
)

result = interpreter.run(
    code="""
import pandas as pd
import numpy as np

df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
result = {'mean_y': df['y'].mean()}
""",
    context={'data': dataframe}  # Inject DataFrames as CSV files
)

print(result)
# {
#     "success": True,
#     "result": {"mean_y": 5.0},
#     "output": "",
#     "error": None,
#     "visualization": None
# }
```

### 2. Data Scientist Agent (`src/agents/scientist.py`)

**Purpose**: Perform advanced analytics on SQL query results.

**Capabilities**:
- **Correlation Analysis**: Identify factors correlated with target variable
- **Time Series Forecasting**: Predict future values (ARIMA, moving average, linear)
- **Statistical Summary**: Descriptive stats, outliers, normality tests
- **Anomaly Detection**: Z-score, IQR, isolation forest methods
- **Trend Analysis**: Detect patterns over time

**Context-Aware**:
- Uses Business Glossary to interpret columns correctly
- Knows "revenue" vs "sales" vs "amount" based on glossary
- Understands business terms like "churned_user", "active_user"

**Agent Creation**:
```python
from src.agents.scientist import create_data_scientist_agent

scientist = create_data_scientist_agent(
    llm=ChatGroq(model="llama-3.3-70b-versatile"),
    business_glossary=glossary_data
)
```

### 3. Visualization Agent (`src/agents/scientist.py`)

**Purpose**: Generate interactive Plotly visualizations.

**Chart Types**:
- **Line Charts**: Time series, trends, forecasts
- **Scatter Plots**: Correlations, anomalies
- **Bar Charts**: Categorical comparisons, summaries
- **Heatmaps**: Correlation matrices

**Output**: Valid Plotly JSON for frontend rendering

**Usage**:
```python
from src.agents.scientist import create_visualization_agent

viz_agent = create_visualization_agent(
    llm=ChatGroq(model="llama-3.3-70b-versatile")
)
```

### 4. Analytics Workflow (`src/agents/crewai_manager.py`)

**New Method**: `generate_with_analytics(query, database)`

**Workflow Steps**:

1. **Intent Detection**: Analyze query for analytics keywords
   - "forecast", "predict" → Forecasting
   - "correlation", "relationship" → Correlation analysis
   - "anomaly", "outlier" → Anomaly detection
   - "summary", "statistics" → Statistical summary

2. **SQL Generation**: Use Phase 1+2 self-healing loop

3. **SQL Execution**: Safe execution with row limits

4. **Parameter Extraction**: Extract analysis parameters from query
   - "next month" → 30-day forecast
   - "next quarter" → 90-day forecast
   - "next year" → 365-day forecast

5. **Code Generation**: Generate analysis code based on intent

6. **Sandbox Execution**: Run code in Docker/RestrictedPython

7. **Visualization**: Generate Plotly JSON if analysis succeeded

8. **Response Assembly**: Return complete result with analytics

## Analytics Types

### Correlation Analysis

**Query Examples**:
- "What factors correlate with churn rate?"
- "Show relationship between price and sales"
- "Impact of marketing spend on revenue"

**Output**:
```json
{
    "correlations": {
        "price": -0.65,
        "quality_score": 0.82,
        "customer_satisfaction": 0.71
    },
    "top_factors": ["quality_score", "customer_satisfaction", "price"],
    "interpretation": "Top correlated factors: quality_score, customer_satisfaction, price",
    "methodology": "Pearson correlation coefficient"
}
```

### Time Series Forecasting

**Query Examples**:
- "Forecast revenue for next month"
- "Predict user signups next quarter"
- "Project sales for next year"

**Output**:
```json
{
    "forecast": [15000, 15200, 15100, ...],
    "forecast_dates": ["2026-02-01", "2026-02-02", ...],
    "model_used": "7-period moving average",
    "interpretation": "Forecast average: 15100.00"
}
```

### Anomaly Detection

**Query Examples**:
- "Find anomalies in daily revenue"
- "Detect unusual spikes in user activity"
- "Identify outliers in transaction amounts"

**Output**:
```json
{
    "anomalies": [45, 67, 123],
    "anomaly_values": [98765, 87654, 99999],
    "threshold_used": 3,
    "interpretation": "Found 3 anomalies beyond 3 standard deviations"
}
```

### Statistical Summary

**Query Examples**:
- "Statistical summary of revenue by region"
- "Distribution of customer ages"
- "Summary statistics for all products"

**Output**:
```json
{
    "summary_stats": {
        "count": 1000,
        "mean": 5432.10,
        "std": 1234.56,
        "min": 100,
        "25%": 3456,
        "50%": 5000,
        "75%": 7890,
        "max": 15000
    },
    "outliers": {"revenue": [45, 67, 123]},
    "missing_data": {"revenue": 2.5, "region": 0.0},
    "key_insights": "Analyzed 5 numeric columns"
}
```

## Installation

### Prerequisites

**Required**:
```bash
pip install pandas numpy scipy statsmodels plotly matplotlib seaborn scikit-learn
```

**For Docker Mode (Recommended)**:
```bash
# Install Docker Desktop (Windows/Mac) or Docker Engine (Linux)
# https://docs.docker.com/get-docker/

pip install docker

# Verify Docker is running
docker ps
```

**For RestrictedPython Fallback**:
```bash
pip install RestrictedPython
```

### Full Installation

```bash
# Install all Phase 3 dependencies
pip install -r requirements.txt

# Pull Python Docker image (for sandbox)
docker pull python:3.11-slim
```

## Usage Examples

### Example 1: Revenue Forecast

```python
from src.agents.crewai_manager import DataOpsManager

manager = DataOpsManager()

result = manager.generate_with_analytics(
    query="Show monthly revenue for last year and forecast next 3 months",
    database="sqlite:///data/sample/sample.db"
)

print(f"SQL: {result['sql']}")
print(f"Analytics Type: {result['analytics_type']}")
print(f"Forecast: {result['analysis_result']['forecast']}")
print(f"Visualization: {result['visualization']}")  # Plotly JSON
```

### Example 2: Correlation Analysis

```python
result = manager.generate_with_analytics(
    query="What factors correlate with customer churn?",
    database="sqlite:///data/sample/sample.db"
)

print(f"Top Factors: {result['analysis_result']['top_factors']}")
print(f"Correlations: {result['analysis_result']['correlations']}")
```

### Example 3: Anomaly Detection

```python
result = manager.generate_with_analytics(
    query="Find anomalies in daily transaction amounts",
    database="sqlite:///data/sample/sample.db"
)

print(f"Anomalies Found: {len(result['analysis_result']['anomalies'])}")
print(f"Anomalous Values: {result['analysis_result']['anomaly_values']}")
```

## FastAPI Integration

Add analytics endpoint to `src/api/main_crewai.py`:

```python
@app.post("/query/analytics")
async def query_with_analytics(request: QueryRequest):
    """
    Process natural language query with analytics.
    
    Automatically detects analytics intent and performs:
    - SQL generation & validation
    - SQL execution
    - Statistical analysis
    - Visualization generation
    """
    try:
        result = dataops_manager.generate_with_analytics(
            query=request.query,
            database=request.database or "sqlite:///data/sample/sample.db"
        )
        
        return {
            "sql": result.get('sql'),
            "confidence": result.get('confidence'),
            "data": result.get('data'),
            "analytics_performed": result.get('analytics_performed'),
            "analytics_type": result.get('analytics_type'),
            "analysis_result": result.get('analysis_result'),
            "visualization": result.get('visualization'),  # Plotly JSON
            "method": result.get('method')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Security Considerations

### Docker Mode Security

✅ **Enforced**:
- Network disabled (`network_disabled=True`)
- Memory limit (512MB default)
- CPU constraints
- No volume mounts with sensitive data
- Timeout enforcement (30s)
- Container auto-removal

❌ **Blocked**:
- Network requests
- File system writes (outside /workspace)
- Subprocess spawning
- Privilege escalation

### RestrictedPython Mode Security

✅ **Allowed**:
- pandas, numpy, scipy operations
- matplotlib, plotly visualization
- Pure computation

❌ **Blocked**:
- `import os`, `import sys`, `import subprocess`
- `eval()`, `exec()`, `compile()`
- `__import__()` for arbitrary modules
- File system access
- Network operations

### Best Practices

1. **Always use Docker mode in production** for maximum isolation
2. **Set conservative timeouts** (30s default) to prevent runaway processes
3. **Limit memory** (512MB default) to prevent resource exhaustion
4. **Monitor execution logs** for suspicious patterns
5. **Validate analysis results** before displaying to users
6. **Use read-only database connections** for SQL execution

## Testing

### Test Code Interpreter

```python
from src.tools.code_interpreter import CodeInterpreterTool

interpreter = CodeInterpreterTool(mode="docker")

# Test basic execution
result = interpreter.run(
    code="""
import pandas as pd
df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
result = {'sum': df['y'].sum()}
"""
)
assert result['success'] == True
assert result['result']['sum'] == 15

# Test security (should fail)
result = interpreter.run(code="import os; result = os.listdir('/')")
assert result['success'] == False
```

### Test Analytics Workflow

```python
from src.agents.crewai_manager import DataOpsManager

manager = DataOpsManager()

# Test forecast detection
result = manager.generate_with_analytics(
    query="Forecast revenue for next month"
)
assert result['analytics_performed'] == True
assert result['analytics_type'] == 'forecast'

# Test correlation detection
result = manager.generate_with_analytics(
    query="What correlates with churn?"
)
assert result['analytics_type'] == 'correlation'
```

## Performance

### Docker Mode

- **Startup**: ~2-3 seconds (container spin-up)
- **Execution**: 1-5 seconds (depends on analysis complexity)
- **Memory**: 100-500MB per execution
- **Concurrent**: 5-10 executions (depends on host resources)

### RestrictedPython Mode

- **Startup**: Instant (no container)
- **Execution**: 0.5-3 seconds
- **Memory**: 50-200MB
- **Concurrent**: 20-50 executions

### Optimization Tips

1. **Pre-pull Docker image**: `docker pull python:3.11-slim`
2. **Use connection pooling** for database
3. **Cache analysis results** for identical queries
4. **Limit result set size** (max 1000 rows recommended)
5. **Use async execution** for multiple analytics requests

## Troubleshooting

### Docker Not Available

**Error**: `RuntimeError: Docker mode selected but docker package not installed`

**Solution**:
```bash
pip install docker
# OR force RestrictedPython mode
interpreter = CodeInterpreterTool(mode="restricted")
```

### Container Timeout

**Error**: `Docker execution error: timeout`

**Solution**:
```python
# Increase timeout
interpreter = CodeInterpreterTool(timeout=60)
```

### Memory Limit Exceeded

**Error**: `Container killed: OOM`

**Solution**:
```python
# Increase memory limit
interpreter = CodeInterpreterTool(memory_limit="1g")
```

### Analysis Code Fails

**Error**: Analysis execution returns `success=False`

**Solution**:
- Check `result['error']` for details
- Verify data format matches expected structure
- Ensure required columns exist in DataFrame
- Check for null/missing values

## Roadmap

### Future Enhancements

- [ ] Support for more ML models (XGBoost, Prophet)
- [ ] Interactive chart customization via API
- [ ] Multi-table join analytics
- [ ] Automated insight generation
- [ ] Scheduled analytics jobs
- [ ] Analytics result caching
- [ ] Custom Python environment per user
- [ ] GPU-accelerated computations

## Summary

Phase 3 completes the Autonomous Multi-Agent Business Intelligence System architecture with:

✅ **Secure Python sandbox** (Docker + RestrictedPython)
✅ **Data Scientist Agent** for advanced analytics
✅ **Visualization Agent** for Plotly charts
✅ **Analytics workflow** integrated with CrewAI Manager
✅ **Business Glossary awareness** for column interpretation
✅ **Multiple analysis types**: forecast, correlation, anomaly, summary
✅ **Production-ready security** with isolation and resource limits

The system now provides end-to-end analytics from natural language query to interactive visualization.
