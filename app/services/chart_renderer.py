"""InsightFlow Plotly chart rendering service, version 2.0."""
from __future__ import annotations

import logging
from collections.abc import Mapping

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)
DEFAULT_MAX_POINTS = 20_000
DEFAULT_BINS = 30
AGGREGATIONS = {"sum", "mean", "median", "count", "min", "max", "last"}


class ChartRenderingError(ValueError):
    """Raised when a chart recommendation cannot be rendered."""


def _validate_df(df):
    if not isinstance(df, pd.DataFrame):
        raise ChartRenderingError("The chart input must be a pandas DataFrame.")
    if df.empty or len(df.columns) == 0:
        raise ChartRenderingError("The dataset contains no data to visualize.")
    if not df.columns.is_unique:
        raise ChartRenderingError("Duplicate column names must be resolved before rendering.")


def _column(df, name, role):
    if not isinstance(name, str) or not name:
        raise ChartRenderingError(f"The recommendation is missing a valid {role} column.")
    if name not in df.columns:
        raise ChartRenderingError(f"The {role} column '{name}' does not exist in the dataset.")
    return name


def _numeric(df, name, role):
    values = pd.to_numeric(df[name], errors="coerce").replace([np.inf, -np.inf], np.nan)
    if values.notna().sum() == 0:
        raise ChartRenderingError(f"The {role} column '{name}' has no usable numeric values.")
    return values


def _theme(fig, recommendation):
    title = recommendation.get("title")
    if title:
        fig.update_layout(title={"text": str(title), "x": 0.02, "xanchor": "left"})
    fig.update_layout(
        template="plotly_white",
        font={"family": "Arial, sans-serif", "size": 12, "color": "#263238"},
        title={"x": 0.02, "xanchor": "left"},
        margin={"l": 55, "r": 30, "t": 75, "b": 55},
        hoverlabel={"font": {"size": 12}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02,
                "xanchor": "right", "x": 1},
        autosize=True,
    )
    return fig


def render_scatter(df, recommendation, *, max_points=DEFAULT_MAX_POINTS, random_state=42):
    _validate_df(df)
    x = _column(df, recommendation.get("x"), "x-axis")
    y = _column(df, recommendation.get("y"), "y-axis")
    if not isinstance(max_points, int) or isinstance(max_points, bool) or max_points < 1:
        raise ChartRenderingError("'max_points' must be a positive integer.")
    data = pd.DataFrame({x: _numeric(df, x, "x-axis"), y: _numeric(df, y, "y-axis")}).dropna()
    if data.empty:
        raise ChartRenderingError("No complete numeric x/y pairs are available for the scatter plot.")
    if len(data) > max_points:
        data = data.sample(n=max_points, random_state=random_state)
        logger.info("Scatter plot sampled to %s rows.", max_points)
    fig = px.scatter(data, x=x, y=y, title=f"{y} vs {x}",
                     render_mode="webgl" if len(data) >= 5000 else "auto", opacity=0.75)
    fig.update_traces(marker={"size": 8})
    return _theme(fig, recommendation)


def render_histogram(df, recommendation, *, bins=DEFAULT_BINS):
    _validate_df(df)
    column = _column(df, recommendation.get("column"), "histogram")
    if not isinstance(bins, int) or isinstance(bins, bool) or bins < 1:
        raise ChartRenderingError("'bins' must be a positive integer.")
    data = pd.DataFrame({column: _numeric(df, column, "histogram")}).dropna()
    fig = px.histogram(data, x=column, nbins=bins, title=f"Distribution of {column}", opacity=0.85)
    fig.update_traces(marker_line_width=0.5)
    return _theme(fig, recommendation)


def render_bar(df, recommendation):
    _validate_df(df)
    category = _column(df, recommendation.get("x", recommendation.get("column")), "category")
    value = recommendation.get("value_column", recommendation.get("y"))
    aggregation = str(recommendation.get("aggregation", "sum")).lower()
    if aggregation not in AGGREGATIONS:
        raise ChartRenderingError(
            f"Unsupported bar aggregation '{aggregation}'. Choose from: {', '.join(sorted(AGGREGATIONS))}."
        )
    if aggregation == "count" and value is None:
        data = df[[category]].dropna().groupby(category, as_index=False).size().rename(columns={"size": "Count"})
        label = "Count"
    else:
        value = _column(df, value, "value")
        numeric = _numeric(df, value, "value")
        working = pd.DataFrame({category: df[category], value: numeric}).dropna(subset=[category])
        if working.empty:
            raise ChartRenderingError("No valid category/value pairs are available for the bar chart.")
        if aggregation == "count":
            data = working.groupby(category, as_index=False)[value].count()
        else:
            data = working.groupby(category, as_index=False)[value].agg(aggregation)
        label = value
    if data.empty:
        raise ChartRenderingError("No categories are available for the bar chart.")
    data = data.sort_values(label, ascending=False, kind="stable")
    fig = px.bar(data, x=category, y=label, title=f"{label} by {category}")
    fig.update_layout(xaxis_title=category, yaxis_title=f"{aggregation.title()} {label}")
    return _theme(fig, recommendation)


def render_line(df, recommendation):
    _validate_df(df)
    x = _column(df, recommendation.get("x"), "date")
    y = _column(df, recommendation.get("y"), "measure")
    frequency = recommendation.get("frequency", "ME")
    aggregation = str(recommendation.get("aggregation", "sum")).lower()
    if not isinstance(frequency, str) or not frequency.strip():
        raise ChartRenderingError("The line-chart frequency must be a valid pandas frequency string.")
    if aggregation not in AGGREGATIONS:
        raise ChartRenderingError(
            f"Unsupported line aggregation '{aggregation}'. Choose from: {', '.join(sorted(AGGREGATIONS))}."
        )
    dates = pd.to_datetime(df[x], errors="coerce")
    values = _numeric(df, y, "measure")
    working = pd.DataFrame({x: dates, y: values}).dropna()
    if working.empty:
        raise ChartRenderingError("No valid date/measure pairs are available for the line chart.")
    try:
        resampler = working.sort_values(x).set_index(x)[y].resample(frequency)
        if aggregation == "last":
            aggregated = resampler.last()
        elif aggregation == "count":
            aggregated = resampler.count()
        else:
            aggregated = getattr(resampler, aggregation)(min_count=1) if aggregation == "sum" else getattr(resampler, aggregation)()
        data = aggregated.dropna().rename_axis(x).reset_index()
    except (ValueError, TypeError) as exc:
        raise ChartRenderingError(f"Invalid line-chart frequency '{frequency}': {exc}") from exc
    if data.empty:
        raise ChartRenderingError("The selected frequency produced no line-chart data.")
    fig = px.line(data, x=x, y=y, title=f"{y} over {x}", markers=True)
    return _theme(fig, recommendation)


def render_box(df, recommendation):
    """Render a numeric distribution grouped by a categorical variable."""
    _validate_df(df)
    category = _column(df, recommendation.get("x"), "category")
    value = _column(df, recommendation.get("y"), "measure")
    numeric = _numeric(df, value, "measure")
    working = pd.DataFrame({category: df[category], value: numeric}).dropna()
    if working.empty:
        raise ChartRenderingError("No valid category/value pairs are available for the box plot.")
    if working[category].nunique(dropna=True) > 30:
        raise ChartRenderingError("Box plots are limited to 30 categories for readability.")
    fig = px.box(working, x=category, y=value, points="outliers",
                 title=f"Distribution of {value} by {category}")
    return _theme(fig, recommendation)


def render_map(df, recommendation):
    _validate_df(df)
    lat_name = _column(df, recommendation.get("latitude"), "latitude")
    lon_name = _column(df, recommendation.get("longitude"), "longitude")
    data = pd.DataFrame({
        lat_name: pd.to_numeric(df[lat_name], errors="coerce"),
        lon_name: pd.to_numeric(df[lon_name], errors="coerce"),
    }).replace([np.inf, -np.inf], np.nan).dropna()
    data = data[data[lat_name].between(-90, 90) & data[lon_name].between(-180, 180)]
    if data.empty:
        raise ChartRenderingError("No valid latitude/longitude pairs are available for the map.")
    fig = px.scatter_map(data, lat=lat_name, lon=lon_name,
                         zoom=recommendation.get("zoom", 2), title="Geographic Distribution")
    return _theme(fig, recommendation)


_RENDERERS = {
    "scatter": render_scatter,
    "histogram": render_histogram,
    "bar": render_bar,
    "line": render_line,
    "box": render_box,
    "map": render_map,
}


def render_chart(df, recommendation, *, max_points=DEFAULT_MAX_POINTS, random_state=42, bins=DEFAULT_BINS):
    """Dispatch a recommendation to its chart renderer."""
    _validate_df(df)
    if not isinstance(recommendation, Mapping):
        raise ChartRenderingError("A chart recommendation must be dictionary-like.")
    chart_type = recommendation.get("type")
    if not isinstance(chart_type, str) or not chart_type.strip():
        raise ChartRenderingError("The chart recommendation must contain a non-empty 'type'.")
    chart_type = chart_type.strip().lower()
    renderer = _RENDERERS.get(chart_type)
    if renderer is None:
        raise ChartRenderingError(
            f"Unsupported chart type '{chart_type}'. Supported types: {', '.join(_RENDERERS)}."
        )
    if chart_type == "scatter":
        return renderer(df, recommendation, max_points=max_points, random_state=random_state)
    if chart_type == "histogram":
        return renderer(df, recommendation, bins=bins)
    return renderer(df, recommendation)
