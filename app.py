"""TeamSync AI — AI-powered team collaboration platform.

Solves: Team coordination and communication challenges by providing
smart standups, simplified task workflows, and real-time visibility.
UI styled to match Google Stitch design system.
"""

import json

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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
from firestore_client import (
    save_task,
    get_all_tasks,
    generate_task_id,
    update_task,
    save_team_members,
    get_team_members,
)

# --- Validate environment on startup ---
try:
    validate_config()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()

# --- Page Configuration ---
st.set_page_config(page_title=APP_NAME, page_icon="🤝", layout="wide")

# --- Design System Color Constants ---
COLOR_PRIMARY = "#6366f1"
COLOR_PRIMARY_LIGHT = "#e0e7ff"
COLOR_STATUS_TODO = "#6b7280"
COLOR_STATUS_PROGRESS = "#3b82f6"
COLOR_STATUS_DONE = "#22c55e"
COLOR_PRIO_CRITICAL = "#ef4444"
COLOR_PRIO_HIGH = "#f97316"
COLOR_PRIO_MEDIUM = "#eab308"
COLOR_PRIO_LOW = "#22c55e"
COLOR_SURFACE = "#f9fafb"
COLOR_ON_SURFACE = "#111827"

# ---------------------------------------------------------------------------
# Custom CSS — Google Stitch design system tokens
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background-color: #f9fafb !important; }
#MainMenu, footer, header[data-testid="stHeader"] {visibility: hidden;}

.stTabs [data-baseweb="tab-list"] {
    gap: 0; background: #ffffff; border-bottom: 1px solid #c7c4d7;
    padding: 0 24px; border-radius: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important; font-weight: 500; font-size: 14px;
    color: #464554; padding: 12px 20px; border-bottom: 2px solid transparent;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #6366f1 !important; border-bottom: 2px solid #6366f1 !important;
    font-weight: 600; background: transparent !important;
}

.stitch-card {
    background: #ffffff; border: 1px solid #c7c4d7; border-radius: 8px;
    padding: 24px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); margin-bottom: 16px;
}
.task-card {
    background: #ffffff; border: 1px solid #c7c4d7; border-radius: 8px;
    padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); margin-bottom: 12px;
}
.task-card.critical-border { border-left: 3px solid #ef4444; }
.task-id { font-size: 11px; font-weight: 500; color: #464554; text-transform: uppercase; letter-spacing: 0.04em; }
.task-title { font-size: 14px; color: #111827; margin: 8px 0 12px; line-height: 20px; }
.task-meta { display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: #767586; }

.badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;
}
.badge-critical { background: #fef2f2; color: #991b1b; }
.badge-high { background: #f3f4f6; color: #464554; }
.badge-high::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: #f97316; }
.badge-medium { background: #f3f4f6; color: #464554; }
.badge-medium::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: #eab308; }
.badge-low { background: #f3f4f6; color: #464554; }
.badge-low::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: #767586; }
.badge-todo { background: #f3f4f6; color: #464554; }
.badge-in_progress { background: #dbeafe; color: #1e40af; }
.badge-done { background: #dcfce7; color: #166534; }

.stitch-display {
    font-size: 36px !important; line-height: 44px; letter-spacing: -0.02em;
    font-weight: 700; color: #111827; margin-bottom: 4px;
}
.stitch-subtitle { font-size: 16px; line-height: 24px; color: #464554; }
.section-title {
    font-size: 18px; font-weight: 600; color: #111827;
    display: flex; align-items: center; gap: 8px; margin-bottom: 16px;
}

.blocker-card { background: #ffdad6; border: 1px solid rgba(186,26,26,0.2); border-radius: 8px; padding: 24px; }
.blocker-item { background: #ffffff; border: 1px solid rgba(199,196,215,0.3); border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; }
.standup-card { background: #ffffff; border: 1px solid #c7c4d7; border-radius: 8px; padding: 24px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); margin-bottom: 16px; }

[data-testid="stMetric"] { background: #ffffff; border: 1px solid #c7c4d7; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
[data-testid="stMetricLabel"] { font-size: 13px !important; font-weight: 500 !important; color: #464554 !important; }
[data-testid="stMetricValue"] { font-size: 36px !important; font-weight: 700 !important; letter-spacing: -0.02em; color: #111827 !important; }
.stPlotlyChart { border-radius: 8px; overflow: hidden; }

/* Force light-mode buttons */
.stButton > button {
    background-color: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #c7c4d7 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
}
.stButton > button:hover {
    background-color: #f3f4f6 !important;
    border-color: #6366f1 !important;
    color: #6366f1 !important;
}
.stButton > button:active, .stButton > button:focus {
    background-color: #e0e7ff !important;
    color: #6366f1 !important;
    border-color: #6366f1 !important;
}

/* Force light-mode selectbox/inputs */
[data-baseweb="select"] > div { background-color: #ffffff !important; color: #111827 !important; }
[data-baseweb="input"] > div { background-color: #ffffff !important; color: #111827 !important; }
.stTextInput > div > div > input { background-color: #ffffff !important; color: #111827 !important; }
.stSelectbox > div > div { background-color: #ffffff !important; color: #111827 !important; }

/* Force light sidebar */
[data-testid="stSidebar"] { background-color: #ffffff !important; }
[data-testid="stSidebar"] * { color: #111827 !important; }

/* Expander light mode */
[data-testid="stExpander"] { background-color: #ffffff !important; border: 1px solid #c7c4d7 !important; border-radius: 8px !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- Initialize Session State ---
if "tasks" not in st.session_state:
    firestore_tasks = get_all_tasks()
    st.session_state.tasks = firestore_tasks if firestore_tasks else list(SAMPLE_TASKS)

if "team_members" not in st.session_state:
    fs_members = get_team_members()
    if fs_members:
        st.session_state.team_members = fs_members
    else:
        st.session_state.team_members = sorted({
            t["assignee"] for t in st.session_state.tasks if t.get("assignee")
        })


# --- Helper Functions ---

def _get_tasks() -> list:
    """Get current task list from session state."""
    return st.session_state.tasks


def _add_task(task: dict) -> None:
    """Add a task to session state and persist to Firestore."""
    task["id"] = generate_task_id()
    st.session_state.tasks.append(task)
    save_task(task)


def _update_task_field(task_id: str, field: str, value: str) -> None:
    """Update a single field on a task in session state + Firestore."""
    for task in st.session_state.tasks:
        if task.get("id") == task_id:
            task[field] = value
            break
    update_task(task_id, {field: value})


PRIORITY_BADGE_MAP: dict[str, str] = {
    "critical": '<span class="badge badge-critical">⚠ Critical</span>',
    "high": '<span class="badge badge-high">High</span>',
    "medium": '<span class="badge badge-medium">Medium</span>',
    "low": '<span class="badge badge-low">Low</span>',
}


def _render_priority_badge(priority: str) -> str:
    """Return HTML for a styled priority badge."""
    return PRIORITY_BADGE_MAP.get(priority, f'<span class="badge">{priority}</span>')


def _plotly_layout() -> dict:
    """Shared Plotly layout config for consistent design system styling."""
    return dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=COLOR_ON_SURFACE, size=14),
        margin=dict(t=40, b=60, l=60, r=20),
        xaxis=dict(
            title_font=dict(size=14, color=COLOR_ON_SURFACE),
            tickfont=dict(size=13, color=COLOR_ON_SURFACE),
        ),
        yaxis=dict(
            title_font=dict(size=14, color=COLOR_ON_SURFACE),
            tickfont=dict(size=13, color=COLOR_ON_SURFACE),
        ),
    )


# ============================================================
# SIDEBAR: Team Members Management (Fix #2)
# ============================================================
with st.sidebar:
    st.markdown("### 🤝 TeamSync AI")
    st.caption("Manage your team")
    st.divider()

    st.subheader("👥 Team Members")
    for i, member in enumerate(st.session_state.team_members):
        col_name, col_del = st.columns([4, 1])
        with col_name:
            st.text(member)
        with col_del:
            if st.button("✕", key=f"del_member_{i}", help=f"Remove {member}"):
                st.session_state.team_members.remove(member)
                save_team_members(st.session_state.team_members)
                st.rerun()

    new_member = st.text_input(
        "Add member", placeholder="Name", key="new_member_input",
        label_visibility="collapsed",
    )
    if st.button("➕ Add Member", key="btn_add_member"):
        name = new_member.strip()
        if name and name not in st.session_state.team_members:
            st.session_state.team_members.append(name)
            save_team_members(st.session_state.team_members)
            st.rerun()
        elif not name:
            st.warning("Enter a name.")


# --- App Header ---
st.markdown(
    '<div class="stitch-display">🤝 TeamSync AI</div>'
    '<div class="stitch-subtitle">' + APP_DESCRIPTION + '</div>',
    unsafe_allow_html=True,
)

# --- Navigation Tabs (Fix #3: Dashboard first) ---
tab_dashboard, tab_board, tab_standup = st.tabs([
    "📊 Dashboard", "📋 Task Board", "🤖 AI Standup",
])


# ============================================================
# TAB 1 (Default): Dashboard + Analytics (Fix #3 + Fix #4)
# ============================================================
with tab_dashboard:
    st.markdown(
        '<div class="stitch-display" style="font-size:28px;line-height:36px;">'
        'Team Analytics</div>'
        '<div class="stitch-subtitle">'
        'Overview of team performance and task distribution.</div>',
        unsafe_allow_html=True,
    )

    tasks_json = json.dumps(_get_tasks())
    metrics = get_team_metrics(tasks_json)

    # --- KPI Cards ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Tasks", metrics["total_tasks"])
    with c2:
        st.metric("Completion Rate", f"{metrics['completion_rate']}%")
    with c3:
        st.metric("Blocked", metrics["blocked_count"])
    with c4:
        st.metric("Overdue", metrics["overdue_count"])

    st.divider()

    # --- Row 1: Status donut + Priority bar (2:1 bento) ---
    chart_c1, chart_c2 = st.columns([2, 1])

    with chart_c1:
        st.markdown(
            '<div class="section-title">Task Status Distribution</div>',
            unsafe_allow_html=True,
        )
        status_data = metrics["by_status"]
        if status_data:
            status_colors = {
                "todo": COLOR_STATUS_TODO,
                "in_progress": COLOR_STATUS_PROGRESS,
                "done": COLOR_STATUS_DONE,
            }
            ordered_labels = [k for k in ["todo", "in_progress", "done"] if k in status_data]
            ordered_values = [status_data[k] for k in ordered_labels]
            ordered_colors = [status_colors.get(k, "#999") for k in ordered_labels]

            fig_status = go.Figure(data=[go.Pie(
                labels=ordered_labels, values=ordered_values,
                hole=0.45, marker=dict(colors=ordered_colors),
                textinfo="label+percent", textposition="outside",
                textfont=dict(size=12),
            )])
            fig_status.update_layout(
                **_plotly_layout(),
                title=dict(text="Tasks by Status", font=dict(size=16)),
                showlegend=True,
                legend=dict(orientation="h", y=-0.1),
            )
            st.plotly_chart(fig_status, use_container_width=True)
            st.caption(
                "Donut chart: todo (gray), in_progress (blue), done (green)."
            )
        else:
            st.info("No task data available.")

    with chart_c2:
        st.markdown(
            '<div class="section-title">Priority Distribution</div>',
            unsafe_allow_html=True,
        )
        prio_data = metrics["by_priority"]
        if prio_data:
            prio_colors = {
                "critical": COLOR_PRIO_CRITICAL, "high": COLOR_PRIO_HIGH,
                "medium": COLOR_PRIO_MEDIUM, "low": COLOR_PRIO_LOW,
            }
            prio_order = [k for k in ["critical", "high", "medium", "low"] if k in prio_data]
            prio_vals = [prio_data[k] for k in prio_order]
            prio_cols = [prio_colors.get(k, "#999") for k in prio_order]

            fig_prio = go.Figure(data=[go.Bar(
                x=prio_order, y=prio_vals,
                marker_color=prio_cols,
                text=prio_vals, textposition="outside",
            )])
            fig_prio.update_layout(
                **_plotly_layout(),
                title=dict(text="Tasks by Priority", font=dict(size=16)),
                xaxis_title="Priority Level",
                yaxis_title="Count",
                showlegend=False,
            )
            st.plotly_chart(fig_prio, use_container_width=True)
            st.caption(
                "Critical (red) > High (orange) > Medium (yellow) > Low (green)."
            )
        else:
            st.info("No priority data available.")

    # --- Row 2: Workload bar chart (full width) ---
    st.markdown(
        '<div class="section-title">👥 Workload per Team Member</div>',
        unsafe_allow_html=True,
    )
    assignee_data = metrics["by_assignee"]
    if assignee_data:
        sorted_members = sorted(assignee_data.items(), key=lambda x: x[1], reverse=True)
        members_names = [m[0] for m in sorted_members]
        members_counts = [m[1] for m in sorted_members]

        fig_workload = go.Figure(data=[go.Bar(
            x=members_names, y=members_counts,
            marker_color=COLOR_PRIMARY,
            text=members_counts, textposition="outside",
        )])
        fig_workload.update_layout(
            **_plotly_layout(),
            title=dict(text="Tasks per Team Member", font=dict(size=16)),
            xaxis_title="Team Member",
            yaxis_title="Task Count",
        )
        st.plotly_chart(fig_workload, use_container_width=True)
        st.caption(
            "Sorted by workload. Uneven bars may indicate workload imbalance."
        )


# ============================================================
# TAB 2: Smart Task Board with inline edit (Fix #1)
# ============================================================
with tab_board:
    st.markdown(
        '<div class="stitch-display" style="font-size:28px;line-height:36px;">'
        'Tasks Board</div>',
        unsafe_allow_html=True,
    )
    st.caption("Manage tasks and create new ones using natural language.")

    # --- NL Task Creation ---
    st.markdown(
        '<div class="section-title">✨ Create Task with AI</div>',
        unsafe_allow_html=True,
    )
    nl_input = st.text_input(
        "Describe your task in plain English:",
        placeholder='e.g. "Assign a high-priority bug to Meena about payment timeouts"',
        key="nl_task_input", label_visibility="collapsed",
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
                st.success(
                    f"✅ Created: **{new_task['title']}** → {new_task['assignee']}"
                )
        else:
            st.warning("Please enter a task description.")

    st.divider()

    # --- Kanban Columns with inline edit ---
    tasks = _get_tasks()
    todo_tasks = [t for t in tasks if t.get("status") == "todo"]
    prog_tasks = [t for t in tasks if t.get("status") == "in_progress"]
    done_tasks = [t for t in tasks if t.get("status") == "done"]

    statuses = ["todo", "in_progress", "done"]
    priorities = ["low", "medium", "high", "critical"]
    members = st.session_state.team_members

    col_todo, col_prog, col_done = st.columns(3)

    # --- Helper to render a task card with edit controls ---
    def _render_task_card(task: dict, column_key: str) -> None:
        """Render a single task card with inline edit expander."""
        tid = task.get("id", "")
        border = "critical-border" if task.get("priority") == "critical" else ""
        blocker_html = ""
        if task.get("blockers", "").strip():
            blocker_html = (
                f'<div style="color:#ef4444;font-size:11px;margin-top:8px;">'
                f'🚫 {task["blockers"]}</div>'
            )

        st.markdown(f"""
        <div class="task-card {border}">
            <div class="task-id">{tid}</div>
            <div class="task-title">{task.get('title','')}</div>
            <div class="task-meta">
                {_render_priority_badge(task.get('priority',''))}
                <span>👤 {task.get('assignee','')}</span>
            </div>
            {blocker_html}
        </div>""", unsafe_allow_html=True)

        with st.expander(f"✏️ Edit {tid}", expanded=False):
            new_status = st.selectbox(
                "Status", statuses,
                index=statuses.index(task.get("status", "todo")),
                key=f"status_{column_key}_{tid}",
            )
            new_priority = st.selectbox(
                "Priority", priorities,
                index=priorities.index(task.get("priority", "medium")),
                key=f"prio_{column_key}_{tid}",
            )
            assignee_idx = 0
            if task.get("assignee") in members:
                assignee_idx = members.index(task["assignee"])
            new_assignee = st.selectbox(
                "Assignee", members,
                index=assignee_idx,
                key=f"assign_{column_key}_{tid}",
            )
            if st.button("💾 Save", key=f"save_{column_key}_{tid}"):
                _update_task_field(tid, "status", new_status)
                _update_task_field(tid, "priority", new_priority)
                _update_task_field(tid, "assignee", new_assignee)
                st.success(f"Updated {tid}")
                st.rerun()

    with col_todo:
        st.markdown(
            f'<div class="section-title">○ To Do '
            f'<span class="badge badge-todo">{len(todo_tasks)}</span></div>',
            unsafe_allow_html=True,
        )
        for t in todo_tasks:
            _render_task_card(t, "todo")

    with col_prog:
        st.markdown(
            f'<div class="section-title" style="color:#3b82f6;">◐ In Progress '
            f'<span class="badge badge-in_progress">{len(prog_tasks)}</span></div>',
            unsafe_allow_html=True,
        )
        for t in prog_tasks:
            _render_task_card(t, "prog")

    with col_done:
        st.markdown(
            f'<div class="section-title" style="color:#22c55e;">✓ Done '
            f'<span class="badge badge-done">{len(done_tasks)}</span></div>',
            unsafe_allow_html=True,
        )
        for t in done_tasks:
            _render_task_card(t, "done")

    # --- Manual Task Add ---
    with st.expander("➕ Add Task Manually"):
        with st.form("manual_task_form"):
            m_title = st.text_input("Title", key="manual_title")
            m_c1, m_c2 = st.columns(2)
            with m_c1:
                m_assignee = st.selectbox(
                    "Assignee", members, key="manual_assignee"
                )
                m_priority = st.selectbox(
                    "Priority", priorities, index=1, key="manual_priority"
                )
            with m_c2:
                m_status = st.selectbox(
                    "Status", statuses, key="manual_status"
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
                    _add_task({
                        "title": sanitize_text(m_title),
                        "assignee": m_assignee,
                        "status": m_status,
                        "priority": m_priority,
                        "due_date": str(m_due),
                        "blockers": sanitize_text(m_blockers),
                        "tags": [],
                    })
                    st.success(f"✅ Added: {m_title}")


# ============================================================
# TAB 3: AI Standup Generator
# ============================================================
with tab_standup:
    st.markdown(
        '<div class="stitch-display">Daily AI Standup</div>'
        '<div class="stitch-subtitle">'
        'Generated summary of team progress and blockers.</div>',
        unsafe_allow_html=True,
    )

    if st.button("🚀 Generate Today's Standup", key="btn_standup"):
        with st.spinner("AI is analyzing your team's tasks..."):
            standup = generate_standup(_get_tasks())

        blockers = standup.get("blockers_alert", [])
        col_blockers, col_main = st.columns([1, 2])

        with col_blockers:
            if blockers:
                st.markdown(
                    '<div class="blocker-card">'
                    '<div style="display:flex;align-items:center;gap:8px;'
                    'color:#991b1b;font-size:22px;font-weight:600;'
                    'margin-bottom:16px;">⚠ Blockers detected</div>',
                    unsafe_allow_html=True,
                )
                for b in blockers:
                    st.markdown(
                        f'<div class="blocker-item">'
                        f'<div style="font-size:13px;font-weight:500;'
                        f'color:#111827;">🚨 {b}</div></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.success("🎉 No blockers! Team is unblocked.")

        with col_main:
            summary = standup.get('team_summary', 'No summary available.')
            st.markdown(f"""
            <div class="standup-card">
                <div class="section-title">📝 Team Summary</div>
                <div style="color:#464554;font-size:14px;line-height:20px;">
                    {summary}
                </div>
            </div>""", unsafe_allow_html=True)

            st.markdown(
                '<div class="standup-card">'
                '<div class="section-title">👥 Member Updates</div>',
                unsafe_allow_html=True,
            )
            for update in standup.get("member_updates", []):
                st.markdown(
                    f'<div style="margin-bottom:12px;">'
                    f'<strong style="color:#111827;">{update["name"]}</strong>'
                    f'<span style="color:#464554;font-size:14px;">'
                    f' — {update["summary"]}</span></div>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)
        st.caption("Standup generated by Gemini AI based on current task data.")

    st.divider()

    # --- Blocker Resolution ---
    st.markdown(
        '<div class="section-title">🔧 AI Blocker Resolution</div>',
        unsafe_allow_html=True,
    )
    st.caption("Get AI-suggested actions to unblock your team.")

    if st.button("Analyze Blockers", key="btn_blockers"):
        with st.spinner("Analyzing blockers..."):
            suggestions = analyze_blockers(_get_tasks())
        if not suggestions:
            st.success("🎉 No blockers found! Team is unblocked.")
        else:
            for s in suggestions:
                st.markdown(f"""
                <div class="stitch-card">
                    <div style="font-weight:600;color:#111827;font-size:14px;">
                        Task {s.get('task_id','?')} — {s.get('blocker','')}
                    </div>
                    <div style="color:#6366f1;font-size:14px;margin-top:8px;">
                        💡 {s.get('suggestion','')}
                    </div>
                </div>""", unsafe_allow_html=True)
            st.caption("Suggestions generated by Gemini AI.")
