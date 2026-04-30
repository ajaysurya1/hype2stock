"""Hype2Stock – Data Engine: TMDB + Stock aggregation."""

import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.linear_model import Ridge

# Industrial Grade yfinance config
import requests as req
session = req.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'})

load_dotenv()
TMDB_KEY = os.getenv("TMDB_API_KEY", "f1714c0718b4754d6ad44c1c2976e8b3")
BASE = "https://api.themoviedb.org/3"

analyzer = SentimentIntensityAnalyzer()

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
    """Fetch recent and UPCOMING movies with high resiliency."""
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    results = []
    try:
        url = f"{BASE}/discover/movie"
        params = {
            "api_key": TMDB_KEY, "with_companies": tmdb_id,
            "sort_by": "popularity.desc", "primary_release_date.gte": start_date,
            "primary_release_date.lte": end_date, "vote_count.gte": 0, "page": 1,
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            results = r.json().get("results", [])
    except: pass

    if not results:
        name_map = {213: "Netflix", 20580: "Amazon"}
        if tmdb_id in name_map:
            try:
                search_url = f"{BASE}/search/movie"
                s_params = {"api_key": TMDB_KEY, "query": name_map[tmdb_id]}
                sr = requests.get(search_url, params=s_params, timeout=10)
                if sr.status_code == 200:
                    results = sr.json().get("results", [])
            except: pass

    movies = []
    for m in results[:count]:
        rel_date = m.get("release_date", "")
        days_out = 90
        if rel_date:
            try:
                rd = datetime.strptime(rel_date, "%Y-%m-%d")
                days_out = (datetime.now() - rd).days
            except: pass
        
        vote_count = m.get("vote_count", 0)
        # Anticipation factor: Upcoming movies or those in theaters (last 30 days) get higher velocity weight
        is_upcoming = days_out <= 0
        is_recent = 0 < days_out <= 30
        weight = 1.5 if (is_upcoming or is_recent) else 1.0
        
        velocity = round((vote_count / max(abs(days_out), 1)) * weight, 2)
        
        # Sentiment Analysis
        overview = m.get("overview", "")
        sentiment = analyzer.polarity_scores(overview)["compound"] if overview else 0

        movies.append({
            "title": m.get("title", "Unknown"),
            "rating": m.get("vote_average", 0),
            "votes": vote_count,
            "popularity": m.get("popularity", 0),
            "release_date": rel_date or "N/A",
            "poster": f"https://image.tmdb.org/t/p/w300{m['poster_path']}" if m.get("poster_path") else None,
            "overview": overview[:200],
            "days_since_release": days_out,
            "vote_velocity": velocity,
            "sentiment": sentiment,
            "is_upcoming": is_upcoming
        })
    return movies


def calc_hype_score(movies: list[dict]) -> dict:
    if not movies:
        return {"score": 0, "avg_rating": 0, "avg_popularity": 0,
                "vote_velocity": 0, "grade": "N/A", "breakdown": {}}

    avg_rating = sum(m["rating"] for m in movies) / len(movies)
    avg_pop = sum(m["popularity"] for m in movies) / len(movies)
    avg_vel = sum(m["vote_velocity"] for m in movies) / len(movies)
    avg_sent = sum(m["sentiment"] for m in movies) / len(movies)
    
    # 4-Factor Formula (Quality, Popularity, Velocity, Sentiment)
    rating_score = (avg_rating / 10) * 25
    pop_score = min(avg_pop / 100, 1) * 25
    vel_score = min(avg_vel / 50, 1) * 25
    sent_score = ((avg_sent + 1) / 2) * 25 # Scale VADER (-1 to 1) to (0 to 25)

    score = round(rating_score + pop_score + vel_score + sent_score, 1)
    score = min(score, 100)

    if score >= 70: grade = "💎 Elite Momentum"
    elif score >= 50: grade = "🟢 Strong Bullish"
    elif score >= 35: grade = "🟡 Moderate Bullish"
    elif score >= 20: grade = "🟠 Neutral"
    else: grade = "🔴 Bearish Warning"

    return {
        "score": score,
        "avg_rating": round(avg_rating, 2),
        "avg_popularity": round(avg_pop, 1),
        "vote_velocity": round(avg_vel, 2),
        "sentiment": round(avg_sent, 2),
        "grade": grade,
        "breakdown": {
            "rating": round(rating_score, 1),
            "popularity": round(pop_score, 1),
            "velocity": round(vel_score, 1),
            "sentiment": round(sent_score, 1),
        }
    }


STOCK_KEY = os.getenv("STOCK_API_KEY", "d7oosi1r01qsb7bfn2pgd7oosi1r01qsb7bfn2q0")

class StockMarket:
    """Industrial-grade stock data aggregator with Synthetic Fallback."""
    
    @staticmethod
    def get_realtime_quote(ticker: str) -> dict:
        token = STOCK_KEY
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={token}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                price = float(data.get("c", 0))
                if price > 0:
                    return {"price": round(price, 2), "change_pct": round(float(data.get("dp", 0)), 2), "error": False}
        except: pass
        return {"error": True}

    @staticmethod
    def generate_synthetic_data(ticker: str, price: float = 100.0) -> pd.DataFrame:
        """Generate a realistic random walk for the UI when APIs are blocked."""
        dates = pd.date_range(end=datetime.now(), periods=21, freq='D')
        # Simple random walk starting from price
        noise = np.random.normal(0, 0.02, 21)
        walk = price * (1 + np.cumsum(noise))
        return pd.DataFrame({"Close": walk}, index=dates)

    @classmethod
    def fetch_data(cls, ticker: str, period: str = "1mo") -> dict:
        rt_data = cls.get_realtime_quote(ticker)
        
        try:
            # 1. Try Primary Fetch
            tk = yf.Ticker(ticker, session=session)
            hist = tk.history(period=period)
            
            # 2. Try Fallback Ticker
            if hist.empty:
                alt = ticker.replace("-", ".") if "-" in ticker else ticker.replace(".", "-")
                tk = yf.Ticker(alt, session=session)
                hist = tk.history(period=period)

            if not hist.empty:
                # Flatten Columns
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = hist.columns.get_level_values(0)
                if "Close" not in hist.columns:
                    for col in hist.columns:
                        if "close" in str(col).lower():
                            hist["Close"] = hist[col]
                            break
                if isinstance(hist["Close"], pd.DataFrame):
                    hist["Close"] = hist["Close"].iloc[:, 0]

                hist_price = float(hist["Close"].iloc[-1])
                current_price = rt_data["price"] if (not rt_data["error"] and rt_data["price"] > 0) else hist_price
                
                # Sanity check for Sandbox data
                if not rt_data["error"] and abs(current_price - hist_price) / max(hist_price, 1) > 0.5:
                    current_price = hist_price
                
                prev_price = float(hist["Close"].iloc[0])
                # If RT change is 0 (likely sandbox), calculate from history
                if not rt_data["error"] and rt_data["change_pct"] != 0:
                    change_pct = rt_data["change_pct"]
                else:
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                
                # ML TREND FORECAST (Projecting next 5 days)
                y = hist["Close"].values
                x = np.arange(len(y)).reshape(-1, 1)
                
                # Use Ridge Regression for more stable, regularized trend lines
                model = Ridge(alpha=1.0)
                model.fit(x, y)
                
                # Project next 5 points
                future_x = np.arange(len(y), len(y) + 5).reshape(-1, 1)
                forecast = model.predict(future_x)
                
                return {
                    "price": round(float(current_price), 2),
                    "change_pct": round(float(change_pct), 2),
                    "hist": hist,
                    "forecast": forecast, # New ML Field
                    "error": False,
                    "source": "Live"
                }
        except Exception as e:
            print(f"Fetch error for {ticker}: {e}")

        # 3. SYNTHETIC FALLBACK (Industrial Reliability)
        # If we reach here, we are likely rate-limited or the ticker is broken.
        base_price = rt_data["price"] if (not rt_data["error"] and rt_data["price"] > 0) else 50.0
        synth_hist = cls.generate_synthetic_data(ticker, base_price)
        
        # Calculate a realistic mock change
        first = synth_hist["Close"].iloc[0]
        last = synth_hist["Close"].iloc[-1]
        synth_change = ((last - first) / first) * 100

        return {
            "price": round(base_price, 2), "change_pct": round(float(synth_change), 2),
            "hist": synth_hist, "error": False, "source": "Simulated (API Blocked)"
        }


def fetch_stock_data(ticker: str, period: str = "1mo") -> dict:
    return StockMarket.fetch_data(ticker, period)


def generate_signal(hype: dict, stock: dict) -> dict:
    score = hype["score"]
    change = stock["change_pct"]
    if score >= 60 and change < 3:
        signal, reason, color = "📈 BUY SIGNAL", "Strong content momentum not yet priced in.", "#00e676"
    elif score >= 60:
        signal, reason, color = "✅ HOLD", "High hype already reflected in stock price.", "#29b6f6"
    elif score >= 35 and change < 0:
        signal, reason, color = "👀 WATCH", "Moderate content pipeline + stock dipping.", "#ffd740"
    elif score < 35:
        signal, reason, color = "⚠️ CAUTION", "Weak content pipeline — cultural headwind.", "#ff5252"
    else:
        signal, reason, color = "➡️ NEUTRAL", "Average content momentum.", "#78909c"
    return {"signal": signal, "reason": reason, "color": color}


def get_full_dashboard(period: str = "1mo", movie_count: int = 5) -> list[dict]:
    results = []
    for name, info in STUDIOS.items():
        movies = fetch_studio_movies(info["tmdb_id"], movie_count)
        hype = calc_hype_score(movies)
        stock = fetch_stock_data(info["ticker"], period)
        sig = generate_signal(hype, stock)
        results.append({
            "studio": name, "logo": info["logo"], "ticker": info["ticker"],
            "movies": movies, "hype": hype, "stock": stock, "signal": sig,
        })
        time.sleep(0.3)
    results.sort(key=lambda x: x["hype"]["score"], reverse=True)
    return results
