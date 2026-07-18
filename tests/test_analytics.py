"""Tests for the analytics module."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

from src.analytics import (
    get_revision_summary,
    get_sector_reaction,
    get_reaction_by_magnitude,
    validate_analytics,
)


def make_sample_df(n_events=20, n_companies=5):
    """Generate a minimal sample DataFrame that mirrors the analytics query output."""
    rng = np.random.default_rng(42)
    tickers = [f"T{i}" for i in range(n_companies)]
    sectors = ["Technology", "Healthcare", "Financials", "Energy", "Consumer Staples"]
    revision_types = ["raised", "lowered", "reaffirmed"]
    metric_types = ["revenue", "eps", "operating_margin"]

    rows = []
    for i in range(n_events):
        for window in [0, 1, 3, 5, 20]:
            rows.append({
                "event_id": i,
                "metric_id": i * 3 + (i % 3),
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


SAMPLE_DF = make_sample_df()


class TestGetRevisionSummary:
    def test_returns_dict(self):
        result = get_revision_summary(SAMPLE_DF)
        assert isinstance(result, dict)

    def test_total_events(self):
        result = get_revision_summary(SAMPLE_DF)
        assert result["total_events"] == SAMPLE_DF["event_id"].nunique()

    def test_total_companies(self):
        result = get_revision_summary(SAMPLE_DF)
        assert result["total_companies"] == SAMPLE_DF["ticker"].nunique()

    def test_date_range_is_tuple(self):
        result = get_revision_summary(SAMPLE_DF)
        assert isinstance(result["date_range"], tuple)
        assert len(result["date_range"]) == 2

    def test_revision_distribution_keys(self):
        result = get_revision_summary(SAMPLE_DF)
        assert isinstance(result["revision_distribution"], dict)
        assert len(result["revision_distribution"]) > 0

    def test_total_metrics(self):
        result = get_revision_summary(SAMPLE_DF)
        assert result["total_metrics"] > 0


class TestGetSectorReaction:
    def test_returns_dataframe(self):
        result = get_sector_reaction(SAMPLE_DF)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self):
        result = get_sector_reaction(SAMPLE_DF)
        assert "sector" in result.columns
        assert "avg_abnormal" in result.columns
        assert "n" in result.columns

    def test_sorted_descending(self):
        result = get_sector_reaction(SAMPLE_DF)
        assert result["avg_abnormal"].is_monotonic_decreasing or len(result) <= 1

    def test_filters_by_window(self):
        for w in [0, 1, 3, 5, 20]:
            result = get_sector_reaction(SAMPLE_DF, window_days=w)
            assert len(result) > 0

    def test_not_empty(self):
        result = get_sector_reaction(SAMPLE_DF)
        assert not result.empty


class TestGetReactionByMagnitude:
    def test_returns_dataframe(self):
        result = get_reaction_by_magnitude(SAMPLE_DF)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self):
        result = get_reaction_by_magnitude(SAMPLE_DF)
        assert "avg_abnormal" in result.columns
        assert "n" in result.columns

    def test_filters_by_metric_type(self):
        for mt in ["revenue", "eps", "operating_margin"]:
            result = get_reaction_by_magnitude(SAMPLE_DF, metric_type=mt)
            assert isinstance(result, pd.DataFrame)

    def test_custom_bins(self):
        result = get_reaction_by_magnitude(SAMPLE_DF, bins=3)
        assert len(result) <= 3


class TestValidateAnalytics:
    def test_passes_on_valid_data(self):
        assert validate_analytics(SAMPLE_DF) is True

    def test_raises_on_empty_df(self):
        with pytest.raises(AssertionError):
            validate_analytics(pd.DataFrame())

    def test_raises_on_invalid_metric_type(self):
        bad_df = SAMPLE_DF.copy()
        bad_df.loc[0, "metric_type"] = "invalid_type"
        with pytest.raises(AssertionError):
            validate_analytics(bad_df)
