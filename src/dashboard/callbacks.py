"""Dash callbacks for the guidance revision dashboard."""

import pandas as pd
from dash import Input, Output, callback

from src.dashboard import figures


def register_callbacks(app, df: pd.DataFrame) -> None:
    """Register all Dash callbacks with the application."""

    @app.callback(
        Output("tab-content", "children"),
        Input("main-tabs", "value"),
        Input("sector-filter", "value"),
        Input("metric-filter", "value"),
        Input("window-filter", "value"),
        Input("revision-filter", "value"),
    )
    def render_tab(
        tab: str,
        selected_sectors: list,
        selected_metric: str,
        selected_window: int,
        selected_revision: str,
    ):
        """Render the active tab with current filter state."""
        from dash import html, dcc
        import plotly.graph_objects as go
        from src.dashboard.theme import BG_CARD, TEXT_PRIMARY

        # Apply filters
        filtered = df.copy()
        if selected_sectors:
            filtered = filtered[filtered["sector"].isin(selected_sectors)]
        if selected_revision and selected_revision != "all":
            filtered = filtered[filtered["revision_type"] == selected_revision]

        if filtered.empty:
            return html.Div("No data matches the current filters.",
                           style={"color": TEXT_PRIMARY, "padding": "2rem"})

        if tab == "overview":
            kpis = figures.kpi_cards(filtered)
            cards = html.Div(
                [
                    html.Div(
                        [
                            html.P(k["label"], style={"color": "#94a3b8", "margin": 0, "fontSize": "0.8rem"}),
                            html.H3(k["value"], style={"color": TEXT_PRIMARY, "margin": 0}),
                        ],
                        style={
                            "background": BG_CARD,
                            "border": "1px solid #334155",
                            "borderRadius": "8px",
                            "padding": "1rem",
                            "flex": "1",
                        },
                    )
                    for k in kpis
                ],
                style={"display": "flex", "gap": "1rem", "flexWrap": "wrap", "marginBottom": "1.5rem"},
            )
            return html.Div([
                cards,
                dcc.Graph(figure=figures.revision_distribution_pie(filtered)),
                dcc.Graph(figure=figures.revision_timeline(filtered)),
            ])

        elif tab == "revisions":
            return html.Div([
                dcc.Graph(figure=figures.revision_magnitude_scatter(
                    filtered, metric_type=selected_metric or "revenue",
                    window_days=selected_window or 1,
                )),
                dcc.Graph(figure=figures.stock_reaction_by_window(filtered)),
            ])

        elif tab == "reactions":
            return html.Div([
                dcc.Graph(figure=figures.stock_reaction_by_window(
                    filtered,
                    metric_type=selected_metric,
                    revision_type=selected_revision if selected_revision != "all" else None,
                )),
            ])

        elif tab == "sectors":
            return html.Div([
                dcc.Graph(figure=figures.abnormal_return_by_sector(
                    filtered, window_days=selected_window or 1,
                )),
                dcc.Graph(figure=figures.sector_heatmap(
                    filtered, window_days=selected_window or 1,
                )),
            ])

        elif tab == "data":
            from dash import dash_table
            display_cols = [
                "ticker", "sector", "announcement_date", "metric_type",
                "revision_type", "pct_change", "abnormal_return", "window_days",
            ]
            table_df = filtered[display_cols].drop_duplicates().round(4)
            return dash_table.DataTable(
                data=table_df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in display_cols],
                page_size=25,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"backgroundColor": BG_CARD, "color": TEXT_PRIMARY, "border": "1px solid #334155"},
                style_header={"backgroundColor": "#0f172a", "fontWeight": "bold", "color": TEXT_PRIMARY},
            )

        return html.Div("Unknown tab")
