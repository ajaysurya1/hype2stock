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
    
    # Force UTF-8 encoding
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
    
    print("\n" + "="*60)
    print(" HYPE2STOCK FULL SYSTEM DIAGNOSTIC")
    print("="*60)
    
    for studio_name, info in STUDIOS.items():
        print(f"\n🚀 STUDIO: {studio_name} (${info['ticker']})")
        print("-" * 45)
        
        # 1. TMDB Test
        try:
            movies = fetch_studio_movies(info["tmdb_id"], count=2)
            if movies:
                print(f" [TMDB] OK: Found {len(movies)} movies. Top: {movies[0]['title']}")
            else:
                print(f" [TMDB] EMPTY: No movies found for ID {info['tmdb_id']}")
        except Exception as e:
            print(f" [TMDB] ERROR: {e}")

        # 2. Stock Test
        try:
            stock = StockMarket.fetch_data(info["ticker"])
            if stock["error"] or stock["price"] == 0:
                print(f" [STOCK] FAILED: Price is 0 or error returned for ${info['ticker']}")
                # Try fallback ticker for Lionsgate
                if info['ticker'] == "LGF-A":
                    print("   --> Testing LGF.A fallback...")
                    alt = StockMarket.fetch_data("LGF.A")
                    if not alt["error"] and alt["price"] > 0:
                        print("   --> LGF.A WORKS!")
            else:
                print(f" [STOCK] OK: ${stock['price']} ({stock['change_pct']}%) via {stock.get('source')}")
                print(f" [CHART] OK: {len(stock['hist'])} history points")
        except Exception as e:
            print(f" [STOCK] ERROR: {e}")

    print("\n" + "="*60)
    print(" DIAGNOSTIC COMPLETE")
    print("="*60 + "\n")

    print("\n" + "="*50)
    print(" DIAGNOSTIC COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_diagnostic()
