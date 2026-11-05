import pandas as pd

from app.services.visualization_engine import recommend_visualizations


def test_numeric_binary_flag_is_not_used_as_scatter_measure():
    df = pd.DataFrame({
        "active": [0, 1, 0, 1, 0, 1],
        "age": [21.2, 34.1, 44.0, 55.5, 61.2, 39.8],
        "bmi": [22.1, 28.4, 25.0, 31.2, 27.3, 24.8],
    })
    recommendations = recommend_visualizations(df)
    assert not any(
        rec["type"] == "scatter" and "active" in (rec.get("x"), rec.get("y"))
        for rec in recommendations
    )


def test_healthcare_understanding_prefers_grouped_distribution_boxplot():
    df = pd.DataFrame({
        "active": [0, 1, 0, 1, 0, 1],
        "age": [21, 34, 44, 55, 61, 39],
    })
    understanding = {
        "domain": "healthcare",
        "column_meanings": [
            {"column": "active", "data_role": "binary_categorical", "semantic_role": "activity status"},
            {"column": "age", "data_role": "continuous", "semantic_role": "patient age"},
        ],
    }
    recommendations = recommend_visualizations(df, understanding=understanding)
    assert any(
        rec["type"] == "box" and rec.get("x") == "active" and rec.get("y") == "age"
        for rec in recommendations
    )


def test_without_ai_understanding_deterministic_fallback_still_works():
    df = pd.DataFrame({"region": ["N", "S", "N", "S"], "sales": [10, 20, 30, 40]})
    recommendations = recommend_visualizations(df)
    assert any(rec["type"] == "bar" and rec.get("x") == "region" for rec in recommendations)


def test_ai_column_role_mapping_is_ignored_for_unknown_column_names():
    df = pd.DataFrame({"sales": [10, 20, 30]})
    understanding = {
        "domain": "commerce",
        "column_meanings": [
            {"column": "not_in_dataframe", "data_role": "binary_categorical"}
        ],
    }
    recommendations = recommend_visualizations(df, understanding=understanding)
    assert any(rec["type"] == "histogram" and rec.get("column") == "sales" for rec in recommendations)


def test_healthcare_box_recommendation_renders_plotly_figure():
    import plotly.graph_objects as go
    from app.services.chart_renderer import render_chart

    df = pd.DataFrame({"group": [0, 1, 0, 1, 0, 1], "measurement": [2, 5, 3, 7, 4, 8]})
    fig = render_chart(df, {"type": "box", "x": "group", "y": "measurement"})
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert set(fig.data[0].x) == {0, 1}


def test_line_renderer_uses_requested_mean_aggregation():
    from app.services.chart_renderer import render_line

    df = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-01", "2025-01-02"],
        "temperature": [10, 20, 30],
    })
    fig = render_line(df, {
        "x": "date", "y": "temperature", "frequency": "D", "aggregation": "mean"
    })
    assert list(fig.data[0].y) == [15, 30]
