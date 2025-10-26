import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from datetime import date as date_class
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
    /* Professional Modern Clean Theme */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap');
    
    :root {
        --primary-blue: #2563eb;
        --primary-dark: #1e40af;
        --accent-green: #10b981;
        --accent-orange: #f59e0b;
        --accent-red: #ef4444;
        --accent-purple: #8b5cf6;
        --bg-main: #f8fafc;
        --bg-secondary: #ffffff;
        --bg-card: #ffffff;
        --bg-hover: #f1f5f9;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        --border-color: #e2e8f0;
        --border-focus: #3b82f6;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Professional metric cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 28px;
        border-radius: 16px;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-lg);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        color: var(--text-primary);
        margin: 12px 0;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--primary-blue), var(--accent-purple));
        border-radius: 16px 0 0 16px;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-xl);
        border-color: var(--primary-blue);
    }
    
    .metric-card h3 {
        margin: 0 0 12px 0;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-secondary);
        font-family: 'Inter', sans-serif;
    }
    
    .metric-card p {
        margin: 0;
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        font-family: 'Poppins', sans-serif;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-dark) 100%);
        border: none;
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        color: white;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
        text-transform: none;
        letter-spacing: 0.3px;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-xl);
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-blue) 100%);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Input fields */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input,
    .stTextArea textarea,
    .stSelectbox>div>div>div,
    .stDateInput>div>div>input {
        background-color: var(--bg-secondary);
        border: 2px solid var(--border-color);
        border-radius: 10px;
        padding: 12px 16px;
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus,
    .stTextArea textarea:focus {
        border-color: var(--border-focus);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        outline: none;
        background-color: #ffffff;
    }
    
    .stTextInput>div>div>input::placeholder,
    .stNumberInput>div>div>input::placeholder,
    .stTextArea textarea::placeholder {
        color: var(--text-muted);
    }
    
    /* DataFrame styling */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-md);
    }
    
    div[data-testid="stDataFrame"] {
        background-color: var(--bg-card);
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid var(--border-color);
        box-shadow: var(--shadow-lg);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }
    
    [data-testid="stSidebar"] hr {
        border-color: var(--border-color);
        margin: 1.5rem 0;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--bg-secondary);
        border: 2px solid var(--border-color);
        border-radius: 10px;
        color: var(--text-primary);
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
        padding: 16px;
        box-shadow: var(--shadow-sm);
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--primary-blue);
        background-color: var(--bg-hover);
        box-shadow: var(--shadow-md);
    }
    
    .streamlit-expanderContent {
        background-color: var(--bg-secondary);
        border: 2px solid var(--border-color);
        border-top: none;
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
        padding: 20px;
    }
    
    /* Alert messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 2px solid var(--accent-green);
        border-radius: 12px;
        padding: 16px 20px;
        color: #065f46;
        box-shadow: var(--shadow-md);
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
        border: 2px solid var(--accent-red);
        border-radius: 12px;
        padding: 16px 20px;
        color: #991b1b;
        box-shadow: var(--shadow-md);
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
        border: 2px solid var(--accent-orange);
        border-radius: 12px;
        padding: 16px 20px;
        color: #92400e;
        box-shadow: var(--shadow-md);
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%);
        border: 2px solid var(--primary-blue);
        border-radius: 12px;
        padding: 16px 20px;
        color: #1e40af;
        box-shadow: var(--shadow-md);
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }
    
    /* Title styling */
    h1 {
        color: var(--text-primary);
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        color: var(--text-primary);
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        margin-top: 2rem;
        margin-bottom: 1rem;
        letter-spacing: -0.3px;
    }
    
    h3 {
        color: var(--text-secondary);
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        margin-bottom: 0.75rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        background-color: transparent;
        color: var(--text-secondary);
        border: none;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--bg-hover);
        color: var(--text-primary);
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--bg-secondary);
        color: var(--primary-blue);
        border-bottom: 3px solid var(--primary-blue);
        box-shadow: var(--shadow-sm);
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: var(--text-primary);
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary);
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricDelta"] {
        color: var(--accent-green);
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }
    
    /* Download button */
    .stDownloadButton>button {
        background: linear-gradient(135deg, var(--accent-green) 0%, #059669 100%);
        border: none;
        box-shadow: var(--shadow-md);
    }
    
    .stDownloadButton>button:hover {
        box-shadow: var(--shadow-xl);
        background: linear-gradient(135deg, #059669 0%, var(--accent-green) 100%);
    }
    
    /* Form styling */
    [data-testid="stForm"] {
        background: var(--bg-card);
        border: 2px solid var(--border-color);
        border-radius: 16px;
        padding: 28px;
        box-shadow: var(--shadow-lg);
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 2rem 0;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-hover);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--primary-blue), var(--primary-dark));
        border-radius: 5px;
        border: 2px solid var(--bg-hover);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--primary-dark), var(--primary-blue));
    }
    
    /* Label styling */
    label {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 8px !important;
    }
    
    /* Radio and checkbox */
    .stRadio > label, .stCheckbox > label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    /* Selectbox & Multiselect */
    .stSelectbox label, .stMultiSelect label {
        color: var(--text-primary) !important;
    }
    
    /* Professional card effect */
    .professional-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        box-shadow: var(--shadow-lg);
        transition: all 0.3s ease;
    }
    
    .professional-card:hover {
        box-shadow: var(--shadow-xl);
        transform: translateY(-2px);
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    
    .badge-primary {
        background-color: rgba(37, 99, 235, 0.1);
        color: var(--primary-blue);
    }
    
    .badge-success {
        background-color: rgba(16, 185, 129, 0.1);
        color: var(--accent-green);
    }
    
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.1);
        color: var(--accent-orange);
    }
    </style>
    """, unsafe_allow_html=True)
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(0, 245, 255, 0.05);
        color: var(--cyber-blue);
        border-color: var(--cyber-blue);
        box-shadow: 0 0 15px rgba(0, 245, 255, 0.2);
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 245, 255, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        color: var(--cyber-blue);
        border-color: var(--cyber-blue);
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: var(--text-primary);
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        text-shadow: 0 0 10px currentColor;
    }
    
    [data-testid="stMetricDelta"] {
        color: var(--cyber-green);
        font-family: 'Rajdhani', sans-serif;
    }
    
    /* Download button with special styling */
    .stDownloadButton>button {
        background: linear-gradient(135deg, var(--cyber-green) 0%, var(--cyber-blue) 100%);
        border: 2px solid var(--cyber-green);
        box-shadow: 0 0 20px rgba(6, 255, 165, 0.3);
    }
    
    .stDownloadButton>button:hover {
        box-shadow: 0 0 40px rgba(6, 255, 165, 0.6);
        border-color: var(--cyber-blue);
    }
    
    /* Form styling */
    [data-testid="stForm"] {
        background: linear-gradient(135deg, rgba(71, 85, 105, 0.9) 0%, rgba(51, 65, 85, 0.9) 100%);
        border: 2px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 217, 255, 0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Divider with glow */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--cyber-blue), transparent);
        margin: 2rem 0;
        box-shadow: 0 0 10px var(--cyber-blue);
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
        border-left: 1px solid var(--border-color);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--cyber-purple), var(--cyber-blue));
        border-radius: 6px;
        border: 2px solid var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--cyber-blue), var(--cyber-pink));
        box-shadow: 0 0 10px var(--cyber-blue);
    }
    
    /* Label styling */
    label {
        color: var(--cyber-blue) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 14px !important;
    }
    
    /* Radio and checkbox */
    .stRadio > label, .stCheckbox > label {
        color: var(--text-primary) !important;
    }
    
    /* Selectbox */
    .stSelectbox label, .stMultiSelect label {
        color: var(--cyber-blue) !important;
    }
    
    /* Cyber grid lines animation */
    @keyframes gridPulse {
        0%, 100% { opacity: 0.03; }
        50% { opacity: 0.08; }
    }
    
    .stApp {
        animation: gridPulse 4s ease-in-out infinite;
    }
    
    /* Neon text effect */
    .neon-text {
        color: var(--cyber-blue);
        text-shadow: 
            0 0 7px var(--cyber-blue),
            0 0 10px var(--cyber-blue),
            0 0 21px var(--cyber-blue),
            0 0 42px var(--cyber-purple);
    }
    
    /* Card scan line effect */
    @keyframes scan {
        0% { top: 0; }
        100% { top: 100%; }
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
    target = datetime.strptime(target_date, "%Y-%m-%d").date() if isinstance(target_date, str) else target_date
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
    tab1, tab2, tab3 = st.tabs(["👥 Client Management", "💹 Profit Management", "📊 Share Profit"])
    
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
                    join_date = st.date_input("Join Date *", value=date_class.today())
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
                    p_date = st.date_input("Profit Date *", value=date_class.today())
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
    
    with tab3:
        st.subheader("📊 Profit Share Distribution")
        st.markdown("View detailed profit distribution across all clients and dates")
        
        clients_df = list_clients_df()
        profits_df = list_profits_df()
        
        if clients_df.empty:
            st.warning("⚠️ No clients registered yet. Please add clients first.")
        elif profits_df.empty:
            st.warning("⚠️ No profit entries yet. Please add profit entries first.")
        else:
            # Get timeseries data for all clients
            result, _, _ = compute_client_timeseries()
            
            # Build comprehensive share profit table
            share_data = []
            
            for client_id, client_ts in result.items():
                client_info = clients_df[clients_df['id'] == client_id].iloc[0]
                
                if len(client_ts['dates']) > 0:
                    for idx, date in enumerate(client_ts['dates']):
                        profit_row = profits_df[pd.to_datetime(profits_df['profit_date']).dt.date == date]
                        
                        if not profit_row.empty:
                            daily_profit = profit_row.iloc[0]['total_profit']
                            
                            # Calculate share for this date
                            allocs = allocations_for_date(date.isoformat())
                            client_alloc = allocs[allocs['id'] == client_id]
                            
                            if not client_alloc.empty and client_alloc.iloc[0]['active']:
                                share_pct = client_alloc.iloc[0]['share']
                                share_amount = daily_profit * share_pct
                                cumulative_gain = client_ts['cumulative_gain'][idx]
                                total_balance = client_info['invested'] + cumulative_gain
                                
                                share_data.append({
                                    'Client ID': client_id,
                                    'Client Name': client_info['name'],
                                    'Profit Date': date,
                                    'Initial Invested': client_info['invested'],
                                    'Share (%)': share_pct * 100,
                                    'Daily Profit': daily_profit,
                                    'Share Profit': share_amount,
                                    'Cumulative Profit': cumulative_gain,
                                    'Total Balance': total_balance
                                })
            
            if share_data:
                share_df = pd.DataFrame(share_data)
                
                # Sorting and filtering options
                st.markdown("### ⚙️ Filter & Sort Options")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    sort_by = st.selectbox(
                        "Sort by",
                        ["Profit Date", "Client ID", "Share Profit", "Total Balance"],
                        index=0,
                        key="sort_by_select"
                    )
                
                with col2:
                    sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True, key="sort_order_radio")
                
                with col3:
                    filter_client = st.multiselect(
                        "Filter by Client",
                        options=clients_df['id'].tolist(),
                        format_func=lambda x: f"ID {x} - {clients_df[clients_df['id']==x]['name'].iloc[0]}",
                        key="filter_client_multi"
                    )
                
                # Apply filters
                display_df = share_df.copy()
                if filter_client:
                    display_df = display_df[display_df['Client ID'].isin(filter_client)]
                
                # Apply sorting
                sort_col_map = {
                    "Profit Date": "Profit Date",
                    "Client ID": "Client ID",
                    "Share Profit": "Share Profit",
                    "Total Balance": "Total Balance"
                }
                ascending = sort_order == "Ascending"
                display_df = display_df.sort_values(sort_col_map[sort_by], ascending=ascending)
                
                # Format for display
                format_df = display_df.copy()
                format_df['Profit Date'] = pd.to_datetime(format_df['Profit Date']).dt.strftime('%d %b %Y')
                format_df['Initial Invested'] = format_df['Initial Invested'].apply(lambda x: f"Rp {x:,.0f}")
                format_df['Share (%)'] = format_df['Share (%)'].apply(lambda x: f"{x:.2f}%")
                format_df['Daily Profit'] = format_df['Daily Profit'].apply(
                    lambda x: f"Rp {x:,.0f}" if x >= 0 else f"-Rp {abs(x):,.0f}"
                )
                format_df['Share Profit'] = format_df['Share Profit'].apply(
                    lambda x: f"Rp {x:,.0f}" if x >= 0 else f"-Rp {abs(x):,.0f}"
                )
                format_df['Cumulative Profit'] = format_df['Cumulative Profit'].apply(
                    lambda x: f"Rp {x:,.0f}" if x >= 0 else f"-Rp {abs(x):,.0f}"
                )
                format_df['Total Balance'] = format_df['Total Balance'].apply(lambda x: f"Rp {x:,.0f}")
                
                # Display summary metrics
                st.markdown("### 📈 Summary Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                total_records = len(display_df)
                total_share_profit = display_df['Share Profit'].sum()
                avg_share_profit = display_df['Share Profit'].mean()
                unique_clients = display_df['Client ID'].nunique()
                
                with col1:
                    st.metric("Total Records", f"{total_records:,}")
                with col2:
                    st.metric("Total Shared Profit", f"Rp {total_share_profit:,.0f}")
                with col3:
                    st.metric("Avg Share Profit", f"Rp {avg_share_profit:,.0f}")
                with col4:
                    st.metric("Active Clients", unique_clients)
                
                st.markdown("---")
                
                # Display main table
                st.markdown("### 📋 Detailed Share Profit Table")
                st.dataframe(
                    format_df,
                    use_container_width=True,
                    height=500,
                    hide_index=True
                )
                
                # Download button
                st.markdown("---")
                csv = display_df.to_csv(index=False)
                today_str = date_class.today().isoformat()
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"share_profit_distribution_{today_str}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # Additional analytics
                with st.expander("📊 View Analytics Charts"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Profit distribution by client
                        st.markdown("#### Total Profit by Client")
                        client_totals = display_df.groupby(['Client ID', 'Client Name'])['Share Profit'].sum().reset_index()
                        client_totals = client_totals.sort_values('Share Profit', ascending=False)
                        
                        fig = go.Figure(go.Bar(
                            x=client_totals['Share Profit'],
                            y=client_totals['Client Name'],
                            orientation='h',
                            marker=dict(
                                color=client_totals['Share Profit'],
                                colorscale='Viridis',
                                showscale=False
                            ),
                            text=client_totals['Share Profit'].apply(lambda x: f"Rp {x:,.0f}"),
                            textposition='outside',
                            hovertemplate='<b>%{y}</b><br>Total: Rp %{x:,.0f}<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            xaxis_title="Total Share Profit (Rp)",
                            yaxis_title="Client",
                            height=400,
                            template="plotly_white",
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='#ffffff',
                            showlegend=False,
                            font=dict(color='#0f172a', family='Inter, sans-serif')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Profit trend over time
                        st.markdown("#### Profit Trend Over Time")
                        date_totals = display_df.groupby('Profit Date')['Share Profit'].sum().reset_index()
                        date_totals['Profit Date'] = pd.to_datetime(date_totals['Profit Date'])
                        date_totals = date_totals.sort_values('Profit Date')
                        
                        fig = go.Figure(go.Scatter(
                            x=date_totals['Profit Date'],
                            y=date_totals['Share Profit'],
                            mode='lines+markers',
                            line=dict(width=3, color='#667eea'),
                            marker=dict(size=8, color='#667eea'),
                            fill='tozeroy',
                            fillcolor='rgba(102, 126, 234, 0.2)',
                            hovertemplate='<b>Date:</b> %{x}<br><b>Total:</b> Rp %{y:,.0f}<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Total Share Profit (Rp)",
                            height=400,
                            template="plotly_white",
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='#ffffff',
                            showlegend=False,
                            font=dict(color='#0f172a', family='Inter, sans-serif')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📭 No share profit data available yet.")

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
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#ffffff',
        showlegend=False,
        font=dict(color='#0f172a', family='Inter, sans-serif')
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
    <div style='text-align: center; padding: 3rem 0 2rem 0;'>
        <div style='background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); 
                    width: 80px; height: 80px; border-radius: 20px; 
                    display: inline-flex; align-items: center; justify-content: center;
                    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.3);
                    margin-bottom: 1.5rem;'>
            <span style='font-size: 40px;'>🔐</span>
        </div>
        <h1 style='color: #0f172a; font-size: 2rem; margin: 0; font-weight: 700;'>Admin Portal</h1>
        <p style='color: #64748b; font-size: 1rem; margin-top: 0.5rem;'>Secure access to management dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("admin_login_form"):
            st.markdown("### 🔑 Administrator Login")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_a, col_b = st.columns([1, 1])
            with col_b:
                submit = st.form_submit_button("Sign In", use_container_width=True)
            
            if submit:
                if verify_admin(username, password):
                    st.session_state["user_type"] = "admin"
                    st.session_state["username"] = username
                    st.success("✅ Login successful! Redirecting to dashboard...")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please check your username and password.")

def client_login_page():
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0 2rem 0;'>
        <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    width: 80px; height: 80px; border-radius: 20px; 
                    display: inline-flex; align-items: center; justify-content: center;
                    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
                    margin-bottom: 1.5rem;'>
            <span style='font-size: 40px;'>👤</span>
        </div>
        <h1 style='color: #0f172a; font-size: 2rem; margin: 0; font-weight: 700;'>Client Portal</h1>
        <p style='color: #64748b; font-size: 1rem; margin-top: 0.5rem;'>Access your investment dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("client_login_form"):
            st.markdown("### 🔑 Client Login")
            
            client_id_input = st.text_input(
                "Client ID",
                placeholder="Enter your Client ID",
                help="Your unique client identifier provided by administrator"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )
            
            col_a, col_b = st.columns([1, 1])
            with col_b:
                submit = st.form_submit_button("Sign In", use_container_width=True)
            
            if submit:
                if not client_id_input:
                    st.error("⚠️ Please enter your Client ID")
                elif not password:
                    st.error("⚠️ Please enter your password")
                else:
                    try:
                        client_id = int(client_id_input)
                        
                        client_data = get_client_by_id(client_id)
                        if not client_data:
                            st.error("❌ Client ID not found. Please check your ID.")
                        elif verify_client(client_id, password):
                            st.session_state["user_type"] = "client"
                            st.session_state["client_id"] = client_id
                            st.session_state["client_name"] = client_data["name"]
                            st.success(f"✅ Welcome, {client_data['name']}! Loading your dashboard...")
                            st.rerun()
                        else:
                            st.error("❌ Invalid password. Please try again.")
                    except ValueError:
                        st.error("⚠️ Client ID must be a number")
        
        with st.expander("ℹ️ Need Help?"):
            st.info("**First time logging in?** Your default password is: `client123`")
            st.info("**Your Client ID** was provided by the administrator when your account was created.")
            st.warning("**Contact administrator to:**")
            st.markdown("""
            - Get your Client ID if you don't have it
            - Reset your password if forgotten
            - Change your default password for security
            """)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%); 
                    padding: 1rem; border-radius: 12px; border: 2px solid #f59e0b;'>
            <strong style='color: #92400e;'>🔒 Security Notice:</strong><br>
            <span style='color: #92400e;'>Never share your Client ID or password with anyone. The administrator will never ask for your password.</span>
        </div>
        """, unsafe_allow_html=True)

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
        <div style='text-align: center; padding: 1rem 0; color: #64748b; font-size: 0.85rem;'>
            <hr style='border: 1px solid #e2e8f0; margin: 1.5rem 0;'>
            <p style='margin: 0.5rem 0;'>© 2025 Investment Consortium</p>
            <p style='margin: 0; font-weight: 500;'>Secure • Professional • Reliable</p>
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
                <div style='background: linear-gradient(135deg, #2563eb 0%, #8b5cf6 100%); 
                            width: 100px; height: 100px; border-radius: 24px; 
                            display: inline-flex; align-items: center; justify-content: center;
                            box-shadow: 0 20px 40px rgba(37, 99, 235, 0.3);
                            margin-bottom: 2rem;'>
                    <span style='font-size: 50px;'>💰</span>
                </div>
                <h1 style='color: #0f172a; font-size: 2.5rem; font-weight: 800; margin: 0;'>Investment Consortium</h1>
                <p style='color: #64748b; font-size: 1.1rem; margin-top: 1rem;'>
                    Professional Investment Management Platform
                </p>
                <hr style='width: 50%; margin: 2rem auto; border: 1px solid #e2e8f0;'>
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
