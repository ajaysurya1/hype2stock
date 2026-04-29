"""
Hype2Stock - API Connection Diagnostic Script
This script verifies that we are successfully pulling data from:
1. TMDB (Movie Hype Data)
2. Industrial API (Real-time Stock Data)
"""

import os
import sys
from dotenv import load_dotenv
from engine import fetch_studio_movies, StockMarket, STUDIOS

def run_diagnostic():
    load_dotenv()
    
    # Force UTF-8 encoding for terminal output
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass # Older python versions
    
    print("\n" + "="*50)
    print(" HYPE2STOCK INDUSTRIAL DIAGNOSTIC")
    print("="*50)
    
    # Test Studio: Disney
    studio_name = "Walt Disney"
    info = STUDIOS[studio_name]
    
    print(f"\n[1] TESTING TMDB API (Movie Data for {studio_name})")
    print("-" * 40)
    try:
        movies = fetch_studio_movies(info["tmdb_id"], count=1)
        if movies:
            movie = movies[0]
            print(f" SUCCESS! Fetched latest movie:")
            print(f"   - Title: {movie['title']}")
            print(f"   - Rating: {movie['rating']}")
            print(f"   - Popularity: {movie['popularity']}")
        else:
            print(" ERROR: No movies found. Check TMDB API key.")
    except Exception as e:
        print(f" ERROR: TMDB Error: {e}")

    print(f"\n[2] TESTING STOCK API (Real-time data for ${info['ticker']})")
    print("-" * 40)
    try:
        # Testing the industrial-grade fetcher
        stock = StockMarket.fetch_data(info["ticker"])
        
        if stock["error"]:
            print(f" WARNING: Stock API Error or Fallback. Check Stock API key.")
        else:
            print(f" SUCCESS! Fetched real-time details:")
            print(f"   - Current Price: ${stock['price']}")
            print(f"   - Day Change: {stock['change_pct']}%")
            print(f"   - Data Source: {stock.get('source', 'Unknown')}")
            print(f"   - History Points: {len(stock['hist'])}")
    except Exception as e:
        print(f" ERROR: Stock API Error: {e}")

    print("\n" + "="*50)
    print(" DIAGNOSTIC COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_diagnostic()
