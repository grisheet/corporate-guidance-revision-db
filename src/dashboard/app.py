"""Main Dash application entry point for the guidance revision dashboard."""

import os
import logging

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from src.analytics import load_full_dataset
from src.dashboard.theme import BG_PAGE, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR
from src.dashboard.callbacks import register_callbacks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(df=None) -> dash.Dash:
    """Factory function — creates and configures the Dash app."""
    if df is None:
        logger.info("Loading dataset from database...")
        df = load_full_dataset()
        logger.info("Loaded %d rows.", len(df))

    sectors = sorted(df["sector"].dropna().unique().tolist())
    metric_types = sorted(df["metric_type"].dropna().unique().tolist())

    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.SLATE],
        title="Guidance Revision Analytics",
        suppress_callback_exceptions=True,
    )

    app.index_string = app.index_string.replace(
        "<body>",
        f'<body style="background-color:{BG_PAGE};margin:0;">',
    )

    FILTER_STYLE = {
        "background": BG_CARD,
        "border": f"1px solid {BORDER_COLOR}",
        "borderRadius": "6px",
        "color": TEXT_PRIMARY,
        "marginBottom": "0.5rem",
    }

    app.layout = html.Div(
        style={"backgroundColor": BG_PAGE, "minHeight": "100vh", "padding": "1.5rem"},
        children=[
            # Header
            html.Div(
                [
                    html.H1(
                        "Corporate Guidance Revision Analytics",
                        style={"color": TEXT_PRIMARY, "marginBottom": "0.25rem", "fontSize": "1.5rem"},
                    ),
                    html.P(
                        "Track how corporate guidance changes move stock prices across sectors and time windows.",
                        style={"color": TEXT_SECONDARY, "margin": 0},
                    ),
                ],
                style={"marginBottom": "1.5rem"},
            ),

            # Filters row
            html.Div(
                style={"display": "flex", "gap": "1rem", "flexWrap": "wrap", "marginBottom": "1.5rem"},
                children=[
                    html.Div([
                        html.Label("Sector", style={"color": TEXT_SECONDARY, "fontSize": "0.8rem"}),
                        dcc.Dropdown(
                            id="sector-filter",
                            options=[{"label": s, "value": s} for s in sectors],
                            multi=True,
                            placeholder="All sectors",
                            style=FILTER_STYLE,
                        ),
                    ], style={"flex": "2", "minWidth": "200px"}),

                    html.Div([
                        html.Label("Metric", style={"color": TEXT_SECONDARY, "fontSize": "0.8rem"}),
                        dcc.Dropdown(
                            id="metric-filter",
                            options=[{"label": m.replace("_", " ").title(), "value": m}
                                     for m in metric_types],
                            placeholder="All metrics",
                            style=FILTER_STYLE,
                        ),
                    ], style={"flex": "1", "minWidth": "150px"}),

                    html.Div([
                        html.Label("Event Window", style={"color": TEXT_SECONDARY, "fontSize": "0.8rem"}),
                        dcc.Dropdown(
                            id="window-filter",
                            options=[{"label": f"Day {w}", "value": w} for w in [0, 1, 3, 5, 20]],
                            value=1,
                            clearable=False,
                            style=FILTER_STYLE,
                        ),
                    ], style={"flex": "1", "minWidth": "130px"}),

                    html.Div([
                        html.Label("Revision Type", style={"color": TEXT_SECONDARY, "fontSize": "0.8rem"}),
                        dcc.Dropdown(
                            id="revision-filter",
                            options=[
                                {"label": "All", "value": "all"},
                                {"label": "Raised", "value": "raised"},
                                {"label": "Lowered", "value": "lowered"},
                                {"label": "Reaffirmed", "value": "reaffirmed"},
                            ],
                            value="all",
                            clearable=False,
                            style=FILTER_STYLE,
                        ),
                    ], style={"flex": "1", "minWidth": "150px"}),
                ],
            ),

            # Tabs
            dcc.Tabs(
                id="main-tabs",
                value="overview",
                style={"marginBottom": "1rem"},
                colors={"border": BORDER_COLOR, "primary": "#6366f1", "background": BG_PAGE},
                children=[
                    dcc.Tab(label="Overview", value="overview"),
                    dcc.Tab(label="Revision Analysis", value="revisions"),
                    dcc.Tab(label="Stock Reactions", value="reactions"),
                    dcc.Tab(label="Sector Comparison", value="sectors"),
                    dcc.Tab(label="Raw Data", value="data"),
                ],
            ),

            # Tab content area
            html.Div(id="tab-content"),
        ],
    )

    register_callbacks(app, df)
    return app


if __name__ == "__main__":
    host = os.getenv("DASH_HOST", "127.0.0.1")
    port = int(os.getenv("DASH_PORT", "8050"))
    debug = os.getenv("DASH_DEBUG", "false").lower() == "true"

    application = create_app()
    application.run(host=host, port=port, debug=debug)
