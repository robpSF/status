import streamlit as st
import requests
import pandas as pd

# --- Password Authentication ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("Please Enter Password")
    password_input = st.text_input("Password", type="password")
    if st.button("Submit"):
        if password_input == st.secrets["password"]:
            st.session_state["authenticated"] = True
            st.success("Authenticated!")
        else:
            st.error("Incorrect password!")
    st.stop()

# --- App Main Content ---
st.set_page_config(page_title="Heartz Monitor Dashboard", layout="wide")

def get_status_color(status):
    """
    Return a colourblind-friendly hex color based on the service status.
    Uses an Okabe–Ito-inspired palette.
    """
    s = str(status).lower()
    if s in ["healthy", "up", "ok", "good"]:
        return "#0072B2"  # Blue
    elif s in ["warning", "degraded", "slow"]:
        return "#E69F00"  # Orange
    elif s in ["down", "fail", "error"]:
        return "#D55E00"  # Vermilion
    else:
        return "#999999"  # Grey

def get_status_emoji(status):
    """
    Return an emoji based on the service status.
    """
    s = str(status).lower()
    if s in ["healthy", "up", "ok", "good"]:
        return "✅"
    elif s in ["warning", "degraded", "slow"]:
        return "⚠️"
    elif s in ["down", "fail", "error"]:
        return "❌"
    else:
        return "ℹ️"

def fetch_data(url):
    """Fetch JSON data from the specified URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data from {url}: {e}")
        return None

def display_service_card_html(service):
    """
    Display a single service's details as a card using inline HTML.
    """
    name = service.get("name", "Unnamed Service")
    status = service.get("status", "unknown")
    description = service.get("description") or "No details provided"
    tags = service.get("tags", [])
    color = get_status_color(status)
    
    card_html = f"""
    <div style="background-color: #f7f7f7; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin-bottom: 8px;">{name}</h3>
        <p style="margin: 0;"><strong>Status:</strong> <span style="color: {color};">{status.upper()}</span></p>
        <p style="margin: 0;"><strong>Description:</strong> {description}</p>
        <p style="margin: 0;"><strong>Tags:</strong> {', '.join(tags) if tags else 'None'}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def main():
    st.title("Heartz Monitor Dashboard")
    
    # Choose between Table view (default) and Card view for monitor data.
    view_option = st.sidebar.radio("Select view", ("Table view", "Card view"))
    
    # --- Main Monitor Data ---
    monitor_url = st.secrets["monitor_url"]
    with st.spinner("Fetching monitor data..."):
        data = fetch_data(monitor_url)
    
    if data is None:
        st.error("Failed to fetch monitor data. Please try again later.")
        return

    with st.expander("Show raw JSON (Debug)"):
        st.json(data)
    
    overall_status = data.get("status", "unknown")
    overall_emoji = get_status_emoji(overall_status)
    st.markdown(f"## Overall System Status: {overall_emoji} {overall_status.upper()}")
    
    if "timestamp" in data:
        st.write("Last Updated:", data["timestamp"])
    
    st.write("---")
    
    services = data.get("results", [])
    if services:
        if view_option == "Table view":
            services_list = []
            for service in services:
                status = service.get("status", "unknown")
                emoji = get_status_emoji(status)
                services_list.append({
                    "Name": service.get("name", "Unnamed Service"),
                    "Status": f"{emoji} {status}",
                    "Description": service.get("description") or "N/A",
                    "Tags": ", ".join(service.get("tags", []))
                })
            df = pd.DataFrame(services_list)
            st.dataframe(df)
        else:
            for service in services:
                display_service_card_html(service)
    else:
        st.write("No service details found in the monitor data.")
    
    st.write("---")
    
    # --- Kafka Lag Data with Progress Bar ---
    st.markdown("## Kafka Lag Information")
    kafka_base_url = st.secrets["kafka_lag_base_url"]
    kafka_lag_list = []
    kafka_debug_info = []  # For debugging purposes
    
    # Create a progress bar for Kafka endpoints.
    progress_bar = st.progress(0)
    total_endpoints = 16
    
    # Loop through endpoints 1 to 16.
    for i in range(1, total_endpoints + 1):
        url_kafka = f"{kafka_base_url}{i}"
        kafka_response = fetch_data(url_kafka)
        if kafka_response:
            topic = kafka_response.get("topic", "Unknown")
            lag = kafka_response.get("lag", "N/A")
            debug_message = f"Endpoint {i} OK"
        else:
            topic = f"Endpoint {i}"
            lag = "Error"
            debug_message = f"Endpoint {i} returned error"
        kafka_lag_list.append({"Topic": topic, "Lag": lag})
        kafka_debug_info.append({
            "Endpoint": i,
            "URL": url_kafka,
            "Response": kafka_response if kafka_response else "Error",
            "Message": debug_message
        })
        progress_bar.progress(i / total_endpoints)
    
    df_kafka = pd.DataFrame(kafka_lag_list)
    st.dataframe(df_kafka)
    
    with st.expander("Kafka Endpoints Debug Info"):
        st.json(kafka_debug_info)
    

if __name__ == "__main__":
    main()
