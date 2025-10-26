# 🔧 Troubleshooting Guide

## Quick Fixes

### 1. ModuleNotFoundError: No module named 'plotly'

**Solution:**
```bash
pip install plotly
# or
pip install -r requirements.txt --upgrade
```

### 2. UnboundLocalError with 'date'

**Cause:** Conflict between imported `date` and variable named `date`

**Solution:** Already fixed in latest version. If you still see this:
```python
from datetime import datetime, date, timedelta
```

### 3. sqlite3.OperationalError: no such column: password

**Cause:** Old database without password column

**Solution:** The app will auto-migrate. If it doesn't:
```bash
# Delete old database (WARNING: This deletes all data)
rm data.db

# Or manually add column:
sqlite3 data.db
ALTER TABLE clients ADD COLUMN password TEXT;
UPDATE clients SET password = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92' WHERE password IS NULL;
.exit
```

The hash above is for password: `client123`

### 4. Missing Submit Button Error

**Cause:** Using `st.form()` without `st.form_submit_button()`

**Solution:** Already fixed - all forms have submit buttons in latest version.

### 5. Database is Locked

**Cause:** Multiple connections or app instances

**Solution:**
```bash
# Kill all Streamlit processes
pkill -f streamlit

# Restart the app
streamlit run app.py
```

## Pre-flight Checks

Run the test script before starting:
```bash
python test_imports.py
```

## Common Issues on Streamlit Cloud

### Issue: App won't start

**Check:**
1. `requirements.txt` is in root directory
2. All dependencies are listed
3. No syntax errors in `app.py`

**Solution:**
```bash
# In Streamlit Cloud dashboard:
# 1. Click "Manage app"
# 2. Click "Reboot app"
# 3. Check logs for specific errors
```

### Issue: Database errors

**Cause:** Database file not writable on Streamlit Cloud

**Solution:**
- Streamlit Cloud recreates database on each restart
- Existing clients will have default password: `client123`
- You may need to use Streamlit Secrets for persistent storage

### Issue: Performance is slow

**Solution:**
1. Add caching:
```python
@st.cache_data
def list_clients_df():
    # existing code
```

2. Limit data displayed
3. Use pagination for large tables

## Development Tips

### 1. Local Testing
```bash
# Always test locally first
python test_imports.py
streamlit run app.py

# Check for errors in terminal
```

### 2. Debug Mode
Add to top of app.py:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 3. Database Backup
```bash
# Backup before testing
cp data.db data.db.backup

# Restore if needed
cp data.db.backup data.db
```

### 4. Reset Everything
```bash
# Nuclear option - fresh start
rm data.db
rm -rf __pycache__
pip install -r requirements.txt --force-reinstall
streamlit run app.py
```

## Error Messages Decoded

### "This app has encountered an error"
- **On Streamlit Cloud:** Click "Manage app" → "View logs"
- **Local:** Check terminal output
- **Common causes:** Missing dependencies, database issues, syntax errors

### "Session state error"
- **Cause:** Session state key conflict
- **Solution:** Use unique keys for all widgets:
  ```python
  st.text_input("Name", key="unique_key_name")
  ```

### "DataFrame error"
- **Cause:** Empty DataFrame operations
- **Solution:** Always check if DataFrame is empty:
  ```python
  if not df.empty:
      # process DataFrame
  ```

## Getting Help

### Check Logs
**Local:**
```bash
streamlit run app.py --logger.level=debug
```

**Streamlit Cloud:**
1. Go to app dashboard
2. Click "Manage app"
3. View logs in real-time

### Common Log Locations
- **Linux/Mac:** `~/.streamlit/logs/`
- **Windows:** `%USERPROFILE%\.streamlit\logs\`

### Report Issues
When reporting issues, include:
1. Full error message
2. Python version: `python --version`
3. Streamlit version: `streamlit version`
4. Operating system
5. Steps to reproduce

## Performance Optimization

### 1. Add Caching
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_dashboard_metrics():
    # expensive computation
    return metrics
```

### 2. Lazy Loading
```python
# Load data only when needed
with st.expander("View Details"):
    data = load_expensive_data()
    st.dataframe(data)
```

### 3. Reduce Reruns
```python
# Use forms to batch inputs
with st.form("my_form"):
    input1 = st.text_input("Input 1")
    input2 = st.text_input("Input 2")
    submit = st.form_submit_button("Submit")
```

## Security Checklist

- [ ] Changed default admin password
- [ ] Using HTTPS in production
- [ ] Database file not in git repository
- [ ] Strong passwords for all clients
- [ ] Regular database backups
- [ ] Session timeout configured
- [ ] Input validation on all forms
- [ ] SQL injection protection (using parameterized queries ✓)
- [ ] XSS protection (Streamlit handles this ✓)

## Contact

If none of these solutions work:
1. Check the GitHub issues
2. Search Streamlit community forum
3. Create a new issue with full error details

---

**Last Updated:** October 2025
