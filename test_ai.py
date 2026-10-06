from app.services.ai_service import generate_ai_analysis


test_context = {
    "dataset": {
        "rows": 9994,
        "columns": 27,
    },
    "metrics": {
        "sales": {
            "total": 2300000,
            "mean": 230.14,
            "median": 85.20,
        },
        "profit": {
            "total": 286000,
            "mean": 28.61,
            "median": 12.40,
        },
    },
    "recommendations": [],
}


result = generate_ai_analysis(
    test_context
)


print("\n=== EXECUTIVE SUMMARY ===")
print(result.executive_summary)

print("\n=== KEY FINDINGS ===")

for finding in result.key_findings:
    print(f"- {finding}")

print("\n=== RECOMMENDATIONS ===")

for recommendation in result.recommendations:
    print(f"- {recommendation}")

print("\n=== RISKS / ANOMALIES ===")

for risk in result.risks_or_anomalies:
    print(f"- {risk}")