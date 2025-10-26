import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import hashlib

DB_PATH = "data.db"

# ----------------------- Page Config -----------------------
st.set_page_config(
    page_title="Investment Consortium Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------- Custom CSS -----------------------
def load_css():
    st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ecc71;
        --danger-color: #e74c3c;
        --background-color: #f8f9fa;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom card styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
        margin: 10px 0;
    }
    
    .metric-card h3 {
        margin: 0;
        font-size: 14px;
        font-weight: 500;
        opacity: 0.9;
    }
    
    .metric-card p {
        margin: 10px 0 0 0;
        font-size: 28px;
        font-weight: 700;
    }
    
    /* Login card styling */
    .login-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Input field styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 0.5rem;
    }
    
    /* DataFrame styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    /* Success/Error message styling */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Title styling */
    h1 {
        color: #2c3e50;
        font-weight: 700;
    }
    
    h2 {
        color: #34495e;
        font-weight: 600;
        margin-top: 2rem;
    }
    
    h3 {
        color: #546e7a;
        font-weight: 500;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ----------------------- Password Hashing -----------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------------- Database helpers -----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create clients table
    c.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        invested REAL NOT NULL,
        join_date TEXT NOT NULL,
        note TEXT
    )""")
    
    # Check if password column exists, if not add it
    c.execute("PRAGMA table_info(clients)")
    columns = [column[1] for column in c.fetchall()]
    if 'password' not in columns:
        c.execute("ALTER TABLE clients ADD COLUMN password TEXT")
        # Set default password for existing clients
        default_password = hash_password("client123")
        c.execute("UPDATE clients SET password = ? WHERE password IS NULL", (default_password,))
        print("✅ Added password column to clients table and set default passwords")
    
    # Create profits table
    c.execute("""
    CREATE TABLE IF NOT EXISTS profits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profit_date TEXT NOT NULL UNIQUE,
        total_profit REAL NOT NULL,
        note TEXT
    )""")
    
    # Create admin_users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )""")
    
    # Create default admin if not exists
    c.execute("SELECT COUNT(*) FROM admin_users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO admin_users (username, password) VALUES (?, ?)", 
                 ("admin", hash_password("admin123")))
        print("✅ Created default admin user")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

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

# ----------------------- Authentication -----------------------
def verify_admin(username, password):
    rows = run_query("SELECT password FROM admin_users WHERE username=?", (username,), fetch=True)
    if rows:
        return rows[0][0] == hash_password(password)
    return False

def verify_client(client_id, password):
    rows = run_query("SELECT password FROM clients WHERE id=?", (client_id,), fetch=True)
    if rows:
        return rows[0][0] == hash_password(password)
    return False

def get_client_by_id(client_id):
    rows = run_query("SELECT id, name, invested, join_date, note FROM clients WHERE id=?", (client_id,), fetch=True)
    if rows:
        return {
            "id": rows[0][0],
            "name": rows[0][1],
            "invested": rows[0][2],
            "join_date": rows[0][3],
            "note": rows[0][4]
        }
    return None

# ----------------------- CRUD operations -----------------------
def add_client(name, invested, join_date, note="", password=""):
    hashed_pw = hash_password(password) if password else hash_password("client123")
    run_query("INSERT INTO clients (name, invested, join_date, note, password) VALUES (?, ?, ?, ?, ?)", 
              (name, invested, join_date, note, hashed_pw))

def update_client(client_id, name, invested, join_date, note="", password=None):
    if password:
        run_query("UPDATE clients SET name=?, invested=?, join_date=?, note=?, password=? WHERE id=?", 
                 (name, invested, join_date, note, hash_password(password), client_id))
    else:
        run_query("UPDATE clients SET name=?, invested=?, join_date=?, note=? WHERE id=?", 
                 (name, invested, join_date, note, client_id))

def delete_client(client_id):
    run_query("DELETE FROM clients WHERE id=?", (client_id,))

def list_clients_df():
    rows = run_query("SELECT id, name, invested, join_date, note FROM clients ORDER BY id", fetch=True)
    return pd.DataFrame(rows, columns=["id","name","invested","join_date","note"]) if rows else pd.DataFrame(columns=["id","name","invested","join_date","note"])

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

# ----------------------- Allocation & calculations -----------------------
def allocations_for_date(target_date):
    clients = list_clients_df()
    if clients.empty:
        return pd.DataFrame(columns=["id","name","invested","join_date","active","share","alloc_profit"])
    clients["join_date"] = pd.to_datetime(clients["join_date"]).dt.date
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
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
    """Get timeseries data for a specific client"""
    result, profits, clients = compute_client_timeseries()
    return result.get(client_id, None)

# ----------------------- Dashboard Metrics -----------------------
def get_dashboard_metrics():
    clients = list_clients_df()
    profits = list_profits_df()
    
    total_clients = len(clients)
    total_invested = clients["invested"].sum() if not clients.empty else 0
    total_profit = profits["total_profit"].sum() if not profits.empty else 0
    avg_return = (total_profit / total_invested * 100) if total_invested > 0 else 0
    
    return {
        "total_clients": total_clients,
        "total_invested": total_invested,
        "total_profit": total_profit,
        "avg_return": avg_return
    }

# ----------------------- Admin Panel -----------------------
def admin_panel():
    st.title("🔐 Admin Dashboard")
    st.markdown("---")
    
    # Metrics Overview
    metrics = get_dashboard_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <h3>👥 Total Clients</h3>
            <p>{metrics['total_clients']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3>💰 Total Invested</h3>
            <p>Rp {metrics['total_invested']:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h3>📈 Total Profit</h3>
            <p>Rp {metrics['total_profit']:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <h3>📊 Avg Return</h3>
            <p>{metrics['avg_return']:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for better organization
    tab1, tab2 = st.tabs(["👥 Client Management", "💹 Profit Management"])
    
    with tab1:
        st.subheader("Client Management")
        
        # Check if there are clients with default password
        clients_df = list_clients_df()
        if not clients_df.empty:
            # Check for clients that might have default password
            st.info("ℹ️ **Note:** Existing clients from old database have default password: `client123`. Please update their passwords for security.")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            with st.expander("➕ Add New Client", expanded=True):
                with st.form("add_client_form"):
                    name = st.text_input("Client Name *")
                    invested = st.number_input("Investment Amount (Rp) *", min_value=0.0, format="%.2f")
                    join_date = st.date_input("Join Date *", value=date.today())
                    password = st.text_input("Client Password *", type="password", help="Password for client login")
                    note = st.text_area("Notes (optional)", height=100)
                    submit = st.form_submit_button("💾 Add Client", use_container_width=True)
                    
                    if submit:
                        if name and invested > 0 and password:
                            add_client(name, float(invested), join_date.isoformat(), note, password)
                            st.success(f"✅ Client '{name}' added successfully!")
                            st.rerun()
                        else:
                            st.error("⚠️ Please fill in all required fields including password")
        
        with col2:
            clients_df = list_clients_df()
            if not clients_df.empty:
                st.markdown("### 📋 Current Clients")
                
                # Format the dataframe for better display
                display_df = clients_df.copy()
                display_df["invested"] = display_df["invested"].apply(lambda x: f"Rp {x:,.0f}")
                display_df["join_date"] = pd.to_datetime(display_df["join_date"]).dt.strftime("%d %b %Y")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                
                st.markdown("### ✏️ Edit / Delete Client")
                edit_id = st.selectbox(
                    "Select Client ID", 
                    clients_df["id"].tolist(),
                    format_func=lambda x: f"ID {x} - {clients_df[clients_df['id']==x]['name'].iloc[0]}"
                )
                
                if edit_id:
                    row = clients_df[clients_df["id"]==edit_id].iloc[0]
                    
                    with st.form("edit_client_form"):
                        e_name = st.text_input("Name", value=row["name"])
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
                            if e_password:
                                update_client(edit_id, e_name, float(e_invested), e_join.isoformat(), e_note, e_password)
                            else:
                                update_client(edit_id, e_name, float(e_invested), e_join.isoformat(), e_note)
                            st.success("✅ Client updated successfully!")
                            st.rerun()
                        
                        if delete:
                            delete_client(edit_id)
                            st.success("✅ Client deleted successfully!")
                            st.rerun()
            else:
                st.info("📭 No clients yet. Add your first client to get started!")
    
    with tab2:
        st.subheader("Profit Management")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            with st.expander("➕ Add Daily Profit", expanded=True):
                with st.form("add_profit_form"):
                    p_date = st.date_input("Profit Date *", value=date.today())
                    p_total = st.number_input("Total Profit (Rp) *", value=0.0, format="%.2f")
                    p_note = st.text_area("Notes (optional)", height=100)
                    submit = st.form_submit_button("💾 Save Profit", use_container_width=True)
                    
                    if submit:
                        add_profit(p_date.isoformat(), float(p_total), p_note)
                        st.success(f"✅ Profit for {p_date.strftime('%d %b %Y')} saved!")
                        st.rerun()
        
        with col2:
            profits_df = list_profits_df()
            if not profits_df.empty:
                st.markdown("### 📊 Profit History")
                
                # Format the dataframe
                display_df = profits_df.copy()
                display_df["total_profit"] = display_df["total_profit"].apply(
                    lambda x: f"Rp {x:,.0f}" if x >= 0 else f"-Rp {abs(x):,.0f}"
                )
                display_df["profit_date"] = pd.to_datetime(display_df["profit_date"]).dt.strftime("%d %b %Y")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                
                st.markdown("### ✏️ Edit / Delete Profit Entry")
                p_edit_id = st.selectbox(
                    "Select Profit ID",
                    profits_df["id"].tolist(),
                    format_func=lambda x: f"ID {x} - {pd.to_datetime(profits_df[profits_df['id']==x]['profit_date'].iloc[0]).strftime('%d %b %Y')}"
                )
                
                if p_edit_id:
                    prow = profits_df[profits_df["id"]==p_edit_id].iloc[0]
                    
                    with st.form("edit_profit_form"):
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
                            st.rerun()
                        
                        if delete:
                            delete_profit(p_edit_id)
                            st.success("✅ Profit deleted successfully!")
                            st.rerun()
            else:
                st.info("📭 No profit entries yet. Add your first entry to get started!")

# ----------------------- Client Personal Dashboard -----------------------
def client_dashboard(client_id):
    client_data = get_client_by_id(client_id)
    if not client_data:
        st.error("Client data not found!")
        return
    
    st.title(f"📊 Welcome, {client_data['name']}!")
    st.markdown("---")
    
    # Get client-specific data
    client_ts = get_client_timeseries(client_id)
    profits_df = list_profits_df()
    
    if not client_ts or len(client_ts['dates']) == 0:
        st.info("📭 No profit data available yet. Please wait for admin to add profit entries.")
        
        # Show basic info
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <h3>💰 Your Investment</h3>
                <p>Rp {client_data['invested']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <h3>📅 Join Date</h3>
                <p>{pd.to_datetime(client_data['join_date']).strftime('%d %b %Y')}</p>
            </div>
            """, unsafe_allow_html=True)
        return
    
    # Calculate current values
    current_gain = client_ts['cumulative_gain'][-1]
    current_pct = client_ts['pct_return'][-1]
    current_value = client_data['invested'] + current_gain
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <h3>💰 Initial Investment</h3>
            <p>Rp {client_data['invested']:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3>📈 Total Profit</h3>
            <p>Rp {current_gain:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h3>💎 Current Value</h3>
            <p>Rp {current_value:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        color = "#43e97b" if current_pct >= 0 else "#e74c3c"
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {'#38f9d7' if current_pct >= 0 else '#c0392b'} 100%);">
            <h3>📊 ROI</h3>
            <p>{current_pct:+.2f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Performance Chart
    st.subheader("📈 Your Investment Performance")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        chart_type = st.radio("Chart Type", ["Line", "Area"], horizontal=True)
    
    fig = go.Figure()
    
    if chart_type == "Area":
        fig.add_trace(go.Scatter(
            x=client_ts['dates'],
            y=client_ts['pct_return'],
            mode='lines',
            fill='tozeroy',
            line=dict(width=2, color='#667eea'),
            fillcolor='rgba(102, 126, 234, 0.3)',
            hovertemplate='<b>Date:</b> %{x}<br><b>Return:</b> %{y:.2f}%<extra></extra>'
        ))
    else:
        fig.add_trace(go.Scatter(
            x=client_ts['dates'],
            y=client_ts['pct_return'],
            mode='lines+markers',
            line=dict(width=3, color='#667eea'),
            marker=dict(size=6, color='#667eea'),
            hovertemplate='<b>Date:</b> %{x}<br><b>Return:</b> %{y:.2f}%<extra></extra>'
        ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Return (%)",
        hovermode='x',
        template="plotly_white",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Profit Distribution Table
    st.markdown("---")
    st.subheader("💼 Your Profit Distribution History")
    
    if not profits_df.empty:
        allocations = []
        profits_df_sorted = profits_df.sort_values("profit_date")
        
        for _, r in profits_df_sorted.iterrows():
            date_str = str(r["profit_date"])
            total_profit = r["total_profit"]
            
            # Get allocation for this date
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
            
            # Format display
            display_df = alloc_df.copy()
            display_df["Total Profit"] = display_df["Total Profit"].apply(
                lambda x: f"Rp {x:,.0f}" if x >= 0 else f"-Rp {abs(x):,.0f}"
            )
            display_df["Your Profit"] = display_df["Your Profit"].apply(
                lambda x: f"Rp {x:,.0f}" if x >= 0 else f"-Rp {abs(x):,.0f}"
            )
            
            st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)
        else:
            st.info("No profit distribution data available for your account yet.")

# ----------------------- Login Pages -----------------------
def admin_login_page():
    st.markdown("""
    <div style='text-align: center; padding: 2rem;'>
        <h1 style='color: #2c3e50; font-size: 3rem;'>🔐</h1>
        <h1 style='color: #2c3e50;'>Admin Portal</h1>
        <p style='color: #7f8c8d; font-size: 1.2rem;'>Secure Administrative Access</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("admin_login_form"):
            st.markdown("### 🔑 Administrator Login")
            username = st.text_input("Username", placeholder="Enter admin username")
            password = st.text_input("Password", type="password", placeholder="Enter admin password")
            submit = st.form_submit_button("🚀 Login as Admin", use_container_width=True)
            
            if submit:
                if verify_admin(username, password):
                    st.session_state["user_type"] = "admin"
                    st.session_state["username"] = username
                    st.success("✅ Admin login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("❌ Invalid admin credentials. Please try again.")
        
        with st.expander("ℹ️ Default Admin Credentials"):
            st.code("Username: admin\nPassword: admin123")
            st.warning("⚠️ Change default credentials in production!")

def client_login_page():
    st.markdown("""
    <div style='text-align: center; padding: 2rem;'>
        <h1 style='color: #2c3e50; font-size: 3rem;'>👤</h1>
        <h1 style='color: #2c3e50;'>Client Portal</h1>
        <p style='color: #7f8c8d; font-size: 1.2rem;'>Access Your Investment Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Get list of clients for dropdown
        clients_df = list_clients_df()
        
        if clients_df.empty:
            st.warning("⚠️ No clients registered yet. Please contact admin.")
            return
        
        with st.form("client_login_form"):
            st.markdown("### 🔑 Client Login")
            
            client_options = {row['id']: f"{row['name']} (ID: {row['id']})" 
                            for _, row in clients_df.iterrows()}
            
            selected_id = st.selectbox(
                "Select Your Account",
                options=list(client_options.keys()),
                format_func=lambda x: client_options[x]
            )
            
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("🚀 Login as Client", use_container_width=True)
            
            if submit:
                if verify_client(selected_id, password):
                    st.session_state["user_type"] = "client"
                    st.session_state["client_id"] = selected_id
                    client_name = clients_df[clients_df['id'] == selected_id].iloc[0]['name']
                    st.session_state["client_name"] = client_name
                    st.success(f"✅ Welcome, {client_name}! Redirecting...")
                    st.rerun()
                else:
                    st.error("❌ Invalid password. Please try again.")
        
        with st.expander("ℹ️ Need Help?"):
            st.info("**First time logging in?** Your default password is: `client123`")
            st.info("If you forgot your password, please contact the administrator.")
            st.info("Your Client ID can be found in communications from the administrator.")
            st.warning("⚠️ Please change your default password after first login by contacting admin.")

# ----------------------- Main Application -----------------------
def main():
    init_db()
    load_css()
    
    # Initialize session state
    if "user_type" not in st.session_state:
        st.session_state["user_type"] = None
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0; color: white;'>
            <h1 style='color: white; font-size: 2.5rem;'>💰</h1>
            <h2 style='color: white;'>Investment Console</h2>
            <hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1rem 0;'>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Show current user status
        if st.session_state["user_type"] == "admin":
            st.success(f"✅ Logged in as Admin")
            st.markdown(f"**User:** {st.session_state.get('username', 'Admin')}")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state["user_type"] = None
                st.session_state.pop("username", None)
                st.rerun()
                
        elif st.session_state["user_type"] == "client":
            st.success(f"✅ Logged in as Client")
            st.markdown(f"**Name:** {st.session_state.get('client_name', 'Client')}")
            st.markdown(f"**ID:** {st.session_state.get('client_id', 'N/A')}")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state["user_type"] = None
                st.session_state.pop("client_id", None)
                st.session_state.pop("client_name", None)
                st.rerun()
        else:
            st.info("👋 Please login to continue")
            
            st.markdown("### 🎯 Choose Login Type")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔐 Admin", use_container_width=True):
                    st.session_state["login_page"] = "admin"
                    st.rerun()
            with col2:
                if st.button("👤 Client", use_container_width=True):
                    st.session_state["login_page"] = "client"
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Quick Stats (visible to all)
        if st.session_state["user_type"]:
            metrics = get_dashboard_metrics()
            st.markdown("### 📊 Quick Stats")
            st.metric("Total Investors", metrics['total_clients'])
            st.metric("Total Investment", 
                     f"Rp {metrics['total_invested']/1000000:.1f}M" if metrics['total_invested'] >= 1000000 
                     else f"Rp {metrics['total_invested']:,.0f}")
            st.metric("Total Profit", 
                     f"Rp {metrics['total_profit']/1000000:.1f}M" if abs(metrics['total_profit']) >= 1000000 
                     else f"Rp {metrics['total_profit']:,.0f}")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style='text-align: center; color: rgba(255,255,255,0.6); font-size: 0.8rem; padding: 1rem 0;'>
            <hr style='border: 1px solid rgba(255,255,255,0.1); margin: 1rem 0;'>
            <p>© 2025 Investment Consortium</p>
            <p>Secure • Professional • Reliable</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main Content Area - Route based on user type
    if st.session_state["user_type"] is None:
        # Show login page based on selection
        login_page_type = st.session_state.get("login_page", "select")
        
        if login_page_type == "admin":
            admin_login_page()
        elif login_page_type == "client":
            client_login_page()
        else:
            # Welcome page
            st.markdown("""
            <div style='text-align: center; padding: 3rem 0;'>
                <h1 style='color: #2c3e50; font-size: 3.5rem;'>💰</h1>
                <h1 style='color: #2c3e50; font-size: 2.5rem;'>Investment Consortium Dashboard</h1>
                <p style='color: #7f8c8d; font-size: 1.3rem; margin-top: 1rem;'>
                    Professional Investment Management Platform
                </p>
                <hr style='width: 50%; margin: 2rem auto; border: 1px solid #e0e0e0;'>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown("### 🎯 Welcome!")
                st.markdown("""
                Choose your login type to access the platform:
                
                **🔐 Admin Portal**
                - Manage client accounts
                - Record daily profits/losses
                - View comprehensive analytics
                - Full system access
                
                **👤 Client Portal**
                - View your investment performance
                - Track returns and profits
                - Access personal dashboard
                - Download statements
                """)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.info("👈 Please select your login type from the sidebar to continue")
                
    elif st.session_state["user_type"] == "admin":
        admin_panel()
        
    elif st.session_state["user_type"] == "client":
        client_dashboard(st.session_state["client_id"])

if __name__ == "__main__":
    main()
