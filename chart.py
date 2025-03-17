import streamlit as st
import pymongo
import plotly.graph_objects as go
import logging
import os
import time

# Set up logging
log_dir = '../logs/'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'dashboard.log')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),
                        logging.FileHandler(log_file)
                    ])

# MongoDB connection setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['rootsense']
collection = db['system_stats']

# Streamlit UI setup
st.set_page_config(page_title="System Metrics Dashboard", layout="wide")
st.sidebar.title("Dashboard Settings")

# Sidebar Controls
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", min_value=1, max_value=10, value=2)

st.sidebar.markdown("### MongoDB Connection Info")
try:
    client.server_info()  # Will raise an exception if connection fails
    st.sidebar.success("Connected to MongoDB")
except Exception as e:
    st.sidebar.error(f"MongoDB connection failed: {e}")

# Sidebar Instructions
st.sidebar.markdown("### How to Use")
st.sidebar.info(
    """
    - Use the **Enable Auto-Refresh** checkbox to toggle automatic updates.
    - Adjust the **Refresh Interval** slider to set how often data updates.
    - Ensure MongoDB is running and accessible at `localhost:27017`.
    - Metrics and charts display real-time system statistics from your database.
    """
)

# About Section
st.sidebar.markdown("### About")
st.sidebar.info(
    """
    This dashboard visualizes real-time system metrics, including:
    - **CPU Usage**: Tracks CPU utilization.
    - **Memory Usage**: Monitors memory consumption.
    - **Disk Usage**: Displays disk usage statistics.
    - **Network Traffic**: Shows data sent and received.

    Built using Streamlit, Plotly, and MongoDB.
    """
)

# Placeholder for real-time updates
st.title("Real-Time System Metrics Dashboard")
col1, col2, col3, col4 = st.columns(4)
metric_placeholders = {
    "cpu": col1.empty(),
    "memory": col2.empty(),
    "disk": col3.empty(),
    "network_sent": col4.empty(),
    "network_recv": col4.empty(),
}

st.markdown("### Detailed Metrics Trends")
cpu_chart = st.empty()
memory_chart = st.empty()
disk_chart = st.empty()
network_chart = st.empty()

# Data storage for trend charts
cpu_trend, memory_trend, disk_trend, network_trend = [], [], [], []

# Caching data fetching function
@st.cache_data(ttl=5)
def fetch_data():
    try:
        logging.debug("Fetching the latest data from MongoDB.")
        latest_data = collection.find().sort("timestamp", pymongo.DESCENDING).limit(1)
        data_list = list(latest_data)
        return data_list[0] if data_list else None
    except Exception as e:
        logging.error(f"Error fetching data from MongoDB: {e}")
        return None

# Real-time data fetching and chart updating
while True:
    data = fetch_data()
    if not data:
        st.error("No data available. Check your MongoDB connection.")
        time.sleep(refresh_interval)
        continue

    # Extract data
    cpu_usage = data['cpu_usage']
    memory_percent = data['memory_percent']
    disk_percent = data['disk_percent']
    network_sent = data['network_sent']
    network_recv = data['network_recv']

    # Update trends
    cpu_trend.append(cpu_usage)
    memory_trend.append(memory_percent)
    disk_trend.append(disk_percent)
    network_trend.append((network_sent, network_recv))

    # Limit trend data size
    max_trend_points = 50
    if len(cpu_trend) > max_trend_points:
        cpu_trend.pop(0)
        memory_trend.pop(0)
        disk_trend.pop(0)
        network_trend.pop(0)

    # Update summary metrics
    metric_placeholders["cpu"].metric("CPU Usage (%)", f"{cpu_usage:.2f}")
    metric_placeholders["memory"].metric("Memory Usage (%)", f"{memory_percent:.2f}")
    metric_placeholders["disk"].metric("Disk Usage (%)", f"{disk_percent:.2f}")
    metric_placeholders["network_sent"].metric("Network Sent (bytes)", f"{network_sent:.2f}")
    metric_placeholders["network_recv"].metric("Network Received (bytes)", f"{network_recv:.2f}")

    # Create and update charts
    cpu_fig = go.Figure()
    cpu_fig.add_trace(go.Bar(
        x=["Current"],
        y=[cpu_usage],
        marker=dict(color='red' if cpu_usage > 80 else 'green'),
        name="Current CPU Usage"
    ))
    cpu_fig.add_trace(go.Scatter(
        x=list(range(len(cpu_trend))),
        y=cpu_trend,
        mode='lines+markers',
        name="CPU Trend",
        line=dict(color='orange')
    ))
    cpu_fig.update_layout(title="CPU Usage", template="plotly_dark", xaxis_title="Time", yaxis_title="%")
    cpu_chart.plotly_chart(cpu_fig, use_container_width=True)

    memory_fig = go.Figure()
    memory_fig.add_trace(go.Bar(
        x=["Current"],
        y=[memory_percent],
        marker=dict(color='red' if memory_percent > 85 else 'green'),
        name="Current Memory Usage"
    ))
    memory_fig.add_trace(go.Scatter(
        x=list(range(len(memory_trend))),
        y=memory_trend,
        mode='lines+markers',
        name="Memory Trend",
        line=dict(color='blue')
    ))
    memory_fig.update_layout(title="Memory Usage", template="plotly_dark", xaxis_title="Time", yaxis_title="%")
    memory_chart.plotly_chart(memory_fig, use_container_width=True)

    disk_fig = go.Figure()
    disk_fig.add_trace(go.Bar(
        x=["Current"],
        y=[disk_percent],
        marker=dict(color='red' if disk_percent > 90 else 'green'),
        name="Current Disk Usage"
    ))
    disk_fig.add_trace(go.Scatter(
        x=list(range(len(disk_trend))),
        y=disk_trend,
        mode='lines+markers',
        name="Disk Trend",
        line=dict(color='purple')
    ))
    disk_fig.update_layout(title="Disk Usage", template="plotly_dark", xaxis_title="Time", yaxis_title="%")
    disk_chart.plotly_chart(disk_fig, use_container_width=True)

    network_fig = go.Figure()
    sent_data, recv_data = zip(*network_trend)
    network_fig.add_trace(go.Bar(
        x=["Sent"],
        y=[network_sent],
        marker=dict(color='orange'),
        name="Current Sent"
    ))
    network_fig.add_trace(go.Bar(
        x=["Received"],
        y=[network_recv],
        marker=dict(color='blue'),
        name="Current Received"
    ))
    network_fig.add_trace(go.Scatter(
        x=list(range(len(sent_data))),
        y=sent_data,
        mode='lines+markers',
        name="Sent Trend",
        line=dict(color='green')
    ))
    network_fig.add_trace(go.Scatter(
        x=list(range(len(recv_data))),
        y=recv_data,
        mode='lines+markers',
        name="Received Trend",
        line=dict(color='red')
    ))
    network_fig.update_layout(title="Network Traffic", template="plotly_dark", xaxis_title="Time", yaxis_title="Bytes")
    network_chart.plotly_chart(network_fig, use_container_width=True)

    # Pause for refresh interval
    if not auto_refresh:
        break
    time.sleep(refresh_interval)

# streamlit run chart.py --server.port=7000