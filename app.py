"""TeamSync AI — AI-powered team collaboration platform.

Solves: Team coordination and communication challenges by providing
smart standups, simplified task workflows, and real-time visibility.
"""

import streamlit as st
import pandas as pd

from config import APP_NAME, APP_DESCRIPTION, validate_config
from core import (
    validate_input,
    validate_task,
    sanitize_text,
    generate_standup,
    analyze_blockers,
    create_task_from_text,
    get_team_metrics,
    SAMPLE_TASKS,
)
from firestore_client import save_task, get_all_tasks, generate_task_id

# --- Validate environment on startup ---
try:
    validate_config()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()

# --- Page Configuration (Accessibility: proper title) ---
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤝",
    layout="wide",
)

# --- Initialize Session State ---
if "tasks" not in st.session_state:
    # Try Firestore first, fall back to sample data
    firestore_tasks = get_all_tasks()
    st.session_state.tasks = firestore_tasks if firestore_tasks else list(SAMPLE_TASKS)

if "team_members" not in st.session_state:
    st.session_state.team_members = list({
        t["assignee"] for t in st.session_state.tasks if t.get("assignee")
    })


def _get_tasks() -> list:
    """Get current task list from session state."""
    return st.session_state.tasks


def _add_task(task: dict) -> None:
    """Add a task to session state and attempt Firestore persistence."""
    task["id"] = generate_task_id()
    st.session_state.tasks.append(task)
    save_task(task)  # Best-effort Firestore save


# --- Accessible Heading Hierarchy ---
st.title(f"🤝 {APP_NAME}")
st.caption(APP_DESCRIPTION)

# --- Navigation Tabs ---
tab_board, tab_standup, tab_dashboard = st.tabs([
    "📋 Task Board",
    "🤖 AI Standup",
    "📊 Dashboard",
])


# ============================================================
# TAB 1: Smart Task Board
# ============================================================
with tab_board:
    st.header("📋 Smart Task Board")
    st.caption("Manage tasks and create new ones using natural language.")

    # --- Natural Language Task Creation ---
    st.subheader("✨ Create Task with AI")
    nl_input = st.text_input(
        "Describe your task in plain English:",
        placeholder='e.g. "Assign a high-priority bug to Meena about payment timeouts"',
        key="nl_task_input",
    )

    if st.button("🪄 Create Task", key="btn_create_task"):
        if nl_input:
            with st.spinner("AI is parsing your task..."):
                new_task = create_task_from_text(
                    nl_input, st.session_state.team_members
                )
            if "error" in new_task:
                st.error(new_task["error"])
            else:
                _add_task(new_task)
                st.success(f"✅ Created: **{new_task['title']}** → {new_task['assignee']}")
        else:
            st.warning("Please enter a task description.")

    st.divider()

    # --- Task Filters ---
    st.subheader("🔍 Filter Tasks")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    with col_filter1:
        filter_status = st.multiselect(
            "Status", options=["todo", "in_progress", "done"],
            default=["todo", "in_progress", "done"],
        )
    with col_filter2:
        filter_priority = st.multiselect(
            "Priority", options=["critical", "high", "medium", "low"],
            default=["critical", "high", "medium", "low"],
        )
    with col_filter3:
        filter_assignee = st.multiselect(
            "Assignee", options=st.session_state.team_members,
            default=st.session_state.team_members,
        )

    # --- Filtered Task Table ---
    tasks = _get_tasks()
    filtered = [
        t for t in tasks
        if t.get("status") in filter_status
        and t.get("priority") in filter_priority
        and t.get("assignee") in filter_assignee
    ]

    if filtered:
        df = pd.DataFrame(filtered)
        display_cols = ["id", "title", "assignee", "status", "priority", "due_date", "blockers"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(
            df[available_cols],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Showing {len(filtered)} of {len(tasks)} tasks.")
    else:
        st.info("No tasks match the current filters.")

    # --- Manual Task Add (Accessible fallback) ---
    with st.expander("➕ Add Task Manually"):
        with st.form("manual_task_form"):
            m_title = st.text_input("Title", key="manual_title")
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                m_assignee = st.selectbox(
                    "Assignee", st.session_state.team_members, key="manual_assignee",
                )
                m_priority = st.selectbox(
                    "Priority", ["low", "medium", "high", "critical"], index=1,
                    key="manual_priority",
                )
            with m_col2:
                m_status = st.selectbox(
                    "Status", ["todo", "in_progress", "done"], key="manual_status",
                )
                m_due = st.date_input("Due Date", key="manual_due")
            m_blockers = st.text_input("Blockers (if any)", key="manual_blockers")
            submitted = st.form_submit_button("Add Task")

            if submitted and m_title:
                is_valid, error = validate_task({
                    "title": m_title, "status": m_status, "priority": m_priority,
                })
                if not is_valid:
                    st.error(error)
                else:
                    new_manual = {
                        "title": sanitize_text(m_title),
                        "assignee": m_assignee,
                        "status": m_status,
                        "priority": m_priority,
                        "due_date": str(m_due),
                        "blockers": sanitize_text(m_blockers),
                        "tags": [],
                    }
                    _add_task(new_manual)
                    st.success(f"✅ Added: {m_title}")


# ============================================================
# TAB 2: AI Standup Generator
# ============================================================
with tab_standup:
    st.header("🤖 AI Standup Generator")
    st.caption(
        "Generate a smart daily standup summary from your team's tasks. "
        "AI analyzes workload, blockers, and priorities."
    )

    if st.button("🚀 Generate Today's Standup", key="btn_standup"):
        with st.spinner("AI is analyzing your team's tasks..."):
            standup = generate_standup(_get_tasks())

        # Team Summary
        st.subheader("📝 Team Summary")
        st.info(standup.get("team_summary", "No summary available."))

        # Per-member Updates
        st.subheader("👥 Member Updates")
        for update in standup.get("member_updates", []):
            st.markdown(f"**{update['name']}**: {update['summary']}")

        # Blocker Alerts
        blockers = standup.get("blockers_alert", [])
        if blockers:
            st.subheader("🚨 Blocker Alerts")
            for b in blockers:
                st.warning(b)
        st.caption("Standup generated by Gemini AI based on current task data.")

    st.divider()

    # --- Blocker Resolution ---
    st.subheader("🔧 AI Blocker Resolution")
    st.caption("Get AI-suggested actions to unblock your team.")

    if st.button("Analyze Blockers", key="btn_blockers"):
        with st.spinner("Analyzing blockers..."):
            suggestions = analyze_blockers(_get_tasks())
        if not suggestions:
            st.success("🎉 No blockers found! Team is unblocked.")
        else:
            for s in suggestions:
                with st.container():
                    st.markdown(f"**Task {s.get('task_id', '?')}** — {s.get('blocker', '')}")
                    st.markdown(f"💡 **Suggestion:** {s.get('suggestion', '')}")
                    st.divider()
            st.caption("Suggestions generated by Gemini AI.")


# ============================================================
# TAB 3: Team Dashboard
# ============================================================
with tab_dashboard:
    st.header("📊 Team Dashboard")
    st.caption("Real-time visibility into your team's workflow and workload.")

    metrics = get_team_metrics(_get_tasks())

    # --- Top-level Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tasks", metrics["total_tasks"])
    with col2:
        st.metric("Completion Rate", f"{metrics['completion_rate']}%")
    with col3:
        st.metric("Blocked", metrics["blocked_count"])
    with col4:
        st.metric("Overdue", metrics["overdue_count"])

    st.divider()

    # --- Charts ---
    import plotly.express as px

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Task Status Breakdown")
        status_data = metrics["by_status"]
        if status_data:
            fig_status = px.pie(
                names=list(status_data.keys()),
                values=list(status_data.values()),
                title="Tasks by Status",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            st.plotly_chart(fig_status, use_container_width=True)
            st.caption("Distribution of tasks across todo, in-progress, and done statuses.")
        else:
            st.info("No task data available.")

    with chart_col2:
        st.subheader("Priority Distribution")
        priority_data = metrics["by_priority"]
        if priority_data:
            fig_priority = px.bar(
                x=list(priority_data.keys()),
                y=list(priority_data.values()),
                title="Tasks by Priority",
                labels={"x": "Priority", "y": "Count"},
                color=list(priority_data.keys()),
                color_discrete_map={
                    "critical": "#ef4444",
                    "high": "#f97316",
                    "medium": "#eab308",
                    "low": "#22c55e",
                },
            )
            st.plotly_chart(fig_priority, use_container_width=True)
            st.caption("Number of tasks at each priority level. Red = critical.")
        else:
            st.info("No priority data available.")

    # --- Workload per Assignee ---
    st.subheader("👥 Workload per Team Member")
    assignee_data = metrics["by_assignee"]
    if assignee_data:
        fig_workload = px.bar(
            x=list(assignee_data.keys()),
            y=list(assignee_data.values()),
            title="Tasks per Team Member",
            labels={"x": "Team Member", "y": "Task Count"},
            color_discrete_sequence=["#6366f1"],
        )
        st.plotly_chart(fig_workload, use_container_width=True)
        st.caption("Task distribution across team members. Uneven bars may indicate workload imbalance.")
    else:
        st.info("No assignee data available.")
