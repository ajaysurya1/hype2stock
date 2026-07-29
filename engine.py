# Hype2Stock - Data Engine
# Simple Python script to get movie data and stock prices

import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()

# Setup TMDB API key
TMDB_KEY = os.getenv("TMDB_API_KEY", "f1714c0718b4754d6ad44c1c2976e8b3")
BASE_URL = "https://api.themoviedb.org/3"

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Dictionary of movie studios and stock tickers
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


# Function to get popular movies for a studio
def fetch_studio_movies(tmdb_id, count=5):
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    results = []

    try:
        url = f"{BASE_URL}/discover/movie"
        params = {
            "api_key": TMDB_KEY,
            "with_companies": tmdb_id,
            "sort_by": "popularity.desc",
            "primary_release_date.gte": start_date,
            "primary_release_date.lte": end_date,
            "vote_count.gte": 0,
            "page": 1,
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            results = r.json().get("results", [])
    except Exception as e:
        print("Error fetching movies:", e)

    # Fallback search if empty
    if not results:
        name_map = {213: "Netflix", 20580: "Amazon"}
        if tmdb_id in name_map:
            try:
                search_url = f"{BASE_URL}/search/movie"
                s_params = {"api_key": TMDB_KEY, "query": name_map[tmdb_id]}
                sr = requests.get(search_url, params=s_params, timeout=10)
                if sr.status_code == 200:
                    results = sr.json().get("results", [])
            except Exception as e:
                print("Fallback error:", e)

    movies = []
    for item in results[:count]:
        rel_date = item.get("release_date", "")
        days_out = 90
        if rel_date:
            try:
                rd = datetime.strptime(rel_date, "%Y-%m-%d")
                days_out = (datetime.now() - rd).days
            except Exception:
                pass

        vote_count = item.get("vote_count", 0)
        is_upcoming = days_out <= 0
        is_recent = 0 < days_out <= 30
        
        weight = 1.5 if (is_upcoming or is_recent) else 1.0
        velocity = round((vote_count / max(abs(days_out), 1)) * weight, 2)

        # Sentiment score from plot overview
        overview = item.get("overview", "")
        sentiment = 0
        if overview:
            sentiment = analyzer.polarity_scores(overview)["compound"]

        poster_url = None
        if item.get("poster_path"):
            poster_url = f"https://image.tmdb.org/t/p/w300{item['poster_path']}"

        movies.append({
            "title": item.get("title", "Unknown"),
            "rating": item.get("vote_average", 0),
            "votes": vote_count,
            "popularity": item.get("popularity", 0),
            "release_date": rel_date if rel_date else "N/A",
            "poster": poster_url,
            "overview": overview[:200],
            "days_since_release": days_out,
            "vote_velocity": velocity,
            "sentiment": sentiment,
            "is_upcoming": is_upcoming
        })

    return movies


# Function to calculate overall hype score
def calc_hype_score(movies):
    if not movies:
        return {
            "score": 0,
            "avg_rating": 0,
            "avg_popularity": 0,
            "vote_velocity": 0,
            "sentiment": 0,
            "grade": "N/A",
            "breakdown": {"rating": 0, "popularity": 0, "velocity": 0, "sentiment": 0}
        }

    total_rating = 0
    total_pop = 0
    total_vel = 0
    total_sent = 0

    for m in movies:
        total_rating += m["rating"]
        total_pop += m["popularity"]
        total_vel += m["vote_velocity"]
        total_sent += m["sentiment"]

    n = len(movies)
    avg_rating = total_rating / n
    avg_pop = total_pop / n
    avg_vel = total_vel / n
    avg_sent = total_sent / n

    # Score out of 100
    rating_score = (avg_rating / 10) * 25
    pop_score = min(avg_pop / 100, 1) * 25
    vel_score = min(avg_vel / 50, 1) * 25
    sent_score = ((avg_sent + 1) / 2) * 25

    score = round(rating_score + pop_score + vel_score + sent_score, 1)
    score = min(score, 100)

    if score >= 70:
        grade = "💎 Elite Momentum"
    elif score >= 50:
        grade = "🟢 Strong Bullish"
    elif score >= 35:
        grade = "🟡 Moderate Bullish"
    elif score >= 20:
        grade = "🟠 Neutral"
    else:
        grade = "🔴 Bearish Warning"

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


# Helper function to generate fallback data if stock API fails
def generate_sample_stock_data(price=100.0):
    dates = pd.date_range(end=datetime.now(), periods=21, freq='D')
    random_changes = np.random.normal(0, 0.02, 21)
    prices = price * (1 + np.cumsum(random_changes))
    return pd.DataFrame({"Close": prices}, index=dates)


# Function to fetch stock data
def fetch_stock_data(ticker, period="1mo"):
    import yfinance as yf

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty and "-" in ticker:
            alt_ticker = ticker.replace("-", ".")
            stock = yf.Ticker(alt_ticker)
            hist = stock.history(period=period)

        if not hist.empty:
            if "Close" in hist.columns:
                close_prices = hist["Close"]
                if isinstance(close_prices, pd.DataFrame):
                    close_prices = close_prices.iloc[:, 0]

                first_price = float(close_prices.iloc[0])
                last_price = float(close_prices.iloc[-1])
                change = ((last_price - first_price) / first_price) * 100

                # Simple trend calculation for next 5 days
                y_values = close_prices.values
                x_values = np.arange(len(y_values))
                # Simple linear trend: y = mx + c
                if len(x_values) > 1:
                    m, c = np.polyfit(x_values, y_values, 1)
                    future_x = np.arange(len(y_values), len(y_values) + 5)
                    forecast = m * future_x + c
                else:
                    forecast = [last_price] * 5

                return {
                    "price": round(last_price, 2),
                    "change_pct": round(change, 2),
                    "hist": hist,
                    "forecast": forecast,
                    "error": False,
                    "source": "Live"
                }

    except Exception as e:
        print(f"Stock error for {ticker}:", e)

    # Return sample data if stock fetch fails
    sample_df = generate_sample_stock_data(50.0)
    p_start = sample_df["Close"].iloc[0]
    p_end = sample_df["Close"].iloc[-1]
    sample_change = ((p_end - p_start) / p_start) * 100

    return {
        "price": round(50.0, 2),
        "change_pct": round(sample_change, 2),
        "hist": sample_df,
        "error": False,
        "source": "Simulated"
    }


# Function to generate trading recommendation
def generate_signal(hype, stock):
    score = hype["score"]
    change = stock["change_pct"]

    if score >= 60 and change < 3:
        signal = "📈 BUY SIGNAL"
        reason = "Strong content momentum not yet priced in."
        color = "#00e676"
    elif score >= 60:
        signal = "✅ HOLD"
        reason = "High hype already reflected in stock price."
        color = "#29b6f6"
    elif score >= 35 and change < 0:
        signal = "👀 WATCH"
        reason = "Moderate content pipeline + stock dipping."
        color = "#ffd740"
    elif score < 35:
        signal = "⚠️ CAUTION"
        reason = "Weak content pipeline — cultural headwind."
        color = "#ff5252"
    else:
        signal = "➡️ NEUTRAL"
        reason = "Average content momentum."
        color = "#78909c"

    return {"signal": signal, "reason": reason, "color": color}


# Main function to get full dashboard dataset
def get_full_dashboard(period="1mo", movie_count=5):
    data_list = []

    for studio_name, info in STUDIOS.items():
        movies = fetch_studio_movies(info["tmdb_id"], count=movie_count)
        hype = calc_hype_score(movies)
        stock = fetch_stock_data(info["ticker"], period=period)
        signal = generate_signal(hype, stock)

        studio_dict = {
            "studio": studio_name,
            "logo": info["logo"],
            "ticker": info["ticker"],
            "movies": movies,
            "hype": hype,
            "stock": stock,
            "signal": signal,
        }
        data_list.append(studio_dict)
        time.sleep(0.2)

    # Sort studios by hype score
    data_list.sort(key=lambda item: item["hype"]["score"], reverse=True)
    return data_list
