import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from engine import get_full_dashboard, STUDIOS
from datetime import datetime, timedelta

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Hype2Stock | Institutional Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Outfit:wght@700;900&display=swap');
    
    :root {
        --primary: #7b2ff7;
        --secondary: #00d2ff;
        --accent: #ff6b9d;
        --bg: #0f111a;
        --card-bg: #1a1d2b;
        --text: #f0f4ff;
    }

    .stApp {
        background: linear-gradient(135deg, #0f111a 0%, #161924 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(26, 29, 43, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    h1, h2, h3 { font-family: 'Outfit', sans-serif; color: var(--text); }
    
    .main-title {
        font-size: 3.5rem; font-weight: 900; margin-bottom: 0;
        background: linear-gradient(90deg, #7b2ff7, #00d2ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    
    .subtitle {
        color: #8b9bb4; font-size: 1.1rem; font-weight: 400;
        margin-top: 4px; margin-bottom: 2rem;
    }

    /* Unified Card Container */
    .unified-card {
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px; margin-bottom: 1rem; overflow: hidden;
        backdrop-filter: blur(12px); transition: transform 0.2s;
    }
    .unified-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 32px rgba(123,47,247,0.2);
        border-color: rgba(123,47,247,0.3);
    }
    .signal-card {
        background: transparent; border: none; padding: 1.5rem 1.5rem 0.5rem 1.5rem;
        margin-bottom: 0; backdrop-filter: none;
    }
    .signal-card:hover { transform: none; box-shadow: none; border: none; }

    .score-big {
        font-size: 2.6rem; font-weight: 900; line-height: 1;
        background: linear-gradient(135deg, #00d2ff, #7b2ff7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    
    .metric-label { color: #8b9bb4; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 1.2rem; font-weight: 700; color: var(--text); }
    
    .signal-badge {
        padding: 6px 16px; border-radius: 99px; font-weight: 800; font-size: 0.85rem;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    .ticker-badge {
        background: rgba(123, 47, 247, 0.15); color: #7b2ff7;
        padding: 2px 10px; border-radius: 6px; font-weight: 700; font-size: 0.85rem;
    }
    
    .movie-pill {
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 4px 12px; border-radius: 99px; font-size: 0.8rem; font-weight: 500;
        color: #b0bfda; display: inline-block; margin-right: 6px; margin-bottom: 6px;
    }

    /* Breakdown Bar */
    .breakdown-container {
        height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px;
        overflow: hidden; display: flex; margin: 12px 0 6px 0;
    }
    .breakdown-segment { height: 100%; transition: width 0.5s ease; }
    
    .bullish { color: #00e676 !important; }
    .bearish { color: #ff5252 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3141/3141158.png", width=60)
    st.markdown("### Settings")
    period = st.selectbox("Stock Period", ["1mo", "3mo", "6mo", "1y"], index=0)
    count = st.slider("Movies per studio", 3, 10, 5)
    
    st.markdown("---")
    st.markdown("### Signal Legend")
    st.markdown("🗳️ **BUY** – High hype, stock hasn't priced it in")
    st.markdown("✅ **HOLD** – Hype reflected in price")
    st.markdown("👀 **WATCH** – Moderate hype, dipping stock")
    st.markdown("➡️ **NEUTRAL** – No clear direction")
    st.markdown("⚠️ **CAUTION** – Weak content pipeline")

# ── Header ───────────────────────────────────────────────────
col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    st.markdown('<div class="main-title">🎬 Hype2Stock</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Predicting Market Moves via Content Momentum Signals</div>', unsafe_allow_html=True)

with st.expander("ℹ️ How it works: The Correlation Engine"):
    st.markdown("""
    This dashboard correlates **Cultural Momentum** (from IMDb/TMDB) with **Stock Performance** (from Yahoo Finance).
    
    **1. Hype Score (0-100):** A 4-factor formula calculating:
    - **Rating (35%):** Quality of content (TMDB Avg).
    - **Popularity (35%):** Total reach and awareness.
    - **Velocity (30%):** Rate of new interest/votes per day.
    
    **2. Market Signal:**
    - We look for **Divergence**. If a studio's Hype Score is rising but their Stock Price is falling or flat, it triggers a **BUY SIGNAL** because the market has not yet "priced in" the upcoming content success.
    """)

# ── Load Data ────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False) # Increased to 15m to avoid rate limits
def load_data(period, count):
    return get_full_dashboard(period, count)

# ── Engine Intelligence Summary ──────────────────────────────
data = load_data(period, count)

with st.container():
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        st.markdown(f"📡 **Data Source:** `Industrial Hybrid (RT)`")
    with c2:
        st.markdown(f"🤖 **Forecasting:** `Active (Linear Projection)`")
    with c3:
        st.markdown(f"⏱️ **Last Sync:** `{datetime.now().strftime('%H:%M:%S')}`")
    
    st.info(f"Analysis successfully synchronized with TMDB Creative Pipeline and Market Liquidity for {len(data)} global studios.")

# ── Top Metrics ──────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
avg_hype = sum(d["hype"]["score"] for d in data) / len(data)
bullish = len([d for d in data if "BUY" in d["signal"]["signal"]])
top_studio = data[0]["studio"]

with m1:
    st.markdown(f'<div class="metric-label">🎯 Avg Hype Score</div><div class="score-big" style="font-size:2.4rem;">{avg_hype:.1f}/100</div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-label">📈 Bullish Studios</div><div class="score-big" style="font-size:2.4rem;">{bullish}/{len(data)}</div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-label">🏆 Top Momentum</div><div class="score-big" style="font-size:2.4rem;">{top_studio}</div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-label">⚡ Signal Status</div><div class="score-big" style="font-size:2.4rem;">{"Active" if avg_hype > 30 else "Cold"}</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Leaderboard Bar Chart ────────────────────────────────────
df_leader = pd.DataFrame([{"Studio": d["studio"], "Hype": d["hype"]["score"]} for d in data])
fig_bar = px.bar(df_leader, x="Hype", y="Studio", orientation='h', 
                 color="Hype", color_continuous_scale="Viridis",
                 template="plotly_dark")
fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
                      margin=dict(l=0, r=0, t=0, b=0), height=300,
                      coloraxis_showscale=False)
st.plotly_chart(fig_bar, use_container_width=True)

# ── Signal Cards ─────────────────────────────────────────────
st.markdown("### 🎬 Studio Breakdown & Signals")

for i in range(0, len(data), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        if i + j < len(data):
            d = data[i + j]
            with col:
                sig_color = d["signal"]["color"]
                stock_display = f"${d['stock']['price']}" if d['stock']['price'] > 0 else "N/A"
                change_pct = d["stock"]["change_pct"]
                change_display = f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%" if d['stock']['price'] > 0 else "—"
                stock_class = "bullish" if change_pct >= 0 else "bearish"
                
                bd = d["hype"]["breakdown"]
                breakdown_html = ""
                if bd:
                    w_rat = int(bd['rating'])
                    w_pop = int(bd['popularity'])
                    w_vel = int(bd['velocity'])
                    breakdown_html = (
                        f'<div class="breakdown-container">'
                        f'<div class="breakdown-segment" style="width:{w_rat}%; background:#7b2ff7;"></div>'
                        f'<div class="breakdown-segment" style="width:{w_pop}%; background:#00d2ff;"></div>'
                        f'<div class="breakdown-segment" style="width:{w_vel}%; background:#ffd740;"></div>'
                        f'</div>'
                        f'<div style="display:flex;gap:12px;font-size:0.7rem;color:#8b9bb4;margin-bottom:8px;">'
                        f'<span><span style="color:#7b2ff7;">&#9679;</span> Rating {w_rat}</span>'
                        f'<span><span style="color:#00d2ff;">&#9679;</span> Pop {w_pop}</span>'
                        f'<span><span style="color:#ffd740;">&#9679;</span> Vel {w_vel}</span>'
                        f'</div>'
                    )

                movie_pills = ""
                for m in d["movies"][:4]:
                    movie_pills += f'<span class="movie-pill">🎥 {m["title"][:28]} · ⭐{m["rating"]}</span> '

                # Convert hex signal color to rgba for transparency
                r_sig, g_sig, b_sig = int(sig_color[1:3], 16), int(sig_color[3:5], 16), int(sig_color[5:7], 16)
                
                # Use conditional strings to avoid empty divs taking up space
                breakdown_section = f'<div style="margin:12px 0;">{breakdown_html}</div>' if breakdown_html else ""
                movie_section = f'<div style="margin:12px 0;">{movie_pills}</div>' if movie_pills else ""

                # Use a non-indented string to prevent markdown from treating it as a code block
                card_html = f"""<div class="signal-card">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
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
        <div class="score-big">{d["hype"]["score"]}</div>
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
        <div class="metric-value">⭐ {d["hype"]["avg_rating"]}</div>
    </div>
    <div>
        <div class="metric-label">Votes/Day</div>
        <div class="metric-value">⚡ {d["hype"]["vote_velocity"]}</div>
    </div>
</div>
{breakdown_section}
{movie_section}
<div style="color:#b0bfda;font-size:0.85rem;font-style:italic;margin-top:8px;">💡 {d["signal"]["reason"]}</div>
</div>"""
                
                # Unified Container for Card + Graph
                st.markdown('<div class="unified-card">', unsafe_allow_html=True)
                
                # 1. Top Card (HTML)
                st.markdown(card_html, unsafe_allow_html=True)
                
                # 2. Bottom Graph (Plotly or Fallback)
                if not d["stock"]["hist"].empty:
                    fig_mini = go.Figure()
                    hist = d["stock"]["hist"]
                    lc = "#00e676" if d["stock"]["change_pct"] >= 0 else "#ff5252"
                    r, g, b = int(lc[1:3],16), int(lc[3:5],16), int(lc[5:7],16)
                    
                    # 2.1 Historical Data
                    fig_mini.add_trace(go.Scatter(
                        x=hist.index, y=hist["Close"], mode="lines", fill="tozeroy",
                        line=dict(color=lc, width=2.5),
                        fillcolor=f"rgba({r},{g},{b},0.1)",
                        name="History"
                    ))
                    
                    # 2.2 ML Forecast (Dashed Line)
                    if "forecast" in d["stock"] and len(d["stock"]["forecast"]) > 0:
                        future_dates = [hist.index[-1] + timedelta(days=i) for i in range(1, 6)]
                        fig_mini.add_trace(go.Scatter(
                            x=future_dates, y=d["stock"]["forecast"], mode="lines",
                            line=dict(color=lc, width=2, dash="dash"),
                            name="ML Projection"
                        ))
                    
                    fig_mini.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=0, r=0, t=5, b=0), height=130,
                        xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False,
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

# ── Hype vs Stock Scatter ────────────────────────────────────
st.markdown("### 📊 Correlation: Content Hype vs Market Performance")
scatter_data = []
for d in data:
    if d["stock"]["price"] > 0:
        scatter_data.append({
            "Studio": d["studio"],
            "Hype Score": d["hype"]["score"],
            "Stock Δ %": d["stock"]["change_pct"],
            "Signal": d["signal"]["signal"]
        })

scatter_df = pd.DataFrame(scatter_data)
if not scatter_df.empty:
    fig_scatter = px.scatter(scatter_df, x="Hype Score", y="Stock Δ %", 
                             text="Studio", color="Signal", size=[20]*len(scatter_df),
                             color_discrete_map={
                                 "📈 BUY SIGNAL": "#00e676",
                                 "✅ HOLD": "#29b6f6",
                                 "👀 WATCH": "#ffd740",
                                 "➡️ NEUTRAL": "#78909c",
                                 "⚠️ CAUTION": "#ff5252"
                             },
                             template="plotly_dark")
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig_scatter.add_vline(x=50, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig_scatter.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Stock data unavailable for scatter plot — market may be closed.")
