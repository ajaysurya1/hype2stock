"""Hype2Stock – Turn movie hype into stock signals."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from engine import get_full_dashboard, STUDIOS

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Hype2Stock – Movie Hype → Stock Signals",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for lighter, contrasting text ─────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%); }

/* Force Streamlit metric text to be bright white */
[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; font-size: 1.8rem !important; }
[data-testid="stMetricLabel"] { color: #e0e6ff !important; font-weight: 600 !important; font-size: 1rem !important; }
[data-testid="stMetricDelta"] { font-weight: 600 !important; }

/* Make all general text lighter */
.stMarkdown, .stMarkdown p, .stMarkdown li { color: #dce4f5 !important; }
h1, h2, h3, h4 { color: #f0f4ff !important; }

.hero-title {
    font-size: 3.2rem; font-weight: 900; text-align: center;
    background: linear-gradient(135deg, #00d2ff, #7b2ff7, #ff6b9d);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0; letter-spacing: -1px;
}
.hero-sub {
    text-align: center; color: #b0bfda; font-size: 1.15rem;
    margin-top: 4px; margin-bottom: 2rem;
}

.signal-card {
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
    backdrop-filter: blur(12px); transition: transform 0.2s, box-shadow 0.2s;
}
.signal-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(123,47,247,0.2);
    border-color: rgba(123,47,247,0.3);
}

.score-big {
    font-size: 2.6rem; font-weight: 900; line-height: 1;
    background: linear-gradient(135deg, #00d2ff, #7b2ff7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.ticker-badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    background: rgba(123,47,247,0.25); color: #d4b8ff;
    font-weight: 700; font-size: 0.85rem;
}
.signal-badge {
    display: inline-block; padding: 6px 16px; border-radius: 20px;
    font-weight: 700; font-size: 0.95rem; color: #fff;
}
.movie-pill {
    display: inline-block; padding: 4px 12px; border-radius: 12px;
    background: rgba(255,255,255,0.08); color: #e0e6ff;
    font-size: 0.82rem; margin: 3px;
}
.metric-label { color: #9faacc; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; }
.metric-value { color: #ffffff; font-size: 1.3rem; font-weight: 700; }
.pos { color: #00e676 !important; }
.neg { color: #ff5252 !important; }

.explain-box {
    background: rgba(123,47,247,0.08); border: 1px solid rgba(123,47,247,0.2);
    border-radius: 16px; padding: 1.5rem 2rem; margin: 1.5rem 0;
    color: #dce4f5;
}
.explain-box h4 { color: #d4b8ff !important; margin-bottom: 12px; }
.explain-box code { background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; color: #00d2ff; }

.breakdown-bar {
    height: 8px; border-radius: 4px; margin: 4px 0;
}

.footer {
    text-align: center; color: #6b7ba0; padding: 2rem 0 1rem;
    font-size: 0.8rem; border-top: 1px solid rgba(255,255,255,0.06);
    margin-top: 3rem;
}

/* Sidebar styling */
section[data-testid="stSidebar"] { background: rgba(10,10,26,0.95) !important; }
section[data-testid="stSidebar"] .stMarkdown { color: #b0bfda !important; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    stock_period = st.selectbox("Stock Period", ["5d", "1mo", "3mo", "6mo"], index=1)
    movie_count = st.slider("Movies per studio", 2, 6, 5)
    st.markdown("---")
    st.markdown("### 🎯 Signal Legend")
    st.markdown("""
    - 📈 **BUY** – High hype, stock hasn't priced it in
    - ✅ **HOLD** – Hype reflected in price
    - 👀 **WATCH** – Moderate hype, dipping stock
    - ➡️ **NEUTRAL** – No clear direction
    - ⚠️ **CAUTION** – Weak content pipeline
    """)
    st.markdown("---")
    st.markdown("### 📐 Score Formula")
    st.markdown("""
    - **35%** IMDb Rating
    - **30%** TMDB Popularity
    - **20%** Vote Velocity (votes/day)
    - **15%** Recency Bonus
    """)
    st.markdown("---")
    st.markdown("""
    <div style='color:#7888a8;font-size:0.75rem;'>
    <b>Hype2Stock</b> v2.0<br>
    Data: TMDB API + Yahoo Finance<br>
    ⚠️ Not financial advice.
    </div>
    """, unsafe_allow_html=True)


# ── Hero ─────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">🎬 Hype2Stock</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Turn movie hype into stock signals — cultural momentum meets market alpha</p>', unsafe_allow_html=True)


# ── How It Works Explanation ─────────────────────────────────
with st.expander("💡 How does movie hype predict stock movement?", expanded=False):
    st.markdown("""
    <div class="explain-box">
    <h4>🔬 The Hype-to-Stock Correlation</h4>
    <p>Studios like Disney, Netflix, and Warner Bros. derive <b>significant revenue</b> from their content pipeline.
    A string of high-rated, popular movies creates <b>cultural momentum</b> that translates to:</p>
    <ul>
        <li>📺 <b>Higher subscriber growth</b> (streaming platforms)</li>
        <li>🎟️ <b>Box office revenue beats</b> (theatrical studios)</li>
        <li>📈 <b>Positive earnings surprises</b> → stock price movement</li>
        <li>🗣️ <b>Brand sentiment lift</b> → analyst upgrades</li>
    </ul>

    <h4>📊 Our 4-Factor Scoring Model</h4>
    <p>We aggregate TMDB/IMDb data into a <b>Content Momentum Score (0-100)</b>:</p>
    <table style="width:100%; color:#dce4f5; margin:12px 0;">
        <tr style="border-bottom:1px solid rgba(255,255,255,0.1);">
            <td style="padding:6px;"><b>Factor</b></td>
            <td style="padding:6px;"><b>Weight</b></td>
            <td style="padding:6px;"><b>Why it matters</b></td>
        </tr>
        <tr><td style="padding:6px;">⭐ IMDb Rating</td><td style="padding:6px;"><code>35%</code></td>
            <td style="padding:6px;">Quality signal — high ratings = audience satisfaction = repeat viewership</td></tr>
        <tr><td style="padding:6px;">🔥 TMDB Popularity</td><td style="padding:6px;"><code>30%</code></td>
            <td style="padding:6px;">Buzz indicator — how much people are searching/talking about the movie</td></tr>
        <tr><td style="padding:6px;">⚡ Vote Velocity</td><td style="padding:6px;"><code>20%</code></td>
            <td style="padding:6px;">Engagement speed — votes per day shows active audience engagement</td></tr>
        <tr><td style="padding:6px;">🕐 Recency Bonus</td><td style="padding:6px;"><code>15%</code></td>
            <td style="padding:6px;">New releases within 60 days have outsized impact on earnings</td></tr>
    </table>

    <h4>🎯 Signal Generation</h4>
    <p>We compare the hype score against the studio's <b>actual stock performance</b>:</p>
    <ul>
        <li><b>High hype + flat stock</b> → The market hasn't priced in the content momentum → <span style="color:#00e676;">📈 BUY</span></li>
        <li><b>High hype + rising stock</b> → Momentum already reflected → <span style="color:#29b6f6;">✅ HOLD</span></li>
        <li><b>Low hype</b> → Weak pipeline = earnings risk → <span style="color:#ff5252;">⚠️ CAUTION</span></li>
    </ul>
    <p style="color:#9faacc;font-size:0.85rem;margin-top:12px;">
    <em>This is a leading cultural indicator — hype data is available before quarterly earnings, giving investors an early read on content performance.</em>
    </p>
    </div>
    """, unsafe_allow_html=True)


# ── Load Data ────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def load_data(period, count):
    return get_full_dashboard(period, count)


with st.spinner("🔄 Fetching live movie hype & stock data..."):
    data = load_data(stock_period, movie_count)


# ── Top Metrics Row ──────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
avg_hype = sum(d["hype"]["score"] for d in data) / len(data) if data else 0
bullish = sum(1 for d in data if d["signal"]["signal"] in ["📈 BUY SIGNAL", "✅ HOLD"])
caution = sum(1 for d in data if "CAUTION" in d["signal"]["signal"])
top = data[0]["studio"] if data else "N/A"

col1.metric("🎯 Avg Hype Score", f"{avg_hype:.1f} / 100")
col2.metric("📈 Bullish Studios", f"{bullish} / {len(data)}")
col3.metric("⚠️ Caution Alerts", caution)
col4.metric("🏆 Top Momentum", top)

st.markdown("---")


# ── Hype Leaderboard Chart ───────────────────────────────────
st.markdown("### 📊 Content Momentum Leaderboard")

studios_sorted = sorted(data, key=lambda x: x["hype"]["score"])
colors = ["#00e676" if d["hype"]["score"] >= 60 else "#ffd740" if d["hype"]["score"] >= 40 else "#ff5252" for d in studios_sorted]

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    y=[f'{d["logo"]} {d["studio"]}' for d in studios_sorted],
    x=[d["hype"]["score"] for d in studios_sorted],
    orientation="h",
    marker=dict(color=colors, line=dict(width=0)),
    text=[f'{d["hype"]["score"]}' for d in studios_sorted],
    textposition="outside",
    textfont=dict(color="#ffffff", size=13, family="Inter"),
))
fig_bar.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#dce4f5", family="Inter"),
    xaxis=dict(range=[0, 110], showgrid=False, title="Hype Score", title_font=dict(color="#9faacc")),
    yaxis=dict(showgrid=False, tickfont=dict(size=13)),
    height=350, margin=dict(l=10, r=50, t=10, b=40),
    showlegend=False,
)
st.plotly_chart(fig_bar, use_container_width=True)


# ── Studio Signal Cards ─────────────────────────────────────
st.markdown("### 🎬 Studio Breakdown & Signals")

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
            stock_display = f"${d['stock']['price']}" if d["stock"]["price"] > 0 else "N/A"
            change_display = f"{stock_arrow} {d['stock']['change_pct']}%" if d["stock"]["price"] > 0 else "—"

            # Score breakdown bar
            bd = d["hype"].get("breakdown", {})
            breakdown_html = ""
            if bd:
                total = max(d["hype"]["score"], 1)
                breakdown_html = f"""
                <div style="margin:8px 0 4px;">
                    <div style="display:flex;gap:2px;height:8px;border-radius:4px;overflow:hidden;">
                        <div style="width:{bd.get('rating',0)/total*100}%;background:#7b2ff7;" title="Rating"></div>
                        <div style="width:{bd.get('popularity',0)/total*100}%;background:#00d2ff;" title="Popularity"></div>
                        <div style="width:{bd.get('velocity',0)/total*100}%;background:#ffd740;" title="Velocity"></div>
                        <div style="width:{bd.get('recency',0)/total*100}%;background:#ff6b9d;" title="Recency"></div>
                    </div>
                    <div style="display:flex;gap:12px;margin-top:4px;font-size:0.65rem;color:#8892b0;">
                        <span>🟣 Rating {bd.get('rating',0)}</span>
                        <span>🔵 Pop {bd.get('popularity',0)}</span>
                        <span>🟡 Vel {bd.get('velocity',0)}</span>
                        <span>🩷 New {bd.get('recency',0)}</span>
                    </div>
                </div>"""

            movie_pills = ""
            for m in d["movies"][:4]:
                movie_pills += f'<span class="movie-pill">🎥 {m["title"][:28]} · ⭐{m["rating"]}</span> '

            st.markdown(f"""
            <div class="signal-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                    <div>
                        <span style="font-size:1.8rem;">{d["logo"]}</span>
                        <span style="font-size:1.4rem;font-weight:700;color:#f0f4ff;margin-left:8px;">{d["studio"]}</span>
                        <span class="ticker-badge" style="margin-left:8px;">${d["ticker"]}</span>
                    </div>
                    <span class="signal-badge" style="background:{sig_color}30;border:1px solid {sig_color};">{d["signal"]["signal"]}</span>
                </div>
                <div style="display:flex;gap:28px;margin-bottom:8px;">
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
                {breakdown_html}
                <div style="margin:8px 0;">{movie_pills}</div>
                <div style="color:#b0bfda;font-size:0.85rem;font-style:italic;">💡 {d["signal"]["reason"]}</div>
            </div>
            """, unsafe_allow_html=True)

            # Mini stock chart
            if not d["stock"]["hist"].empty:
                fig_mini = go.Figure()
                hist = d["stock"]["hist"]
                lc = "#00e676" if d["stock"]["change_pct"] >= 0 else "#ff5252"
                r, g, b = int(lc[1:3],16), int(lc[3:5],16), int(lc[5:7],16)
                fig_mini.add_trace(go.Scatter(
                    x=hist.index, y=hist["Close"], mode="lines", fill="tozeroy",
                    line=dict(color=lc, width=2),
                    fillcolor=f"rgba({r},{g},{b},0.08)",
                ))
                fig_mini.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=0, b=0), height=90,
                    xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False,
                )
                st.plotly_chart(fig_mini, use_container_width=True, key=f"chart_{d['ticker']}")


# ── Hype vs Stock Scatter ────────────────────────────────────
st.markdown("---")
st.markdown("### 🔗 Hype Score vs Stock Performance")
st.markdown("*This scatter plot reveals which studios have content momentum that the market hasn't priced in yet.*")

scatter_df = pd.DataFrame([{
    "Studio": f'{d["logo"]} {d["studio"]}',
    "Hype Score": d["hype"]["score"],
    "Stock Change %": d["stock"]["change_pct"],
    "Signal": d["signal"]["signal"],
} for d in data if d["stock"]["price"] > 0])

if not scatter_df.empty:
    fig_s = go.Figure()
    for _, row in scatter_df.iterrows():
        clr = "#00e676" if row["Hype Score"] >= 60 else "#ffd740" if row["Hype Score"] >= 40 else "#ff5252"
        fig_s.add_trace(go.Scatter(
            x=[row["Hype Score"]], y=[row["Stock Change %"]],
            mode="markers+text", text=[row["Studio"]], textposition="top center",
            marker=dict(size=18, color=clr, line=dict(width=2, color="rgba(255,255,255,0.12)")),
            textfont=dict(color="#e0e6ff", size=11), showlegend=False,
        ))
    fig_s.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.15)")
    fig_s.add_vline(x=50, line_dash="dash", line_color="rgba(255,255,255,0.15)")
    fig_s.add_annotation(x=80, y=scatter_df["Stock Change %"].max()*0.9, text="🚀 Undervalued Hype",
                         showarrow=False, font=dict(color="#00e676", size=11))
    fig_s.add_annotation(x=20, y=scatter_df["Stock Change %"].min()*0.9, text="💀 Weak Pipeline",
                         showarrow=False, font=dict(color="#ff5252", size=11))
    fig_s.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce4f5", family="Inter"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", title="Content Momentum Score",
                   title_font=dict(color="#9faacc")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", title="Stock Price Change %",
                   title_font=dict(color="#9faacc")),
        height=420, margin=dict(l=10, r=10, t=10, b=40), showlegend=False,
    )
    st.plotly_chart(fig_s, use_container_width=True)
else:
    st.info("Stock data unavailable for scatter plot — market may be closed.")


# ── Summary Table ────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Full Signal Summary")

table_df = pd.DataFrame([{
    "Studio": f'{d["logo"]} {d["studio"]}',
    "Ticker": d["ticker"],
    "Hype Score": d["hype"]["score"],
    "Avg Rating": d["hype"]["avg_rating"],
    "Popularity": d["hype"]["avg_popularity"],
    "Votes/Day": d["hype"]["vote_velocity"],
    "Stock $": d["stock"]["price"],
    "Stock Δ%": d["stock"]["change_pct"],
    "Signal": d["signal"]["signal"],
    "Grade": d["hype"]["grade"],
} for d in data])

st.dataframe(
    table_df, use_container_width=True, hide_index=True,
    column_config={
        "Hype Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
        "Stock Δ%": st.column_config.NumberColumn(format="%.2f%%"),
    },
)


# ── Footer ───────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    🎬 <b>Hype2Stock</b> v2.0 — Cultural momentum meets market alpha<br>
    Data: TMDB API + Yahoo Finance · Scores update every 10 min · Not financial advice
</div>
""", unsafe_allow_html=True)
