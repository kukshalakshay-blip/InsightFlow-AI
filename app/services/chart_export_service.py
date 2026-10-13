from io import BytesIO

import pandas as pd
import plotly.io as pio

from app.services.chart_renderer import render_chart
from app.services.visualization_engine import recommend_visualizations


def export_chart_to_png(
    df: pd.DataFrame,
    recommendation: dict,
    width: int = 1000,
    height: int = 600,
) -> bytes:
    """
    Render a recommended Plotly chart and export it as PNG bytes.

    Parameters
    ----------
    df:
        Dataset used to render the chart.

    recommendation:
        Visualization recommendation from the visualization engine.

    width:
        Export image width in pixels.

    height:
        Export image height in pixels.

    Returns
    -------
    bytes:
        PNG image suitable for embedding in a PDF.
    """

    figure = render_chart(
        df,
        recommendation,
    )

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

    Individual chart failures are skipped so one unsupported
    chart does not prevent the remaining charts from exporting.
    """

    if max_charts <= 0:
        return []

    recommendations = recommend_visualizations(df)

    chart_images = []

    for recommendation in recommendations[:max_charts]:

        try:
            image_bytes = export_chart_to_png(
                df,
                recommendation,
            )

            chart_images.append(
                {
                    "title": recommendation.get(
                        "title",
                        recommendation.get(
                            "type",
                            "Visualization",
                        ).title(),
                    ),
                    "type": recommendation.get(
                        "type",
                        "chart",
                    ),
                    "image": image_bytes,
                }
            )

        except Exception:
            # A failed chart must not block other charts.
            continue

    return chart_images