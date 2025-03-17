import pymongo
import streamlit as st
from datetime import datetime

# MongoDB Setup
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["rootsense"]

# Collections
system_stats_collection = db["system_stats"]
tickets_collection = db["tickets"]
root_cause_collection = db["rootsense"]
predictive_analysis_collection = db["predictions"]
rei_collection = db["rei"]

# Streamlit UI setup
st.set_page_config(page_title="System Resource Report", layout="wide")

# Custom Styles
st.markdown("""
    <style>
    body {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc;
    }
    .main-header {
        font-size: 2.5em;
        font-weight: 700;
        color: #ffffff;
        background: linear-gradient(90deg, #4e73df, #1cc88a);
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
    }
    .section-header {
        font-size: 1.75em;
        font-weight: 600;
        color: #2e4053;
        margin-bottom: 15px;
        margin-top: 30px;
    }
    .description {
        font-size: 1em;
        color: #5a5c69;
        margin-bottom: 10px;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e3e6f0;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.2);
    }
    .metric-card-header {
        font-size: 1.2em;
        font-weight: 600;
        color: #4e5d6d;
    }
    .metric-card-value {
        font-size: 2em;
        font-weight: bold;
        color: #1e2a38;
        margin-top: 10px;
    }
    .table-container {
        margin-top: 20px;
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
    }
    .ticket-table th {
        background-color: #f8f9fc;
        color: #3e4a60;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    }
    .ticket-table td {
        padding: 10px;
        text-align: center;
        border-bottom: 1px solid #f1f1f1;
    }
    </style>
""", unsafe_allow_html=True)

# Fetch Data Functions
def fetch_system_stats():
    stats = system_stats_collection.find().sort("timestamp", -1).limit(1)
    return list(stats)[0] if stats else {}

def fetch_root_cause_analysis():
    rca_data = root_cause_collection.find().sort("timestamp", -1).limit(1)
    return list(rca_data)[0] if rca_data else {}

def fetch_predictive_analysis():
    predictive_data = predictive_analysis_collection.find().sort("timestamp", -1).limit(1)
    return list(predictive_data)[0] if predictive_data else {}

def fetch_tickets():
    tickets = tickets_collection.find().limit(5)
    return list(tickets)

def fetch_rei():
    rei_data = rei_collection.find().sort("timestamp", -1).limit(1)
    return list(rei_data)[0] if rei_data else {}

# Generate and display the report
def generate_report():
    # Fetch all necessary data 
    system_stats = fetch_system_stats()
    rca_data = fetch_root_cause_analysis()
    predictive_data = fetch_predictive_analysis()
    tickets = fetch_tickets()
    rei_data = fetch_rei()

    # --- Main Header ---
    st.markdown('<div class="main-header">🌟 Rootsense System Resource Dashboard</div>', unsafe_allow_html=True)

    # --- System Stats Section ---
    st.markdown('<div class="section-header">📊 System Stats Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="description">An overview of current system resource usage based on the latest available data.</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-header">CPU Usage</div>
            <div class="metric-card-value">{system_stats.get("cpu_usage", 0):,.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-header">Memory Usage</div>
            <div class="metric-card-value">{system_stats.get("memory_percent", 0):,.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-header">Disk Usage</div>
            <div class="metric-card-value">{system_stats.get("disk_percent", 0):,.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Root Cause Analysis Section ---
    st.markdown('<div class="section-header">🔍 Root Cause Analysis Predictions</div>', unsafe_allow_html=True)
    if rca_data:
        st.write(f"**Timestamp**: {rca_data.get('timestamp')}")
        st.write(f"**Predicted CPU Usage**: {rca_data.get('cpu_usage_predictions', 0):,.2f}%")
        st.write(f"**Predicted Memory Usage**: {rca_data.get('memory_percent_predictions', 0):,.2f}%")
        st.write(f"**Predicted Disk Usage**: {rca_data.get('disk_percent_predictions', 0):,.2f}%")
    else:
        st.write("No Root Cause Analysis data found.")

    # --- Predictive Analysis Section ---
    st.markdown('<div class="section-header">📈 Predictive Analysis</div>', unsafe_allow_html=True)
    if predictive_data:
        predictions = predictive_data.get('predictions', {})
        if isinstance(predictions, dict):
            for time_interval, predicted_value in predictions.items():
                st.write(f"**{time_interval} min Prediction**: {predicted_value:,.2f}%")
        elif isinstance(predictions, float):
            st.write(f"**Predicted Value**: {predictions:,.2f}%")
    else:
        st.write("No Predictive Analysis data found.")

    # --- Tickets Section ---
    st.markdown('<div class="section-header">🎫 Current Tickets</div>', unsafe_allow_html=True)
    if tickets:
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        ticket_table = [
            ["ID", "Metric", "Value", "Threshold", "Timestamp", "Status", "Logs"]
        ]
        for ticket in tickets:
            ticket_table.append([
                ticket.get('_id'),
                ticket.get('metric'),
                ticket.get('value'),
                ticket.get('threshold'),
                ticket.get('timestamp'),
                ticket.get('status'),
                ticket.get('logs'),
            ])
        st.table(ticket_table)
    else:
        st.write("No current tickets found.")

    # --- REI Section ---
    st.markdown('<div class="section-header">💡 Resource Efficiency Index (REI)</div>', unsafe_allow_html=True)
    if rei_data:
        st.write(f"**Timestamp**: {rei_data.get('timestamp')}")
        st.write(f"**Collective REI**: {rei_data.get('collective_rei', 0):,.2f}%")
        st.write(f"**Insights**: {rei_data.get('insights')}")
    else:
        st.write("No REI data found.")

# Run the report generator
if __name__ == "__main__":
    generate_report()
