import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date as date_class
import plotly.graph_objects as go
import hashlib
from typing import Optional
import smtplib
from email.message import EmailMessage

DB_PATH = "data.db"

st.set_page_config(
    page_title="Investment Consortium Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------- Utilities -----------------------
def safe_rerun():
    """Call experimental_rerun if available; otherwise toggle a session flag to force rerender."""
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            # Fallback: toggle a session flag to re-execute
            st.session_state["_rerun_toggle"] = not st.session_state.get("_rerun_toggle", False)
    except Exception:
        # In case rerun raised AttributeError in some environments, just set flag
        st.session_state["_rerun_toggle"] = not st.session_state.get("_rerun_toggle", False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        rows = c.fetchall()
        conn.close()
        return rows
    conn.commit()
    conn.close()

# ----------------------- DB init & migrations -----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE,
        invested REAL NOT NULL,
        join_date TEXT NOT NULL,
        note TEXT,
        password TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS pending_clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        invested REAL NOT NULL,
        join_date TEXT NOT NULL,
        note TEXT,
        created_at TEXT NOT NULL
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS profits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profit_date TEXT NOT NULL UNIQUE,
        total_profit REAL NOT NULL,
        note TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )""")
    # approvals history
    c.execute("""
    CREATE TABLE IF NOT EXISTS approvals_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pending_id INTEGER,
        action TEXT,
        admin_username TEXT,
        reason TEXT,
        timestamp TEXT
    )""")
    c.execute("SELECT COUNT(*) FROM admin_users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO admin_users (username, password) VALUES (?, ?)", ("admin", hash_password("admin123")))
    conn.commit()
    conn.close()

# ----------------------- Email helper (optional) -----------------------
def send_email_notification(to_email: str, subject: str, body: str):
    # Only attempt if SMTP config provided in st.secrets (recommended keys: smtp_server, smtp_port, smtp_user, smtp_password, from_email)
    try:
        secrets = st.secrets.get("smtp", {}) if isinstance(st.secrets, dict) else {}
    except Exception:
        secrets = {}
    smtp_server = secrets.get("smtp_server")
    smtp_port = secrets.get("smtp_port")
    smtp_user = secrets.get("smtp_user")
    smtp_password = secrets.get("smtp_password")
    from_email = secrets.get("from_email", smtp_user)
    if not smtp_server or not smtp_port or not smtp_user or not smtp_password:
        # SMTP not configured - skip sending, but log to approvals_history or app logs
        print("SMTP not configured; skipping email send. Subject:", subject)
        return False, "SMTP not configured"
    try:
        msg = EmailMessage()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP_SSL(smtp_server, int(smtp_port)) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True, "Email sent"
    except Exception as e:
        print("Failed to send email:", e)
        return False, str(e)

# ----------------------- Pending clients (signup) -----------------------
def add_pending_client(name: str, username: str, password: str, invested: float, join_date: str, note: str=""):
    pw = hash_password(password)
    run_query("INSERT INTO pending_clients (name, username, password, invested, join_date, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", 
              (name, username, pw, invested, join_date, note, datetime.utcnow().isoformat()))

def list_pending_clients_df():
    rows = run_query("SELECT id, name, username, invested, join_date, note, created_at FROM pending_clients ORDER BY created_at", fetch=True)
    return pd.DataFrame(rows, columns=["id","name","username","invested","join_date","note","created_at"]) if rows else pd.DataFrame(columns=["id","name","username","invested","join_date","note","created_at"])

def get_pending_by_id(pid: int):
    rows = run_query("SELECT id, name, username, password, invested, join_date, note, created_at FROM pending_clients WHERE id=?", (pid,), fetch=True)
    if rows:
        r = rows[0]
        return {"id": r[0], "name": r[1], "username": r[2], "password": r[3], "invested": r[4], "join_date": r[5], "note": r[6], "created_at": r[7]}
    return None

def log_approval_action(pending_id:int, action:str, admin_username:str, reason:str=""):
    run_query("INSERT INTO approvals_history (pending_id, action, admin_username, reason, timestamp) VALUES (?, ?, ?, ?, ?)", 
              (pending_id, action, admin_username, reason, datetime.utcnow().isoformat()))

def approve_pending_client(pid: int, admin_username:str):
    p = get_pending_by_id(pid)
    if not p:
        return False, "Pending request not found"
    try:
        run_query("INSERT INTO clients (name, username, invested, join_date, note, password) VALUES (?, ?, ?, ?, ?, ?)", 
                  (p["name"], p["username"], p["invested"], p["join_date"], p["note"], p["password"]))
        run_query("DELETE FROM pending_clients WHERE id=?", (pid,))
        log_approval_action(pid, "approved", admin_username, "")
        # Optionally send email to user if admin configured email and if we had their email (we don't collect email in this form)
        return True, "Approved and client created"
    except Exception as e:
        return False, str(e)

def reject_pending_client(pid: int, admin_username:str, reason:str=""):
    p = get_pending_by_id(pid)
    if not p:
        return False, "Pending request not found"
    run_query("DELETE FROM pending_clients WHERE id=?", (pid,))
    log_approval_action(pid, "rejected", admin_username, reason)
    return True, "Rejected"

def list_approvals_history_df():
    rows = run_query("SELECT id, pending_id, action, admin_username, reason, timestamp FROM approvals_history ORDER BY timestamp DESC", fetch=True)
    return pd.DataFrame(rows, columns=["id","pending_id","action","admin_username","reason","timestamp"]) if rows else pd.DataFrame(columns=["id","pending_id","action","admin_username","reason","timestamp"])

def is_username_taken(username: str) -> bool:
    rows1 = run_query("SELECT 1 FROM clients WHERE username=?", (username,), fetch=True)
    rows2 = run_query("SELECT 1 FROM pending_clients WHERE username=?", (username,), fetch=True)
    return bool(rows1 or rows2)

# ----------------------- Clients CRUD & auth -----------------------
def add_client(name, invested, join_date, note="", password="client123", username: Optional[str]=None):
    hashed_pw = hash_password(password)
    run_query("INSERT INTO clients (name, username, invested, join_date, note, password) VALUES (?, ?, ?, ?, ?, ?)", 
              (name, username, invested, join_date, note, hashed_pw))

def update_client(client_id, name, invested, join_date, note="", password=None, username: Optional[str]=None):
    if password:
        run_query("UPDATE clients SET name=?, invested=?, join_date=?, note=?, password=?, username=? WHERE id=?", 
                 (name, invested, join_date, note, hash_password(password), username, client_id))
    else:
        run_query("UPDATE clients SET name=?, invested=?, join_date=?, note=?, username=? WHERE id=?", 
                 (name, invested, join_date, note, username, client_id))

def change_client_password(client_id:int, new_password:str):
    run_query("UPDATE clients SET password=? WHERE id=?", (hash_password(new_password), client_id))

def delete_client(client_id):
    run_query("DELETE FROM clients WHERE id=?", (client_id,))

def list_clients_df():
    rows = run_query("SELECT id, name, username, invested, join_date, note FROM clients ORDER BY id", fetch=True)
    return pd.DataFrame(rows, columns=["id","name","username","invested","join_date","note"]) if rows else pd.DataFrame(columns=["id","name","username","invested","join_date","note"])

def get_client_by_id(client_id):
    rows = run_query("SELECT id, name, username, invested, join_date, note FROM clients WHERE id=?", (client_id,), fetch=True)
    if rows:
        r = rows[0]
        return {"id": r[0], "name": r[1], "username": r[2], "invested": r[3], "join_date": r[4], "note": r[5]}
    return None

def get_client_by_username(username):
    rows = run_query("SELECT id, name, username, invested, join_date, note FROM clients WHERE username=?", (username,), fetch=True)
    if rows:
        r = rows[0]
        return {"id": r[0], "name": r[1], "username": r[2], "invested": r[3], "join_date": r[4], "note": r[5]}
    return None

def verify_admin(username, password):
    rows = run_query("SELECT password FROM admin_users WHERE username=?", (username,), fetch=True)
    if rows:
        return rows[0][0] == hash_password(password)
    return False

def verify_client_by_id(client_id, password):
    rows = run_query("SELECT password FROM clients WHERE id=?", (client_id,), fetch=True)
    if rows:
        return rows[0][0] == hash_password(password)
    return False

def verify_client_by_username(username, password):
    rows = run_query("SELECT password FROM clients WHERE username=?", (username,), fetch=True)
    if rows:
        return rows[0][0] == hash_password(password)
    return False

# ----------------------- Profits & Allocations (unchanged) -----------------------
def add_profit(profit_date, total_profit, note=""):
    run_query("INSERT OR REPLACE INTO profits (profit_date, total_profit, note) VALUES (?, ?, ?)", 
              (profit_date, total_profit, note))

def update_profit(profit_id, profit_date, total_profit, note=""):
    run_query("UPDATE profits SET profit_date=?, total_profit=?, note=? WHERE id=?", 
              (profit_date, total_profit, note, profit_id))

def delete_profit(profit_id):
    run_query("DELETE FROM profits WHERE id=?", (profit_id,))

def list_profits_df():
    rows = run_query("SELECT id, profit_date, total_profit, note FROM profits ORDER BY profit_date", fetch=True)
    return pd.DataFrame(rows, columns=["id","profit_date","total_profit","note"]) if rows else pd.DataFrame(columns=["id","profit_date","total_profit","note"])

def allocations_for_date(target_date):
    clients = list_clients_df()
    if clients.empty:
        return pd.DataFrame(columns=["id","name","username","invested","join_date","active","share","alloc_profit"])
    clients["join_date"] = pd.to_datetime(clients["join_date"]).dt.date
    if isinstance(target_date, str):
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
    elif isinstance(target_date, datetime):
        target = target_date.date()
    else:
        target = target_date
    clients["active"] = clients["join_date"] <= target
    active_sum = clients.loc[clients["active"], "invested"].sum()
    if active_sum == 0:
        clients["share"] = 0.0
    else:
        clients["share"] = clients["invested"] / active_sum
        clients.loc[~clients["active"], "share"] = 0.0
    return clients

def compute_client_timeseries():
    profits = list_profits_df()
    clients = list_clients_df()
    if profits.empty or clients.empty:
        return {}, profits, clients
    profits["profit_date"] = pd.to_datetime(profits["profit_date"]).dt.date
    clients["join_date"] = pd.to_datetime(clients["join_date"]).dt.date

    profits = profits.sort_values("profit_date")
    client_ids = clients["id"].tolist()
    timeseries = {cid: [] for cid in client_ids}
    dates = []
    cum_gain = {cid: 0.0 for cid in client_ids}

    for _, row in profits.iterrows():
        d = row["profit_date"]
        dates.append(d)
        total_profit = row["total_profit"]
        active = clients[clients["join_date"] <= d]
        total_active = active["invested"].sum()
        if total_active == 0:
            for cid in client_ids:
                timeseries[cid].append(cum_gain[cid])
        else:
            for _, c in clients.iterrows():
                cid = c["id"]
                if c["join_date"] <= d:
                    share = c["invested"] / total_active if total_active>0 else 0.0
                    gain = total_profit * share
                else:
                    gain = 0.0
                cum_gain[cid] += gain
                timeseries[cid].append(cum_gain[cid])
    result = {}
    for _, c in clients.iterrows():
        cid = c["id"]
        invested = c["invested"]
        gains = timeseries[cid] if len(timeseries[cid])>0 else []
        pct = [(g / invested * 100) if invested>0 else 0.0 for g in gains]
        result[cid] = {
            "name": c["name"],
            "invested": invested,
            "join_date": c["join_date"],
            "dates": dates,
            "cumulative_gain": gains,
            "pct_return": pct
        }
    return result, profits, clients

def get_client_timeseries(client_id):
    result, profits, clients = compute_client_timeseries()
    return result.get(client_id, None)

def get_dashboard_metrics():
    clients = list_clients_df()
    profits = list_profits_df()
    total_clients = len(clients)
    total_invested = clients["invested"].sum() if not clients.empty else 0
    total_profit = profits["total_profit"].sum() if not profits.empty else 0
    avg_return = (total_profit / total_invested * 100) if total_invested > 0 else 0
    return {"total_clients": total_clients, "total_invested": total_invested, "total_profit": total_profit, "avg_return": avg_return}

def load_css():
    st.markdown("<style> body {background-color: #0e1117; color: #fff;} </style>", unsafe_allow_html=True)

# ----------------------- UI: Admin -----------------------
def admin_panel():
    st.title("🔐 Admin Dashboard")
    st.markdown("---")
    pending_df = list_pending_clients_df()
    pending_count = len(pending_df)
    st.write(f"🔔 Pending signups: **{pending_count}**")
    if pending_count > 0:
        with st.expander(f"View {pending_count} pending signup(s)", expanded=True):
            for _, row in pending_df.iterrows():
                st.markdown(f"**ID {row['id']} — {row['name']} ({row['username']})** — Invested: Rp {row['invested']:,.0f} — Joined: {row['join_date']}")
                cols = st.columns([1,1,4])
                with cols[0]:
                    if st.button(f"✅ Approve##{row['id']}", key=f"approve_{row['id']}"):
                        ok, msg = approve_pending_client(int(row['id']), st.session_state.get('username','admin'))
                        if ok:
                            st.success(f"Approved: {row['name']} ({row['username']})")
                            # optionally notify via email (not collected here)
                            safe_rerun()
                        else:
                            st.error(f"Failed to approve: {msg}")
                with cols[1]:
                    if st.button(f"❌ Reject##{row['id']}", key=f"reject_{row['id']}"):
                        # ask for reason in a small modal-like input using text_input with unique key
                        reason = st.text_input(f"Reason for reject {row['id']}", key=f"reject_reason_{row['id']}")
                        if st.button(f"Confirm Reject##{row['id']}", key=f"confirm_reject_{row['id']}"):
                            ok, msg = reject_pending_client(int(row['id']), st.session_state.get('username','admin'), reason or "")
                            if ok:
                                st.warning(f"Rejected: {row['name']} ({row['username']})")
                                safe_rerun()
                            else:
                                st.error(f"Failed to reject: {msg}")
                with cols[2]:
                    st.write(f"Notes: {row['note'] or '-'}  |  Requested at: {row['created_at']}")
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Client Management", "💹 Profit Management", "📊 Share Profit", "🔔 Approvals History"])
    with tab1:
        st.subheader("Client Management")
        col1, col2 = st.columns([1,2])
        with col1:
            with st.expander("➕ Add New Client (admin created)", expanded=True):
                with st.form("add_client_form_admin"):
                    name = st.text_input("Client Name *")
                    username = st.text_input("Username (unique) *")
                    invested = st.number_input("Investment Amount (Rp) *", min_value=0.0, format="%.2f")
                    join_date = st.date_input("Join Date *", value=date_class.today())
                    password = st.text_input("Client Password *", type="password", help="Password for client login")
                    note = st.text_area("Notes (optional)", height=100)
                    submit = st.form_submit_button("💾 Add Client", use_container_width=True)
                    if submit:
                        if not username:
                            st.error("Username required")
                        elif is_username_taken(username):
                            st.error("Username already taken")
                        elif name and invested > 0 and password:
                            add_client(name, float(invested), join_date.isoformat(), note, password, username)
                            st.success(f"✅ Client '{name}' added successfully!")
                            safe_rerun()
                        else:
                            st.error("Please fill required fields")
        with col2:
            clients_df = list_clients_df()
            if not clients_df.empty:
                display_df = clients_df.copy()
                display_df["invested"] = display_df["invested"].apply(lambda x: f"Rp {x:,.0f}")
                display_df["join_date"] = pd.to_datetime(display_df["join_date"]).dt.strftime("%d %b %Y")
                st.dataframe(display_df, use_container_width=True, height=300)
                st.markdown("### ✏️ Edit / Delete Client")
                edit_id = st.selectbox("Select Client ID", clients_df["id"].tolist(), format_func=lambda x: f"ID {x} - {clients_df[clients_df['id']==x]['name'].iloc[0]}")
                if edit_id:
                    row = clients_df[clients_df["id"]==edit_id].iloc[0]
                    with st.form("edit_client_form_admin"):
                        e_name = st.text_input("Name", value=row["name"])
                        e_username = st.text_input("Username", value=row["username"])
                        e_invested = st.number_input("Invested", value=float(row["invested"]), min_value=0.0)
                        e_join = st.date_input("Join Date", value=pd.to_datetime(row["join_date"]).date())
                        e_note = st.text_area("Note", value=row["note"], height=100)
                        e_password = st.text_input("New Password (leave blank to keep current)", type="password")
                        col1, col2 = st.columns(2)
                        with col1:
                            update = st.form_submit_button("💾 Update", use_container_width=True)
                        with col2:
                            delete = st.form_submit_button("🗑️ Delete", use_container_width=True, type="primary")
                        if update:
                            if e_username and is_username_taken(e_username) and e_username != row["username"]:
                                st.error("Username already taken by someone else")
                            else:
                                if e_password:
                                    update_client(edit_id, e_name, float(e_invested), e_join.isoformat(), e_note, e_password, e_username)
                                else:
                                    update_client(edit_id, e_name, float(e_invested), e_join.isoformat(), e_note, None, e_username)
                                st.success("✅ Client updated successfully!")
                                safe_rerun()
                        if delete:
                            delete_client(edit_id)
                            st.success("✅ Client deleted successfully!")
                            safe_rerun()
            else:
                st.info("📭 No clients yet. Add your first client to get started!")
    with tab2:
        st.subheader("Profit Management")
        col1, col2 = st.columns([1,2])
        with col1:
            with st.expander("➕ Add Daily Profit", expanded=True):
                with st.form("add_profit_form_admin"):
                    p_date = st.date_input("Profit Date *", value=date_class.today())
                    p_total = st.number_input("Total Profit (Rp) *", value=0.0, format="%.2f")
                    p_note = st.text_area("Notes (optional)", height=100)
                    submit = st.form_submit_button("💾 Save Profit", use_container_width=True)
                    if submit:
                        add_profit(p_date.isoformat(), float(p_total), p_note)
                        st.success(f"✅ Profit for {p_date.strftime('%d %b %Y')} saved!")
                        safe_rerun()
        with col2:
            profits_df = list_profits_df()
            if not profits_df.empty:
                display_df = profits_df.copy()
                display_df["total_profit"] = display_df["total_profit"].apply(lambda x: f"Rp {x:,.0f}" if x >= 0 else f"-Rp {abs(x):,.0f}")
                display_df["profit_date"] = pd.to_datetime(display_df["profit_date"]).dt.strftime("%d %b %Y")
                st.dataframe(display_df, use_container_width=True, height=300)
                st.markdown("### ✏️ Edit / Delete Profit Entry")
                p_edit_id = st.selectbox("Select Profit ID", profits_df["id"].tolist(), format_func=lambda x: f"ID {x} - {pd.to_datetime(profits_df[profits_df['id']==x]['profit_date'].iloc[0]).strftime('%d %b %Y')}")
                if p_edit_id:
                    prow = profits_df[profits_df["id"]==p_edit_id].iloc[0]
                    with st.form("edit_profit_form_admin"):
                        pe_date = st.date_input("Profit Date", value=pd.to_datetime(prow["profit_date"]).date())
                        pe_total = st.number_input("Total Profit", value=float(prow["total_profit"]))
                        pe_note = st.text_area("Note", value=prow["note"], height=100)
                        col1, col2 = st.columns(2)
                        with col1:
                            update = st.form_submit_button("💾 Update", use_container_width=True)
                        with col2:
                            delete = st.form_submit_button("🗑️ Delete", use_container_width=True, type="primary")
                        if update:
                            update_profit(p_edit_id, pe_date.isoformat(), float(pe_total), pe_note)
                            st.success("✅ Profit updated successfully!")
                            safe_rerun()
                        if delete:
                            delete_profit(p_edit_id)
                            st.success("✅ Profit deleted successfully!")
                            safe_rerun()
            else:
                st.info("📭 No profit entries yet. Add your first entry to get started!")
    with tab3:
        st.subheader("📊 Share Profit")
        st.info("View profit share distribution (kept minimal here)")
        st.write("Use Profit Management to add profit and Client Management to see clients.")
    with tab4:
        st.subheader("🔔 Approvals History")
        hist_df = list_approvals_history_df()
        if hist_df.empty:
            st.info("No approval/rejection history yet.")
        else:
            hist_df["timestamp"] = pd.to_datetime(hist_df["timestamp"]).dt.strftime("%d %b %Y %H:%M:%S")
            st.dataframe(hist_df, use_container_width=True, height=400)

# ----------------------- UI: Client -----------------------
def client_dashboard(client_id):
    client_data = get_client_by_id(client_id)
    if not client_data:
        st.error("Client data not found!")
        return
    st.title(f"📊 Welcome, {client_data['name']}!")
    st.markdown("---")
    # change password option
    with st.expander("🔐 Change Password"):
        old_pw = st.text_input("Current Password", type="password", key="cp_old")
        new_pw = st.text_input("New Password", type="password", key="cp_new")
        confirm_pw = st.text_input("Confirm New Password", type="password", key="cp_confirm")
        if st.button("Change Password"):
            if not old_pw or not new_pw:
                st.error("Please fill both current and new password")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match")
            elif verify_client_by_id(client_id, old_pw):
                change_client_password(client_id, new_pw)
                st.success("Password changed successfully")
            else:
                st.error("Current password incorrect")
    client_ts = get_client_timeseries(client_id)
    profits_df = list_profits_df()
    if not client_ts or len(client_ts['dates']) == 0:
        st.info("📭 No profit data available yet. Please wait for admin to add profit entries.")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div style='background:#667eea;padding:1rem;border-radius:8px;'><h3>💰 Investment</h3><p>Rp {client_data['invested']:,.0f}</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='background:#4facfe;padding:1rem;border-radius:8px;'><h3>📅 Join Date</h3><p>{pd.to_datetime(client_data['join_date']).strftime('%d %b %Y')}</p></div>", unsafe_allow_html=True)
        return
    current_gain = client_ts['cumulative_gain'][-1]
    current_pct = client_ts['pct_return'][-1]
    current_value = client_data['invested'] + current_gain
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div style='background:#667eea;padding:1rem;border-radius:8px;'><h3>💰 Initial Investment</h3><p>Rp {client_data['invested']:,.0f}</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='background:#f093fb;padding:1rem;border-radius:8px;'><h3>📈 Total Profit</h3><p>Rp {current_gain:,.0f}</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='background:#4facfe;padding:1rem;border-radius:8px;'><h3>💎 Current Value</h3><p>Rp {current_value:,.0f}</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div style='background:#43e97b;padding:1rem;border-radius:8px;'><h3>📊 ROI</h3><p>{current_pct:+.2f}%</p></div>", unsafe_allow_html=True)
    st.subheader("📈 Your Investment Performance")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=client_ts['dates'], y=client_ts['pct_return'], mode='lines+markers', line=dict(width=3), marker=dict(size=6)))
    fig.update_layout(xaxis_title="Date", yaxis_title="Return (%)", height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    st.subheader("💼 Your Profit Distribution History")
    if not profits_df.empty:
        allocations = []
        profits_df_sorted = profits_df.sort_values("profit_date")
        for _, r in profits_df_sorted.iterrows():
            date_str = str(r["profit_date"])
            total_profit = r["total_profit"]
            allocs = allocations_for_date(date_str)
            client_alloc = allocs[allocs["id"] == client_id]
            if not client_alloc.empty:
                share = client_alloc.iloc[0]["share"]
                allocated = total_profit * share
                active = client_alloc.iloc[0]["active"]
                allocations.append({
                    "Date": pd.to_datetime(date_str).strftime("%d %b %Y"),
                    "Total Profit": total_profit,
                    "Your Share": f"{share*100:.2f}%",
                    "Your Profit": allocated,
                    "Status": "✅ Active" if active else "❌ Not Active"
                })
        if allocations:
            alloc_df = pd.DataFrame(allocations)
            display_df = alloc_df.copy()
            display_df["Total Profit"] = display_df["Total Profit"].apply(lambda x: f"Rp {x:,.0f}" if x >= 0 else f"-Rp {abs(x):,.0f}")
            display_df["Your Profit"] = display_df["Your Profit"].apply(lambda x: f"Rp {x:,.0f}" if x >= 0 else f"-Rp {abs(x):,.0f}")
            st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)
        else:
            st.info("No profit distribution data available for your account yet.")

# ----------------------- Login & Signup -----------------------
def admin_login_page():
    st.markdown("<div style='text-align:center;padding:2rem;'><h1>🔐 Admin Portal</h1></div>", unsafe_allow_html=True)
    with st.form("admin_login_form"):
        st.markdown("### 🔑 Administrator Login")
        username = st.text_input("Username", placeholder="Enter admin username")
        password = st.text_input("Password", type="password", placeholder="Enter admin password")
        submit = st.form_submit_button("🚀 Login as Admin")
        if submit:
            if verify_admin(username, password):
                st.session_state["user_type"] = "admin"
                st.session_state["username"] = username
                st.success("✅ Admin login successful!")
                safe_rerun()
            else:
                st.error("❌ Invalid admin credentials.")

def client_login_page():
    st.markdown("<div style='text-align:center;padding:2rem;'><h1>👤 Client Portal</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("client_login_form"):
            st.markdown("### 🔑 Client Login (username or id)")
            identifier = st.text_input("Username or Client ID", placeholder="e.g. johndoe or 1")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("🚀 Login")
            if submit:
                if not identifier:
                    st.error("Please enter username or client ID")
                elif not password:
                    st.error("Please enter password")
                else:
                    logged_in = False
                    try:
                        cid = int(identifier)
                        if verify_client_by_id(cid, password):
                            client = get_client_by_id(cid)
                            st.session_state["user_type"] = "client"
                            st.session_state["client_id"] = cid
                            st.session_state["client_name"] = client["name"]
                            st.success(f"✅ Welcome, {client['name']}!")
                            safe_rerun()
                            logged_in = True
                    except Exception:
                        pass
                    if not logged_in:
                        if verify_client_by_username(identifier, password):
                            client = get_client_by_username(identifier)
                            st.session_state["user_type"] = "client"
                            st.session_state["client_id"] = client["id"]
                            st.session_state["client_name"] = client["name"]
                            st.success(f"✅ Welcome, {client['name']}!")
                            safe_rerun()
                        else:
                            st.error("❌ Invalid credentials or account not approved yet. If you just signed up, wait for admin approval.")

    with st.expander("ℹ️ First time? Sign up here"):
        st.markdown("If you don't have an account, use the Sign Up form in the client portal (or the button below).")

def client_signup_page():
    st.markdown("<div style='text-align:center;padding:2rem;'><h1>📝 Client Sign Up</h1></div>", unsafe_allow_html=True)
    with st.form("client_signup_form"):
        st.markdown("### Create your account (will be approved by admin)")
        name = st.text_input("Full Name *")
        username = st.text_input("Desired Username *")
        password = st.text_input("Password *", type="password")
        invested = st.number_input("Investment Amount (Rp) *", min_value=0.0, format="%.2f")
        join_date = st.date_input("Join Date *", value=date_class.today())
        note = st.text_area("Notes (optional)", height=100)
        email = st.text_input("Email (optional) - used for notifications", help="Provide email if you want to receive approval notifications")
        submit = st.form_submit_button("📝 Submit Signup Request")
        if submit:
            if not name or not username or not password or invested <= 0:
                st.error("Please fill required fields and ensure investment > 0")
            elif is_username_taken(username):
                st.error("Username already taken or pending")
            else:
                add_pending_client(name, username, password, float(invested), join_date.isoformat(), note)
                st.success("✅ Signup request submitted. Please wait for admin approval.")
                st.info("Admin will see your request in the dashboard and can approve it. Once approved you can login using your username and password.")

# ----------------------- Main -----------------------
def main():
    init_db()
    load_css()
    if "user_type" not in st.session_state:
        st.session_state["user_type"] = None
    with st.sidebar:
        st.markdown("<div style='text-align:center;padding:1rem;'><h2>💰 Investment Console</h2></div>", unsafe_allow_html=True)
        if st.session_state["user_type"] == "admin":
            st.success("Logged in as Admin")
            st.markdown(f"**{st.session_state.get('username','admin')}**")
            if st.button("🚪 Logout"):
                st.session_state["user_type"] = None
                st.session_state.pop("username", None)
                safe_rerun()
        elif st.session_state["user_type"] == "client":
            st.success("Logged in as Client")
            st.markdown(f"**{st.session_state.get('client_name','Client')}** (ID: {st.session_state.get('client_id')})")
            if st.button("🚪 Logout"):
                st.session_state["user_type"] = None
                st.session_state.pop("client_id", None)
                st.session_state.pop("client_name", None)
                safe_rerun()
        else:
            st.info("Please login or sign up")
            if st.button("🔐 Admin Login"):
                st.session_state["login_page"] = "admin"
                safe_rerun()
            if st.button("👤 Client Login"):
                st.session_state["login_page"] = "client"
                safe_rerun()
            if st.button("📝 Client Sign Up"):
                st.session_state["login_page"] = "signup"
                safe_rerun()
    if st.session_state["user_type"] is None:
        page = st.session_state.get("login_page", "welcome")
        if page == "admin":
            admin_login_page()
        elif page == "client":
            client_login_page()
        elif page == "signup":
            client_signup_page()
        else:
            st.markdown("<div style='text-align:center;padding:3rem;'><h1>Welcome to Investment Consortium</h1></div>", unsafe_allow_html=True)
    elif st.session_state["user_type"] == "admin":
        admin_panel()
    elif st.session_state["user_type"] == "client":
        client_dashboard(st.session_state["client_id"])

if __name__ == "__main__":
    main()
