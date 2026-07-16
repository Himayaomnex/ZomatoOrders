import os
import sys
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# ── Path setup ───────────────────────────────────────────────────────────────
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "agent-starter"))

# ── Page config (MUST be very first Streamlit call) ──────────────────────────
st.set_page_config(
    page_title="ZomatoOrders AI Analyst",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load env ──────────────────────────────────────────────────────────────────
load_dotenv(project_root / ".env")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
GROQ_KEY     = os.getenv("GROQ_API_KEY", "")

# ── SQLite Data Helper for Calendar ──────────────────────────────────────────
@st.cache_data
def get_orders_by_date():
    import sqlite3
    db_path = project_root / "zomato.db"
    if not db_path.exists():
        return {}
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT order_date, COUNT(*) FROM orders GROUP BY order_date")
        data = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        return data
    except Exception:
        return {}

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
.stCodeBlock, code, pre    { font-family: 'JetBrains Mono', monospace !important; }

/* hero */
.hero-wrap {
    background: linear-gradient(135deg, #1a0a0a 0%, #2d0a0a 40%, #1a1a2e 100%);
    border: 1px solid rgba(255,65,108,0.25);
    border-radius: 20px;
    padding: 2rem 2.5rem 1.8rem;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 250px; height: 250px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,65,108,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FF416C 0%, #FF9A3C 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.3rem;
    line-height: 1.2;
}
.hero-sub { font-size: 0.95rem; color: #9ca3af; margin: 0; }

/* pipeline tracker */
.pipeline-wrap {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 1rem;
}
.pipe-title {
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #6b7280; margin-bottom: 0.8rem;
}
.pipe-steps { display: flex; align-items: center; gap: 0; }
.pipe-step {
    display: flex; align-items: center; gap: 0.45rem;
    font-size: 0.83rem; font-weight: 600; color: #4b5563; transition: color 0.3s;
}
.pipe-step.done   { color: #10b981; }
.pipe-step.active { color: #FF416C; }
.pipe-dot {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; background: rgba(255,255,255,0.05);
    border: 1.5px solid #374151; transition: all 0.3s;
}
.pipe-step.done   .pipe-dot { background: rgba(16,185,129,0.15);  border-color: #10b981; }
.pipe-step.active .pipe-dot { background: rgba(255,65,108,0.15); border-color: #FF416C; animation: pulse 1.2s infinite; }
.pipe-arrow {
    flex: 1; height: 1.5px;
    background: linear-gradient(90deg, #374151, rgba(255,255,255,0.05));
    margin: 0 0.4rem; min-width: 20px;
}
@keyframes pulse {
    0%,100% { box-shadow: 0 0 0 0   rgba(255,65,108,0.4); }
    50%      { box-shadow: 0 0 0 6px rgba(255,65,108,0);   }
}

/* stat cards */
.stat-card {
    background: linear-gradient(135deg, rgba(255,65,108,0.08) 0%, rgba(26,26,46,0.6) 100%);
    border: 1px solid rgba(255,65,108,0.18);
    border-radius: 14px; padding: 1.1rem 1.3rem; text-align: center;
}
.stat-value {
    font-size: 1.9rem; font-weight: 800;
    background: linear-gradient(135deg, #FF416C, #FF9A3C);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1; margin-bottom: 0.25rem;
}
.stat-label {
    font-size: 0.78rem; font-weight: 600; color: #6b7280;
    text-transform: uppercase; letter-spacing: 0.07em;
}

/* chat */
.stChatMessage {
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    margin-bottom: 0.9rem !important;
}

/* sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0a0a 0%, #160a0a 100%) !important;
    border-right: 1px solid rgba(255,65,108,0.15) !important;
}

/* sql badge */
.sql-badge {
    display: inline-block;
    background: rgba(255,65,108,0.12); border: 1px solid rgba(255,65,108,0.3);
    color: #FF6B8A; font-size: 0.75rem; font-weight: 700;
    padding: 0.15rem 0.6rem; border-radius: 6px;
    letter-spacing: 0.08em; margin-bottom: 0.4rem;
}

/* sample pills */
.pill-wrap { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.6rem; }
.pill {
    background: rgba(255,65,108,0.08); border: 1px solid rgba(255,65,108,0.2);
    border-radius: 20px; padding: 0.3rem 0.75rem;
    font-size: 0.78rem; color: #f87171; white-space: nowrap;
}

/* sidebar status rows */
.status-row {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.45rem 0; font-size: 0.84rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🍛 ZomatoOrders")
    st.markdown("<p style='color:#6b7280;font-size:0.82rem;margin-top:-0.5rem;'>AI Business Analyst v1.0</p>",
                unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("**🤖 LLM Provider**")
    llm_choice = st.selectbox(
        "model", ["Gemini", "Groq", "Ollama"],
        index=0, label_visibility="collapsed"
    )
    os.environ["LLM_PROVIDER"] = {"Gemini": "gemini", "Groq": "groq", "Ollama": "ollama"}[llm_choice]

    st.markdown("---")
    st.markdown("**🔌 System Status**")

    def _status(label, ok):
        dot  = "🟢" if ok else "🔴"
        word = "OK" if ok else "Missing"
        col  = "#10b981" if ok else "#ef4444"
        st.markdown(
            f'<div class="status-row">{dot} {label} &nbsp; '
            f'<span style="color:{col};font-weight:600;">{word}</span></div>',
            unsafe_allow_html=True
        )

    _status("Supabase URL",  bool(SUPABASE_URL))
    _status("Supabase Key",  bool(SUPABASE_KEY) and "PASTE" not in SUPABASE_KEY)
    _status("Gemini Key",    bool(GEMINI_KEY)   and "PASTE" not in GEMINI_KEY)
    _status("Groq Key",      bool(GROQ_KEY)     and "PASTE" not in GROQ_KEY)

    st.markdown("---")
    st.markdown("**📋 Architecture**")
    st.markdown("""
<div style='font-size:0.8rem;color:#6b7280;line-height:1.8'>
🔴 MCP Billing Server<br>&nbsp;&nbsp;&nbsp;↓<br>
🟠 Ingestion & ETL (CSV)<br>&nbsp;&nbsp;&nbsp;↓<br>
🟡 RIA Agent (Tools)<br>&nbsp;&nbsp;&nbsp;↓<br>
🟢 Supabase Cloud DB
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.query_count = 0
        st.rerun()


# ════════════════════════════════════════════════════════════════
# HERO HEADER
# ════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-wrap">
    <div class="hero-title">🍛 ZomatoOrders — AI Business Analyst</div>
    <p class="hero-sub">
        Ask natural-language questions about your restaurant orders, revenue, and customers.<br>
        The AI pipeline fetches live data, writes SQL, and returns insights — automatically.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Stats row ──────────────────────────────────────────────────
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

c1, c2, c3, c4 = st.columns(4)
for col, val, lbl in [
    (c1, "5",    "DB Tables"),
    (c2, "1",    "AI Agent"),
    (c3, "150K+","Orders"),
    (c4, str(st.session_state.query_count), "Queries Run"),
]:
    with col:
        st.markdown(
            f'<div class="stat-card"><div class="stat-value">{val}</div>'
            f'<div class="stat-label">{lbl}</div></div>',
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Sample questions ───────────────────────────────────────────
st.markdown("**💡 Try asking:**")
st.markdown("""
<div class="pill-wrap">
  <span class="pill">📅 How did my restaurant perform on 2017-10-04?</span>
  <span class="pill">🏆 Top 5 restaurants by revenue</span>
  <span class="pill">👤 Top 5 customers on 2017-10-04</span>
  <span class="pill">🍗 Most ordered food items</span>
  <span class="pill">🌆 Best city by revenue</span>
</div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Interactive Calendar Widget ─────────────────────────────────────────────
with st.expander("📅 Interactive Sales Calendar (Click Green Dates to Filter)", expanded=False):
    st.markdown("""
    <p style="font-size:0.85rem;color:#9ca3af;margin-top:-0.5rem;margin-bottom:1rem;">
        Dates colored in <span style="color:#10b981;font-weight:700;">GREEN</span> contain active orders in the billing simulation system.
        Dates colored in <span style="color:#ef4444;font-weight:700;">RED</span> do not contain any order data (holidays, future dates, weekends without data).
        Click on any green date to lock the system filter to that day, then ask your custom question.
    </p>
    """, unsafe_allow_html=True)
    
    # Load available dates
    orders_by_date = get_orders_by_date()
    
    # Month & Year selector
    c_yr, c_mo = st.columns(2)
    with c_yr:
        sel_year = st.selectbox("Select Calendar Year", [2017, 2018, 2019, 2020], index=0, key="cal_yr")
    with c_mo:
        months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        sel_month = st.selectbox("Select Calendar Month", months_list, index=9, key="cal_mo") # default October

    month_num = months_list.index(sel_month) + 1
    
    import calendar
    cal = calendar.Calendar(firstweekday=6) # start on Sunday
    month_days = cal.monthdayscalendar(sel_year, month_num)
    
    # Headers
    headers = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
    cols_header = st.columns(7)
    for idx, h in enumerate(headers):
        cols_header[idx].markdown(f"<p style='text-align:center;font-weight:800;color:#6b7280;margin:0;'>{h}</p>", unsafe_allow_html=True)
    
    # Calendar Grid Rows
    for week_idx, week in enumerate(month_days):
        cols = st.columns(7)
        for day_idx, day in enumerate(week):
            if day == 0:
                cols[day_idx].write("")
            else:
                date_str = f"{sel_year}-{month_num:02d}-{day:02d}"
                order_count = orders_by_date.get(date_str, 0)
                
                if order_count > 0:
                    btn_label = f"🟢 {day}"
                    help_text = f"{order_count} orders on this day. Click to set date filter."
                    if cols[day_idx].button(btn_label, key=f"btn_{date_str}", help=help_text, use_container_width=True):
                        st.session_state.selected_calendar_date = date_str
                        st.rerun()
                else:
                    btn_label = f"🔴 {day}"
                    help_text = "No orders found for this date."
                    cols[day_idx].button(btn_label, key=f"btn_{date_str}", help=help_text, disabled=True, use_container_width=True)

# Active Date Filter Banner
if st.session_state.get("selected_calendar_date"):
    sel_date = st.session_state.selected_calendar_date
    st.markdown("<br>", unsafe_allow_html=True)
    c_banner, c_clear = st.columns([5, 1])
    with c_banner:
        st.info(f"📅 **Active Date Filter: {sel_date}** — Ask any question below and it will run specifically on this date.")
    with c_clear:
        if st.button("❌ Clear", use_container_width=True, key="clear_filter_btn"):
            st.session_state.selected_calendar_date = None
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# PIPELINE TRACKER WIDGET
# ════════════════════════════════════════════════════════════════
def render_pipeline(active_step: int) -> str:
    """Return HTML for 2-step pipeline tracker. active_step 0=Ingestion, 1=RIA, 2=done."""
    steps = [("📦", "Data Ingestion"), ("🤖", "RIA Agent")]
    html = '<div class="pipeline-wrap"><div class="pipe-title">⚡ Live Pipeline Status</div><div class="pipe-steps">'
    for i, (icon, label) in enumerate(steps):
        if i < active_step:
            cls, dot_icon = "done", "✓"
        elif i == active_step:
            cls, dot_icon = "active", icon
        else:
            cls, dot_icon = "", icon
        html += f'<div class="pipe-step {cls}"><div class="pipe-dot">{dot_icon}</div>{label}</div>'
        if i < len(steps) - 1:
            html += '<div class="pipe-arrow"></div>'
    html += "</div></div>"
    return html


# ════════════════════════════════════════════════════════════════
# CHAT HISTORY
# ════════════════════════════════════════════════════════════════
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            "👋 Hello! I'm your **AI Business Analyst** for ZomatoOrders.\n\n"
            "I use the **Restaurant Intelligent Agent (RIA)** equipped with three tools:\n"
            "1. 📦 **Data Ingestion** — Fetches daily CSV files from the MCP billing system & loads them into Supabase.\n"
            "2. 🤖 **RIA Processing** — Coordinates three core tools:\n"
            "   - 🗃️ **SQL Tool** — Queries Supabase PostgreSQL to retrieve relevant records.\n"
            "   - 📊 **Analytical Tool** — Computes key business KPIs (Revenue, Average Order Value).\n"
            "   - 📋 **Report Tool** — Compiles reports and displays data export options.\n\n"
            "Type your question below to get started! 🚀"
        ),
    }]

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            st.markdown('<div class="sql-badge">🗃️ GENERATED SQL</div>', unsafe_allow_html=True)
            with st.expander("View SQL Query", expanded=False):
                st.code(msg["sql"], language="sql")
        if msg["role"] == "assistant" and msg.get("content") and "Hello!" not in msg.get("content"):
            st.markdown("---")
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📥 Download Report (Markdown)",
                    data=msg["content"],
                    file_name="restaurant_report.md",
                    mime="text/markdown",
                    key=f"dl_report_{idx}",
                    use_container_width=True
                )
            if msg.get("raw_data"):
                import pandas as pd
                df_export = pd.DataFrame(msg["raw_data"])
                csv_data = df_export.to_csv(index=False).encode('utf-8')
                with col_dl2:
                    st.download_button(
                        label="📥 Export Raw Data (CSV)",
                        data=csv_data,
                        file_name="query_data.csv",
                        mime="text/csv",
                        key=f"dl_data_{idx}",
                        use_container_width=True
                    )


# ════════════════════════════════════════════════════════════════
# CHAT INPUT + PIPELINE EXECUTION
# ════════════════════════════════════════════════════════════════
question = st.chat_input("Ask a business question about your orders...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Credentials guard
    if not SUPABASE_URL or not SUPABASE_KEY or "PASTE" in SUPABASE_KEY:
        with st.chat_message("assistant"):
            st.error("⚠️ Supabase credentials missing in `.env`. Configure `SUPABASE_URL` and `SUPABASE_KEY` first.")
        st.stop()

    with st.chat_message("assistant"):
        pipe_ph   = st.empty()
        status_ph = st.empty()

        pipe_ph.markdown(render_pipeline(0), unsafe_allow_html=True)
        status_ph.info("📦 **Data Engineer** — Connecting to MCP billing server and fetching daily CSV...")

        try:
            # Clear cached module so LLM provider change takes effect
            if "graph" in sys.modules:
                del sys.modules["graph"]

            from graph import build_graph, AgentState

            graph = build_graph()

            filter_date = st.session_state.get("selected_calendar_date")
            initial_state: AgentState = {
                "user_question":     question,
                "csv_data":          None,
                "cleaned_data":      None,
                "extraction_status": "pending",
                "sql_query":         None,
                "requirements":      None,
                "analysis_result":   None,
                "report":            None,
                "error":             None,
                "target_dates":      [filter_date] if filter_date else None,
            }

            config = {"configurable": {"thread_id": "streamlit-ui"}}

            # ── Stream nodes for live pipeline updates ─────────────
            final_state = {}
            try:
                for state_update in graph.stream(initial_state, config):
                    node_name = list(state_update.keys())[0] if state_update else None
                    if node_name:
                        final_state.update(state_update.get(node_name, {}))
                    if node_name == "data_engineer":
                        pipe_ph.markdown(render_pipeline(1), unsafe_allow_html=True)
                        status_ph.info("🤖 **RIA Agent** — Executing SQL, Analytics, and Report Tools...")
                    elif node_name == "restaurant_intelligent_agent":
                        pipe_ph.markdown(render_pipeline(2), unsafe_allow_html=True)
                        status_ph.success("✅ Pipeline complete!")
            except Exception:
                # Fallback: plain invoke if streaming not supported
                final_state = graph.invoke(initial_state, config)

            pipe_ph.empty()
            status_ph.empty()

            # ── Render result ──────────────────────────────────────
            err    = final_state.get("error")
            report = final_state.get("report", "")
            sql    = final_state.get("sql_query", "")

            if err:
                st.error(f"❌ Pipeline error: {err}")
                st.session_state.messages.append({"role": "assistant", "content": f"❌ {err}"})
            else:
                st.markdown(render_pipeline(2), unsafe_allow_html=True)

                if sql:
                    st.markdown('<div class="sql-badge">🗃️ GENERATED SQL</div>', unsafe_allow_html=True)
                    with st.expander("View Generated SQL Query", expanded=False):
                        st.code(sql, language="sql")

                st.markdown(report or "_No report returned._")
                
                # Add actual Download / Export Buttons
                if report:
                    st.markdown("---")
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📥 Download Report (Markdown)",
                            data=report,
                            file_name="restaurant_report.md",
                            mime="text/markdown",
                            key=f"dl_report_current",
                            use_container_width=True
                        )
                    raw_rows = final_state.get("raw_query_data")
                    if raw_rows:
                        import pandas as pd
                        df_export = pd.DataFrame(raw_rows)
                        csv_data = df_export.to_csv(index=False).encode('utf-8')
                        with col_dl2:
                            st.download_button(
                                label="📥 Export Raw Data (CSV)",
                                data=csv_data,
                                file_name="query_data.csv",
                                mime="text/csv",
                                key=f"dl_data_current",
                                use_container_width=True
                            )

                st.session_state.query_count += 1

                entry = {"role": "assistant", "content": report}
                if sql:
                    entry["sql"] = sql
                if final_state.get("raw_query_data"):
                    entry["raw_data"] = final_state.get("raw_query_data")
                st.session_state.messages.append(entry)

        except ImportError as e:
            pipe_ph.empty(); status_ph.empty()
            st.error(
                f"❌ Could not import agent graph: `{e}`\n\n"
                "Run from project root:\n```bash\nstreamlit run streamlit_app.py\n```"
            )
        except Exception as e:
            pipe_ph.empty(); status_ph.empty()
            st.error(f"❌ Unexpected error: `{e}`")
            st.session_state.messages.append({"role": "assistant", "content": f"Pipeline crashed: {e}"})
