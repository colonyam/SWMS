# src/dashboard/app.py
dashboard_content = '''
"""
Streamlit Dashboard for Smart Waste Management System
Provides real-time visualization and management interface
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import time
import threading
from config import settings

# Page configuration
st.set_page_config(
    page_title="Smart Waste Management",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint
API_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E7D32;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .critical { color: #d32f2f; font-weight: bold; }
    .high { color: #f57c00; font-weight: bold; }
    .medium { color: #fbc02d; font-weight: bold; }
    .low { color: #388e3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def fetch_data(endpoint):
    """Fetch data from API"""
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def render_sidebar():
    """Render sidebar navigation"""
    st.sidebar.title("🗑️ Smart Waste")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Live Map", "Analytics", "Predictions", "Route Optimization", "Alerts"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("Real-time IoT Waste Management System")
    
    # Auto-refresh toggle
    st.sidebar.markdown("---")
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)
    
    return page, auto_refresh

def render_dashboard():
    """Render main dashboard"""
    st.markdown('<p class="main-header">Smart Waste Management Dashboard</p>', unsafe_allow_html=True)
    
    # Fetch data
    data = fetch_data("/analytics/dashboard")
    
    if not data:
        st.warning("No data available. Is the API running?")
        return
    
    summary = data.get("summary", {})
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Bins", summary.get("total_bins", 0))
    with col2:
        st.metric("Active Bins", summary.get("active_bins", 0))
    with col3:
        critical = summary.get("critical_bins", 0)
        st.metric("Bins Needing Collection", critical, 
                 delta=f"{critical} critical" if critical > 0 else None,
                 delta_color="inverse")
    with col4:
        st.metric("Open Alerts", summary.get("open_alerts", 0))
    
    st.markdown("---")
    
    # Zone statistics
    st.subheader("Zone Performance")
    zone_data = data.get("zone_statistics", [])
    if zone_data:
        df_zones = pd.DataFrame(zone_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(df_zones, x="zone", y="avg_fill", color="bin_type",
                        title="Average Fill Level by Zone",
                        labels={"avg_fill": "Fill Level %", "zone": "Zone"})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(df_zones, names="zone", values="reading_count",
                        title="Sensor Readings Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent alerts
    st.subheader("Recent Alerts")
    alerts = data.get("recent_alerts", [])
    if alerts:
        for alert in alerts:
            severity_color = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(alert.get("severity", "medium"), "⚪")
            
            st.write(f"{severity_color} **{alert.get('type', 'Unknown')}**: {alert.get('message', '')}")
            st.caption(f"Time: {alert.get('created_at', 'Unknown')}")
    else:
        st.info("No active alerts")

def render_live_map():
    """Render real-time map of bins"""
    st.subheader("Live Bin Locations")
    
    bins_data = fetch_data("/bins?limit=1000")
    if not bins_data or not bins_data.get("bins"):
        st.warning("No bin data available")
        return
    
    df = pd.DataFrame(bins_data["bins"])
    
    # Color code by fill level
    def get_color(fill):
        if fill >= 90: return "#d32f2f"  # Red
        elif fill >= 75: return "#f57c00"  # Orange
        elif fill >= 50: return "#fbc02d"  # Yellow
        else: return "#388e3c"  # Green
    
    df["color"] = df["fill_level"].apply(get_color)
    
    fig = px.scatter_mapbox(
        df,
        lat="location.lat",
        lon="location.lon",
        color="fill_level",
        size="fill_level",
        hover_name="device_id",
        hover_data=["zone", "bin_type", "battery"],
        color_continuous_scale=["green", "yellow", "orange", "red"],
        zoom=12,
        height=600,
        title="Real-time Bin Fill Levels"
    )
    
    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Bin list