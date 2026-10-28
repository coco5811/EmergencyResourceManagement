import streamlit as st
import pandas as pd
import plotly.express as px

from src.incident_manager import (
    register_incident, get_all_incidents, get_incident_by_id,
    filter_incidents, update_incident_status,
)
from src.resource_manager import (
    get_all_resources, get_available_resources, filter_resources,
    add_resource, allocate_resource, release_allocation, get_allocations,
)
from src.analytics import (
    get_incident_summary, get_resource_summary, get_resource_usage_by_type,
    get_resources_by_hospital, get_resources_by_location,
)
from src.operation_service import (
    create_incident_with_event, update_incident_status_with_event,
    allocate_resource_with_event, release_allocation_with_event,
)
from src.mongo_manager import get_incident_history, get_recent_events, aggregate_events_by_type

st.set_page_config(page_title="Emergency Resource Management", page_icon="🚨", layout="wide")

# Custom CSS for Modern Minimalist Analytics Dashboard Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Typography Hierarchy */
    h1, h2, h3 {
        font-weight: 700 !important;
        color: #2C3E50 !important; /* Slate gray */
    }
    
    /* Card Styling */
    div[data-testid="stMetric"], div.stForm, div[data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); /* 5% faint shadow */
        border: none;
    }
    
    /* Metric Typography */
    div[data-testid="stMetricValue"] {
        font-weight: 700;
        color: #C35A42; /* Terracotta */
    }
    
    div[data-testid="stMetricLabel"] {
        font-weight: 500;
        color: #6C7A89; /* Lighter gray for secondary labels */
    }
</style>
""", unsafe_allow_html=True)

st.title("🚨 Emergency Resource Management System")
st.caption("Academic demo using MySQL for operational records and MongoDB for event history.")

role = st.sidebar.radio("Choose view", ["User View", "Dispatcher View"], help="Role selection is for demonstration only; it is not secure authentication.")
st.sidebar.divider()

def apply_chart_theme(fig):
    """Applies flat styling, muted secondary colors, and removes glowing/3D effects."""
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="Inter",
        font_color="#373D3F",
        margin=dict(t=40, b=40, l=40, r=40)
    )
    fig.update_xaxes(showgrid=False, linecolor="#E0E0E0")
    fig.update_yaxes(showgrid=True, gridcolor="#F0F0F0", linecolor="#E0E0E0")
    return fig

def show_df(rows, empty_message):
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)

def show_event_history(incident_id):
    result = get_incident_history(int(incident_id))
    if result.get("ok") and result.get("events"):
        events = result["events"]
        for item in events:
            if item.get("timestamp"):
                item["timestamp"] = str(item["timestamp"])
        st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
    elif not result.get("ok"):
        st.warning("Event history is unavailable. Check MongoDB configuration and connection.")
    else:
        st.info("No event history has been recorded for this incident yet.")

if role == "User View":
    st.header("👤 Public / User Portal")
    st.write("Report an emergency incident and use its incident ID to check the current status.")
    report_tab, track_tab = st.tabs(["Report an Incident", "Track an Incident"])

    with report_tab:
        with st.form("user_report_incident", clear_on_submit=True):
            incident_type = st.selectbox("Incident type", ["Road Accident", "Medical Emergency", "Fire", "Flood", "Building Collapse", "Other"])
            if incident_type == "Other":
                incident_type = st.text_input("Specify incident type")
            location = st.text_input("Location / address")
            severity = st.select_slider("Severity", options=["Low", "Medium", "High", "Critical"], value="Medium")
            description = st.text_area("Additional details (optional)", max_chars=2000)
            submitted = st.form_submit_button("Submit Emergency Report", type="primary")
        if submitted:
            if not str(incident_type).strip() or not location.strip():
                st.error("Please provide an incident type and location.")
            else:
                try:
                    result = create_incident_with_event(str(incident_type).strip(), location.strip(), severity, description.strip() or None)
                    st.success(f"Report submitted. Your incident ID is **{result['incident_id']}**. Save this ID to track updates.")
                    if not result.get("log_status", {}).get("ok"):
                        st.warning("The report was saved, but the event history service is currently unavailable.")
                except Exception as exc:
                    st.error(f"Could not submit report: {exc}")

    with track_tab:
        incident_id = st.number_input("Incident ID", min_value=1, step=1, key="user_track_id")
        if st.button("Check Status", type="primary"):
            try:
                incident = get_incident_by_id(int(incident_id))
                if not incident:
                    st.error("No incident found with that ID.")
                else:
                    st.subheader(f"Incident #{incident['incident_id']}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Status", incident.get("status", "Unknown"))
                    c2.metric("Severity", incident.get("severity", "Unknown"))
                    c3.metric("Type", incident.get("incident_type", "Unknown"))
                    st.write(f"**Location:** {incident.get('location', 'Not recorded')}")
                    st.write(f"**Description:** {incident.get('description') or 'No additional details'}")
                    st.write("**Event history**")
                    show_event_history(int(incident_id))
            except Exception as exc:
                st.error(f"Could not retrieve incident: {exc}")

else:
    st.header("🧭 Dispatcher Console")
    page = st.sidebar.radio("Dispatcher tools", ["Dashboard", "Incidents", "Resources", "Allocations", "Reports & Analytics", "Event History"])

    if page == "Dashboard":
        try:
            inc = get_incident_summary()
            res = get_resource_summary()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Incidents", inc.get("total_incidents", 0))
            c2.metric("Active Incidents", inc.get("active_incidents", 0))
            c3.metric("High / Critical", inc.get("high_critical_incidents", 0))
            c4.metric("Available Resources", f"{res.get('available_resources', 0)} / {res.get('total_resources', 0)}")
            
            st.subheader("Resource availability by type")
            usage = get_resource_usage_by_type()
            if usage:
                df = pd.DataFrame(usage)
                # Apply secondary accent colors (Muted Sage Green & Deep Maroon)
                fig = px.bar(df, x="resource_type", y=["available_quantity", "in_use_quantity"], 
                             barmode="stack", title="Available vs in-use quantities",
                             color_discrete_sequence=["#8FA896", "#8A3324"]) 
                fig = apply_chart_theme(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No resource data available.")
                
            st.subheader("Recent incidents")
            show_df(get_all_incidents()[:10], "No incidents have been reported.")
        except Exception as exc:
            st.error(f"Dashboard could not load: {exc}")

    elif page == "Incidents":
        view_tab, create_tab, status_tab = st.tabs(["View / Filter", "Register Incident", "Update Status"])
        with view_tab:
            c1, c2 = st.columns(2)
            severity = c1.selectbox("Severity", ["All", "Low", "Medium", "High", "Critical"])
            status = c2.selectbox("Status", ["All", "Reported", "In Progress", "Resolved", "Cancelled"])
            try:
                show_df(filter_incidents(None if severity == "All" else severity, None if status == "All" else status), "No incidents match these filters.")
            except Exception as exc:
                st.error(str(exc))
        with create_tab:
            with st.form("dispatcher_create_incident"):
                incident_type = st.text_input("Incident type")
                location = st.text_input("Location")
                severity = st.selectbox("Severity level", ["Low", "Medium", "High", "Critical"], index=1)
                description = st.text_area("Description")
                submit = st.form_submit_button("Register incident")
            if submit:
                try:
                    result = create_incident_with_event(incident_type, location, severity, description or None)
                    st.success(f"Incident created: #{result['incident_id']}")
                    if not result["log_status"].get("ok"):
                        st.warning("Saved to MySQL, but MongoDB logging failed.")
                except Exception as exc:
                    st.error(str(exc))
        with status_tab:
            with st.form("dispatcher_update_status"):
                incident_id = st.number_input("Incident ID", min_value=1, step=1)
                new_status = st.selectbox("New status", ["Reported", "In Progress", "Resolved", "Cancelled"])
                submit = st.form_submit_button("Update status")
            if submit:
                try:
                    result = update_incident_status_with_event(int(incident_id), new_status)
                    st.success(f"Incident #{incident_id} status updated to {new_status}.")
                    if not result["log_status"].get("ok"):
                        st.warning("Status saved to MySQL, but MongoDB logging failed.")
                except Exception as exc:
                    st.error(str(exc))

    elif page == "Resources":
        inv_tab, add_tab = st.tabs(["Inventory", "Add Resource"])
        with inv_tab:
            c1, c2 = st.columns(2)
            resource_type = c1.selectbox("Resource type", ["All", "Ambulance", "Hospital Bed", "Medical Supply", "Personnel", "Rescue Equipment"])
            location = c2.text_input("Location contains")
            try:
                show_df(filter_resources(None if resource_type == "All" else resource_type, location.strip() or None), "No resources match these filters.")
            except Exception as exc:
                st.error(str(exc))
        with add_tab:
            with st.form("add_resource"):
                name = st.text_input("Resource name")
                kind = st.selectbox("Resource type", ["Ambulance", "Hospital Bed", "Medical Supply", "Personnel", "Rescue Equipment"])
                total = st.number_input("Total quantity", min_value=1, value=1)
                location = st.text_input("Storage location")
                hospital_id = st.number_input("Hospital ID (0 for none)", min_value=0, value=0)
                submit = st.form_submit_button("Add resource")
            if submit:
                try:
                    new_id = add_resource(name, kind, int(total), location, hospital_id=int(hospital_id) or None)
                    st.success(f"Resource added. ID: {new_id}")
                except Exception as exc:
                    st.error(str(exc))

    elif page == "Allocations":
        alloc_tab, release_tab, history_tab = st.tabs(["Allocate", "Release", "Allocation History"])
        with alloc_tab:
            with st.form("allocate_resource"):
                incident_id = st.number_input("Incident ID", min_value=1, step=1)
                resource_id = st.number_input("Resource ID", min_value=1, step=1)
                quantity = st.number_input("Quantity", min_value=1, value=1)
                submit = st.form_submit_button("Allocate resource")
            if submit:
                try:
                    result = allocate_resource_with_event(int(incident_id), int(resource_id), int(quantity))
                    st.success(f"Allocation created: #{result['allocation_id']}")
                    if not result["log_status"].get("ok"):
                        st.warning("Allocation saved to MySQL, but MongoDB logging failed.")
                except Exception as exc:
                    st.error(str(exc))
        with release_tab:
            with st.form("release_resource"):
                allocation_id = st.number_input("Allocation ID", min_value=1, step=1)
                submit = st.form_submit_button("Release allocation")
            if submit:
                try:
                    result = release_allocation_with_event(int(allocation_id))
                    st.success(f"Allocation released; restored {result['quantity_restored']} unit(s).")
                    if not result["log_status"].get("ok"):
                        st.warning("Release saved to MySQL, but MongoDB logging failed.")
                except Exception as exc:
                    st.error(str(exc))
        with history_tab:
            try:
                show_df(get_allocations(), "No allocation records found.")
            except Exception as exc:
                st.error(str(exc))

    elif page == "Reports & Analytics":
        hosp_tab, loc_tab = st.tabs(["By Hospital", "By Location"])
        with hosp_tab:
            try:
                rows = get_resources_by_hospital()
                show_df(rows, "No hospital resource data available.")
                if rows:
                    df = pd.DataFrame(rows)
                    if "hospital_name" in df.columns and "total_quantity" in df.columns:
                        fig = px.bar(df, x="hospital_name", y="total_quantity", title="Resource quantity by hospital", color_discrete_sequence=["#C35A42"])
                        fig = apply_chart_theme(fig)
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as exc:
                st.error(str(exc))
        with loc_tab:
            try:
                rows = get_resources_by_location()
                show_df(rows, "No location resource data available.")
                if rows:
                    df = pd.DataFrame(rows)
                    fig = px.bar(df, x=df.columns[0], y=df.columns[-1], title="Resources by location", color_discrete_sequence=["#3A7371"]) # Muted Teal
                    fig = apply_chart_theme(fig)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as exc:
                st.error(str(exc))

    elif page == "Event History":
        recent_tab, incident_tab, aggregate_tab = st.tabs(["Recent Events", "Incident History", "Event Summary"])
        with recent_tab:
            try:
                result = get_recent_events(100)
                if result.get("ok"):
                    rows = result.get("events", [])
                    for item in rows:
                        if item.get("timestamp"):
                            item["timestamp"] = str(item["timestamp"])
                    show_df(rows, "No events have been logged yet.")
                else:
                    st.warning("MongoDB is unavailable: " + result.get("error", "unknown error"))
            except Exception as exc:
                st.warning(f"MongoDB event history unavailable: {exc}")
        with incident_tab:
            incident_id = st.number_input("Incident ID to inspect", min_value=1, step=1, key="dispatcher_history_id")
            if st.button("Load incident events"):
                show_event_history(int(incident_id))
        with aggregate_tab:
            try:
                result = aggregate_events_by_type()
                if result.get("ok"):
                    show_df(result.get("results", []), "No event summary available.")
                else:
                    st.warning("MongoDB is unavailable: " + result.get("error", "unknown error"))
            except Exception as exc:
                st.warning(f"MongoDB event summary unavailable: {exc}")

st.sidebar.caption("Demo only — not for real emergency dispatch. Role selection is not authentication.")
