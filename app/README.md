# Autonomous Multi-Agent Business Intelligence System - Streamlit UI

Modern web dashboard for Autonomous Multi-Agent Business Intelligence System's AI-powered SQL generation system.

## 🎨 Features

### 💬 Interactive Query Interface
- Natural language to SQL conversion
- Three query modes:
  - **Standard**: SQL generation only
  - **Analytics**: SQL + statistical analysis + visualization
  - **Research**: SQL + external market research
- Side-by-side performance comparison (Internal vs. Market)
- Real-time query execution
- Agent reasoning trace visualization

### 📊 Real-time Monitoring Dashboard
- Live metric tracking (5 default metrics)
- Anomaly alert feed with severity indicators
- Manual metric checks on demand
- Trend visualization with baselines
- WebSocket connection for real-time alerts

### 🤖 Agent Trace Viewer
- Step-by-step agent execution visualization
- Role and task display for each agent
- Input/output tracking
- Validation results
- Token usage statistics

### 📚 Query History
- Full query history with timestamps
- SQL and result preview
- Re-run past queries

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install streamlit plotly requests
```

Or use the full requirements:
```bash
pip install -r requirements.txt
```

### 2. Start Backend

Ensure the FastAPI backend is running:
```bash
python -m uvicorn src.api.main_crewai:app --reload --host 127.0.0.1 --port 8000
```

### 3. Launch Dashboard

```bash
streamlit run app/streamlit_ui.py
```

The dashboard will open at **http://localhost:8501**

## 📸 Screenshots

### Query Interface
Ask natural language questions and see SQL generation, data results, and visualizations.

### Monitoring Dashboard
Track key metrics in real-time with anomaly detection and alerts.

### Agent Trace
Visualize the reasoning process of each AI agent in the workflow.

## 🎯 Usage Examples

### Example 1: Standard Query
```
User: "Show me total revenue for the last quarter"

Result:
- Generated SQL
- Data preview
- Agent trace showing Query Analyst → Librarian → SQL Architect → Validator
```

### Example 2: Analytics Query
```
User: "Forecast revenue for next month based on trends"

Result:
- Generated SQL
- Executed data
- Statistical forecast analysis
- Interactive Plotly chart
- Agent trace including Data Scientist and Visualization agents
```

### Example 3: Research Query
```
User: "Is our 10% growth good compared to the market?"

Result:
- Internal SQL analysis: 10% growth
- External research: Industry averaged 12% (via Tavily)
- Unified insights: "Your 10% is slightly below market average"
- Side-by-side metric cards showing Internal vs. Market
```

### Example 4: Real-time Monitoring
```
Dashboard automatically:
- Checks metrics every 5 minutes
- Detects 50% revenue spike
- Broadcasts alert via WebSocket
- Displays in alert feed with severity indicator
- Shows root cause analysis
```

## 🧩 Component Structure

```
app/
├── streamlit_ui.py              # Main dashboard entry point
├── components/
│   ├── __init__.py              # Component exports
│   ├── agent_trace.py           # Agent reasoning visualization
│   └── monitoring_dashboard.py  # Real-time monitoring UI
```

### Component: `AgentTraceViewer`

Displays step-by-step agent execution:
```python
from components.agent_trace import AgentTraceViewer

viewer = AgentTraceViewer()
viewer.display(query_result)
```

### Component: `MonitoringDashboard`

Real-time metric monitoring:
```python
from components.monitoring_dashboard import MonitoringDashboard

dashboard = MonitoringDashboard(api_base_url="http://localhost:8000")
dashboard.render()
```

## ⚙️ Configuration

### Backend URL
Default: `http://localhost:8000`

Change in sidebar or code:
```python
API_BASE_URL = "http://your-backend-url:8000"
```

### Display Options
- **Show SQL by default**: Auto-expand SQL code blocks
- **Auto-expand visualizations**: Show charts immediately
- **Enable notifications**: Browser notifications for alerts
- **Dark mode**: Toggle dark theme

## 🎨 Styling

### Custom CSS
The dashboard uses custom CSS for modern UI:
- Gradient headers
- Colored metric cards
- Alert severity indicators
- Agent step containers

### Metrics Cards
Side-by-side comparison:
```python
col1, col2 = st.columns(2)

with col1:
    st.metric("Internal Performance", "10%", delta="-2% vs. market")

with col2:
    st.metric("Market Sentiment", "12%")
```

## 📊 Dashboard Tabs

### 1. Query Tab
- Natural language input
- Query mode selector
- Execute button
- Results display (SQL, data, visualizations)
- Agent trace toggle

### 2. Monitoring Tab
- Status metrics (4 cards)
- Alert feed
- Monitored metrics list
- Manual check interface
- Trend charts

### 3. History Tab
- Chronological query list
- Expandable details
- SQL preview
- Result summary

### 4. Settings Tab
- API configuration
- Display preferences
- Data management (clear history)
- Reset options

## 🔌 API Integration

### Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Backend status check |
| `POST /query` | Standard SQL generation |
| `POST /query/analytics` | Analytics workflow |
| `POST /query/research` | Research workflow |
| `GET /alerts/recent` | Fetch alert history |
| `POST /alerts/check/{metric}` | Manual metric check |

### WebSocket Connection
```javascript
ws://localhost:8000/ws/alerts
```

Real-time alert broadcasting (future enhancement for live dashboard updates).

## 🐛 Troubleshooting

### Backend Connection Failed
**Symptom**: "❌ Backend Offline" in sidebar

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check firewall settings (port 8000)
3. Ensure correct API_BASE_URL

### No Visualizations Displayed
**Symptom**: "Could not display visualization"

**Solutions**:
1. Check analytics query returned `visualization` field
2. Verify Plotly is installed: `pip install plotly`
3. Check JSON format of visualization data

### Monitoring Dashboard Empty
**Symptom**: No alerts or metrics shown

**Solutions**:
1. Ensure Sentry Agent is running in backend
2. Check `/alerts/recent` endpoint returns data
3. Verify database has sufficient historical data (7+ days)

### Slow Query Execution
**Symptom**: Queries take >30 seconds

**Solutions**:
1. Use Standard mode instead of Research (faster)
2. Check backend logs for bottlenecks
3. Verify database performance
4. Consider caching for Tavily searches

## 🚀 Performance Tips

### Optimize Loading
- **Lazy load components**: Only render active tabs
- **Cache data**: Use `st.cache_data` for API calls
- **Debounce inputs**: Add delays to prevent excessive API calls

### Reduce Token Usage
- Use Standard mode when research not needed
- Limit query history size
- Disable auto-expand for large results

### Improve Responsiveness
- Use `st.spinner()` for long operations
- Show progress bars for multi-step workflows
- Implement pagination for large result sets

## 🔒 Security

### Best Practices
1. **Never commit API keys**: Use environment variables
2. **Sanitize inputs**: Backend validates all queries
3. **HTTPS in production**: Use SSL certificates
4. **Authentication**: Add user login (Streamlit supports auth)
5. **Rate limiting**: Prevent abuse with request throttling

### Production Deployment

**Streamlit Cloud**:
```bash
streamlit run app/streamlit_ui.py --server.port=8501 --server.address=0.0.0.0
```

**Docker**:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_ui.py"]
```

## 📦 Dependencies

Core dependencies:
```
streamlit>=1.31.0
plotly>=5.18.0
requests>=2.31.0
```

Optional enhancements:
```
streamlit-aggrid  # Enhanced tables
streamlit-echarts  # Alternative charts
streamlit-option-menu  # Custom navigation
```

## 🗺️ Roadmap

### Phase UI 1.1
- [ ] User authentication
- [ ] Saved query templates
- [ ] Export results (CSV, Excel)
- [ ] Dark mode theme

### Phase UI 1.2
- [ ] Real-time WebSocket alerts in UI
- [ ] Custom metric definitions
- [ ] Alert notification settings
- [ ] Email/Slack alert routing

### Phase UI 1.3
- [ ] Collaborative features (share queries)
- [ ] Dashboard customization
- [ ] Widget builder
- [ ] Advanced filtering

## 🤝 Contributing

### Adding New Components

1. Create component file in `app/components/`
2. Implement reusable class/function
3. Export in `__init__.py`
4. Import in `streamlit_ui.py`

### Example Component
```python
# app/components/my_component.py

import streamlit as st

class MyComponent:
    def render(self, data):
        st.subheader("My Component")
        st.write(data)

# app/streamlit_ui.py
from components.my_component import MyComponent

component = MyComponent()
component.render(my_data)
```

## 📝 License

Same as Autonomous Multi-Agent Business Intelligence System project.

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review backend logs: `src/api/main_crewai.py`
3. Verify all dependencies installed
4. Check Streamlit documentation: https://docs.streamlit.io

---

**Built with ❤️ using Streamlit**

*Version: 2.0.4*
*Last Updated: January 2026*
