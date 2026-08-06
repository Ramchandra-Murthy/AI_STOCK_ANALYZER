"""
==========================================================
AI Stock Analyzer - Main Entry Point (CLI)
==========================================================
"""
import argparse
import sys

def run_analysis(ticker: str):
    print(f"[AI Stock Analyzer V6] Executing research pipeline for: {ticker}")
    # Integration point for application use cases / DI container bootstrap

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Stock Analyzer CLI")
    parser.add_argument("--ticker", type=str, default="RELIANCE.NS", help="Stock ticker to analyze")
    args = parser.parse_args()
    
    print(f"Analyzing {args.ticker}...")
    run_analysis(args.ticker)
