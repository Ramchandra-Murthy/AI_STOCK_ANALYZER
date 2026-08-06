"""
==========================================================
AI Stock Analyzer - Main Entry Point (CLI)
==========================================================
"""
import argparse
from core.container import bootstrap_container, container, ServiceKey

def run_analysis(ticker: str):
    print(f"[AI Stock Analyzer V6] Executing research pipeline for: {ticker}")
    
    # 1. Initialize Application via Composition Root
    bootstrap_container()
    
    # 2. Resolve required service without instantiating it directly
    research_service = container.resolve(ServiceKey.RESEARCH)
    
    # 3. Execute
    result = research_service.run_pipeline(ticker)
    print(f"Pipeline Result: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Stock Analyzer CLI")
    parser.add_argument("--ticker", type=str, default="RELIANCE.NS", help="Stock ticker to analyze")
    args = parser.parse_args()
    
    run_analysis(args.ticker)
