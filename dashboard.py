import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Hype2Stock Dashboard", layout="wide", page_icon="🚀")

# Custom Dark Theme Styling
st.markdown("""
    <style>
    .main { background-color: #0f1117; color: white; }
    .stMetric { background-color: #1a1d27; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .studio-card { 
        background-color: #1a1d27; 
        padding: 24px; 
        border-radius: 16px; 
        border-left: 6px solid #22c55e; 
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .signal-bullish { color: #22c55e; font-weight: bold; }
    .signal-neutral { color: #f59e0b; font-weight: bold; }
    .signal-warning { color: #ef4444; font-weight: bold; }
    .ticker-label { color: #888; font-size: 0.8em; margin-left: 8px; }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🎬 Hype2Stock Dashboard")
st.markdown("### *Where Movie Hype Meets Market Signals*")

def fetch_live_data():
    try:
        r = requests.get("http://localhost:3002/api/dashboard", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        return None

data = fetch_live_data()

# Fallback/Demo Mode logic from Phase B3
if not data:
    st.info("💡 **Demo Mode Active**: Upstream API servers are currently sleeping. Showing high-fidelity mock data.")
    from mockData import MOCK_DASHBOARD
    data = MOCK_DASHBOARD
else:
    st.success("🟢 **Live Mode**: Connected to Port 3002 Middleware.")

# Top Summary Row
col1, col2, col3, col4 = st.columns(4)
studios = data.get('studios', [])

if studios:
    bullish_count = len([s for s in studios if s['signal']['overallSignal'] == "BULLISH"])
    avg_content = sum([s['signal']['contentScore'] for s in studios]) / len(studios)
    avg_hype = sum([s['signal']['hypeScore'] for s in studios]) / len(studios)
    
    col1.metric("🐂 Bullish Signals", bullish_count)
    col2.metric("📽️ Avg Content Score", f"{avg_content:.1f}/100")
    col3.metric("🔥 Avg Hype Score", f"{avg_hype:.1f}/100")
    col4.metric("🕒 Last Updated", data.get('lastUpdated', 'Just now')[:19].replace('T', ' '))

st.divider()

# Main Grid
cols = st.columns(2)
for i, studio in enumerate(studios):
    with cols[i % 2]:
        sig = studio['signal']
        signal_class = f"signal-{sig['overallSignal'].lower()}"
        
        st.markdown(f"""
            <div class="studio-card" style="border-left-color: {sig['badge']['color']}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h2 style="margin:0;">{studio['studio']} <span class="ticker-label">${studio['ticker']}</span></h2>
                    <span class="{signal_class}" style="background: rgba(0,0,0,0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.9em;">
                        {sig['overallSignal']}
                    </span>
                </div>
                <p style="font-size: 1.2em; margin-top: 10px;">
                    Price: <b>${studio['stock']['currentPrice']}</b> 
                    <span style="color: {'#22c55e' if studio['stock']['changePercent'] >= 0 else '#ef4444'}">
                        ({'+' if studio['stock']['changePercent'] > 0 else ''}{studio['stock']['changePercent']}%)
                    </span>
                </p>
                <div style="margin: 15px 0;">
                    <small>CONTENT SCORE: {sig['contentScore']}/100</small>
                    <div style="background: #333; height: 8px; border-radius: 4px;">
                        <div style="background: #3b82f6; width: {sig['contentScore']}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                <div style="margin: 15px 0;">
                    <small>HYPE SCORE: {sig['hypeScore']}/100</small>
                    <div style="background: #333; height: 8px; border-radius: 4px;">
                        <div style="background: #a855f7; width: {sig['hypeScore']}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                <p style="margin-top: 15px; border-top: 1px solid #333; padding-top: 10px;">
                    <i>"{studio['insight']}"</i>
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Stock Trend Sparkline
        history = studio['stock'].get('priceHistory', [])
        if history:
            prices = [p['close'] for p in history]
            st.line_chart(prices, height=120, use_container_width=True)

st.divider()
st.caption("Powered by TMDB + Yahoo Finance | Not Financial Advice | Built with Antigravity AI")
