import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import matplotlib.pyplot as plt

DB_PATH = "data.db"

# ----------------------- Database helpers -----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        invested REAL NOT NULL,
        join_date TEXT NOT NULL,
        note TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS profits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profit_date TEXT NOT NULL UNIQUE,
        total_profit REAL NOT NULL,
        note TEXT
    )""")
    conn.commit()
    conn.close()

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

# ----------------------- CRUD operations -----------------------
def add_client(name, invested, join_date, note=""):
    run_query("INSERT INTO clients (name, invested, join_date, note) VALUES (?, ?, ?, ?)", (name, invested, join_date, note))

def update_client(client_id, name, invested, join_date, note=""):
    run_query("UPDATE clients SET name=?, invested=?, join_date=?, note=? WHERE id=?", (name, invested, join_date, note, client_id))

def delete_client(client_id):
    run_query("DELETE FROM clients WHERE id=?", (client_id,))

def list_clients_df():
    rows = run_query("SELECT id, name, invested, join_date, note FROM clients ORDER BY id", fetch=True)
    return pd.DataFrame(rows, columns=["id","name","invested","join_date","note"]) if rows else pd.DataFrame(columns=["id","name","invested","join_date","note"])

def add_profit(profit_date, total_profit, note=""):
    run_query("INSERT OR REPLACE INTO profits (profit_date, total_profit, note) VALUES (?, ?, ?)", (profit_date, total_profit, note))

def update_profit(profit_id, profit_date, total_profit, note=""):
    run_query("UPDATE profits SET profit_date=?, total_profit=?, note=? WHERE id=?", (profit_date, total_profit, note, profit_id))

def delete_profit(profit_id):
    run_query("DELETE FROM profits WHERE id=?", (profit_id,))

def list_profits_df():
    rows = run_query("SELECT id, profit_date, total_profit, note FROM profits ORDER BY profit_date", fetch=True)
    return pd.DataFrame(rows, columns=["id","profit_date","total_profit","note"]) if rows else pd.DataFrame(columns=["id","profit_date","total_profit","note"])

# ----------------------- Allocation & calculations -----------------------
def allocations_for_date(target_date):
    # target_date is string 'YYYY-MM-DD'
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

    # Sort profits by date ascending
    profits = profits.sort_values("profit_date")
    # Prepare dataframe to accumulate per-client gains
    client_ids = clients["id"].tolist()
    timeseries = {cid: [] for cid in client_ids}
    dates = []
    # Initialize cumulative gains dict
    cum_gain = {cid: 0.0 for cid in client_ids}

    for _, row in profits.iterrows():
        d = row["profit_date"]
        dates.append(d)
        total_profit = row["total_profit"]
        # find active clients on that date
        active = clients[clients["join_date"] <= d]
        total_active = active["invested"].sum()
        alloc = {}
        if total_active == 0:
            # no active clients -> gains stay zero
            for cid in client_ids:
                timeseries[cid].append(cum_gain[cid])
        else:
            for _, c in clients.iterrows():
                cid = c["id"]
                if c["join_date"] <= d:
                    share = c["invested"] / total_active if total_active>0 else 0.0
                    gain = total_profit * share
                else:
                    share = 0.0
                    gain = 0.0
                cum_gain[cid] += gain
                timeseries[cid].append(cum_gain[cid])
    # Build result: for each client, percentage over invested
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

# ----------------------- Streamlit UI -----------------------
def admin_panel():
    st.header("Admin Dashboard")
    st.write("Gunakan panel ini untuk menambah / edit / hapus **clients** dan **daily profits**.")

    st.subheader("Clients (add / edit / delete)")
    with st.expander("Tambah client baru"):
        name = st.text_input("Nama client", key="new_name")
        invested = st.number_input("Jumlah investasi (mis. 10000)", value=0.0, min_value=0.0, key="new_invested")
        join_date = st.date_input("Tanggal bergabung", value=date.today(), key="new_join_date")
        note = st.text_area("Catatan (opsional)", key="new_note", height=50)
        if st.button("Tambah client"):
            add_client(name, float(invested), join_date.isoformat(), note)
            st.success("Client ditambahkan. Refresh halaman bila perlu.")

    clients_df = list_clients_df()
    if not clients_df.empty:
        st.write(clients_df)
        st.subheader("Edit / Hapus client")
        edit_id = st.selectbox("Pilih client (id) untuk edit/hapus", clients_df["id"].tolist(), key="edit_client_select")
        if edit_id:
            row = clients_df[clients_df["id"]==edit_id].iloc[0]
            e_name = st.text_input("Nama", value=row["name"], key="e_name")
            e_invested = st.number_input("Invested", value=float(row["invested"]), min_value=0.0, key="e_invested")
            e_join = st.date_input("Join date", value=pd.to_datetime(row["join_date"]).date(), key="e_join")
            e_note = st.text_area("Note", value=row["note"], key="e_note")
            if st.button("Update client"):
                update_client(edit_id, e_name, float(e_invested), e_join.isoformat(), e_note)
                st.success("Client updated.")
            if st.button("Delete client"):
                delete_client(edit_id)
                st.success("Client deleted.")

    st.subheader("Daily Profits (add / edit / delete)")
    with st.expander("Tambah / Update daily profit"):
        p_date = st.date_input("Tanggal profit", value=date.today(), key="p_date")
        p_total = st.number_input("Total profit untuk tanggal ini (positif/negatif)", value=0.0, key="p_total")
        p_note = st.text_area("Catatan (opsional)", key="p_note", height=50)
        if st.button("Simpan profit (insert or replace)"):
            add_profit(p_date.isoformat(), float(p_total), p_note)
            st.success("Profit disimpan (insert or replace)")

    profits_df = list_profits_df()
    if not profits_df.empty:
        st.write(profits_df)
        st.subheader("Edit / Hapus profit")
        p_edit_id = st.selectbox("Pilih profit (id)", profits_df["id"].tolist(), key="p_edit_select")
        if p_edit_id:
            prow = profits_df[profits_df["id"]==p_edit_id].iloc[0]
            pe_date = st.date_input("Tanggal profit", value=pd.to_datetime(prow["profit_date"]).date(), key="pe_date")
            pe_total = st.number_input("Total profit", value=float(prow["total_profit"]), key="pe_total")
            pe_note = st.text_area("Note", value=prow["note"], key="pe_note")
            if st.button("Update profit"):
                update_profit(p_edit_id, pe_date.isoformat(), float(pe_total), pe_note)
                st.success("Profit updated.")
            if st.button("Delete profit"):
                delete_profit(p_edit_id)
                st.success("Profit deleted.")

def user_dashboard():
    st.header("User Dashboard (visualisasi hasil)")
    st.write("Halaman ini read-only: pengguna hanya dapat melihat visualisasi pembagian profit berdasarkan modal yang disetor.")

    result, profits_df, clients_df = compute_client_timeseries()

    if not profits_df.empty and not clients_df.empty:
        st.subheader("Tabel alokasi per tanggal (contoh)")
        # Build allocation table for each profit date
        allocations = []
        for _, r in profits_df.iterrows():
            date_str = r["profit_date"]
            total_profit = r["total_profit"]
            allocs = allocations_for_date(date_str)
            allocs = allocs[["id","name","invested","join_date","active","share"]].copy()
            allocs["alloc_profit"] = allocs["share"] * total_profit
            allocs["date"] = date_str
            allocations.append(allocs)
        alloc_df = pd.concat(allocations, ignore_index=True) if allocations else pd.DataFrame()
        st.dataframe(alloc_df)

        st.subheader("Chart: Cumulative return (%) per client terhadap modal awal")
        # Let user pick client(s)
        clients = clients_df.set_index("id").to_dict(orient="index")
        client_options = {cid: clients[cid]["name"] for cid in clients}
        sel = st.multiselect("Pilih client untuk tampilkan (bisa lebih dari satu)", options=list(client_options.keys()), format_func=lambda x: f"{x} - {client_options[x]}")
        if sel:
            plt.figure(figsize=(8,4))
            for cid in sel:
                r = result.get(cid)
                if r and len(r["dates"])>0:
                    dates = r["dates"]
                    pct = r["pct_return"]
                    plt.plot(dates, pct, label=f"{r['name']} (invested {r['invested']})")
            plt.legend()
            plt.ylabel("Cumulative return (%)")
            plt.xlabel("Date")
            plt.grid(True)
            st.pyplot(plt)
        else:
            st.info("Silakan pilih minimal satu client untuk melihat chart.")
    else:
        st.info("Belum ada data clients atau profits. Admin harus menambahkan data terlebih dahulu.")

def main():
    init_db()
    st.title("Konsorsium Investasi - Streamlit Dashboard")
    menu = st.sidebar.selectbox("Mode", ["User View", "Admin Login"])

    if menu == "Admin Login":
        st.sidebar.subheader("Admin Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            # simple hardcoded auth (you should replace with secure auth for production)
            if username == "admin" and password == "admin123":
                st.session_state["is_admin"] = True
                st.success("Login berhasil sebagai admin")
            else:
                st.session_state["is_admin"] = False
                st.error("Login gagal. Gunakan credentials default admin / admin123")
        if st.session_state.get("is_admin"):
            admin_panel()
    else:
        user_dashboard()

if __name__ == "__main__":
    main()