"""All Plotly figure construction for the guidance revision dashboard."""

from typing import Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.dashboard.theme import (
    base_layout, REVISION_COLOR_MAP, SECTOR_COLORS,
    COLOR_RAISED, COLOR_LOWERED, COLOR_REAFFIRMED,
    COLOR_NEUTRAL, COLOR_BENCHMARK, TEXT_PRIMARY, TEXT_SECONDARY, BG_CARD,
)


def revision_distribution_pie(df: pd.DataFrame) -> go.Figure:
    """Pie chart of guidance revision types."""
    counts = (
        df.drop_duplicates("metric_id")["revision_type"]
        .value_counts()
        .reset_index()
    )
    counts.columns = ["revision_type", "count"]
    colors = [REVISION_COLOR_MAP.get(rt, COLOR_NEUTRAL) for rt in counts["revision_type"]]

    fig = go.Figure(go.Pie(
        labels=counts["revision_type"],
        values=counts["count"],
        marker_colors=colors,
        hole=0.4,
        textfont=dict(color=TEXT_PRIMARY),
    ))
    fig.update_layout(**base_layout(title="Guidance Revision Distribution", showlegend=True))
    return fig


def abnormal_return_by_sector(
    df: pd.DataFrame,
    window_days: int = 1,
) -> go.Figure:
    """Bar chart: average abnormal return by sector."""
    filtered = df[df["window_days"] == window_days].copy()
    grouped = (
        filtered.groupby("sector")["abnormal_return"]
        .mean()
        .reset_index()
        .sort_values("abnormal_return", ascending=False)
    )

    colors = [
        COLOR_RAISED if v >= 0 else COLOR_LOWERED
        for v in grouped["abnormal_return"]
    ]

    fig = go.Figure(go.Bar(
        x=grouped["sector"],
        y=grouped["abnormal_return"],
        marker_color=colors,
        text=grouped["abnormal_return"].round(2).astype(str) + "%",
        textposition="outside",
        textfont=dict(color=TEXT_PRIMARY, size=11),
    ))
    fig.update_layout(**base_layout(
        title=f"Avg Abnormal Return by Sector (Day {window_days})",
        xaxis_title="Sector",
        yaxis_title="Abnormal Return (%)",
    ))
    return fig


def stock_reaction_by_window(
    df: pd.DataFrame,
    metric_type: Optional[str] = None,
    revision_type: Optional[str] = None,
) -> go.Figure:
    """Box plot: stock return distributions across event windows."""
    filtered = df.copy()
    if metric_type:
        filtered = filtered[filtered["metric_type"] == metric_type]
    if revision_type:
        filtered = filtered[filtered["revision_type"] == revision_type]

    windows = sorted(filtered["window_days"].dropna().unique())
    fig = go.Figure()
    for w in windows:
        subset = filtered[filtered["window_days"] == w]["abnormal_return"].dropna()
        fig.add_trace(go.Box(
            y=subset,
            name=f"Day {int(w)}",
            marker_color=COLOR_NEUTRAL,
            line_color=COLOR_NEUTRAL,
        ))

    fig.update_layout(**base_layout(
        title="Stock Reaction by Event Window",
        xaxis_title="Window",
        yaxis_title="Abnormal Return (%)",
        showlegend=False,
    ))
    return fig


def revision_magnitude_scatter(
    df: pd.DataFrame,
    metric_type: str = "revenue",
    window_days: int = 1,
) -> go.Figure:
    """Scatter: revision magnitude vs stock reaction."""
    filtered = df[
        (df["metric_type"] == metric_type)
        & (df["window_days"] == window_days)
        & df["pct_change"].notna()
        & df["abnormal_return"].notna()
    ].copy()

    colors = [REVISION_COLOR_MAP.get(rt, COLOR_NEUTRAL) for rt in filtered["revision_type"]]

    fig = go.Figure(go.Scatter(
        x=filtered["pct_change"].astype(float),
        y=filtered["abnormal_return"].astype(float),
        mode="markers",
        marker=dict(color=colors, size=7, opacity=0.75),
        text=filtered["ticker"],
        hovertemplate="%{text}<br>Revision: %{x:.1f}%<br>Abnormal Return: %{y:.2f}%",
    ))
    fig.update_layout(**base_layout(
        title=f"{metric_type.title()} Revision Magnitude vs Stock Reaction (Day {window_days})",
        xaxis_title="Guidance Revision (%)",
        yaxis_title="Abnormal Return (%)",
        showlegend=False,
    ))
    return fig


def revision_timeline(df: pd.DataFrame) -> go.Figure:
    """Time series of guidance event counts by revision type."""
    events = df.drop_duplicates("metric_id").copy()
    events["announcement_date"] = pd.to_datetime(events["announcement_date"])
    events["month"] = events["announcement_date"].dt.to_period("M").astype(str)

    grouped = (
        events.groupby(["month", "revision_type"])
        .size()
        .reset_index(name="count")
    )

    fig = go.Figure()
    for rtype, color in REVISION_COLOR_MAP.items():
        subset = grouped[grouped["revision_type"] == rtype]
        if not subset.empty:
            fig.add_trace(go.Scatter(
                x=subset["month"],
                y=subset["count"],
                name=rtype.title(),
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=5),
            ))

    fig.update_layout(**base_layout(
        title="Guidance Revision Events Over Time",
        xaxis_title="Month",
        yaxis_title="Event Count",
    ))
    return fig


def sector_heatmap(
    df: pd.DataFrame,
    window_days: int = 1,
) -> go.Figure:
    """Heatmap: avg abnormal return by sector and revision type."""
    filtered = df[df["window_days"] == window_days].copy()
    pivot = (
        filtered.groupby(["sector", "revision_type"])["abnormal_return"]
        .mean()
        .unstack(fill_value=0)
    )

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[[0, COLOR_LOWERED], [0.5, BG_CARD], [1, COLOR_RAISED]],
        text=[[f"{v:.2f}%" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(color=TEXT_PRIMARY, size=10),
    ))
    fig.update_layout(**base_layout(
        title=f"Avg Abnormal Return: Sector x Revision Type (Day {window_days})",
        showlegend=False,
    ))
    return fig


def kpi_cards(df: pd.DataFrame) -> list[dict]:
    """Return KPI values as a list of dicts for display cards."""
    total_events = df["event_id"].nunique()
    total_companies = df["ticker"].nunique()
    pct_raised = (
        (df.drop_duplicates("metric_id")["revision_type"] == "raised").mean() * 100
        if not df.empty else 0
    )
    avg_day1 = df[df["window_days"] == 1]["abnormal_return"].mean()

    return [
        {"label": "Total Events", "value": f"{total_events:,}"},
        {"label": "Companies", "value": f"{total_companies:,}"},
        {"label": "% Raised", "value": f"{pct_raised:.1f}%"},
        {"label": "Avg Day-1 Abnormal Return", "value": f"{avg_day1:.2f}%" if pd.notna(avg_day1) else "N/A"},
    ]
