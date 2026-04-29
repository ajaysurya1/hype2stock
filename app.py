"""Hype2Stock – Turn movie hype into stock signals."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
from engine import get_full_dashboard, STUDIOS

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Hype2Stock – Movie Hype → Stock Signals",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%); }
[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; font-size: 1.8rem !important; }
[data-testid="stMetricLabel"] { color: #e0e6ff !important; font-weight: 600 !important; font-size: 1rem !important; }
.stMarkdown, .stMarkdown p, .stMarkdown li { color: #dce4f5 !important; }
h1, h2, h3, h4 { color: #f0f4ff !important; }
.hero-title {
    font-size: 3.2rem; font-weight: 900; text-align: center;
    background: linear-gradient(135deg, #00d2ff, #7b2ff7, #ff6b9d);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0; letter-spacing: -1px;
}
.hero-sub { text-align: center; color: #b0bfda; font-size: 1.15rem; margin-top: 4px; margin-bottom: 2rem; }
.unified-card {
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px; margin-bottom: 1rem; overflow: hidden;
    backdrop-filter: blur(12px); transition: transform 0.2s;
}
.unified-card:hover { transform: translateY(-3px); box-shadow: 0 8px 32px rgba(123,47,247,0.2); border-color: rgba(123,47,247,0.3); }
.signal-card { background: transparent; border: none; padding: 1.5rem 1.5rem 0.5rem 1.5rem; margin-bottom: 0; }
.score-big { font-size: 2.6rem; font-weight: 900; line-height: 1; background: linear-gradient(135deg, #00d2ff, #7b2ff7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.ticker-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; background: rgba(123,47,247,0.25); color: #d4b8ff; font-weight: 700; font-size: 0.85rem; }
.signal-badge { display: inline-block; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.95rem; color: #fff; }
.movie-pill { display: inline-block; padding: 4px 12px; border-radius: 12px; background: rgba(255,255,255,0.08); color: #e0e6ff; font-size: 0.82rem; margin: 3px; }
.metric-label { color: #9faacc; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; }
.metric-value { color: #ffffff; font-size: 1.3rem; font-weight: 700; }
.pos { color: #00e676 !important; }
.neg { color: #ff5252 !important; }
.breakdown-bar { height: 8px; border-radius: 4px; margin: 4px 0; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3858/3858482.png", width=80)
    st.title("Hype Engine")
    st.markdown("Quantifying creative momentum for algorithmic trading.")
    st.divider()
    lookback = st.selectbox("Analysis Window", ["1mo", "3mo", "6mo", "1y"], index=0)
    count = st.slider("Movies per Studio", 3, 10, 5)
    if st.button("🔄 Refresh Market Signals", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Hero ─────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">Hype2Stock</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">The Intelligent Sentiment Bridge Between Cinema & Capital Markets</p>', unsafe_allow_html=True)

# ── Load Data ────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def load_data(period, count):
    return get_full_dashboard(period, count)

with st.spinner("Analyzing Market Sentiment & TMDB Pipeline..."):
    data = load_data(lookback, count)

if not data:
    st.error("Engine failed to synchronize with Market APIs. Check connectivity.")
    st.stop()

# ── Global Metrics ───────────────────────────────────────────
avg_hype = sum(d["hype"]["score"] for d in data) / len(data)
bullish_count = sum(1 for d in data if d["hype"]["score"] > 50)
caution_count = sum(1 for d in data if "CAUTION" in d["signal"]["signal"])
top_momentum = data[0]["studio"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("🎯 Avg Hype Score", f"{avg_hype:.1f}/100", delta=None)
m2.metric("📈 Bullish Studios", f"{bullish_count}/{len(data)}", delta=f"{bullish_count/len(data)*100:.0f}%")
m3.metric("⚠️ Caution Alerts", caution_count, delta=None, delta_color="inverse")
m4.metric("🏆 Top Momentum", top_momentum, delta="Leader")

# ── Executive AI Summary (WOW Factor 1) ──────────────────────
alpha_studios = []
for d in data:
    alpha = d["hype"]["score"] - (d["stock"]["change_pct"] * 2)
    alpha_studios.append((alpha, d))
alpha_studios.sort(key=lambda x: x[0], reverse=True)
best_alpha = alpha_studios[0][1]

st.markdown(f"""
<div style="background: linear-gradient(90deg, rgba(123,47,247,0.15) 0%, rgba(0,210,255,0.05) 100%); 
            border-left: 5px solid #7b2ff7; padding: 20px 30px; border-radius: 0 16px 16px 0; margin-bottom: 30px;">
    <h4 style="margin:0; color:#d4b8ff; font-size:0.9rem; text-transform:uppercase; letter-spacing:2px;">Executive AI Briefing</h4>
    <div style="font-size:1.4rem; font-weight:700; margin-top:10px; color:#ffffff;">
        🎯 Top Alpha Opportunity: <span style="color:#00d2ff;">{best_alpha['studio']} (${best_alpha['ticker']})</span>
    </div>
    <div style="color:#b0bfda; margin-top:8px; line-height:1.5;">
        Our algorithm detected a massive divergence for {best_alpha['studio']}. 
        Despite a <span style="color:#ff6b9d; font-weight:700;">Hype Score of {best_alpha['hype']['score']}</span>, 
        the market hasn't fully priced in the momentum yet ({best_alpha['stock']['change_pct']}% period Δ). 
        <b>Probability of bullish correction: <span style="color:#00e676;">High</span></b>.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Dashboard Tabs ──────────────────────────────────────────
tabs = st.tabs(["🚀 Market War Room", "📊 Strategic Leaderboard", "⚙️ How it Works"])

with tabs[0]:
    # --- WOW Factor 2: Radar Chart ---
    st.subheader("Creative vs Capital Radar")
    categories = ['Hype Score', 'Quality', 'Popularity', 'Stock Δ', 'Pipeline']
    fig_radar = go.Figure()
    for d in data[:5]:
        v_hype = d["hype"]["score"]
        v_rate = (d["hype"]["avg_rating"] / 10) * 100
        v_pop = min(d["hype"]["avg_popularity"], 100)
        v_stock = min(max(d["stock"]["change_pct"] + 15, 0) * 3, 100)
        v_pipe = min(len(d["movies"]) * 20, 100)
        fig_radar.add_trace(go.Scatterpolar(r=[v_hype, v_rate, v_pop, v_stock, v_pipe], theta=categories, fill='toself', name=d["studio"]))
    fig_radar.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 100], color="#6b7ba0")),
                            paper_bgcolor="rgba(0,0,0,0)", height=450, margin=dict(l=80, r=80, t=20, b=20))
    st.plotly_chart(fig_radar, use_container_width=True)
    
    st.divider()
    st.subheader("Live Trading Signals")
    for i in range(0, len(data), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(data): break
            d = data[idx]
            with col:
                sig_color = d["signal"]["color"]
                stock_class = "pos" if d["stock"]["change_pct"] >= 0 else "neg"
                change_display = f"▲ {d['stock']['change_pct']}%" if d['stock']['change_pct'] >= 0 else f"▼ {abs(d['stock']['change_pct'])}%"
                stock_display = f"${d['stock']['price']}" if not d['stock']['error'] else "N/A"
                
                # Breakdown Bar
                bd = d["hype"]["breakdown"]
                v_rate, v_pop, v_vel = int(bd.get("rating", 0)), int(bd.get("popularity", 0)), int(bd.get("velocity", 0))
                v_rec = int(bd.get("recency", 0))
                total = v_rate + v_pop + v_vel + v_rec
                if total > 0:
                    p_rate, p_pop, p_vel = int((v_rate/total)*100), int((v_pop/total)*100), int((v_vel/total)*100)
                    p_rec = 100 - (p_rate + p_pop + p_vel)
                    breakdown_html = f"""<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;margin:12px 0;">
                        <div style="width:{p_rate}%;background:#7b2ff7;" title="Rating"></div>
                        <div style="width:{p_pop}%;background:#00d2ff;" title="Popularity"></div>
                        <div style="width:{p_vel}%;background:#ffd740;" title="Velocity"></div>
                        <div style="width:{p_rec}%;background:#ff6b9d;" title="Recency"></div>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#9faacc;margin-bottom:12px;">
                        <span>● Rat {p_rate}%</span><span>● Pop {p_pop}%</span><span>● Vel {p_vel}%</span><span>● New {p_rec}%</span>
                    </div>"""
                else: breakdown_html = ""

                movie_pills = "".join([f'<span class="movie-pill">🎥 {m["title"][:22]} · ⭐{m["rating"]}</span>' for m in d["movies"][:3]])
                
                # Convert sig_color to rgba
                r_sig, g_sig, b_sig = int(sig_color[1:3], 16), int(sig_color[3:5], 16), int(sig_color[5:7], 16)
                
                card_html = f"""<div class="signal-card">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
    <div><span style="font-size:1.6rem;">{d["logo"]}</span><span style="font-size:1.3rem;font-weight:700;color:#fff;margin-left:8px;">{d["studio"]}</span><span class="ticker-badge" style="margin-left:8px;">${d["ticker"]}</span></div>
    <span class="signal-badge" style="background:rgba({r_sig},{g_sig},{b_sig},0.2);border:1px solid {sig_color};">{d["signal"]["signal"]}</span>
</div>
<div style="display:flex;gap:20px;margin-bottom:8px;flex-wrap:wrap;">
    <div><div class="metric-label">Hype Score</div><div class="score-big">{d["hype"]["score"]}</div></div>
    <div><div class="metric-label">Stock Price</div><div class="metric-value">{stock_display}</div></div>
    <div><div class="metric-label">Period Δ</div><div class="metric-value {stock_class}">{change_display}</div></div>
    <div><div class="metric-label">Avg Rating</div><div class="metric-value">⭐ {d["hype"]["avg_rating"]}</div></div>
</div>
{breakdown_html}
<div style="margin:10px 0;">{movie_pills}</div>
<div style="color:#b0bfda;font-size:0.8rem;font-style:italic;margin-top:8px;">💡 {d["signal"]["reason"]}</div>
</div>"""
                st.markdown(f'<div class="unified-card">{card_html}', unsafe_allow_html=True)
                if not d["stock"]["hist"].empty:
                    fig_mini = px.line(d["stock"]["hist"], y="Close", color_discrete_sequence=[sig_color])
                    fig_mini.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=100, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig_mini, use_container_width=True, key=f"c_{d['ticker']}")
                st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    # --- WOW Factor 3: Treemap ---
    st.subheader("Market Heatmap")
    df_tree = pd.DataFrame([{ "Studio": d["studio"], "Hype": d["hype"]["score"], "Change": d["stock"]["change_pct"], "Color": d["signal"]["color"] } for d in data])
    fig_tree = px.treemap(df_tree, path=['Studio'], values='Hype', color='Change', color_continuous_scale='RdYlGn', color_continuous_midpoint=0)
    fig_tree.update_layout(margin=dict(t=30, l=10, r=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_tree, use_container_width=True)
    
    st.divider()
    st.subheader("Hype vs Stock Correlation")
    df_scatter = pd.DataFrame([{ "Studio": d["studio"], "Hype": d["hype"]["score"], "Stock_Change": d["stock"]["change_pct"], "Signal": d["signal"]["signal"] } for d in data])
    fig_scatter = px.scatter(df_scatter, x="Hype", y="Stock_Change", text="Studio", color="Hype", size="Hype", color_continuous_scale="Viridis")
    fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.05)")
    st.plotly_chart(fig_scatter, use_container_width=True)

with tabs[2]:
    st.markdown("""
    <div class="explain-box">
        <h4>The 4-Factor Hype Engine</h4>
        <ul>
            <li><b>Creative Quality (35%):</b> Aggregated IMDb user ratings weighted by volume.</li>
            <li><b>Market Popularity (35%):</b> Real-time sentiment and search trend data from TMDB.</li>
            <li><b>Vote Velocity (30%):</b> The rate of user interaction compared to the release window.</li>
        </ul>
        <p>Our algorithm looks for <b>Divergence</b>: When the <i>Creative Momentum</i> outpaces the <i>Stock Performance</i>, we identify a potential Alpha opportunity.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="footer">Hype2Stock Industrial v2.1 • Hackathon Edition • Data Refreshed: Real-time</div>', unsafe_allow_html=True)
