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