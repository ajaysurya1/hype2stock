# Hype2Stock - Streamlit Dashboard App
# Movie Hype and Stock Performance Tracker

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from engine import get_full_dashboard, STUDIOS

# 1. Page Configuration
st.set_page_config(
    page_title="Hype2Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0f111a 0%, #161924 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar style */
    [data-testid="stSidebar"] {
        background-color: rgba(26, 29, 43, 0.8) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    .main-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #7b2ff7, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .subtitle {
        color: #8b9bb4;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    .unified-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        margin-bottom: 1rem;
        overflow: hidden;
    }

    .signal-card {
        padding: 1.5rem;
    }

    .score-big {
        font-size: 2.5rem;
        font-weight: 800;
        color: #00d2ff;
    }
    
    .metric-label {
        color: #8b9bb4;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .metric-value {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f0f4ff;
    }
    
    .signal-badge {
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.85rem;
    }
    
    .ticker-badge {
        background: rgba(123, 47, 247, 0.15);
        color: #7b2ff7;
        padding: 2px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    
    .movie-pill {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        color: #b0bfda;
        display: inline-block;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    .breakdown-container {
        height: 6px;
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        margin: 12px 0 6px 0;
    }

    .breakdown-segment {
        height: 100%;
    }
    
    .bullish { color: #00e676 !important; }
    .bearish { color: #ff5252 !important; }
</style>
""", unsafe_allow_html=True)

# 3. Sidebar Controls
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3141/3141158.png", width=60)
    st.markdown("### Settings")
    period = st.selectbox("Stock Period", ["1mo", "3mo", "6mo", "1y"], index=0)
    count = st.slider("Movies per studio", 3, 10, 5)
    
    st.markdown("---")
    st.markdown("### Signal Legend")
    st.markdown("💎 **ELITE** – Strong momentum")
    st.markdown("🗳️ **BUY** – High hype, stock hasn't priced it in")
    st.markdown("✅ **HOLD** – Hype reflected in price")
    st.markdown("👀 **WATCH** – Moderate hype, stock dipping")
    st.markdown("➡️ **NEUTRAL** – No clear signal")
    st.markdown("⚠️ **CAUTION** – Low hype pipeline")

# 4. Header Section
col_title, col_info = st.columns([2, 1])
with col_title:
    st.markdown('<div class="main-title">🎬 Hype2Stock</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Predicting Market Moves via Content Momentum Signals</div>', unsafe_allow_html=True)

with st.expander("ℹ️ How it works: The Correlation Engine"):
    st.markdown("""
    This dashboard correlates **Movie Hype** (from TMDB) with **Stock Performance** (from Yahoo Finance).
    
    - **Hype Score (0-100):** Combines Movie Ratings, Popularity, Velocity, and Overview Sentiment.
    - **Market Signal:** Triggers **BUY SIGNAL** when Hype is high but Stock Price is lagging.
    """)

# 5. Data Loading with Cache
@st.cache_data(ttl=900, show_spinner=False)
def load_dashboard_data(selected_period, movie_count):
    return get_full_dashboard(selected_period, movie_count)

data = load_dashboard_data(period, count)

# 6. Status Bar
c1, c2, c3 = st.columns(3)
c1.markdown("📡 **Data Source:** `Live APIs` ")
c2.markdown("🤖 **Forecasting:** `Polynomial Trend` ")
c3.markdown(f"⏱️ **Last Sync:** `{datetime.now().strftime('%H:%M:%S')}`")

st.info(f"Loaded dashboard data for {len(data)} movie studios.")

# 7. Summary Metrics
m1, m2, m3, m4 = st.columns(4)

total_hype = 0
bullish_count = 0

for d in data:
    total_hype += d["hype"].get("score", 0)
    if "BUY" in d["signal"]["signal"]:
        bullish_count += 1

avg_hype = total_hype / len(data) if data else 0
top_studio_name = data[0]["studio"] if data else "N/A"

with m1:
    st.markdown(f'<div class="metric-label">🎯 Avg Hype Score</div><div class="score-big">{avg_hype:.1f}/100</div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-label">📈 Bullish Studios</div><div class="score-big">{bullish_count}/{len(data)}</div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-label">🏆 Top Studio</div><div class="score-big">{top_studio_name}</div>', unsafe_allow_html=True)
with m4:
    status_text = "Active" if avg_hype > 30 else "Cold"
    st.markdown(f'<div class="metric-label">⚡ Status</div><div class="score-big">{status_text}</div>', unsafe_allow_html=True)

st.markdown("---")

# 8. Leaderboard Chart
leaderboard_rows = []
for d in data:
    leaderboard_rows.append({"Studio": d["studio"], "Hype": d["hype"].get("score", 0)})

df_leader = pd.DataFrame(leaderboard_rows)
fig_bar = px.bar(
    df_leader, 
    x="Hype", 
    y="Studio", 
    orientation='h', 
    color="Hype", 
    color_continuous_scale="Viridis",
    template="plotly_dark"
)
fig_bar.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", 
    paper_bgcolor="rgba(0,0,0,0)", 
    margin=dict(l=0, r=0, t=0, b=0), 
    height=300,
    coloraxis_showscale=False
)
st.plotly_chart(fig_bar, use_container_width=True)

# 9. Studio Cards Grid
st.markdown("### 🎬 Studio Breakdown & Signals")

for i in range(0, len(data), 2):
    columns = st.columns(2)
    for j, col in enumerate(columns):
        if i + j < len(data):
            d = data[i + j]
            with col:
                sig_color = d["signal"]["color"]
                stock_price = d["stock"].get("price", 0)
                change_pct = d["stock"].get("change_pct", 0)

                stock_display = f"${stock_price}" if stock_price > 0 else "N/A"
                
                sign_str = "+" if change_pct >= 0 else ""
                change_display = f"{sign_str}{change_pct:.2f}%" if stock_price > 0 else "—"
                stock_class = "bullish" if change_pct >= 0 else "bearish"

                # Breakdown Bar
                bd = d["hype"].get("breakdown", {})
                w_rat = int(bd.get('rating', 0))
                w_pop = int(bd.get('popularity', 0))
                w_vel = int(bd.get('velocity', 0))
                w_sen = int(bd.get('sentiment', 0))

                breakdown_html = f"""
                <div class="breakdown-container">
                    <div class="breakdown-segment" style="width:{w_rat}%; background:#7b2ff7;"></div>
                    <div class="breakdown-segment" style="width:{w_pop}%; background:#00d2ff;"></div>
                    <div class="breakdown-segment" style="width:{w_vel}%; background:#ffd740;"></div>
                    <div class="breakdown-segment" style="width:{w_sen}%; background:#ff6b9d;"></div>
                </div>
                <div style="display:flex;gap:12px;font-size:0.7rem;color:#8b9bb4;margin-bottom:8px;">
                    <span><span style="color:#7b2ff7;">●</span> Rating {w_rat}</span>
                    <span><span style="color:#00d2ff;">●</span> Pop {w_pop}</span>
                    <span><span style="color:#ffd740;">●</span> Vel {w_vel}</span>
                    <span><span style="color:#ff6b9d;">●</span> Sentiment {w_sen}</span>
                </div>
                """

                # Movies list
                movie_pills = ""
                for m in d["movies"][:4]:
                    movie_pills += f'<span class="movie-pill">🎥 {m["title"][:28]} · ⭐{m["rating"]}</span> '

                # Convert hex color to rgba for badge background
                r_sig = int(sig_color[1:3], 16)
                g_sig = int(sig_color[3:5], 16)
                b_sig = int(sig_color[5:7], 16)

                card_html = f"""
                <div class="signal-card">
                    <div style="display:flex;justify-space-between;align-items:center;margin-bottom:12px;">
                        <div>
                            <span style="font-size:1.8rem;">{d["logo"]}</span>
                            <span style="font-size:1.4rem;font-weight:700;color:#f0f4ff;margin-left:8px;">{d["studio"]}</span>
                            <span class="ticker-badge" style="margin-left:8px;">${d["ticker"]}</span>
                        </div>
                        <span class="signal-badge" style="background:rgba({r_sig},{g_sig},{b_sig},0.2);border:1px solid {sig_color};">{d["signal"]["signal"]}</span>
                    </div>
                    <div style="display:flex;gap:28px;margin-bottom:8px;flex-wrap:wrap;">
                        <div>
                            <div class="metric-label">Hype Score</div>
                            <div class="score-big">{d["hype"].get("score", 0)}</div>
                        </div>
                        <div>
                            <div class="metric-label">Stock Price</div>
                            <div class="metric-value">{stock_display}</div>
                        </div>
                        <div>
                            <div class="metric-label">Period Δ</div>
                            <div class="metric-value {stock_class}">{change_display}</div>
                        </div>
                        <div>
                            <div class="metric-label">Avg Rating</div>
                            <div class="metric-value">⭐ {d["hype"].get("avg_rating", 0)}</div>
                        </div>
                        <div>
                            <div class="metric-label">Sentiment</div>
                            <div class="metric-value">🎭 {d["hype"].get("sentiment", 0)}</div>
                        </div>
                        <div>
                            <div class="metric-label">Votes/Day</div>
                            <div class="metric-value">⚡ {d["hype"].get("vote_velocity", 0)}</div>
                        </div>
                    </div>
                    <div style="margin:12px 0;">{breakdown_html}</div>
                    <div style="margin:12px 0;">{movie_pills}</div>
                    <div style="color:#b0bfda;font-size:0.85rem;font-style:italic;margin-top:8px;">💡 {d["signal"]["reason"]}</div>
                </div>
                """

                st.markdown('<div class="unified-card">', unsafe_allow_html=True)
                st.markdown(card_html, unsafe_allow_html=True)

                # Plot stock history chart
                hist = d["stock"].get("hist", pd.DataFrame())
                if not hist.empty and "Close" in hist.columns:
                    fig_mini = go.Figure()
                    lc = "#00e676" if change_pct >= 0 else "#ff5252"
                    r_lc = int(lc[1:3], 16)
                    g_lc = int(lc[3:5], 16)
                    b_lc = int(lc[5:7], 16)

                    # Historical stock line
                    fig_mini.add_trace(go.Scatter(
                        x=hist.index, 
                        y=hist["Close"], 
                        mode="lines", 
                        fill="tozeroy",
                        line=dict(color=lc, width=2.5),
                        fillcolor=f"rgba({r_lc},{g_lc},{b_lc},0.1)",
                        name="History"
                    ))

                    # Projection line
                    forecast = d["stock"].get("forecast", [])
                    if len(forecast) > 0:
                        future_dates = [hist.index[-1] + timedelta(days=step) for step in range(1, 6)]
                        fig_mini.add_trace(go.Scatter(
                            x=future_dates, 
                            y=forecast, 
                            mode="lines",
                            line=dict(color=lc, width=2, dash="dash"),
                            name="Projection"
                        ))

                    fig_mini.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", 
                        paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=0, r=0, t=5, b=0), 
                        height=130,
                        xaxis=dict(visible=False), 
                        yaxis=dict(visible=False), 
                        showlegend=False,
                    )
                    st.plotly_chart(fig_mini, use_container_width=True, key=f"chart_{d['ticker']}_{i}_{j}")
                else:
                    st.markdown(f"""
                    <div style="height:100px; display:flex; align-items:center; justify-content:center; 
                                background:rgba(255,255,255,0.01); color:#6b7ba0; font-size:0.8rem; border-top:1px solid rgba(255,255,255,0.05);">
                        📈 Stock data currently unavailable for {d['ticker']}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

# 10. Correlation Scatter Plot
st.markdown("### 📊 Correlation: Content Hype vs Market Performance")
scatter_rows = []
for d in data:
    if d["stock"].get("price", 0) > 0:
        scatter_rows.append({
            "Studio": d["studio"],
            "Hype Score": d["hype"].get("score", 0),
            "Stock Δ %": d["stock"].get("change_pct", 0),
            "Signal": d["signal"]["signal"]
        })

scatter_df = pd.DataFrame(scatter_rows)
if not scatter_df.empty:
    fig_scatter = px.scatter(
        scatter_df, 
        x="Hype Score", 
        y="Stock Δ %", 
        text="Studio", 
        color="Signal", 
        size=[20] * len(scatter_df),
        color_discrete_map={
            "📈 BUY SIGNAL": "#00e676",
            "✅ HOLD": "#29b6f6",
            "👀 WATCH": "#ffd740",
            "➡️ NEUTRAL": "#78909c",
            "⚠️ CAUTION": "#ff5252"
        },
        template="plotly_dark"
    )
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig_scatter.add_vline(x=50, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig_scatter.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Stock data unavailable for scatter plot.")
