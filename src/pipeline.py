"""ETL pipeline for ingesting and processing guidance revision events."""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.db import get_session
from src.models import (
    Company, GuidanceEvent, GuidanceMetric, EventWindow, BenchmarkHistory, PriceHistory
)

logger = logging.getLogger(__name__)

EVENT_WINDOWS = [0, 1, 3, 5, 20]


def compute_revision_type(prior: Optional[Decimal], new: Optional[Decimal]) -> Optional[str]:
    """Determine if a guidance revision is raised, lowered, or reaffirmed."""
    if prior is None or new is None:
        return None
    if new > prior * Decimal("1.005"):
        return "raised"
    elif new < prior * Decimal("0.995"):
        return "lowered"
    else:
        return "reaffirmed"


def compute_pct_change(prior: Optional[Decimal], new: Optional[Decimal]) -> Optional[Decimal]:
    """Compute percentage change from prior to new value."""
    if prior is None or new is None or prior == 0:
        return None
    return ((new - prior) / abs(prior)) * 100


def get_price_return(
    session: Session,
    company_id: int,
    event_date: date,
    window_days: int,
) -> Optional[Decimal]:
    """Get cumulative stock return from event_date over window_days."""
    start = session.query(PriceHistory).filter(
        PriceHistory.company_id == company_id,
        PriceHistory.trade_date >= event_date,
    ).order_by(PriceHistory.trade_date).first()

    if start is None:
        return None

    end_date = event_date + timedelta(days=window_days + 14)  # buffer for non-trading days
    prices = session.query(PriceHistory).filter(
        PriceHistory.company_id == company_id,
        PriceHistory.trade_date >= start.trade_date,
        PriceHistory.trade_date <= end_date,
    ).order_by(PriceHistory.trade_date).all()

    if len(prices) <= window_days:
        return None

    start_price = prices[0].close
    end_price = prices[min(window_days, len(prices) - 1)].close

    if start_price == 0:
        return None

    return ((end_price - start_price) / start_price) * 100


def get_benchmark_return(
    session: Session,
    event_date: date,
    window_days: int,
    index_name: str = "SPY",
) -> Optional[Decimal]:
    """Get benchmark index return over same window."""
    benchmarks = session.query(BenchmarkHistory).filter(
        BenchmarkHistory.index_name == index_name,
        BenchmarkHistory.trade_date >= event_date,
    ).order_by(BenchmarkHistory.trade_date).limit(window_days + 5).all()

    if len(benchmarks) <= window_days:
        return None

    start_close = benchmarks[0].close
    end_close = benchmarks[min(window_days, len(benchmarks) - 1)].close

    if start_close == 0:
        return None

    return ((end_close - start_close) / start_close) * 100


def process_metric(session: Session, metric: GuidanceMetric) -> int:
    """Compute and store event window data for a single metric. Returns window count."""
    event = metric.event
    company_id = event.company_id
    event_date = event.announcement_date

    # Compute revision metadata
    if metric.prior_value is None and metric.prior_high is not None and metric.prior_low is not None:
        metric.prior_value = (metric.prior_high + metric.prior_low) / 2
    if metric.new_value is None and metric.new_high is not None and metric.new_low is not None:
        metric.new_value = (metric.new_high + metric.new_low) / 2

    if metric.revision_type is None:
        metric.revision_type = compute_revision_type(metric.prior_value, metric.new_value)
    if metric.pct_change is None:
        metric.pct_change = compute_pct_change(metric.prior_value, metric.new_value)
    if metric.abs_change is None and metric.prior_value is not None and metric.new_value is not None:
        metric.abs_change = metric.new_value - metric.prior_value

    window_count = 0
    for days in EVENT_WINDOWS:
        stock_ret = get_price_return(session, company_id, event_date, days)
        bench_ret = get_benchmark_return(session, event_date, days)

        abnormal = None
        if stock_ret is not None and bench_ret is not None:
            abnormal = stock_ret - bench_ret

        window = EventWindow(
            metric_id=metric.id,
            window_days=days,
            stock_return=stock_ret,
            benchmark_return=bench_ret,
            abnormal_return=abnormal,
            is_positive_revision=(
                metric.revision_type in ("raised", "initiated")
                if metric.revision_type else None
            ),
        )
        session.add(window)
        window_count += 1

    return window_count


def run_pipeline() -> dict:
    """Run the full ETL pipeline. Returns a summary dict."""
    summary = {"events": 0, "metrics": 0, "windows": 0, "skipped": 0}

    with get_session() as session:
        events = session.query(GuidanceEvent).all()
        summary["events"] = len(events)

        for event in events:
            for metric in event.metrics:
                try:
                    wc = process_metric(session, metric)
                    summary["metrics"] += 1
                    summary["windows"] += wc
                except Exception as exc:
                    logger.warning("Skipping metric %s: %s", metric.id, exc)
                    summary["skipped"] += 1

    logger.info(
        "Pipeline complete: %d events, %d metrics, %d windows, %d skipped",
        summary["events"],
        summary["metrics"],
        summary["windows"],
        summary["skipped"],
    )
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_pipeline()
    print(result)
