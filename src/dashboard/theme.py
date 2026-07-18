"""Design tokens and shared Plotly styling for the guidance dashboard."""

# Colour palette
COLOR_RAISED = "#22c55e"     # green
COLOR_LOWERED = "#ef4444"    # red
COLOR_REAFFIRMED = "#f59e0b" # amber
COLOR_NEUTRAL = "#6366f1"    # indigo
COLOR_BENCHMARK = "#94a3b8"  # slate

SECTOR_COLORS = [
    "#6366f1", "#22c55e", "#f59e0b", "#ef4444",
    "#0ea5e9", "#a855f7", "#14b8a6", "#f97316",
]

# Background / surface
BG_PAGE = "#0f172a"
BG_CARD = "#1e293b"
BG_INPUT = "#334155"
TEXT_PRIMARY = "#f1f5f9"
TEXT_SECONDARY = "#94a3b8"
BORDER_COLOR = "#334155"

# Layout
GUTTER = 16  # px
BORDER_RADIUS = 8  # px


def base_layout(
    title: str = "",
    xaxis_title: str = "",
    yaxis_title: str = "",
    height: int = 420,
    showlegend: bool = True,
) -> dict:
    """Return a standard Plotly layout dict for the dark theme."""
    return dict(
        title=dict(text=title, font=dict(color=TEXT_PRIMARY, size=15)),
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_CARD,
        font=dict(color=TEXT_PRIMARY, family="Inter, sans-serif", size=12),
        height=height,
        showlegend=showlegend,
        legend=dict(
            bgcolor=BG_PAGE,
            bordercolor=BORDER_COLOR,
            borderwidth=1,
            font=dict(color=TEXT_PRIMARY),
        ),
        xaxis=dict(
            title=xaxis_title,
            gridcolor=BORDER_COLOR,
            zerolinecolor=BORDER_COLOR,
            color=TEXT_SECONDARY,
        ),
        yaxis=dict(
            title=yaxis_title,
            gridcolor=BORDER_COLOR,
            zerolinecolor=BORDER_COLOR,
            color=TEXT_SECONDARY,
        ),
        margin=dict(l=55, r=20, t=50, b=50),
    )


REVISION_COLOR_MAP = {
    "raised": COLOR_RAISED,
    "lowered": COLOR_LOWERED,
    "reaffirmed": COLOR_REAFFIRMED,
    "initiated": COLOR_NEUTRAL,
    "withdrawn": TEXT_SECONDARY,
}
