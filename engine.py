"""Hype2Stock – Data Engine: TMDB + Stock aggregation."""

import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
TMDB_KEY = os.getenv("TMDB_API_KEY", "f1714c0718b4754d6ad44c1c2976e8b3")
BASE = "https://api.themoviedb.org/3"

# Studio → TMDB company ID + stock ticker
STUDIOS = {
    "Walt Disney":      {"tmdb_id": 2,    "ticker": "DIS",   "logo": "🏰"},
    "Warner Bros.":     {"tmdb_id": 174,  "ticker": "WBD",   "logo": "🎬"},
    "Netflix":          {"tmdb_id": 213,  "ticker": "NFLX",  "logo": "🔴"},
    "Paramount":        {"tmdb_id": 4,    "ticker": "PARA",  "logo": "⛰️"},
    "Sony Pictures":    {"tmdb_id": 34,   "ticker": "SONY",  "logo": "🎮"},
    "Universal":        {"tmdb_id": 33,   "ticker": "CMCSA", "logo": "🌍"},
    "Lionsgate":        {"tmdb_id": 1632, "ticker": "LGF",   "logo": "🦁"},
    "Amazon Studios":   {"tmdb_id": 20580,"ticker": "AMZN",  "logo": "📦"},
}


def fetch_studio_movies(tmdb_id: int, count: int = 3) -> list[dict]:
    """Fetch the most recent movies for a studio from TMDB."""
    url = f"{BASE}/discover/movie"
    params = {
        "api_key": TMDB_KEY,
        "with_companies": tmdb_id,
        "sort_by": "primary_release_date.desc",
        "primary_release_date.lte": datetime.now().strftime("%Y-%m-%d"),
        "primary_release_date.gte": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        "vote_count.gte": 10,
        "page": 1,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])[:count]
        movies = []
        for m in results:
            movies.append({
                "title": m.get("title", "Unknown"),
                "rating": m.get("vote_average", 0),
                "votes": m.get("vote_count", 0),
                "popularity": m.get("popularity", 0),
                "release_date": m.get("release_date", "N/A"),
                "poster": f"https://image.tmdb.org/t/p/w200{m['poster_path']}" if m.get("poster_path") else None,
                "overview": m.get("overview", ""),
            })
        return movies
    except Exception as e:
        print(f"TMDB error for company {tmdb_id}: {e}")
        return []


def calc_hype_score(movies: list[dict]) -> dict:
    """Calculate content momentum score from a list of movies."""
    if not movies:
        return {"score": 0, "avg_rating": 0, "avg_popularity": 0, "vote_velocity": 0, "grade": "N/A"}

    avg_rating = sum(m["rating"] for m in movies) / len(movies)
    avg_pop = sum(m["popularity"] for m in movies) / len(movies)
    vote_vel = sum(m["votes"] for m in movies) / len(movies)

    # Normalize: rating /10 * 40 + popularity capped * 30 + vote velocity capped * 30
    r_norm = (avg_rating / 10) * 40
    p_norm = min(avg_pop / 100, 1) * 30
    v_norm = min(vote_vel / 5000, 1) * 30
    score = round(r_norm + p_norm + v_norm, 1)

    if score >= 75:
        grade = "🟢 Strong Bullish"
    elif score >= 55:
        grade = "🟡 Moderate Bullish"
    elif score >= 35:
        grade = "🟠 Neutral"
    else:
        grade = "🔴 Bearish Warning"

    return {
        "score": score,
        "avg_rating": round(avg_rating, 2),
        "avg_popularity": round(avg_pop, 1),
        "vote_velocity": round(vote_vel, 0),
        "grade": grade,
    }


def fetch_stock_data(ticker: str, period: str = "1mo") -> dict:
    """Fetch stock price data via yfinance."""
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period=period)
        if hist.empty:
            return {"price": 0, "change_pct": 0, "hist": pd.DataFrame()}
        current = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[0]
        change = ((current - prev) / prev) * 100
        return {
            "price": round(current, 2),
            "change_pct": round(change, 2),
            "hist": hist,
        }
    except Exception as e:
        print(f"Stock error for {ticker}: {e}")
        return {"price": 0, "change_pct": 0, "hist": pd.DataFrame()}


def generate_signal(hype: dict, stock: dict) -> dict:
    """Compare hype score vs stock performance → trading signal."""
    score = hype["score"]
    change = stock["change_pct"]

    if score >= 65 and change < 5:
        signal = "📈 BUY SIGNAL"
        reason = "High content momentum but stock hasn't priced it in yet."
        color = "#00e676"
    elif score >= 65 and change >= 5:
        signal = "✅ HOLD"
        reason = "High hype already reflected in stock price."
        color = "#29b6f6"
    elif score < 35:
        signal = "⚠️ CAUTION"
        reason = "Low content momentum – potential downside risk."
        color = "#ff5252"
    else:
        signal = "👀 WATCH"
        reason = "Moderate hype – monitor for catalysts."
        color = "#ffd740"

    return {"signal": signal, "reason": reason, "color": color}


def get_full_dashboard() -> list[dict]:
    """Build complete dashboard data for all studios."""
    results = []
    for name, info in STUDIOS.items():
        movies = fetch_studio_movies(info["tmdb_id"])
        hype = calc_hype_score(movies)
        stock = fetch_stock_data(info["ticker"])
        sig = generate_signal(hype, stock)
        results.append({
            "studio": name,
            "logo": info["logo"],
            "ticker": info["ticker"],
            "movies": movies,
            "hype": hype,
            "stock": stock,
            "signal": sig,
        })
    # Sort by hype score descending
    results.sort(key=lambda x: x["hype"]["score"], reverse=True)
    return results
