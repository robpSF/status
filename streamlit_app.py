import streamlit as st
import requests
import pandas as pd

# Configure the page
st.set_page_config(page_title="Heartz Monitor Dashboard", layout="wide")

def get_status_color(status):
    """
    Return a colourblind-friendly hex color based on the service status.
    Uses an Okabe–Ito-inspired palette:
      - Blue (#0072B2) for healthy/up statuses,
      - Orange (#E69F00) for warnings,
      - Vermilion (#D55E00) for errors,
      - Grey for unknown statuses.
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
        st.error(f"Error fetching data: {e}")
        return None

def display_service_card_html(service):
    """
    Display a single service's details as a card using inline HTML.
    This function uses st.markdown with unsafe_allow_html=True.
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
    
    # Default view is Table view.
    view_option = st.sidebar.radio("Select view", ("Table view", "Card view"))
    
    url = "https://monitor.conducttr.com/heartz?detailed=true"
    with st.spinner("Fetching data..."):
        data = fetch_data(url)
    
    if data is None:
        st.error("Failed to fetch data. Please try again later.")
        return

    # Debug: Expand to show the raw JSON (optional)
    with st.expander("Show raw JSON (Debug)"):
        st.json(data)
    
    # Display overall system status.
    overall_status = data.get("status", "unknown")
    overall_emoji = get_status_emoji(overall_status)
    st.markdown(f"## Overall System Status: {overall_emoji} {overall_status.upper()}")
    
    if "timestamp" in data:
        st.write("Last Updated:", data["timestamp"])
    
    st.write("---")
    
    # Extract service details from the "results" key.
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
            # Card view: Render each service using the HTML-based card.
            for service in services:
                display_service_card_html(service)
    else:
        st.write("No service details found in the data.")
    
    # Refresh button to re-run the app and fetch updated data.
    if st.button("Refresh Data"):
        st.experimental_rerun()

if __name__ == "__main__":
    main()

