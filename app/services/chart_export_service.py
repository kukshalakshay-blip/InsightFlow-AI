import logging
from io import BytesIO

import pandas as pd
import plotly.io as pio

from app.services.chart_renderer import render_chart
from app.services.visualization_engine import recommend_visualizations


logger = logging.getLogger(__name__)


def export_chart_to_png(
    df: pd.DataFrame,
    recommendation: dict,
    width: int = 1000,
    height: int = 600,
) -> bytes:
    """
    Render a recommended Plotly chart and export it as PNG bytes.
    """
    figure = render_chart(df, recommendation)

    image_bytes = pio.to_image(
        figure,
        format="png",
        width=width,
        height=height,
        scale=1,
    )

    return image_bytes


def generate_chart_images(
    df: pd.DataFrame,
    max_charts: int = 3,
) -> list[dict]:
    """
    Generate PNG images for recommended visualizations.

    Individual chart failures are logged and skipped so one
    unsupported chart does not prevent the remaining charts
    from exporting.
    """
    if max_charts <= 0:
        return []

    recommendations = recommend_visualizations(df)
    chart_images = []

    for recommendation in recommendations[:max_charts]:
        chart_type = recommendation.get("type", "chart")
        chart_title = recommendation.get(
            "title",
            str(chart_type).title(),
        )

        try:
            image_bytes = export_chart_to_png(
                df,
                recommendation,
            )

            chart_images.append(
                {
                    "title": chart_title,
                    "type": chart_type,
                    "image": image_bytes,
                }
            )

        except Exception:
            logger.warning(
                "Failed to export chart '%s' (type: %s).",
                chart_title,
                chart_type,
                exc_info=True,
            )
            continue

    return chart_images
