"""
Production-Grade Streamlit Frontend for Smart Home AI Agent
Interactive dashboard for device control and analytics
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional

# Configure page
st.set_page_config(
    page_title="Smart Home AI Agent",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 0rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success { color: #00CC00; }
    .warning { color: #FFA500; }
    .error { color: #FF0000; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'backend_url' not in st.session_state:
    st.session_state.backend_url = st.secrets.get("BACKEND_URL", "http://127.0.0.1:5000")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartHomeUI:
    """Streamlit UI controller"""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, timeout: int = 10) -> Optional[Dict]:
        """Make API request with error handling"""
        try:
            url = f"{self.backend_url}{endpoint}"
            response = self.session.request(method, url, json=data, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot connect to backend at {self.backend_url}")
            return None
        except requests.exceptions.Timeout:
            st.error("⏱️ Backend request timeout")
            return None
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                st.warning("⚠️ Rate limit exceeded. Please wait a moment.")
            else:
                st.error(f"❌ API error: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            logger.error(f"Request error: {e}")
            return None
    
    def get_status(self) -> Optional[Dict]:
        """Get system status"""
        return self.make_request("GET", "/status")
    
    def get_devices(self) -> Optional[Dict]:
        """Get all devices"""
        return self.make_request("GET", "/devices")
    
    def control_device(self, device: str, action: str) -> Optional[Dict]:
        """Control a device"""
        return self.make_request("POST", "/device/control", {
            "device": device,
            "action": action
        })
    
    def process_command(self, command: str, context: Optional[Dict] = None) -> Optional[Dict]:
        """Process natural language command"""
        return self.make_request("POST", "/command", {
            "command": command,
            "context": context or {}
        })
    
    def get_forecast(self, periods: int = 24, format_type: str = "detailed") -> Optional[Dict]:
        """Get energy forecast"""
        return self.make_request("GET", f"/forecast?periods={periods}&format={format_type}")
    
    def get_peak_probability(self) -> Optional[Dict]:
        """Get peak load probability"""
        return self.make_request("GET", "/forecast/peak-probability")
    
    def get_optimization(self, auto_apply: bool = False) -> Optional[Dict]:
        """Get optimization decisions"""
        return self.make_request("POST", "/optimize", {"auto_apply": auto_apply})
    
    def get_decision_history(self, limit: int = 50) -> Optional[Dict]:
        """Get decision history"""
        return self.make_request("GET", f"/history/decisions?limit={limit}")

# Initialize UI controller
ui = SmartHomeUI(st.session_state.backend_url)

# ===== MAIN LAYOUT =====

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    st.image("https://via.placeholder.com/150x50?text=Smart+Home", width=150)
with col2:
    st.title("🏠 Smart Home AI Agent")
with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.divider()

# Sidebar navigation
with st.sidebar:
    st.markdown("## Navigation")
    page = st.radio("Select Page", [
        "Dashboard",
        "Device Control",
        "Energy Analytics",
        "Command Center",
        "Optimization",
        "Settings"
    ])
    
    st.divider()
    st.markdown("### System Status")
    status = ui.get_status()
    if status:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Status", "🟢 Online" if status.get('status') == 'running' else "🔴 Offline")
        with col2:
            st.metric("Devices", status.get('device_count', 0))

# ===== PAGE: DASHBOARD =====

if page == "Dashboard":
    st.markdown("## System Overview")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    status = ui.get_status()
    if status:
        with col1:
            st.metric("Agent Status", "Running ✓")
        with col2:
            st.metric("Connected Devices", status.get('device_count', 0))
        with col3:
            st.metric("Recent Decisions", status.get('recent_decisions', 0))
        with col4:
            st.metric("LLM Available", "Yes ✓" if status.get('llm_available') else "No ✗")
    
    st.divider()
    
    # Current context
    col1, col2 = st.columns(2)
    
    if status and 'context' in status:
        context = status['context']
        
        with col1:
            st.markdown("### Current Environment")
            st.metric("Temperature", f"{context.get('temperature', 0):.1f}°C")
            st.metric("Humidity", f"{context.get('humidity', 0):.0f}%")
            st.metric("Occupancy", "Occupied" if context.get('occupancy') else "Unoccupied")
        
        with col2:
            st.markdown("### Energy Status")
            energy = context.get('energy_consumed', 0)
            st.metric("Current Power", f"{energy:.0f}W")
            peak_prob = context.get('peak_prediction')
            st.metric("Peak Risk", "⚠️ HIGH" if peak_prob else "✓ LOW")
    
    st.divider()
    
    # Energy forecast chart
    st.markdown("### Energy Forecast (Next 24 Hours)")
    forecast_data = ui.get_forecast(periods=24)
    
    if forecast_data and 'forecast' in forecast_data:
        forecast_list = forecast_data['forecast']
        
        df_forecast = pd.DataFrame([
            {
                'time': pd.to_datetime(f['timestamp']),
                'yhat': f['yhat'],
                'lower': f['yhat_lower'],
                'upper': f['yhat_upper']
            }
            for f in forecast_list
        ])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_forecast['time'], y=df_forecast['yhat'],
            mode='lines+markers',
            name='Forecast',
            line=dict(color='#00CC96', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=df_forecast['time'],
            y=df_forecast['upper'],
            fill=None,
            mode='lines',
            line_color='rgba(0,0,0,0)',
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=df_forecast['time'],
            y=df_forecast['lower'],
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,0,0,0)',
            name='95% Confidence',
            fillcolor='rgba(0,204,150,0.2)'
        ))
        
        fig.update_layout(
            title="Energy Consumption Forecast",
            yaxis_title="Power (W)",
            xaxis_title="Time",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

# ===== PAGE: DEVICE CONTROL =====

elif page == "Device Control":
    st.markdown("## Device Management")
    
    devices = ui.get_devices()
    
    if devices and 'devices' in devices:
        device_list = devices['devices']
        
        if not device_list:
            st.info("No devices connected")
        else:
            # Create device control cards
            cols = st.columns(3)
            device_names = list(device_list.keys())
            
            for idx, device_name in enumerate(device_names):
                with cols[idx % 3]:
                    device_state = device_list[device_name]
                    
                    st.markdown(f"### {device_name.title()}")
                    st.markdown(f"**State:** {device_state}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("ON", key=f"on_{device_name}", use_container_width=True):
                            result = ui.control_device(device_name, "on")
                            if result:
                                st.success(f"✓ {device_name} turned ON")
                            else:
                                st.error(f"✗ Failed to turn ON {device_name}")
                    
                    with col2:
                        if st.button("OFF", key=f"off_{device_name}", use_container_width=True):
                            result = ui.control_device(device_name, "off")
                            if result:
                                st.success(f"✓ {device_name} turned OFF")
                            else:
                                st.error(f"✗ Failed to turn OFF {device_name}")
    
    st.divider()
    
    # Quick actions
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌙 Goodnight Mode", use_container_width=True):
            actions = [
                ("lights", "off"),
                ("hvac", "low"),
                ("plugs", "off")
            ]
            failures = []
            for device, action in actions:
                res = ui.control_device(device, action)
                if not res:
                    failures.append(device)
            if failures:
                st.error(f"✗ Failed to apply actions for: {', '.join(failures)}")
            else:
                st.success("✓ Goodnight mode activated")
    
    with col2:
        if st.button("☀️ Good Morning", use_container_width=True):
            actions = [
                ("lights", "on"),
                ("thermostat", "auto"),
                ("hvac", "on")
            ]
            failures = []
            for device, action in actions:
                res = ui.control_device(device, action)
                if not res:
                    failures.append(device)
            if failures:
                st.error(f"✗ Failed to apply actions for: {', '.join(failures)}")
            else:
                st.success("✓ Good morning mode activated")
    
    with col3:
        if st.button("🏃 Away Mode", use_container_width=True):
            actions = [
                ("lights", "off"),
                ("hvac", "eco_mode"),
                ("plugs", "off")
            ]
            failures = []
            for device, action in actions:
                res = ui.control_device(device, action)
                if not res:
                    failures.append(device)
            if failures:
                st.error(f"✗ Failed to apply actions for: {', '.join(failures)}")
            else:
                st.success("✓ Away mode activated")

# ===== PAGE: ENERGY ANALYTICS =====

elif page == "Energy Analytics":
    st.markdown("## Energy Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forecast_data = ui.get_forecast(periods=24, format_type="summary")
        if forecast_data and 'forecast_summary' in forecast_data:
            summary = forecast_data['forecast_summary']
            st.metric("Average (24h)", f"{summary['average']:.0f}W")
    
    with col2:
        if forecast_data and 'forecast_summary' in forecast_data:
            summary = forecast_data['forecast_summary']
            st.metric("Peak (24h)", f"{summary['max']:.0f}W")
    
    with col3:
        peak_prob = ui.get_peak_probability()
        if peak_prob:
            prob = peak_prob['peak_probability']
            st.metric("Peak Probability", f"{prob:.0%}", 
                     delta=f"{('⚠️ HIGH' if prob > 0.7 else '✓ LOW')}")
    
    st.divider()
    
    # Extended forecast
    st.markdown("### 7-Day Forecast")
    forecast_data = ui.get_forecast(periods=168, format_type="detailed")
    
    if forecast_data and 'forecast' in forecast_data:
        forecast_list = forecast_data['forecast']
        
        # Aggregate by day
        daily_data = []
        current_day = None
        day_values = []
        
        for f in forecast_list:
            ts = pd.to_datetime(f['timestamp'])
            day = ts.date()
            
            if current_day != day and day_values:
                daily_data.append({
                    'date': current_day,
                    'avg': sum(day_values) / len(day_values),
                    'max': max(day_values),
                    'min': min(day_values)
                })
                day_values = []
            
            current_day = day
            day_values.append(f['yhat'])
        
        if day_values:
            daily_data.append({
                'date': current_day,
                'avg': sum(day_values) / len(day_values),
                'max': max(day_values),
                'min': min(day_values)
            })
        
        df_daily = pd.DataFrame(daily_data)
        
        fig = px.bar(df_daily, x='date', y=['min', 'avg', 'max'],
                    title="Daily Energy Profile",
                    barmode='overlay',
                    color_discrete_sequence=['#FF6B6B', '#00CC96', '#FF8C42'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

# ===== PAGE: COMMAND CENTER =====

elif page == "Command Center":
    st.markdown("## Natural Language Commands")
    st.info("💡 Try: 'turn on lights', 'what is the temperature', 'forecast energy', etc.")
    
    command = st.text_input("Enter command:", placeholder="e.g., turn on the bedroom lights")
    
    if st.button("Execute", type="primary", use_container_width=True):
        if command:
            with st.spinner("Processing..."):
                result = ui.process_command(command)
                if result:
                    st.success("✓ Command executed")
                    st.markdown(f"**Response:** {result.get('response', 'No response')}")
        else:
            st.warning("Please enter a command")
    
    st.divider()
    
    # Command examples
    st.markdown("### Example Commands")
    
    examples = [
        ("Device Control", [
            "Turn on the lights",
            "Set thermostat to 22 degrees",
            "Turn off the HVAC"
        ]),
        ("Information Queries", [
            "What is the current temperature?",
            "What is the energy forecast?",
            "Is the house occupied?",
            "What is the weather?"
        ]),
        ("Automation", [
            "Enable eco mode",
            "Activate night mode",
            "Optimize energy consumption"
        ])
    ]
    
    for category, cmds in examples:
        st.markdown(f"**{category}**")
        for cmd in cmds:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"• {cmd}")

# ===== PAGE: OPTIMIZATION =====

elif page == "Optimization":
    st.markdown("## Energy Optimization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Optimization Controls")
        
        auto_optimize = st.checkbox("Enable Auto-Optimization", value=True)
        
        if st.button("Get Optimization Suggestions", use_container_width=True, type="primary"):
            with st.spinner("Analyzing..."):
                opt_result = ui.get_optimization(auto_apply=auto_optimize)
                if opt_result and 'decisions' in opt_result:
                    decisions = opt_result['decisions']
                    
                    st.success(f"✓ Generated {len(decisions)} optimization decisions")
                    
                    for device, action in decisions.items():
                        st.caption(f"• {device}: {action}")
    
    with col2:
        st.markdown("### Decision History")
        history = ui.get_decision_history(limit=20)
        
        if history and 'decisions' in history:
            decisions = history['decisions']
            
            if decisions:
                df_history = pd.DataFrame([
                    {
                        'Time': pd.to_datetime(d['timestamp']).strftime('%H:%M:%S'),
                        'Device': d['device'],
                        'Action': d['action'],
                        'Source': d['source']
                    }
                    for d in decisions[-10:]
                ])
                
                st.dataframe(df_history, use_container_width=True, hide_index=True)

# ===== PAGE: SETTINGS =====

elif page == "Settings":
    st.markdown("## System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Backend Configuration")
        backend_url = st.text_input("Backend URL", value=st.session_state.backend_url)
        
        if st.button("Update", use_container_width=True):
                st.session_state.backend_url = backend_url
                # Update runtime client so changes take effect immediately
                try:
                    ui.backend_url = backend_url
                except Exception:
                    pass
                st.success("✓ Backend URL updated")
    
    with col2:
        st.markdown("### About")
        st.caption("""
        **Smart Home AI Agent v1.0**
        
        Production-grade intelligent home automation system
        - Real-time device control via MQTT
        - AI-powered optimization
        - Energy forecasting
        - Natural language commands
        """)
    
    st.divider()
    
    st.markdown("### System Health")
    
    if st.button("Run Health Check", use_container_width=True):
        with st.spinner("Checking..."):
            status = ui.make_request("GET", "/health")
            if status:
                st.success("✓ System healthy")
                st.json(status)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Smart Home AI Agent • Dashboard v1.0</p>
    <p style='font-size: 0.8rem;'>Last Updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
