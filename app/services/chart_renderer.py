import pandas as pd
import plotly.express as px


def render_scatter(
    df: pd.DataFrame,
    recommendation: dict,
):
    """
    Create a scatter plot from a visualization recommendation.
    """

    x_column = recommendation["x"]
    y_column = recommendation["y"]

    figure = px.scatter(
        df,
        x=x_column,
        y=y_column,
        title=f"{y_column} vs {x_column}",
    )

    return figure


def render_histogram(
    df: pd.DataFrame,
    recommendation: dict,
):
    """
    Create a histogram from a visualization recommendation.
    """

    column = recommendation["column"]

    figure = px.histogram(
        df,
        x=column,
        title=f"Distribution of {column}",
    )

    return figure


def render_bar(
    df: pd.DataFrame,
    recommendation: dict,
):
    """
    Create a bar chart from a visualization recommendation.
    """

    column = recommendation["column"]

    counts = (
        df[column]
        .value_counts()
        .reset_index()
    )

    counts.columns = [
        column,
        "count",
    ]

    figure = px.bar(
        counts,
        x=column,
        y="count",
        title=f"Category Frequency: {column}",
    )

    return figure


def render_line(
    df: pd.DataFrame,
    recommendation: dict,
):
    """
    Create a line chart from a visualization recommendation.
    """

    x_column = recommendation["x"]
    y_column = recommendation["y"]

    chart_data = df[
        [x_column, y_column]
    ].copy()

    chart_data[x_column] = pd.to_datetime(
        chart_data[x_column],
        errors="coerce",
        format="mixed",
    )

    chart_data = chart_data.dropna(
        subset=[x_column, y_column]
    )

    chart_data = (
        chart_data
        .groupby(x_column, as_index=False)[y_column]
        .mean()
        .sort_values(x_column)
    )

    figure = px.line(
        chart_data,
        x=x_column,
        y=y_column,
        title=f"{y_column} over {x_column}",
    )

    return figure

def render_map(
    df: pd.DataFrame,
    recommendation: dict,
):
    """
    Create a geographic scatter map from a visualization
    recommendation.
    """

    latitude_column = recommendation["latitude"]
    longitude_column = recommendation["longitude"]

    figure = px.scatter_map(
        df,
        lat=latitude_column,
        lon=longitude_column,
        zoom=10,
        title="Geographic Distribution",
    )

    return figure


def render_chart(
    df: pd.DataFrame,
    recommendation: dict,
):
    """
    Render a chart based on the recommendation type.
    """

    chart_type = recommendation["type"]

    if chart_type == "scatter":
        return render_scatter(
            df,
            recommendation,
        )

    if chart_type == "histogram":
        return render_histogram(
            df,
            recommendation,
        )

    if chart_type == "bar":
        return render_bar(
            df,
            recommendation,
        )

    if chart_type == "line":
        return render_line(
            df,
            recommendation,
        )

    if chart_type == "map":
        return render_map(
            df,
            recommendation,
        )

    raise ValueError(
        f"Unsupported chart type: {chart_type}"
    )