
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Civic Complaint Analytics",
    page_icon="🏙️",
    layout="wide"
)

# Load datasets
@st.cache_data
def load_data():
    complaints = pd.read_csv("complaints.csv", parse_dates=["created_at"])
    events = pd.read_csv("status_events.csv", parse_dates=["event_time"])
    df = pd.read_csv(
        "complaint_metrics.csv",
        parse_dates=["created_at", "first_response_at",
                     "last_updated", "resolution_time"]
    )
    return complaints, events, df

complaints, events, df = load_data()

# Dashboard title
st.title("🏙️ Civic Complaint SLA & Resolution Analytics")
st.caption("Municipal Complaint Monitoring and Performance Dashboard")

# Sidebar filters
st.sidebar.header("Dashboard Filters")

wards = sorted(df["ward"].dropna().unique().tolist())
categories = sorted(df["category"].dropna().unique().tolist())
departments = sorted(df["department"].dropna().unique().tolist())
statuses = sorted(df["latest_status"].dropna().unique().tolist())

selected_wards = st.sidebar.multiselect(
    "Select Ward", wards, default=wards
)
selected_categories = st.sidebar.multiselect(
    "Select Category", categories, default=categories
)
selected_departments = st.sidebar.multiselect(
    "Select Department", departments, default=departments
)
selected_statuses = st.sidebar.multiselect(
    "Select Complaint Status", statuses, default=statuses
)

# Apply filters
filtered = df[
    df["ward"].isin(selected_wards) &
    df["category"].isin(selected_categories) &
    df["department"].isin(selected_departments) &
    df["latest_status"].isin(selected_statuses)
].copy()

# Convert boolean columns safely
for col in ["is_open", "response_sla_met", "resolution_sla_met"]:
    filtered[col] = filtered[col].astype(str).str.lower().eq("true")

# KPI calculations
total = len(filtered)
open_cases = int(filtered["is_open"].sum())
resolved = total - open_cases

response_data = filtered.dropna(subset=["first_response_hours"])
resolution_data = filtered.dropna(subset=["resolution_hours"])

avg_response = response_data["first_response_hours"].mean()
avg_resolution = resolution_data["resolution_hours"].mean()

response_sla = (
    response_data["response_sla_met"].mean() * 100
    if len(response_data) else 0
)
resolution_sla = (
    resolution_data["resolution_sla_met"].mean() * 100
    if len(resolution_data) else 0
)

# KPI cards
st.subheader("📊 Overall Performance")

c1, c2, c3 = st.columns(3)
c1.metric("Total Complaints", total)
c2.metric("Open Backlog", open_cases)
c3.metric("Resolved Complaints", resolved)

c4, c5, c6 = st.columns(3)
c4.metric(
    "Average First Response",
    f"{avg_response:.2f} hrs" if pd.notna(avg_response) else "N/A"
)
c5.metric(
    "Average Resolution Time",
    f"{avg_resolution:.2f} hrs" if pd.notna(avg_resolution) else "N/A"
)
c6.metric("Response SLA Compliance", f"{response_sla:.1f}%")

st.metric("Resolution SLA Compliance", f"{resolution_sla:.1f}%")

st.divider()

# Charts
st.subheader("📈 Complaint Analytics")

left, right = st.columns(2)

with left:
    status_counts = filtered["latest_status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    fig = px.pie(
        status_counts,
        names="Status",
        values="Count",
        title="Complaint Status Distribution",
        hole=0.4
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    ward_data = filtered.groupby("ward").size().reset_index(name="Complaints")

    fig = px.bar(
        ward_data,
        x="ward",
        y="Complaints",
        title="Complaints by Ward",
        color="ward"
    )
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    category_data = filtered.groupby("category").size().reset_index(name="Complaints")

    fig = px.bar(
        category_data,
        x="category",
        y="Complaints",
        title="Complaints by Category",
        color="category"
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    dept_data = filtered.groupby("department").size().reset_index(name="Complaints")

    fig = px.bar(
        dept_data,
        x="department",
        y="Complaints",
        title="Complaints by Department",
        color="department"
    )
    st.plotly_chart(fig, use_container_width=True)

# SLA analysis
st.subheader("⏱️ SLA Performance")

sla_data = pd.DataFrame({
    "SLA Type": ["First Response", "Resolution"],
    "Compliance (%)": [response_sla, resolution_sla]
})

fig = px.bar(
    sla_data,
    x="SLA Type",
    y="Compliance (%)",
    color="SLA Type",
    range_y=[0, 100],
    title="SLA Compliance Overview"
)
st.plotly_chart(fig, use_container_width=True)

# Complaint explorer
st.divider()
st.subheader("🔍 Complaint Explorer")

search_id = st.text_input("Search Complaint ID")

case_data = filtered.copy()

if search_id.strip():
    case_data = case_data[
        case_data["complaint_id"].astype(str).str.contains(
            search_id.strip(), case=False, na=False
        )
    ]

st.dataframe(case_data, use_container_width=True, hide_index=True)

# Complaint history
st.subheader("📋 Individual Complaint History")

if not case_data.empty:
    available_ids = sorted(
        case_data["complaint_id"].dropna().unique().tolist()
    )
    selected_id = st.selectbox("Select Complaint ID", available_ids)

    selected_history = events[
        events["complaint_id"] == selected_id
    ].sort_values("event_time")

    st.write(f"Status timeline for Complaint {selected_id}")
    st.dataframe(selected_history, use_container_width=True, hide_index=True)
else:
    st.info("No matching complaints found.")

# Download filtered records
st.subheader("📥 Export Data")

csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Filtered Complaint Data",
    data=csv_data,
    file_name="filtered_complaints.csv",
    mime="text/csv"
)

st.caption(
    "Project demonstration data | First-response SLA: 4 hours | "
    "Resolution SLA: 48 hours"
)
