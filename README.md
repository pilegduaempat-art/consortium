# Konsorsium Investasi - Streamlit Dashboard

A simple Streamlit web app to manage an investment consortium. 
Features:
- Admin panel (login required) to add/edit/delete clients and daily profit entries.
- User dashboard for read-only visualizations.
- Daily profits are distributed to active clients proportionally to their invested capital at that date.
- Cumulative gains per client are shown as percentage of their initial invested capital.

## How to run locally

1. Create virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # mac/linux
venv\Scripts\activate     # windows
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Sharing / GitHub
- Push this repository to GitHub.
- Connect your repo to Streamlit Cloud (https://streamlit.io/cloud) and select `app.py` as entry point.
- Make sure `requirements.txt` is in repo root.

## Notes & Security
- Authentication here is minimal (username `admin`, password `admin123`). Replace with proper auth for production.
- DB uses sqlite `data.db` in app folder. Back it up if needed.