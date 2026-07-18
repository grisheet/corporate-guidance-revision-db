"""Tests for the dashboard figures and theme modules."""

import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.dashboard import theme, figures


def make_sample_df(n_events=20, n_companies=5):
    """Generate test data matching the analytics output schema."""
    rng = np.random.default_rng(99)
    tickers = [f"T{i}" for i in range(n_companies)]
    sectors = ["Technology", "Healthcare", "Financials", "Energy", "Consumer Staples"]
    revision_types = ["raised", "lowered", "reaffirmed"]
    metric_types = ["revenue", "eps", "operating_margin"]

    rows = []
    for i in range(n_events):
        for window in [0, 1, 3, 5, 20]:
            rows.append({
                "event_id": i,
                "metric_id": i,
                "ticker": tickers[i % n_companies],
                "sector": sectors[i % len(sectors)],
                "announcement_date": pd.Timestamp("2023-01-01") + pd.Timedelta(days=i * 10),
                "metric_type": metric_types[i % len(metric_types)],
                "revision_type": revision_types[i % len(revision_types)],
                "pct_change": float(rng.uniform(-10, 10)),
                "abs_change": float(rng.uniform(-5, 5)),
                "window_days": window,
                "stock_return": float(rng.normal(0, 2)),
                "benchmark_return": float(rng.normal(0, 1)),
                "abnormal_return": float(rng.normal(0, 1.5)),
                "is_positive_revision": bool(i % 2),
                "market_cap_usd": float(rng.uniform(1e9, 1e12)),
            })
    return pd.DataFrame(rows)


DF = make_sample_df()


class TestTheme:
    def test_base_layout_returns_dict(self):
        layout = theme.base_layout()
        assert isinstance(layout, dict)

    def test_base_layout_has_required_keys(self):
        layout = theme.base_layout(title="Test")
        assert "paper_bgcolor" in layout
        assert "plot_bgcolor" in layout
        assert "font" in layout

    def test_revision_color_map_has_all_types(self):
        for rtype in ["raised", "lowered", "reaffirmed", "initiated", "withdrawn"]:
            assert rtype in theme.REVISION_COLOR_MAP

    def test_color_values_are_hex(self):
        for key, val in theme.REVISION_COLOR_MAP.items():
            assert val.startswith("#"), f"{key} color {val} is not a hex color"

    def test_sector_colors_list(self):
        assert isinstance(theme.SECTOR_COLORS, list)
        assert len(theme.SECTOR_COLORS) > 0

    def test_base_layout_custom_height(self):
        layout = theme.base_layout(height=600)
        assert layout["height"] == 600

    def test_base_layout_title(self):
        layout = theme.base_layout(title="My Chart")
        assert layout["title"]["text"] == "My Chart"


class TestFigures:
    def test_revision_distribution_pie_returns_figure(self):
        fig = figures.revision_distribution_pie(DF)
        assert isinstance(fig, go.Figure)

    def test_revision_distribution_pie_has_data(self):
        fig = figures.revision_distribution_pie(DF)
        assert len(fig.data) > 0

    def test_abnormal_return_by_sector_returns_figure(self):
        fig = figures.abnormal_return_by_sector(DF)
        assert isinstance(fig, go.Figure)

    def test_abnormal_return_by_sector_respects_window(self):
        for w in [0, 1, 3, 5, 20]:
            fig = figures.abnormal_return_by_sector(DF, window_days=w)
            assert isinstance(fig, go.Figure)

    def test_stock_reaction_by_window_returns_figure(self):
        fig = figures.stock_reaction_by_window(DF)
        assert isinstance(fig, go.Figure)

    def test_stock_reaction_by_window_filters_metric_type(self):
        fig = figures.stock_reaction_by_window(DF, metric_type="revenue")
        assert isinstance(fig, go.Figure)

    def test_stock_reaction_by_window_filters_revision_type(self):
        fig = figures.stock_reaction_by_window(DF, revision_type="raised")
        assert isinstance(fig, go.Figure)

    def test_revision_magnitude_scatter_returns_figure(self):
        fig = figures.revision_magnitude_scatter(DF)
        assert isinstance(fig, go.Figure)

    def test_revision_magnitude_scatter_different_metrics(self):
        for mt in ["revenue", "eps", "operating_margin"]:
            fig = figures.revision_magnitude_scatter(DF, metric_type=mt)
            assert isinstance(fig, go.Figure)

    def test_revision_timeline_returns_figure(self):
        fig = figures.revision_timeline(DF)
        assert isinstance(fig, go.Figure)

    def test_revision_timeline_has_traces(self):
        fig = figures.revision_timeline(DF)
        assert len(fig.data) >= 1

    def test_sector_heatmap_returns_figure(self):
        fig = figures.sector_heatmap(DF)
        assert isinstance(fig, go.Figure)

    def test_sector_heatmap_different_windows(self):
        for w in [1, 5, 20]:
            fig = figures.sector_heatmap(DF, window_days=w)
            assert isinstance(fig, go.Figure)

    def test_kpi_cards_returns_list(self):
        cards = figures.kpi_cards(DF)
        assert isinstance(cards, list)
        assert len(cards) == 4

    def test_kpi_cards_have_required_keys(self):
        cards = figures.kpi_cards(DF)
        for card in cards:
            assert "label" in card
            assert "value" in card

    def test_kpi_cards_total_events(self):
        cards = figures.kpi_cards(DF)
        events_card = next(c for c in cards if c["label"] == "Total Events")
        expected = str(DF["event_id"].nunique())
        assert expected in events_card["value"]
