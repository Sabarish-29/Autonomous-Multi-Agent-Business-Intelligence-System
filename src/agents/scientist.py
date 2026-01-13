"""
Data Scientist Agent for Autonomous Multi-Agent Business Intelligence System Phase 3.

Performs secondary analytics on SQL query results including:
- Correlation analysis
- Time series forecasting
- Statistical tests
- Anomaly detection
- Trend analysis

Uses Business Glossary for column interpretation and generates Plotly visualizations.
"""

from typing import Dict, Any, Optional, List
from crewai import Agent, Task
from langchain_groq import ChatGroq
import logging

logger = logging.getLogger(__name__)


def create_data_scientist_agent(llm: ChatGroq, business_glossary: Optional[Dict] = None) -> Agent:
    """
    Create Data Scientist Agent for advanced analytics.
    
    Args:
        llm: Language model for the agent
        business_glossary: Business glossary for column interpretation
    
    Returns:
        CrewAI Agent configured for data science tasks
    """
    glossary_context = ""
    if business_glossary:
        glossary_context = f"""
Business Context:
- Business Terms: {', '.join(business_glossary.get('business_terms', {}).keys())}
- Column Aliases: {business_glossary.get('column_aliases', {})}
- Use this glossary to understand which columns represent revenue, users, churn, etc.
"""
    
    return Agent(
        role="Senior Data Scientist",
        goal=(
            "Perform advanced statistical analysis, forecasting, and machine learning "
            "on SQL query results to extract actionable insights. Generate clear, "
            "interpretable visualizations using Plotly."
        ),
        backstory=(
            "You are an expert data scientist with 10+ years of experience in "
            "statistical analysis, time series forecasting, and machine learning. "
            "You excel at translating complex analytical results into clear insights "
            "for business stakeholders. You always validate assumptions and explain "
            "your methodology.\n\n"
            f"{glossary_context}"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


def create_visualization_agent(llm: ChatGroq) -> Agent:
    """
    Create Visualization Agent for generating Plotly charts.
    
    Args:
        llm: Language model for the agent
    
    Returns:
        CrewAI Agent configured for visualization tasks
    """
    return Agent(
        role="Data Visualization Specialist",
        goal=(
            "Create beautiful, interactive Plotly visualizations that clearly "
            "communicate analytical insights. Generate valid Plotly JSON that "
            "can be rendered in a web frontend."
        ),
        backstory=(
            "You are a visualization expert who understands both the technical "
            "aspects of Plotly.js and the principles of effective data communication. "
            "You choose the right chart type for each analysis (line charts for trends, "
            "scatter plots for correlations, heatmaps for matrices, etc.) and ensure "
            "all visualizations are accessible and interpretable."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=2
    )


def create_scenario_architect_agent(llm: ChatGroq, business_glossary: Optional[Dict] = None) -> Agent:
    """
    Create Scenario Architect Agent for predictive simulations and what-if analysis.
    
    Args:
        llm: Language model for the agent
        business_glossary: Business glossary for identifying sensitive variables
    
    Returns:
        CrewAI Agent configured for Monte Carlo simulation and scenario planning
    """
    glossary_context = ""
    sensitive_variables = []
    
    if business_glossary:
        # Extract price/demand sensitive columns from business terms
        business_terms = business_glossary.get('business_terms', {})
        for term, metadata in business_terms.items():
            if isinstance(metadata, dict):
                sensitivity = metadata.get('sensitivity', '').lower()
                if 'price' in sensitivity or 'demand' in sensitivity or 'revenue' in sensitivity:
                    sensitive_variables.append(term)
        
        glossary_context = f"""
Business Context for Simulation:
- Sensitive Variables: {', '.join(sensitive_variables) if sensitive_variables else 'price, demand, revenue'}
- Column Aliases: {business_glossary.get('column_aliases', {})}
- Use this glossary to identify which variables impact revenue, churn, or other KPIs
"""
    
    return Agent(
        role="Predictive Scenario Architect",
        goal=(
            "Generate Monte Carlo simulations and what-if scenarios to predict probable "
            "outcomes under different business conditions. Create synthetic 'shadow data' "
            "by applying hypothetical changes to key variables (e.g., price +10%, shipping -2 days) "
            "and output probability distributions showing Low, Expected, and High outcomes."
        ),
        backstory=(
            "You are a seasoned scenario planning expert with expertise in stochastic modeling "
            "and Monte Carlo simulations. You understand how business variables interact and "
            "can quantify uncertainty in forecasts. You use numpy for probabilistic distributions "
            "and pandas for data manipulation, always validating assumptions and explaining "
            "confidence intervals to stakeholders.\n\n"
            f"{glossary_context}"
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


class DataScienceTaskBuilder:
    """
    Builder for creating CrewAI tasks for various data science operations.
    """
    
    @staticmethod
    def build_correlation_task(
        agent: Agent,
        dataframe_name: str,
        target_column: str,
        context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create task for correlation analysis.
        
        Args:
            agent: Data Scientist agent
            dataframe_name: Variable name of the dataframe in context
            target_column: Target column for correlation analysis
            context: Previous tasks to use as context
        
        Returns:
            CrewAI Task for correlation analysis
        """
        return Task(
            description=(
                f"Analyze the dataset '{dataframe_name}' and compute correlations "
                f"with the target column '{target_column}'.\n\n"
                "Steps:\n"
                "1. Load the dataframe from context\n"
                "2. Identify numeric columns\n"
                "3. Compute Pearson correlation coefficients\n"
                "4. Rank correlations by absolute value\n"
                "5. Interpret the top 5 strongest correlations\n"
                "6. Store results in 'result' variable\n\n"
                "Store correlation matrix in 'result' and interpretation in 'analysis'."
            ),
            expected_output=(
                "A Python dictionary with:\n"
                "- 'correlations': Dict of {column: correlation_value}\n"
                "- 'interpretation': String explaining the findings\n"
                "- 'top_factors': List of top 5 correlated features\n"
                "- 'methodology': Description of analysis approach"
            ),
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def build_forecasting_task(
        agent: Agent,
        dataframe_name: str,
        time_column: str,
        target_column: str,
        periods: int = 7,
        context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create task for time series forecasting.
        
        Args:
            agent: Data Scientist agent
            dataframe_name: Variable name of the dataframe
            time_column: Column containing timestamps
            target_column: Column to forecast
            periods: Number of periods to forecast
            context: Previous tasks
        
        Returns:
            CrewAI Task for forecasting
        """
        return Task(
            description=(
                f"Perform time series forecasting on '{dataframe_name}'.\n\n"
                f"Time column: {time_column}\n"
                f"Target column: {target_column}\n"
                f"Forecast horizon: {periods} periods\n\n"
                "Steps:\n"
                "1. Prepare time series data (sort by time, handle missing values)\n"
                "2. Detect seasonality and trend\n"
                "3. Choose appropriate model (ARIMA, exponential smoothing, or linear)\n"
                "4. Fit model and generate forecasts\n"
                "5. Calculate confidence intervals if possible\n"
                "6. Store forecast in 'result' variable\n\n"
                "If advanced models unavailable, use simple moving average or linear regression."
            ),
            expected_output=(
                "A Python dictionary with:\n"
                "- 'forecast': List of predicted values\n"
                "- 'forecast_dates': List of corresponding dates/periods\n"
                "- 'confidence_intervals': Dict with 'lower' and 'upper' bounds\n"
                "- 'model_used': Name of the model\n"
                "- 'interpretation': Business insights from the forecast"
            ),
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def build_statistical_summary_task(
        agent: Agent,
        dataframe_name: str,
        columns: Optional[List[str]] = None,
        context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create task for comprehensive statistical summary.
        
        Args:
            agent: Data Scientist agent
            dataframe_name: Variable name of the dataframe
            columns: Specific columns to analyze (None = all)
            context: Previous tasks
        
        Returns:
            CrewAI Task for statistical analysis
        """
        columns_spec = f"columns: {columns}" if columns else "all numeric columns"
        
        return Task(
            description=(
                f"Generate comprehensive statistical summary for '{dataframe_name}' ({columns_spec}).\n\n"
                "Steps:\n"
                "1. Compute descriptive statistics (mean, median, std, quartiles)\n"
                "2. Identify outliers using IQR method\n"
                "3. Check for normality (if sample size > 30)\n"
                "4. Detect missing values and patterns\n"
                "5. Calculate coefficient of variation for variability assessment\n"
                "6. Store results in 'result' variable"
            ),
            expected_output=(
                "A Python dictionary with:\n"
                "- 'summary_stats': DataFrame.describe() output as dict\n"
                "- 'outliers': Dict of {column: list of outlier indices}\n"
                "- 'missing_data': Dict of {column: percentage_missing}\n"
                "- 'distributions': Dict describing normality for each column\n"
                "- 'key_insights': String with main findings"
            ),
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def build_anomaly_detection_task(
        agent: Agent,
        dataframe_name: str,
        target_column: str,
        method: str = "zscore",
        context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create task for anomaly detection.
        
        Args:
            agent: Data Scientist agent
            dataframe_name: Variable name of the dataframe
            target_column: Column to check for anomalies
            method: Detection method ("zscore", "iqr", or "isolation_forest")
            context: Previous tasks
        
        Returns:
            CrewAI Task for anomaly detection
        """
        return Task(
            description=(
                f"Detect anomalies in column '{target_column}' of '{dataframe_name}' "
                f"using {method} method.\n\n"
                "Steps:\n"
                f"1. Apply {method} anomaly detection\n"
                "2. Identify anomalous data points\n"
                "3. Calculate anomaly scores\n"
                "4. Summarize patterns in anomalies (time-based, value ranges)\n"
                "5. Store results in 'result' variable"
            ),
            expected_output=(
                "A Python dictionary with:\n"
                "- 'anomalies': List of indices or timestamps of anomalies\n"
                "- 'anomaly_values': Corresponding anomalous values\n"
                "- 'anomaly_scores': Severity scores\n"
                "- 'threshold_used': Detection threshold\n"
                "- 'interpretation': Explanation of findings"
            ),
            agent=agent,
            context=context or []
        )
    
    @staticmethod
    def build_visualization_task(
        agent: Agent,
        chart_type: str,
        data_description: str,
        analysis_context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create task for generating Plotly visualization.
        
        Args:
            agent: Visualization agent
            chart_type: Type of chart (line, scatter, bar, heatmap, etc.)
            data_description: Description of data to visualize
            analysis_context: Previous analysis tasks
        
        Returns:
            CrewAI Task for visualization generation
        """
        return Task(
            description=(
                f"Generate an interactive {chart_type} chart using Plotly.\n\n"
                f"Data to visualize: {data_description}\n\n"
                "Requirements:\n"
                "1. Use plotly.graph_objects or plotly.express\n"
                "2. Create a figure with appropriate chart type\n"
                "3. Add clear axis labels and title\n"
                "4. Enable hover data for interactivity\n"
                "5. Use professional color scheme\n"
                "6. Store figure in 'fig' variable\n"
                "7. Store fig.to_json() in 'visualization' variable\n\n"
                "The JSON must be valid Plotly format for frontend rendering."
            ),
            expected_output=(
                "A Python dictionary with:\n"
                "- 'visualization': Plotly figure as JSON string (fig.to_json())\n"
                "- 'chart_type': Type of chart created\n"
                "- 'description': Brief description of what the chart shows"
            ),
            agent=agent,
            context=analysis_context or []
        )
    
    @staticmethod
    def build_simulation_task(
        agent: Agent,
        dataframe_name: str,
        hypothetical_variables: List[Dict[str, Any]],
        target_column: str,
        num_iterations: int = 1000,
        context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create task for Monte Carlo simulation with hypothetical scenarios.
        
        Args:
            agent: Scenario Architect agent
            dataframe_name: Variable name of the base dataframe
            hypothetical_variables: List of dicts with 'column', 'change_pct', 'change_type'
                Example: [{'column': 'price', 'change_pct': 10, 'change_type': 'increase'},
                         {'column': 'shipping_days', 'change_pct': -20, 'change_type': 'decrease'}]
            target_column: Target column to predict (e.g., 'revenue', 'sales')
            num_iterations: Number of Monte Carlo iterations
            context: Previous tasks
        
        Returns:
            CrewAI Task for Monte Carlo simulation
        """
        variables_desc = ", ".join([
            f"{v['column']} {v['change_type']} by {abs(v['change_pct'])}%"
            for v in hypothetical_variables
        ])
        
        return Task(
            description=(
                f"Run Monte Carlo simulation on '{dataframe_name}' to predict impact on '{target_column}'.\n\n"
                f"Hypothetical Changes: {variables_desc}\n"
                f"Iterations: {num_iterations}\n\n"
                "Steps:\n"
                "1. Load base dataframe and calculate baseline target mean\n"
                "2. For each hypothetical variable, generate normal distribution around the change percentage\n"
                "   - Use numpy.random.normal(mean=change_pct, std=change_pct/3, size=num_iterations)\n"
                "3. Create shadow dataframes for each iteration with modified values\n"
                "4. Calculate target column for each iteration (apply business logic)\n"
                "5. Aggregate results into percentiles: P10 (Low), P50 (Expected), P90 (High)\n"
                "6. Store simulation results in 'result' variable\n\n"
                "Use pandas for data manipulation and numpy for probabilistic sampling."
            ),
            expected_output=(
                "A Python dictionary with:\n"
                "- 'baseline': Original mean of target column\n"
                "- 'scenarios': Dict with keys 'low' (P10), 'expected' (P50), 'high' (P90)\n"
                "- 'distribution': Full array of simulated outcomes (for histogram)\n"
                "- 'hypothetical_variables': Echo of input variables\n"
                "- 'confidence_interval': 95% confidence interval [P2.5, P97.5]\n"
                "- 'interpretation': Business insights about probable outcomes\n"
                "- 'sensitivity_analysis': Which variable had the biggest impact"
            ),
            agent=agent,
            context=context or []
        )


def generate_analysis_code(
    analysis_type: str,
    dataframe_name: str = "df",
    **kwargs
) -> str:
    """
    Generate Python code template for various analysis types.
    
    Args:
        analysis_type: Type of analysis (correlation, forecast, summary, anomaly)
        dataframe_name: Variable name of the dataframe
        **kwargs: Additional parameters specific to analysis type
    
    Returns:
        Python code as string
    """
    if analysis_type == "correlation":
        target = kwargs.get("target_column", "target")
        return f"""
import pandas as pd
import numpy as np

# Compute correlations with {target}
numeric_cols = {dataframe_name}.select_dtypes(include=[np.number]).columns
correlations = {{}}

if '{target}' in {dataframe_name}.columns:
    for col in numeric_cols:
        if col != '{target}':
            corr = {dataframe_name}[col].corr({dataframe_name}['{target}'])
            correlations[col] = corr

# Sort by absolute value
sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
top_factors = [item[0] for item in sorted_corr[:5]]

result = {{
    'correlations': correlations,
    'top_factors': top_factors,
    'interpretation': f"Top correlated factors: {{', '.join(top_factors[:3])}}",
    'methodology': 'Pearson correlation coefficient'
}}
"""
    
    elif analysis_type == "forecast":
        time_col = kwargs.get("time_column", "date")
        target_col = kwargs.get("target_column", "value")
        periods = kwargs.get("periods", 7)
        return f"""
import pandas as pd
import numpy as np
from datetime import timedelta

# Prepare time series
{dataframe_name}['{time_col}'] = pd.to_datetime({dataframe_name}['{time_col}'])
{dataframe_name} = {dataframe_name}.sort_values('{time_col}')

# Simple moving average forecast
window = min(7, len({dataframe_name}) // 2)
ma = {dataframe_name}['{target_col}'].rolling(window=window).mean()
last_value = ma.iloc[-1]

# Generate forecast
forecast = [last_value] * {periods}
last_date = {dataframe_name}['{time_col}'].iloc[-1]
forecast_dates = [last_date + timedelta(days=i+1) for i in range({periods})]

result = {{
    'forecast': forecast,
    'forecast_dates': [str(d) for d in forecast_dates],
    'model_used': f'{{window}}-period moving average',
    'interpretation': f'Forecast average: {{last_value:.2f}}'
}}
"""
    
    elif analysis_type == "summary":
        return f"""
import pandas as pd
import numpy as np

# Comprehensive statistical summary
summary_stats = {dataframe_name}.describe().to_dict()
missing_data = {{{dataframe_name}.isnull().sum() / len({dataframe_name}) * 100}}

# Detect outliers using IQR
numeric_cols = {dataframe_name}.select_dtypes(include=[np.number]).columns
outliers = {{}}

for col in numeric_cols:
    Q1 = {dataframe_name}[col].quantile(0.25)
    Q3 = {dataframe_name}[col].quantile(0.75)
    IQR = Q3 - Q1
    outlier_mask = ({dataframe_name}[col] < Q1 - 1.5*IQR) | ({dataframe_name}[col] > Q3 + 1.5*IQR)
    outliers[col] = {dataframe_name}[outlier_mask].index.tolist()

result = {{
    'summary_stats': summary_stats,
    'outliers': outliers,
    'missing_data': missing_data,
    'key_insights': f'Analyzed {{len(numeric_cols)}} numeric columns'
}}
"""
    
    elif analysis_type == "anomaly":
        target = kwargs.get("target_column", "value")
        return f"""
import pandas as pd
import numpy as np

# Z-score anomaly detection
mean = {dataframe_name}['{target}'].mean()
std = {dataframe_name}['{target}'].std()
threshold = 3

z_scores = ({dataframe_name}['{target}'] - mean) / std
anomalies = {dataframe_name}[abs(z_scores) > threshold].index.tolist()
anomaly_values = {dataframe_name}.loc[anomalies, '{target}'].tolist()

result = {{
    'anomalies': anomalies,
    'anomaly_values': anomaly_values,
    'threshold_used': threshold,
    'interpretation': f'Found {{len(anomalies)}} anomalies beyond {{threshold}} standard deviations'
}}
"""
    
    elif analysis_type == "simulation":
        target = kwargs.get("target_column", "revenue")
        hypothetical_vars = kwargs.get("hypothetical_variables", [])
        num_iterations = kwargs.get("num_iterations", 1000)
        
        # Generate code for applying hypothetical changes per iteration
        change_code_lines = []
        for var in hypothetical_vars:
            col = var['column']
            change_pct = var['change_pct']
            change_code_lines.append(f"    # Simulate {col} change: {change_pct}% variation")
            change_code_lines.append(f"    {col}_change = np.random.normal({change_pct}/100, abs({change_pct})/300)")
            change_code_lines.append(f"    shadow_df['{col}'] = {dataframe_name}['{col}'].mean() * (1 + {col}_change)")
        
        changes_block = "\n".join(change_code_lines) if change_code_lines else "    pass  # No hypothetical variables specified"
        
        # Build sensitivity dict code
        sensitivity_lines = []
        for var in hypothetical_vars:
            sensitivity_lines.append(f"sensitivity['{var['column']}'] = abs({var['change_pct']})")
        sensitivity_block = "\n".join(sensitivity_lines) if sensitivity_lines else "pass"
        
        code_template = f"""
import pandas as pd
import numpy as np

# Baseline calculation
baseline = {dataframe_name}['{target}'].mean()

# Monte Carlo simulation with {num_iterations} iterations
np.random.seed(42)  # For reproducibility
simulation_results = []

for i in range({num_iterations}):
    # Create shadow dataframe for this iteration
    shadow_df = {dataframe_name}.copy()
    
{changes_block}
    
    # Calculate target column based on modified variables
    # Assuming linear relationship (adjust business logic as needed)
    simulated_target = shadow_df.select_dtypes(include=[np.number]).mean().sum() * (baseline / {dataframe_name}.select_dtypes(include=[np.number]).mean().sum())
    simulation_results.append(simulated_target)

# Calculate percentiles
simulation_array = np.array(simulation_results)
low = np.percentile(simulation_array, 10)
expected = np.percentile(simulation_array, 50)
high = np.percentile(simulation_array, 90)
ci_low = np.percentile(simulation_array, 2.5)
ci_high = np.percentile(simulation_array, 97.5)

# Sensitivity analysis
sensitivity = {{}}
{sensitivity_block}
most_sensitive = max(sensitivity.items(), key=lambda x: x[1])[0] if sensitivity else 'N/A'

result = {{
    'baseline': float(baseline),
    'scenarios': {{
        'low': float(low),
        'expected': float(expected),
        'high': float(high)
    }},
    'distribution': simulation_array.tolist(),
    'hypothetical_variables': {hypothetical_vars},
    'confidence_interval': [float(ci_low), float(ci_high)],
    'interpretation': f'Expected outcome: {{{{expected:.2f}}}} (baseline: {{{{baseline:.2f}}}}, change: {{{{(expected-baseline)/baseline*100:.1f}}}}%)',
    'sensitivity_analysis': f'Most sensitive variable: {{{{most_sensitive}}}}'
}}
"""
        return code_template
    
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")


def generate_plotly_visualization_code(
    chart_type: str,
    x_col: str,
    y_col: str,
    dataframe_name: str = "df",
    title: str = "Data Visualization",
    **kwargs
) -> str:
    """
    Generate Python code for Plotly visualizations.
    
    Args:
        chart_type: Type of chart (line, scatter, bar, heatmap)
        x_col: X-axis column
        y_col: Y-axis column
        dataframe_name: Variable name of the dataframe
        title: Chart title
        **kwargs: Additional parameters
    
    Returns:
        Python code as string
    """
    if chart_type == "line":
        return f"""
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x={dataframe_name}['{x_col}'],
    y={dataframe_name}['{y_col}'],
    mode='lines+markers',
    name='{y_col}'
))

fig.update_layout(
    title='{title}',
    xaxis_title='{x_col}',
    yaxis_title='{y_col}',
    hovermode='x unified'
)

visualization = fig.to_json()
"""
    
    elif chart_type == "scatter":
        return f"""
import plotly.express as px

fig = px.scatter(
    {dataframe_name},
    x='{x_col}',
    y='{y_col}',
    title='{title}',
    trendline='ols'  # Add trend line
)

visualization = fig.to_json()
"""
    
    elif chart_type == "bar":
        return f"""
import plotly.express as px

fig = px.bar(
    {dataframe_name},
    x='{x_col}',
    y='{y_col}',
    title='{title}'
)

fig.update_layout(xaxis_title='{x_col}', yaxis_title='{y_col}')
visualization = fig.to_json()
"""
    
    elif chart_type == "heatmap":
        return f"""
import plotly.graph_objects as go
import numpy as np

# Assuming correlation matrix in {dataframe_name}
fig = go.Figure(data=go.Heatmap(
    z={dataframe_name}.values,
    x={dataframe_name}.columns.tolist(),
    y={dataframe_name}.index.tolist(),
    colorscale='RdBu',
    zmid=0
))

fig.update_layout(title='{title}')
visualization = fig.to_json()
"""
    
    elif chart_type == "simulation_distribution":
        # Monte Carlo simulation distribution histogram
        distribution_var = kwargs.get("distribution_var", "distribution")
        baseline_var = kwargs.get("baseline_var", "baseline")
        scenarios_var = kwargs.get("scenarios_var", "scenarios")
        
        return f"""
import plotly.graph_objects as go
import numpy as np

# Extract simulation data from result
distribution = {distribution_var}
baseline = {baseline_var}
scenarios = {scenarios_var}

# Create histogram of simulation results
fig = go.Figure()

# Add histogram
fig.add_trace(go.Histogram(
    x=distribution,
    nbinsx=50,
    name='Simulation Distribution',
    marker_color='lightblue',
    opacity=0.7
))

# Add vertical lines for key values
fig.add_vline(x=baseline, line_dash="dash", line_color="red", 
              annotation_text="Baseline", annotation_position="top")
fig.add_vline(x=scenarios['low'], line_dash="dot", line_color="orange",
              annotation_text="P10 (Low)", annotation_position="top left")
fig.add_vline(x=scenarios['expected'], line_dash="solid", line_color="green",
              annotation_text="P50 (Expected)", annotation_position="top")
fig.add_vline(x=scenarios['high'], line_dash="dot", line_color="purple",
              annotation_text="P90 (High)", annotation_position="top right")

fig.update_layout(
    title='{title}',
    xaxis_title='Simulated Outcome',
    yaxis_title='Frequency',
    hovermode='x unified',
    showlegend=True
)

visualization = fig.to_json()
"""
    
    elif chart_type == "scenario_comparison":
        # Bar chart comparing baseline vs scenarios
        scenarios_var = kwargs.get("scenarios_var", "scenarios")
        baseline_var = kwargs.get("baseline_var", "baseline")
        
        return f"""
import plotly.graph_objects as go

# Extract scenario data
baseline = {baseline_var}
scenarios = {scenarios_var}

# Create comparison bar chart
categories = ['Baseline', 'Low (P10)', 'Expected (P50)', 'High (P90)']
values = [baseline, scenarios['low'], scenarios['expected'], scenarios['high']]
colors = ['gray', 'orange', 'green', 'purple']

fig = go.Figure(data=[
    go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        text=[f'{{v:.2f}}' for v in values],
        textposition='auto'
    )
])

fig.update_layout(
    title='{title}',
    xaxis_title='Scenario',
    yaxis_title='Predicted Value',
    showlegend=False
)

visualization = fig.to_json()
"""
    
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")
