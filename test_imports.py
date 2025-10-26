#!/usr/bin/env python3
"""
Quick test script to verify imports and basic functionality
Run this before running the main app to catch errors early
"""

import sys

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import streamlit as st
        print("✓ Streamlit imported")
    except ImportError as e:
        print(f"✗ Streamlit import failed: {e}")
        return False
    
    try:
        import sqlite3
        print("✓ SQLite3 imported")
    except ImportError as e:
        print(f"✗ SQLite3 import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ Pandas imported")
    except ImportError as e:
        print(f"✗ Pandas import failed: {e}")
        return False
    
    try:
        from datetime import datetime, date, timedelta
        print("✓ Datetime imported")
    except ImportError as e:
        print(f"✗ Datetime import failed: {e}")
        return False
    
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        print("✓ Plotly imported")
    except ImportError as e:
        print(f"✗ Plotly import failed: {e}")
        print("  Run: pip install plotly")
        return False
    
    try:
        import hashlib
        print("✓ Hashlib imported")
    except ImportError as e:
        print(f"✗ Hashlib import failed: {e}")
        return False
    
    return True

def test_date_functionality():
    """Test date functionality"""
    print("\nTesting date functionality...")
    
    try:
        from datetime import date, datetime
        today = date.today()
        print(f"✓ Today's date: {today}")
        
        dt = datetime.now()
        print(f"✓ Current datetime: {dt}")
        
        iso = today.isoformat()
        print(f"✓ ISO format: {iso}")
        
        return True
    except Exception as e:
        print(f"✗ Date functionality failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Investment Consortium App - Pre-flight Check")
    print("=" * 50)
    
    imports_ok = test_imports()
    date_ok = test_date_functionality()
    
    print("\n" + "=" * 50)
    if imports_ok and date_ok:
        print("✓ All tests passed! You can run the app.")
        print("\nRun the app with:")
        print("  streamlit run app.py")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)
