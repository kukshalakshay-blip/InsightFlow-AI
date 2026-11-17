import numpy as np
import pandas as pd

from app.services.analysis_engine import (
    analyze_correlation,
    analyze_trend,
    detect_outliers,
)


def _finite_numeric_values(series: pd.Series) -> pd.Series:
    """Return numeric, finite observations while preserving the index."""
    numeric = pd.to_numeric(series, errors="coerce")
    finite_mask = np.isfinite(numeric.to_numpy(dtype=float, na_value=np.nan))
    return numeric.loc[finite_mask]


def _is_continuous_measurement(series: pd.Series, column_name: object) -> bool:
    """Return whether a numeric column is suitable for IQR screening."""
    if (
        not pd.api.types.is_numeric_dtype(series)
        or pd.api.types.is_bool_dtype(series)
    ):
        return False

    values = _finite_numeric_values(series)
    if values.empty or values.nunique() <= 2:
        return False

    name = str(column_name).strip().lower()
    normalized = name.replace("-", "_").replace(" ", "_")
    tokens = set(normalized.split("_"))

    categorical_tokens = {
        "active", "alcohol", "alco", "smoke", "smoking", "gluc",
        "cholesterol", "gender", "sex", "status", "class", "grade",
        "level", "category", "code", "flag", "indicator", "type",
        "stage", "tier", "ordinal",
    }
    if tokens & categorical_tokens:
        return False

    continuous_tokens = {
        "age", "height", "weight", "pressure", "ap_hi", "ap_lo",
        "temperature", "temp", "price", "sales", "revenue", "amount",
        "cost", "profit", "income", "distance", "duration", "bmi",
        "salary", "volume", "quantity", "mass", "length", "width", "score", "rate",
    }
    if tokens & continuous_tokens:
        return True

    if pd.api.types.is_integer_dtype(series) and values.nunique() <= 5:
        return False

    return True


def generate_business_recommendations(
    df: pd.DataFrame,
    visualization_recommendations: list[dict],
) -> list[dict]:
    """Generate universal data quality and analytical recommendations for any domain."""
    if not isinstance(df, pd.DataFrame) or df.empty:
        return []

    if visualization_recommendations is None:
        visualization_recommendations = []

    recommendations = []

    # ======================================================
    # 1. DATA QUALITY: MISSING VALUES
    # ======================================================
    total_cells = df.size
    missing_cells = int(df.isna().sum().sum())

    missing_by_column = (
        df.isna()
        .sum()
        .loc[lambda counts: counts > 0]
        .sort_values(ascending=False)
    )

    missing_column_details = []
    for column, count in missing_by_column.items():
        column_percentage = (count / len(df)) * 100
        missing_column_details.append(
            f"{column}: {count:,} ({column_percentage:.2f}% of rows)"
        )

    if total_cells > 0 and missing_cells > 0:
        missing_percentage = (missing_cells / total_cells) * 100
        priority = "high" if missing_percentage >= 5 else "medium"

        recommendations.append({
            "rule_id": "missing_data",
            "category": "data_quality",
            "priority": priority,
            "title": "Investigate missing data points",
            "finding": (
                f"The dataset contains {missing_cells:,} missing cells "
                f"({missing_percentage:.2f}% of all cells). Affected columns: "
                f"{'; '.join(missing_column_details)}."
            ),
            "action": (
                "Review affected columns to determine whether missing values "
                "should be imputed, averaged, or excluded from specific calculations."
            ),
            "rationale": (
                "Unaddressed missing values can skew aggregate calculations "
                "and reduce analytical reliability."
            ),
        })

    # ======================================================
    # 2. DATA QUALITY: DUPLICATE ROWS
    # ======================================================
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count > 0:
        duplicate_percentage = (duplicate_count / len(df)) * 100
        recommendations.append({
            "rule_id": "duplicate_rows",
            "category": "data_quality",
            "priority": "high" if duplicate_percentage >= 5 else "medium",
            "title": "Review duplicate records",
            "finding": (
                f"The dataset contains {duplicate_count:,} duplicate rows "
                f"({duplicate_percentage:.2f}% of all records)."
            ),
            "action": (
                "Verify whether duplicate entries represent legitimate repeated "
                "events or accidental data duplication."
            ),
            "rationale": (
                "Unintentional duplicates inflate totals and distort overall percentages."
            ),
        })

    # ======================================================
    # 3. DATA QUALITY: NUMERICAL OUTLIERS
    # ======================================================
    excluded_columns = {"id", "row_id", "postal_code", "zip_code"}
    outlier_findings = []

    for column in df.columns:
        column_name = str(column).lower().strip()
        if column_name in excluded_columns or not _is_continuous_measurement(df[column], column):
            continue

        valid_values = _finite_numeric_values(df[column])
        if len(valid_values) < 10 or valid_values.nunique() < 2:
            continue

        result = detect_outliers(df, column)
        outlier_count = int(result["outlier_count"])
        outlier_percentage = float(result["outlier_percentage"])

        if outlier_count == 0 or outlier_percentage >= 25:
            continue

        outlier_findings.append({
            "column": column,
            "count": outlier_count,
            "percentage": outlier_percentage,
            "lower_bound": result["lower_bound"],
            "upper_bound": result["upper_bound"],
        })

    outlier_findings.sort(key=lambda item: item["percentage"], reverse=True)

    for item in outlier_findings[:3]:
        column = item["column"]
        priority = "medium" if item["percentage"] >= 5 else "low"
        recommendations.append({
            "rule_id": f"numerical_outliers:{column}",
            "category": "data_quality",
            "priority": priority,
            "title": f"Review statistical outliers in {column}",
            "finding": (
                f"IQR detection identified {item['count']:,} outlier records in '{column}' "
                f"({item['percentage']:.2f}% of valid records falling outside bounds "
                f"{item['lower_bound']:.4g} to {item['upper_bound']:.4g})."
            ),
            "action": (
                f"Inspect flagged values in '{column}' to confirm whether they represent "
                "legitimate extreme extremes or data entry anomalies."
            ),
            "rationale": (
                "Statistical outliers highlight variance extremes that warrant context evaluation."
            ),
        })

    # Deduplicate and sort recommendations
    unique_recommendations = []
    seen_rule_ids = set()
    for rec in recommendations:
        if rec["rule_id"] in seen_rule_ids:
            continue
        seen_rule_ids.add(rec["rule_id"])
        unique_recommendations.append(rec)

    priority_order = {"high": 0, "medium": 1, "low": 2}
    unique_recommendations.sort(key=lambda x: priority_order.get(x.get("priority"), 3))

    return unique_recommendations