"""Run visualization and business recommendations against a local CSV file.

Usage:
    python scripts/demo_recommendations.py path/to/dataset.csv
"""

import argparse
from pathlib import Path

import pandas as pd
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.recommendation_engine import generate_business_recommendations
from app.services.visualization_engine import recommend_visualizations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="Path to a CSV dataset")
    args = parser.parse_args()

    if not args.dataset.is_file():
        parser.error(f"Dataset not found: {args.dataset}")

    df = pd.read_csv(args.dataset)
    visualization_recommendations = recommend_visualizations(df)
    business_recommendations = generate_business_recommendations(
        df, visualization_recommendations
    )

    print("\n=== BUSINESS RECOMMENDATIONS ===")
    if not business_recommendations:
        print("No business recommendations were triggered.")
        return

    for index, recommendation in enumerate(business_recommendations, start=1):
        print(f"\n{index}. {recommendation['title']}")
        print(f"Priority: {recommendation['priority'].upper()}")
        print(f"Category: {recommendation['category']}")
        print(f"Finding: {recommendation['finding']}")
        print(f"Suggested action: {recommendation['action']}")
        print(f"Rationale: {recommendation['rationale']}")


if __name__ == "__main__":
    main()
