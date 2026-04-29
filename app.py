"""Hype2Stock – Turn movie hype into stock signals."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from engine import get_full_dashboard, STUDIOS, fetch_studio_movies, calc_hype_score, fetch_stock_data, generate_signal

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

.hero-title {
    font-size: 3.2rem; font-weight: 900; text-align: center;
    background: linear-gradient(135deg, #00d2ff, #7b2ff7, #ff6b9d);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.hero-sub {
    text-align: center; color: #8892b0; font-size: 1.1rem;
    margin-top: 0; margin-bottom: 2rem;
}

.signal-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
    backdrop-filter: blur(12px); transition: transform 0.2s, box-shadow 0.2s;
}
.signal-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(123,47,247,0.15);
}

.score-big {
    font-size: 2.8rem; font-weight: 900; line-height: 1;
    background: linear-gradient(135deg, #00d2ff, #7b2ff7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.ticker-badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    background: rgba(123,47,247,0.2); color: #b388ff;
    font-weight: 700; font-size: 0.85rem;
}
.signal-badge {
    display: inline-block; padding: 6px 16px; border-radius: 20px;
    font-weight: 700; font-size: 0.95rem; color: #fff;
}
.movie-pill {
    display: inline-block; padding: 4px 10px; border-radius: 12px;
    background: rgba(255,255,255,0.06); color: #ccd6f6;
    font-size: 0.8rem; margin: 2px;
}
.metric-label { color: #8892b0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
.metric-value { color: #ccd6f6; font-size: 1.3rem; font-weight: 700; }
.pos { color: #00e676; }
.neg { color: #ff5252; }

.footer {
    text-align: center; color: #4a5568; padding: 2rem 0 1rem;
    font-size: 0.8rem; border-top: 1px solid rgba(255,255,255,0.05);
    margin-top: 3rem;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    stock_period = st.selectbox("Stock Period", ["5d", "1mo", "3mo", "6mo"], index=1)
    movie_count = st.slider("Movies per studio", 1, 5, 3)
    st.markdown("---")
    st.markdown("### 🎯 Signal Legend")
    st.markdown("""
    - 📈 **BUY** – High hype, stock lagging
    - ✅ **HOLD** – Hype priced in
    - 👀 **WATCH** – Moderate momentum
    - ⚠️ **CAUTION** – Low hype risk
    """)
    st.markdown("---")
    st.markdown("""
    <div style='color:#64748b;font-size:0.75rem;'>
    <b>Hype2Stock</b> v1.0<br>
    Data: TMDB + Yahoo Finance<br>
    Not financial advice.
    </div>
    """, unsafe_allow_html=True)


# ── Hero ─────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">🎬 Hype2Stock</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Turn movie hype into stock signals — cultural momentum meets market alpha</p>', unsafe_allow_html=True)


# ── Load Data ────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def load_data(period, count):
    results = []
    for name, info in STUDIOS.items():
        movies = fetch_studio_movies(info["tmdb_id"], count)
        hype = calc_hype_score(movies)
        stock = fetch_stock_data(info["ticker"], period)
        sig = generate_signal(hype, stock)
        results.append({
            "studio": name, "logo": info["logo"], "ticker": info["ticker"],
            "movies": movies, "hype": hype, "stock": stock, "signal": sig,
        })
    results.sort(key=lambda x: x["hype"]["score"], reverse=True)
    return results


with st.spinner("🔄 Fetching live movie hype & stock data..."):
    data = load_data(stock_period, movie_count)


# ── Top Metrics Row ──────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
avg_hype = sum(d["hype"]["score"] for d in data) / len(data) if data else 0
bullish_count = sum(1 for d in data if "BUY" in d["signal"]["signal"] or "HOLD" in d["signal"]["signal"])
bearish_count = sum(1 for d in data if "CAUTION" in d["signal"]["signal"])
top_studio = data[0]["studio"] if data else "N/A"

col1.metric("🎯 Avg Hype Score", f"{avg_hype:.1f}/100")
col2.metric("📈 Bullish Studios", f"{bullish_count}/{len(data)}")
col3.metric("⚠️ Caution Alerts", bearish_count)
col4.metric("🏆 Top Momentum", top_studio)

st.markdown("---")


# ── Hype Leaderboard Chart ───────────────────────────────────
st.markdown("### 📊 Content Momentum Leaderboard")

fig_bar = go.Figure()
studios_sorted = sorted(data, key=lambda x: x["hype"]["score"])
colors = []
for d in studios_sorted:
    s = d["hype"]["score"]
    if s >= 65:
        colors.append("#00e676")
    elif s >= 45:
        colors.append("#ffd740")
    else:
        colors.append("#ff5252")

fig_bar.add_trace(go.Bar(
    y=[f'{d["logo"]} {d["studio"]}' for d in studios_sorted],
    x=[d["hype"]["score"] for d in studios_sorted],
    orientation="h",
    marker=dict(color=colors, line=dict(width=0)),
    text=[f'{d["hype"]["score"]}' for d in studios_sorted],
    textposition="outside",
    textfont=dict(color="#ccd6f6", size=13, family="Inter"),
))
fig_bar.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#ccd6f6", family="Inter"),
    xaxis=dict(range=[0, 105], showgrid=False, title="Hype Score"),
    yaxis=dict(showgrid=False),
    height=350, margin=dict(l=10, r=40, t=10, b=30),
    showlegend=False,
)
st.plotly_chart(fig_bar, use_container_width=True)


# ── Studio Signal Cards ─────────────────────────────────────
st.markdown("### 🎬 Studio Signals")

for i in range(0, len(data), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        idx = i + j
        if idx >= len(data):
            break
        d = data[idx]
        with col:
            sig_color = d["signal"]["color"]
            stock_class = "pos" if d["stock"]["change_pct"] >= 0 else "neg"
            stock_arrow = "▲" if d["stock"]["change_pct"] >= 0 else "▼"

            movie_pills = ""
            for m in d["movies"]:
                stars = "⭐" * max(1, int(m["rating"] / 2))
                movie_pills += f'<span class="movie-pill">{m["title"][:25]} · {m["rating"]} {stars}</span> '

            st.markdown(f"""
            <div class="signal-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                    <div>
                        <span style="font-size:1.8rem;">{d["logo"]}</span>
                        <span style="font-size:1.4rem;font-weight:700;color:#e2e8f0;margin-left:8px;">{d["studio"]}</span>
                        <span class="ticker-badge" style="margin-left:8px;">${d["ticker"]}</span>
                    </div>
                    <span class="signal-badge" style="background:{sig_color}40;border:1px solid {sig_color};">{d["signal"]["signal"]}</span>
                </div>
                <div style="display:flex;gap:24px;margin-bottom:12px;">
                    <div>
                        <div class="metric-label">Hype Score</div>
                        <div class="score-big">{d["hype"]["score"]}</div>
                    </div>
                    <div>
                        <div class="metric-label">Stock Price</div>
                        <div class="metric-value">${d["stock"]["price"]}</div>
                    </div>
                    <div>
                        <div class="metric-label">Stock Δ</div>
                        <div class="metric-value {stock_class}">{stock_arrow} {d["stock"]["change_pct"]}%</div>
                    </div>
                    <div>
                        <div class="metric-label">Avg Rating</div>
                        <div class="metric-value">⭐ {d["hype"]["avg_rating"]}</div>
                    </div>
                </div>
                <div style="margin-bottom:8px;">{movie_pills}</div>
                <div style="color:#8892b0;font-size:0.85rem;font-style:italic;">💡 {d["signal"]["reason"]}</div>
            </div>
            """, unsafe_allow_html=True)

            # Mini stock chart
            if not d["stock"]["hist"].empty:
                fig_mini = go.Figure()
                hist = d["stock"]["hist"]
                line_color = "#00e676" if d["stock"]["change_pct"] >= 0 else "#ff5252"
                fig_mini.add_trace(go.Scatter(
                    x=hist.index, y=hist["Close"],
                    mode="lines", fill="tozeroy",
                    line=dict(color=line_color, width=2),
                    fillcolor=f"rgba({','.join(str(int(line_color.lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.1)",
                ))
                fig_mini.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=0, b=0), height=100,
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                    showlegend=False,
                )
                st.plotly_chart(fig_mini, use_container_width=True, key=f"chart_{d['ticker']}")


# ── Correlation Scatter ──────────────────────────────────────
st.markdown("---")
st.markdown("### 🔗 Hype vs Stock Performance")

scatter_data = pd.DataFrame([{
    "Studio": f'{d["logo"]} {d["studio"]}',
    "Hype Score": d["hype"]["score"],
    "Stock Change %": d["stock"]["change_pct"],
    "Signal": d["signal"]["signal"],
} for d in data])

if not scatter_data.empty:
    fig_scatter = px.scatter(
        scatter_data, x="Hype Score", y="Stock Change %",
        text="Studio", size=[40]*len(scatter_data),
        color_discrete_sequence=["#7b2ff7"],
    )
    fig_scatter.update_traces(textposition="top center", textfont=dict(color="#ccd6f6", size=11))
    fig_scatter.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ccd6f6", family="Inter"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Content Momentum (Hype Score)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Stock Price Change %"),
        height=400, margin=dict(l=10, r=10, t=10, b=30),
        showlegend=False,
    )
    # Quadrant lines
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.15)")
    fig_scatter.add_vline(x=50, line_dash="dash", line_color="rgba(255,255,255,0.15)")
    # Quadrant labels
    fig_scatter.add_annotation(x=80, y=max(scatter_data["Stock Change %"])*0.8, text="🚀 High Hype + Rising", showarrow=False, font=dict(color="#00e676", size=11))
    fig_scatter.add_annotation(x=20, y=min(scatter_data["Stock Change %"])*0.8, text="💀 Low Hype + Falling", showarrow=False, font=dict(color="#ff5252", size=11))
    st.plotly_chart(fig_scatter, use_container_width=True)


# ── Summary Table ────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Full Signal Summary")

table_data = pd.DataFrame([{
    "Studio": f'{d["logo"]} {d["studio"]}',
    "Ticker": d["ticker"],
    "Hype Score": d["hype"]["score"],
    "Avg Rating": d["hype"]["avg_rating"],
    "Popularity": d["hype"]["avg_popularity"],
    "Stock $": d["stock"]["price"],
    "Stock Δ%": d["stock"]["change_pct"],
    "Signal": d["signal"]["signal"],
    "Grade": d["hype"]["grade"],
} for d in data])

st.dataframe(
    table_data,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Hype Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
        "Stock Δ%": st.column_config.NumberColumn(format="%.2f%%"),
    },
)


# ── Footer ───────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    🎬 <b>Hype2Stock</b> – Cultural momentum meets market alpha<br>
    Data sourced from TMDB & Yahoo Finance · Not financial advice · Built with Streamlit
</div>
""", unsafe_allow_html=True)
