from __future__ import annotations

import argparse

from core.container import ServiceKey, bootstrap_container, container


def run_analysis(ticker: str):
    """Execute the restored EROS pipeline through the composition root."""
    bootstrap_container()
    research_service = container.resolve(ServiceKey.RESEARCH)
    return research_service.run_pipeline(ticker)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Stock Analyzer / EROS 3.0")
    parser.add_argument("--ticker", default="RELIANCE.NS", help="Stock ticker to analyze")
    args = parser.parse_args()

    result = run_analysis(args.ticker)
    print(f"Pipeline status: {result.get('status')}")
    print(f"Pipeline version: {result.get('version')}")
    print(f"Symbol: {result.get('symbol')}")
    if result.get("errors"):
        print("Stage errors:")
        for error in result["errors"]:
            print(f" - {error}")


if __name__ == "__main__":
    main()
