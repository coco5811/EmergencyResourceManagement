import streamlit as st
import pandas as pd
import plotly.express as px

# Backend imports from src package
from src.incident_manager import (
    register_incident, get_all_incidents, filter_incidents, update_incident_status
)
from src.resource_manager import (
    get_all_resources, get_available_resources, filter_resources,
    add_resource, allocate_resource, release_allocation, get_allocations
)
from src.analytics import (
    get_incident_summary, get_resource_summary,
    get_resource_usage_by_type, get_resources_by_hospital, get_resources_by_location
)

# Page configuration
st.set_page_config(page_title="Emergency Resource Management System", layout="wide")
st.title("🚨 Emergency Resource Management System")

# Navigation Sidebar
navigation = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Incident Management", "Resource Management", "Resource Allocation", "Reports & Analytics"]
)

# =========================================================
# 1. DASHBOARD SCREEN
# =========================================================
if navigation == "Dashboard":
    st.header("📊 Executive Dashboard")
    
    try:
        inc_summary = get_incident_summary()
        res_summary = get_resource_summary()
        
        # KPI Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Incidents", inc_summary.get("total_incidents", 0))
        col2.metric("Active Incidents", inc_summary.get("active_incidents", 0))
        col3.metric("High/Critical Incidents", inc_summary.get("high_critical_incidents", 0))
        col4.metric("Available Resources", f"{res_summary.get('available_resources', 0)} / {res_summary.get('total_resources', 0)}")
        
        st.divider()
        
        # Plotly Chart: Resource Usage by Type
        st.subheader("Resource Usage by Type")
        usage_data = get_resource_usage_by_type()
        if usage_data:
            df_usage = pd.DataFrame(usage_data)
            fig = px.bar(
                df_usage, 
                x="resource_type", 
                y=["available_quantity", "in_use_quantity"],
                title="Available vs In-Use Quantities",
                labels={"value": "Quantity", "resource_type": "Resource Type", "variable": "Status"},
                barmode="stack"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No resource data available.")

    except Exception as e:
        st.error(f"Error loading dashboard metrics: {e}")

# =========================================================
# 2. INCIDENT MANAGEMENT SCREEN
# =========================================================
elif navigation == "Incident Management":
    st.header("🚨 Incident Management")
    
    tab1, tab2, tab3 = st.tabs(["View & Filter Incidents", "Register Incident", "Update Incident Status"])
    
    with tab1:
        st.subheader("Filter Incidents")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            sev_filter = st.selectbox("Severity", ["All", "Low", "Medium", "High", "Critical"])
        with col_f2:
            stat_filter = st.selectbox("Status", ["All", "Reported", "In Progress", "Resolved", "Cancelled"])
            
        sev = None if sev_filter == "All" else sev_filter
        stat = None if stat_filter == "All" else stat_filter
        
        incidents = filter_incidents(severity=sev, status=stat)
        if incidents:
            st.dataframe(pd.DataFrame(incidents), use_container_width=True)
        else:
            st.info("No incidents found matching the selected filters.")

    with tab2:
        st.subheader("Register New Emergency Incident")
        with st.form("register_incident_form"):
            inc_type = st.text_input("Incident Type (e.g. Road Accident, Structure Fire)")
            loc = st.text_input("Location")
            sev = st.selectbox("Severity Level", ["Low", "Medium", "High", "Critical"], index=1)
            desc = st.text_area("Description (Optional)")
            
            if st.form_submit_button("Register Incident"):
                if not inc_type or not loc:
                    st.warning("Incident Type and Location are required.")
                else:
                    try:
                        new_id = register_incident(inc_type, loc, severity=sev, description=desc)
                        st.success(f"Incident registered successfully! Allocated ID: **{new_id}**")
                    except Exception as err:
                        st.error(f"Failed to register incident: {err}")

    with tab3:
        st.subheader("Update Status of Existing Incident")
        with st.form("update_status_form"):
            inc_id = st.number_input("Incident ID", min_value=1, step=1)
            new_status = st.selectbox("New Status", ["Reported", "In Progress", "Resolved", "Cancelled"])
            
            if st.form_submit_button("Update Status"):
                try:
                    updated = update_incident_status(int(inc_id), new_status)
                    st.success(f"Incident {inc_id} updated to status: **{new_status}**")
                except ValueError as err:
                    st.error(str(err))

# =========================================================
# 3. RESOURCE MANAGEMENT SCREEN
# =========================================================
elif navigation == "Resource Management":
    st.header("📦 Resource Inventory")
    
    tab1, tab2 = st.tabs(["Search Inventory", "Add New Resource"])
    
    with tab1:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            type_filter = st.selectbox("Resource Type", ["All", "Ambulance", "Hospital Bed", "Medical Supply", "Personnel", "Rescue Equipment"])
        with col_r2:
            loc_search = st.text_input("Filter Location Substring")
            
        r_type = None if type_filter == "All" else type_filter
        r_loc = loc_search if loc_search.strip() else None
        
        resources = filter_resources(resource_type=r_type, location=r_loc)
        if resources:
            st.dataframe(pd.DataFrame(resources), use_container_width=True)
        else:
            st.info("No resources found matching criteria.")
            
    with tab2:
        st.subheader("Add Resource Entry")
        with st.form("add_resource_form"):
            res_name = st.text_input("Resource Name (e.g. ICU Bed, Type A Ambulance)")
            res_type = st.selectbox("Resource Type", ["Ambulance", "Hospital Bed", "Medical Supply", "Personnel", "Rescue Equipment"])
            total_q = st.number_input("Total Quantity", min_value=1, value=5)
            res_loc = st.text_input("Storage Location")
            hosp_id = st.number_input("Hospital ID (Optional, 0 for None)", min_value=0, value=0)
            
            if st.form_submit_button("Add Resource"):
                if not res_name or not res_loc:
                    st.warning("Resource Name and Location are required.")
                else:
                    try:
                        h_id = int(hosp_id) if hosp_id > 0 else None
                        r_id = add_resource(res_name, res_type, int(total_q), res_loc, hospital_id=h_id)
                        st.success(f"Resource added successfully! New Resource ID: **{r_id}**")
                    except Exception as err:
                        st.error(f"Failed to add resource: {err}")

# =========================================================
# 4. RESOURCE ALLOCATION SCREEN
# =========================================================
elif navigation == "Resource Allocation":
    st.header("🔄 Resource Allocation & Release")
    
    col_alloc, col_release = st.columns(2)
    
    with col_alloc:
        st.subheader("Allocate Resource to Incident")
        with st.form("allocate_form"):
            inc_id = st.number_input("Incident ID", min_value=1, step=1)
            res_id = st.number_input("Resource ID", min_value=1, step=1)
            qty = st.number_input("Quantity Required", min_value=1, value=1)
            
            if st.form_submit_button("Submit Allocation"):
                try:
                    alloc_id = allocate_resource(int(inc_id), int(res_id), int(qty))
                    st.success(f"Allocation Successful! Allocation ID: **{alloc_id}**")
                except ValueError as err:
                    st.error(f"Allocation Denied: {err}")

    with col_release:
        st.subheader("Release Active Allocation")
        with st.form("release_form"):
            target_alloc_id = st.number_input("Allocation ID to Release", min_value=1, step=1)
            
            if st.form_submit_button("Release Allocation"):
                try:
                    res = release_allocation(int(target_alloc_id))
                    st.success(f"Allocation **{target_alloc_id}** released! Restored **{res['quantity_restored']}** unit(s).")
                except (ValueError, RuntimeError) as err:
                    st.error(f"Release Failed: {err}")
                    
    st.divider()
    st.subheader("Allocation History")
    allocations = get_allocations()
    if allocations:
        st.dataframe(pd.DataFrame(allocations), use_container_width=True)
    else:
        st.info("No active or past allocation records.")

# =========================================================
# 5. REPORTS & ANALYTICS SCREEN
# =========================================================
elif navigation == "Reports & Analytics":
    st.header("📈 System Reports & Location Analytics")
    
    tab_hosp, tab_loc = st.tabs(["Hospital Breakdown", "Location Breakdown"])
    
    with tab_hosp:
        st.subheader("Resources Grouped by Hospital")
        hosp_data = get_resources_by_hospital()
        if hosp_data:
            df_hosp = pd.DataFrame(hosp_data)
            st.dataframe(df_hosp, use_container_width=True)
            
            fig_hosp = px.bar(
                df_hosp, 
                x="hospital_name", 
                y=["total_quantity", "available_quantity"],
                title="Hospital Resource Capacity",
                barmode="group"
            )
            st.plotly_chart(fig_hosp, use_container_width=True)
        else:
            st.info("No hospital breakdown data available.")
            
    with tab_loc:
        st.subheader("Resources Grouped by Location & Type")
        loc_data = get_resources_by_location()
        if loc_data:
            st.dataframe(pd.DataFrame(loc_data), use_container_width=True)
        else:
            st.info("No location breakdown data available.")
