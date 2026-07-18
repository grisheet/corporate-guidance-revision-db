"""Tests for the ETL pipeline module."""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.pipeline import (
    compute_revision_type,
    compute_pct_change,
    get_price_return,
    get_benchmark_return,
    process_metric,
    run_pipeline,
    EVENT_WINDOWS,
)


class TestComputeRevisionType:
    def test_raised(self):
        assert compute_revision_type(Decimal("10"), Decimal("11")) == "raised"

    def test_lowered(self):
        assert compute_revision_type(Decimal("10"), Decimal("9")) == "lowered"

    def test_reaffirmed_exact(self):
        assert compute_revision_type(Decimal("10"), Decimal("10")) == "reaffirmed"

    def test_reaffirmed_within_band(self):
        assert compute_revision_type(Decimal("10"), Decimal("10.003")) == "reaffirmed"

    def test_none_prior(self):
        assert compute_revision_type(None, Decimal("10")) is None

    def test_none_new(self):
        assert compute_revision_type(Decimal("10"), None) is None

    def test_both_none(self):
        assert compute_revision_type(None, None) is None

    def test_large_raise(self):
        assert compute_revision_type(Decimal("100"), Decimal("150")) == "raised"

    def test_large_lower(self):
        assert compute_revision_type(Decimal("100"), Decimal("50")) == "lowered"

    def test_boundary_raise_just_above(self):
        assert compute_revision_type(Decimal("100"), Decimal("100.6")) == "raised"

    def test_boundary_lower_just_below(self):
        assert compute_revision_type(Decimal("100"), Decimal("99.4")) == "lowered"


class TestComputePctChange:
    def test_positive(self):
        result = compute_pct_change(Decimal("100"), Decimal("110"))
        assert result == pytest.approx(Decimal("10.0"), rel=1e-4)

    def test_negative(self):
        result = compute_pct_change(Decimal("100"), Decimal("90"))
        assert result == pytest.approx(Decimal("-10.0"), rel=1e-4)

    def test_zero_prior(self):
        assert compute_pct_change(Decimal("0"), Decimal("10")) is None

    def test_none_values(self):
        assert compute_pct_change(None, Decimal("10")) is None
        assert compute_pct_change(Decimal("10"), None) is None

    def test_no_change(self):
        result = compute_pct_change(Decimal("50"), Decimal("50"))
        assert result == Decimal("0")

    def test_negative_prior(self):
        result = compute_pct_change(Decimal("-10"), Decimal("-5"))
        assert result is not None


class TestGetPriceReturn:
    def _make_price(self, close_val):
        ph = MagicMock()
        ph.close = Decimal(str(close_val))
        return ph

    def test_returns_none_when_no_prices(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = get_price_return(session, 1, __import__('datetime').date(2023, 1, 1), 1)
        assert result is None

    def test_returns_correct_return(self):
        from datetime import date
        session = MagicMock()
        start_price = self._make_price(100)
        start_price.trade_date = date(2023, 1, 2)
        end_price = self._make_price(110)
        end_price.trade_date = date(2023, 1, 3)

        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = start_price
        session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
            start_price, end_price
        ]
        result = get_price_return(session, 1, date(2023, 1, 2), 1)
        assert result == Decimal("10")

    def test_insufficient_prices(self):
        from datetime import date
        session = MagicMock()
        start_price = self._make_price(100)
        start_price.trade_date = date(2023, 1, 2)

        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = start_price
        session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
            start_price
        ]
        result = get_price_return(session, 1, date(2023, 1, 2), 5)
        assert result is None

    def test_zero_start_price(self):
        from datetime import date
        session = MagicMock()
        start = self._make_price(0)
        start.trade_date = date(2023, 1, 2)
        end = self._make_price(10)
        end.trade_date = date(2023, 1, 3)

        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = start
        session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
            start, end
        ]
        result = get_price_return(session, 1, date(2023, 1, 2), 1)
        assert result is None


class TestGetBenchmarkReturn:
    def _make_bench(self, close_val, trade_date):
        bh = MagicMock()
        bh.close = Decimal(str(close_val))
        bh.trade_date = trade_date
        return bh

    def test_returns_none_when_insufficient_data(self):
        from datetime import date
        session = MagicMock()
        session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = get_benchmark_return(session, date(2023, 1, 1), 5)
        assert result is None

    def test_returns_correct_value(self):
        from datetime import date
        session = MagicMock()
        benchmarks = [
            self._make_bench(400, date(2023, 1, 2)),
            self._make_bench(420, date(2023, 1, 3)),
        ]
        session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = benchmarks
        result = get_benchmark_return(session, date(2023, 1, 2), 1)
        assert result == Decimal("5")


class TestEventWindows:
    def test_correct_windows_defined(self):
        assert EVENT_WINDOWS == [0, 1, 3, 5, 20]

    def test_five_windows(self):
        assert len(EVENT_WINDOWS) == 5
