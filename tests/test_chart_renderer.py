import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from app.services.chart_renderer import (
    ChartRenderingError, render_bar, render_chart, render_histogram,
    render_line, render_map, render_scatter,
)


def test_scatter_returns_plotly_figure():
    fig = render_chart(pd.DataFrame({"x": [1, 2], "y": [3, 4]}),
                       {"type": "scatter", "x": "x", "y": "y"})
    assert isinstance(fig, go.Figure)
    assert len(fig.data[0].x) == 2


def test_scatter_drops_invalid_pairs_and_samples_deterministically():
    df = pd.DataFrame({"x": list(range(100)) + [None], "y": list(range(100)) + [2]})
    a = render_scatter(df, {"x": "x", "y": "y"}, max_points=10)
    b = render_scatter(df, {"x": "x", "y": "y"}, max_points=10)
    assert len(a.data[0].x) == 10
    assert list(a.data[0].x) == list(b.data[0].x)


@pytest.mark.parametrize("limit", [0, -1, 1.5, True])
def test_scatter_rejects_invalid_limit(limit):
    with pytest.raises(ChartRenderingError):
        render_scatter(pd.DataFrame({"x": [1], "y": [2]}),
                       {"x": "x", "y": "y"}, max_points=limit)


def test_histogram_bins_and_null_handling():
    fig = render_histogram(pd.DataFrame({"v": [1, 2, None, 3]}), {"column": "v"}, bins=7)
    assert fig.data[0].nbinsx == 7
    assert len(fig.data[0].x) == 3


@pytest.mark.parametrize("aggregation, expected", [
    ("sum", 30), ("mean", 15), ("median", 15), ("count", 2), ("min", 10), ("max", 20)
])
def test_bar_aggregations(aggregation, expected):
    df = pd.DataFrame({"group": ["A", "A", "B"], "value": [10, 20, 5]})
    fig = render_bar(df, {"column": "group", "value_column": "value",
                          "aggregation": aggregation})
    assert expected in list(fig.data[0].y)


def test_bar_defaults_to_sum_for_legacy_recommendations():
    df = pd.DataFrame({"region": ["N", "N", "S"], "sales": [10, 20, 5]})
    fig = render_chart(df, {"type": "bar", "column": "region", "x": "region",
                            "y": "sales", "value_column": "sales"})
    assert 30 in list(fig.data[0].y)


def test_bar_count_without_measure_column():
    fig = render_bar(pd.DataFrame({"region": ["N", "N", "S"]}),
                     {"column": "region", "aggregation": "count"})
    assert sorted(list(fig.data[0].y)) == [1, 2]


def test_bar_rejects_unsupported_aggregation():
    with pytest.raises(ChartRenderingError, match="Unsupported bar aggregation"):
        render_bar(pd.DataFrame({"g": ["A"], "v": [1]}),
                   {"column": "g", "value_column": "v", "aggregation": "mode"})


def test_line_sorts_and_aggregates_dates():
    df = pd.DataFrame({"date": ["2025-01-02", "2025-01-01", "2025-01-02"],
                       "sales": [20, 10, 5]})
    fig = render_line(df, {"x": "date", "y": "sales", "frequency": "D"})
    assert list(fig.data[0].y) == [10, 25]


def test_line_rejects_invalid_frequency():
    with pytest.raises(ChartRenderingError, match="Invalid line-chart frequency"):
        render_line(pd.DataFrame({"d": pd.date_range("2025-01-01", periods=2), "v": [1, 2]}),
                    {"x": "d", "y": "v", "frequency": "not-a-frequency"})


def test_map_filters_out_of_range_coordinates():
    df = pd.DataFrame({"lat": [28.6, 95, None], "lon": [77.2, 10, 72]})
    fig = render_map(df, {"latitude": "lat", "longitude": "lon"})
    assert len(fig.data[0].lat) == 1
    assert float(fig.data[0].lat[0]) == pytest.approx(28.6)


@pytest.mark.parametrize("df, rec", [
    (pd.DataFrame(), {"type": "histogram", "column": "x"}),
    (pd.DataFrame({"x": [1]}), {"type": "histogram", "column": "missing"}),
    (pd.DataFrame({"x": ["a", "b"]}), {"type": "histogram", "column": "x"}),
    (pd.DataFrame({"x": [1]}), {"type": "unsupported"}),
    (pd.DataFrame({"x": [1]}), {}),
])
def test_invalid_inputs_raise_chart_rendering_error(df, rec):
    with pytest.raises(ChartRenderingError):
        render_chart(df, rec)


def test_theme_is_applied():
    fig = render_chart(pd.DataFrame({"v": [1, 2, 3]}),
                       {"type": "histogram", "column": "v"})
    assert fig.layout.margin.l == 55
    assert fig.layout.template.layout.paper_bgcolor is not None


def test_non_dataframe_is_rejected():
    with pytest.raises(ChartRenderingError, match="pandas DataFrame"):
        render_chart([1, 2], {"type": "histogram", "column": "x"})
