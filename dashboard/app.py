"""
Streamlit Dashboard for the Silver Prediction Agent.
Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Silver Prediction Agent",
    page_icon="🥈",
    layout="wide"
)

def main():
    with st.sidebar:
        st.title("🥈 Silver Agent")
        page = st.radio("Navigation", ["📊 Dashboard", "📈 Prices", "📰 News", "🤖 Logs"])
    
    if page == "📊 Dashboard":
        st.title("📊 Silver Prediction Dashboard")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Silver (XAG/USD)", "$29.45", "+0.32")
        with col2:
            st.metric("24h High", "$29.78")
        with col3:
            st.metric("Agent Confidence", "78%")
    elif page == "📈 Prices":
        st.title("📈 Price History")
        st.info("Connect Supabase to view data")
    elif page == "📰 News":
        st.title("📰 News Feed")
        st.info("Connect Supabase to view news")
    else:
        st.title("🤖 Agent Logs")
        st.info("Connect Supabase to view logs")

if __name__ == "__main__":
    main()
