import pandas as pd
import pytest

from app.services.chart_export_service import (
    export_chart_to_png,
    generate_chart_images,
)


def test_export_chart_to_png_returns_png_bytes():
    df = pd.DataFrame(
        {
            "revenue": [100, 200, 300, 400],
        }
    )

    recommendation = {
        "type": "histogram",
        "column": "revenue",
        "title": "Revenue Distribution",
    }

    image_bytes = export_chart_to_png(
        df,
        recommendation,
    )

    assert isinstance(image_bytes, bytes)
    assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(image_bytes) > 1000


def test_generate_chart_images_returns_a_list():
    df = pd.DataFrame(
        {
            "revenue": [100, 200, 300, 400, 500],
            "profit": [10, 20, 25, 35, 45],
        }
    )

    images = generate_chart_images(
        df,
        max_charts=2,
    )

    assert isinstance(images, list)
    assert len(images) <= 2

    for chart in images:
        assert "image" in chart
        assert chart["image"].startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_chart_images_respects_zero_limit():
    df = pd.DataFrame(
        {
            "revenue": [100, 200, 300],
        }
    )

    images = generate_chart_images(
        df,
        max_charts=0,
    )

    assert images == []


def test_generate_chart_images_handles_chart_failures(monkeypatch):
    import app.services.chart_export_service as service

    df = pd.DataFrame(
        {
            "revenue": [100, 200, 300],
        }
    )

    monkeypatch.setattr(
        service,
        "recommend_visualizations",
        lambda dataframe: [
            {
                "type": "histogram",
                "column": "revenue",
            }
        ],
    )

    def fail_export(*args, **kwargs):
        raise RuntimeError("Simulated image export failure")

    monkeypatch.setattr(
        service,
        "export_chart_to_png",
        fail_export,
    )

    images = service.generate_chart_images(df)

    assert images == []