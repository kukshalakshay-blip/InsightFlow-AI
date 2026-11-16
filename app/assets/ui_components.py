"""Reusable InsightFlow UI building blocks.

Place at: app/assets/ui_components.py
"""
from __future__ import annotations

import html
from typing import Iterable, Optional

import streamlit as st

PLOT_COLORWAY = [
    "#22e66b", "#2dd4bf", "#a3e635", "#fbbf24",
    "#60a5fa", "#f472b6", "#c084fc", "#fb923c",
]


def _html(markup: str) -> str:
    """Collapse indentation so Markdown never mistakes HTML for a code block."""
    return "".join(line.strip() for line in markup.splitlines())


def _render(markup: str) -> None:
    st.markdown(_html(markup), unsafe_allow_html=True)


def card(name: str):
    """Glass card container. Usage: `with card("summary"): ...` (needs Streamlit >= 1.39)."""
    return st.container(key=f"card_{name}")


# ----------------------------------------------------------------------
# Headers & hero
# ----------------------------------------------------------------------
def render_header(title: str, subtitle: str, badge: str = "") -> None:
    badge_html = f'<span class="if-pill if-pill--ready">{html.escape(badge)}</span>' if badge else ""
    _render(
        f"""
        <div class="if-header">
            <h1>{html.escape(title)} {badge_html}</h1>
            <p>{html.escape(subtitle)}</p>
        </div>
        """
    )


def render_hero(eyebrow: str, title: str, body: str, highlight: str = "") -> None:
    hl = f' <span class="if-grad">{html.escape(highlight)}</span>' if highlight else ""
    _render(
        f"""
        <div class="if-hero">
            <span class="if-eyebrow">{html.escape(eyebrow)}</span>
            <h2>{html.escape(title)}{hl}</h2>
            <p>{html.escape(body)}</p>
        </div>
        """
    )


def render_ticker(text: str = "INSIGHTFLOW AI", repeat: int = 12) -> None:
    """Scrolling neon brand strip (decorative)."""
    items = "".join(f'<span class="if-ticker__item">{html.escape(text)}</span>' for _ in range(repeat * 2))
    _render(f'<div class="if-ticker"><div class="if-ticker__track">{items}</div></div>')


# ----------------------------------------------------------------------
# Metric card (optional sparkline)
# ----------------------------------------------------------------------
def _sparkline_svg(values: Iterable[float], w: int = 110, h: int = 38) -> str:
    vals = [float(v) for v in values if v is not None]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    pts = [
        (i * w / (len(vals) - 1), h - 4 - ((v - lo) / span) * (h - 8))
        for i, v in enumerate(vals)
    ]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{line} L{w},{h} L0,{h} Z"
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        '<defs><linearGradient id="ifg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#22e66b" stop-opacity="0.45"/>'
        '<stop offset="100%" stop-color="#22e66b" stop-opacity="0"/></linearGradient></defs>'
        f'<path d="{area}" fill="url(#ifg)"/>'
        f'<path d="{line}" fill="none" stroke="#4ef08e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        "</svg>"
    )


def render_metric_card(
    label: str,
    value: str,
    delta: str = "",
    trend: str = "up",
    sparkline: Optional[Iterable[float]] = None,
) -> None:
    """KPI card. trend: 'up' | 'down' | 'flat'. Only pass a sparkline built from real data."""
    trend = trend if trend in {"up", "down", "flat"} else "flat"
    arrow = {"up": "↑", "down": "↓", "flat": "•"}[trend]
    delta_html = (
        f'<span class="if-stat__delta if-stat__delta--{trend}">{arrow} {html.escape(delta)}</span>'
        if delta else ""
    )
    spark_html = _sparkline_svg(sparkline) if sparkline is not None else ""
    _render(
        f"""
        <div class="if-stat">
            <div>
                <div class="if-stat__label">{html.escape(label)}</div>
                <div class="if-stat__value">{html.escape(str(value))}</div>
                {delta_html}
            </div>
            <div>{spark_html}</div>
        </div>
        """
    )


# ----------------------------------------------------------------------
# Workflow step card
# ----------------------------------------------------------------------
_STATUS = {
    "done": ("Done ✓", "if-pill--done"),
    "ready": ("Ready", "if-pill--ready"),
    "next": ("Start here", "if-pill--next"),
    "locked": ("Needs data", "if-pill--locked"),
}


def render_step_card(number: str, title: str, description: str, status: str = "locked") -> None:
    label, css = _STATUS.get(status, _STATUS["locked"])
    _render(
        f"""
        <div class="if-step">
            <div class="if-step__top">
                <span class="if-step__num">{html.escape(number)}</span>
                <span class="if-pill {css}">{label}</span>
            </div>
            <div class="if-step__title">{html.escape(title)}</div>
            <div class="if-step__desc">{html.escape(description)}</div>
        </div>
        """
    )


# ----------------------------------------------------------------------
# Empty state (replaces the st.info + st.stop pattern)
# ----------------------------------------------------------------------
def render_empty_state(
    icon: str,
    title: str,
    message: str,
    page: Optional[str] = None,
    label: str = "Continue",
    cta_icon: Optional[str] = None,
) -> None:
    _render(
        f"""
        <div class="if-empty">
            <div class="if-empty__icon">{html.escape(icon)}</div>
            <div class="if-empty__title">{html.escape(title)}</div>
            <div class="if-empty__msg">{html.escape(message)}</div>
        </div>
        """
    )
    if page:
        st.page_link(page, label=label, icon=cta_icon, use_container_width=True)


# ----------------------------------------------------------------------
# Sidebar: active dataset card (call AFTER pg.run() so it is never stale)
# ----------------------------------------------------------------------
def render_sidebar_status() -> None:
    with st.sidebar:
        if "dataset" in st.session_state:
            df = st.session_state["dataset"]
            name = html.escape(str(st.session_state.get("dataset_name", "Unnamed dataset")))
            body = (
                f'<div class="if-sidebar-status__name">{name}</div>'
                f'<div class="if-sidebar-status__meta">{len(df):,} rows · {len(df.columns):,} columns</div>'
            )
        else:
            body = '<div class="if-sidebar-status__meta">No dataset loaded yet</div>'
        _render(
            f"""
            <div class="if-sidebar-status">
                <div class="if-sidebar-status__label">Active dataset</div>
                {body}
            </div>
            """
        )


# ----------------------------------------------------------------------
# Plotly: make every chart match the theme
# ----------------------------------------------------------------------
def style_figure(fig):
    """Apply the dark violet look to a Plotly figure and return it."""
    grid = "rgba(255,255,255,0.06)"
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#c5d6cc", size=12),
        colorway=PLOT_COLORWAY,
        margin=dict(l=10, r=10, t=48, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#0c1a13", font_size=12),
    )
    fig.update_xaxes(gridcolor=grid, zerolinecolor=grid, linecolor=grid)
    fig.update_yaxes(gridcolor=grid, zerolinecolor=grid, linecolor=grid)
    return fig