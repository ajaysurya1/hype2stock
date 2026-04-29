"""Hype2Stock – Data Engine: TMDB + Stock aggregation."""

import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import time

load_dotenv()
TMDB_KEY = os.getenv("TMDB_API_KEY", "f1714c0718b4754d6ad44c1c2976e8b3")
BASE = "https://api.themoviedb.org/3"

# Studio → TMDB company ID + stock ticker (verified tickers)
STUDIOS = {
    "Walt Disney":      {"tmdb_id": 2,     "ticker": "DIS",   "logo": "🏰"},
    "Warner Bros.":     {"tmdb_id": 174,   "ticker": "WBD",   "logo": "🎬"},
    "Netflix":          {"tmdb_id": 213,   "ticker": "NFLX",  "logo": "🔴"},
    "Sony Pictures":    {"tmdb_id": 34,    "ticker": "SONY",  "logo": "🎮"},
    "Universal":        {"tmdb_id": 33,    "ticker": "CMCSA", "logo": "🌍"},
    "Amazon Studios":   {"tmdb_id": 20580, "ticker": "AMZN",  "logo": "📦"},
    "Paramount":        {"tmdb_id": 4,     "ticker": "PARA",  "logo": "⛰️"},
    "Lionsgate":        {"tmdb_id": 1632,  "ticker": "LGF-A", "logo": "🦁"},
}


def fetch_studio_movies(tmdb_id: int, count: int = 5) -> list[dict]:
    """Fetch the most recent movies for a studio from TMDB."""
    url = f"{BASE}/discover/movie"
    today = datetime.now().strftime("%Y-%m-%d")
    year_ago = (datetime.now() - timedelta(days=548)).strftime("%Y-%m-%d")  # ~18 months back
    params = {
        "api_key": TMDB_KEY,
        "with_companies": tmdb_id,
        "sort_by": "popularity.desc",
        "primary_release_date.lte": today,
        "primary_release_date.gte": year_ago,
        "vote_count.gte": 5,
        "page": 1,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        results = r.json().get("results", [])[:count]
        movies = []
        for m in results:
            # Calculate days since release for velocity calc
            rel_date = m.get("release_date", "")
            days_out = 1
            if rel_date:
                try:
                    rd = datetime.strptime(rel_date, "%Y-%m-%d")
                    days_out = max((datetime.now() - rd).days, 1)
                except ValueError:
                    days_out = 90

            vote_count = m.get("vote_count", 0)
            vote_velocity = round(vote_count / days_out, 2)  # votes per day

            movies.append({
                "title": m.get("title", "Unknown"),
                "rating": m.get("vote_average", 0),
                "votes": vote_count,
                "popularity": m.get("popularity", 0),
                "release_date": rel_date or "N/A",
                "poster": f"https://image.tmdb.org/t/p/w300{m['poster_path']}" if m.get("poster_path") else None,
                "overview": m.get("overview", "")[:200],
                "days_since_release": days_out,
                "vote_velocity": vote_velocity,
            })
        return movies
    except Exception as e:
        print(f"TMDB error for company {tmdb_id}: {e}")
        return []


def calc_hype_score(movies: list[dict]) -> dict:
    """
    Calculate content momentum score from a list of movies.

    Formula:
      - Rating Component (35%): avg IMDb rating normalized to 0-35
      - Popularity Component (30%): avg TMDB popularity normalized to 0-30
      - Vote Velocity Component (20%): avg votes/day normalized to 0-20
      - Recency Bonus (15%): boost for movies released in last 60 days
    """
    if not movies:
        return {"score": 0, "avg_rating": 0, "avg_popularity": 0,
                "vote_velocity": 0, "grade": "N/A", "breakdown": {}}

    avg_rating = sum(m["rating"] for m in movies) / len(movies)
    avg_pop = sum(m["popularity"] for m in movies) / len(movies)
    avg_vel = sum(m["vote_velocity"] for m in movies) / len(movies)

    # Count recent releases (< 60 days)
    recent_count = sum(1 for m in movies if m["days_since_release"] < 60)
    recency_ratio = recent_count / len(movies)

    # Component scores
    rating_score = (avg_rating / 10) * 35
    pop_score = min(avg_pop / 80, 1) * 30        # Cap at 80 popularity
    vel_score = min(avg_vel / 50, 1) * 20         # Cap at 50 votes/day
    recency_score = recency_ratio * 15

    score = round(rating_score + pop_score + vel_score + recency_score, 1)
    score = min(score, 100)

    if score >= 70:
        grade = "🟢 Strong Bullish"
    elif score >= 50:
        grade = "🟡 Moderate Bullish"
    elif score >= 30:
        grade = "🟠 Neutral"
    else:
        grade = "🔴 Bearish Warning"

    return {
        "score": score,
        "avg_rating": round(avg_rating, 2),
        "avg_popularity": round(avg_pop, 1),
        "vote_velocity": round(avg_vel, 2),
        "grade": grade,
        "breakdown": {
            "rating": round(rating_score, 1),
            "popularity": round(pop_score, 1),
            "velocity": round(vel_score, 1),
            "recency": round(recency_score, 1),
        }
    }


STOCK_KEY = os.getenv("STOCK_API_KEY", "d7oosi1r01qsb7bfn2pgd7oosi1r01qsb7bfn2q0")

class StockMarket:
    """Industrial-grade stock data aggregator with real-time API and resilient fallbacks."""
    
    @staticmethod
    def get_realtime_quote(ticker: str) -> dict:
        """Fetch real-time price using the provided industrial API (Finnhub-style)."""
        # Using the provided key as a Finnhub-style token
        # If it's a Finnhub key, we use it directly. 
        # The key provided is 40 chars, possibly two 20-char keys concatenated.
        # We'll try the full key first.
        token = STOCK_KEY
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={token}"
        
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get("c"): # 'c' is current price in Finnhub
                    return {
                        "price": round(float(data["c"]), 2),
                        "change_pct": round(float(data.get("dp", 0)), 2),
                        "source": "Finnhub RT",
                        "error": False
                    }
            
            # If full key fails, try first 20 chars (standard Finnhub length)
            if len(token) > 20:
                url_alt = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={token[:20]}"
                r = requests.get(url_alt, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("c"):
                        return {
                            "price": round(float(data["c"]), 2),
                            "change_pct": round(float(data.get("dp", 0)), 2),
                            "source": "Finnhub RT",
                            "error": False
                        }
        except Exception as e:
            print(f"Industrial API error for {ticker}: {e}")
        
        return {"error": True}

    @classmethod
    def fetch_data(cls, ticker: str, period: str = "1mo") -> dict:
        """Complete industrial-grade fetch: Real-time price + Historical history."""
        # 1. Try Real-time API
        rt_data = cls.get_realtime_quote(ticker)
        
        # 2. Fetch History (yfinance remains best for free historical sparklines)
        try:
            tk = yf.Ticker(ticker)
            hist = tk.history(period=period)
            
            if hist.empty:
                # Fallback ticker check for complex symbols
                if "-" in ticker:
                    tk = yf.Ticker(ticker.replace("-", "."))
                    hist = tk.history(period=period)
            
            if not hist.empty:
                current_price = rt_data["price"] if not rt_data["error"] else hist["Close"].iloc[-1]
                
                # Calculate change based on real-time vs yesterday's close or period start
                # For sparklines, we use the hist, but for the 'Price' shown, we use RT if available
                prev_price = hist["Close"].iloc[0]
                change_pct = rt_data["change_pct"] if not rt_data["error"] else ((current_price - prev_price) / prev_price) * 100
                
                return {
                    "price": round(float(current_price), 2),
                    "change_pct": round(float(change_pct), 2),
                    "hist": hist,
                    "error": False,
                    "source": "Industrial Hybrid" if not rt_data["error"] else "Fallback"
                }
        except Exception as e:
            print(f"Resilient fetch error for {ticker}: {e}")
            
        return {"price": 0, "change_pct": 0, "hist": pd.DataFrame(), "error": True}


def fetch_stock_data(ticker: str, period: str = "1mo") -> dict:
    """Wrapper to maintain compatibility with app.py while using industrial engine."""
    return StockMarket.fetch_data(ticker, period)


def generate_signal(hype: dict, stock: dict) -> dict:
    """
    Compare hype score vs stock performance → trading signal.

    Logic:
    - High hype (>=60) + stock flat/down (<3%) → BUY (market hasn't priced in the momentum)
    - High hype (>=60) + stock already up (>=3%) → HOLD (momentum reflected)
    - Medium hype (35-60) + stock down → WATCH (could recover)
    - Low hype (<35) → CAUTION (content pipeline weak)
    """
    score = hype["score"]
    change = stock["change_pct"]

    if score >= 60 and change < 3:
        signal = "📈 BUY SIGNAL"
        reason = "Strong content momentum not yet reflected in stock price — potential upside."
        color = "#00e676"
        strength = "Strong"
    elif score >= 60 and change >= 3:
        signal = "✅ HOLD"
        reason = "High hype already being priced in — hold and monitor earnings."
        color = "#29b6f6"
        strength = "Moderate"
    elif 35 <= score < 60 and change < 0:
        signal = "👀 WATCH"
        reason = "Moderate content pipeline + stock dipping — potential recovery play."
        color = "#ffd740"
        strength = "Speculative"
    elif 35 <= score < 60:
        signal = "➡️ NEUTRAL"
        reason = "Average content momentum — no strong directional signal."
        color = "#78909c"
        strength = "Weak"
    else:
        signal = "⚠️ CAUTION"
        reason = "Weak content pipeline — cultural headwind may pressure stock."
        color = "#ff5252"
        strength = "Strong"

    return {"signal": signal, "reason": reason, "color": color, "strength": strength}


def get_full_dashboard(period: str = "1mo", movie_count: int = 5) -> list[dict]:
    """Build complete dashboard data for all studios."""
    results = []
    for name, info in STUDIOS.items():
        movies = fetch_studio_movies(info["tmdb_id"], movie_count)
        hype = calc_hype_score(movies)
        stock = fetch_stock_data(info["ticker"], period)
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
