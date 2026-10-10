import pandas as pd

from app.services.recommendation_engine import (
    generate_business_recommendations,
)

from app.services.visualization_engine import (
    recommend_visualizations,
)


# ==========================================================
# LOAD TEST DATASET
# ==========================================================

dataset_path = (
    r"C:\Users\HP\OneDrive\Documents"
    r"\data set\final_engineered_data.csv"
)

df = pd.read_csv(
    dataset_path
)


# ==========================================================
# GENERATE VISUALIZATION RECOMMENDATIONS
# ==========================================================

visualization_recommendations = (
    recommend_visualizations(df)
)


# ==========================================================
# GENERATE BUSINESS RECOMMENDATIONS
# ==========================================================

business_recommendations = (
    generate_business_recommendations(
        df,
        visualization_recommendations,
    )
)


# ==========================================================
# DISPLAY RESULTS
# ==========================================================

print("\n=== BUSINESS RECOMMENDATIONS ===")

if not business_recommendations:

    print(
        "No business recommendations were triggered."
    )

else:

    for index, recommendation in enumerate(
        business_recommendations,
        start=1,
    ):

        print(
            f"\n{index}. "
            f"{recommendation['title']}"
        )

        print(
            f"Priority: "
            f"{recommendation['priority'].upper()}"
        )

        print(
            f"Category: "
            f"{recommendation['category']}"
        )

        print(
            f"Finding: "
            f"{recommendation['finding']}"
        )

        print(
            f"Suggested action: "
            f"{recommendation['action']}"
        )

        print(
            f"Rationale: "
            f"{recommendation['rationale']}"
        )