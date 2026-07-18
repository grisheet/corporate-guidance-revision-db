"""Analytics queries and aggregation logic for guidance revisions."""

import pandas as pd
from sqlalchemy import text

from src.db import engine


DEFAULT_WINDOWS = [0, 1, 3, 5, 20]


def load_full_dataset() -> pd.DataFrame:
    """Load all guidance events with metrics and window data into a DataFrame."""
    query = text("""
        SELECT
            c.ticker,
            c.name AS company_name,
            c.sector,
            c.exchange,
            c.market_cap_usd,
            ge.id AS event_id,
            ge.announcement_date,
            ge.fiscal_year,
            ge.fiscal_quarter,
            ge.source_type,
            gm.id AS metric_id,
            gm.metric_type,
            gm.prior_value,
            gm.new_value,
            gm.revision_type,
            gm.pct_change,
            gm.abs_change,
            gm.unit,
            ew.window_days,
            ew.stock_return,
            ew.benchmark_return,
            ew.abnormal_return,
            ew.is_positive_revision
        FROM companies c
        JOIN guidance_events ge ON ge.company_id = c.id
        JOIN guidance_metrics gm ON gm.event_id = ge.id
        LEFT JOIN event_windows ew ON ew.metric_id = gm.id
        ORDER BY ge.announcement_date DESC, c.ticker
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    return df


def get_revision_summary(df: pd.DataFrame) -> dict:
    """Return high-level summary stats for a dataset."""
    return {
        "total_events": df["event_id"].nunique(),
        "total_metrics": df["metric_id"].nunique(),
        "total_companies": df["ticker"].nunique(),
        "date_range": (
            str(df["announcement_date"].min()),
            str(df["announcement_date"].max()),
        ),
        "revision_distribution": (
            df.drop_duplicates("metric_id")["revision_type"]
            .value_counts()
            .to_dict()
        ),
    }


def get_sector_reaction(df: pd.DataFrame, window_days: int = 1) -> pd.DataFrame:
    """Average abnormal return by sector for a given event window."""
    filtered = df[df["window_days"] == window_days].copy()
    return (
        filtered.groupby("sector")["abnormal_return"]
        .agg(["mean", "median", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "avg_abnormal", "count": "n"})
        .sort_values("avg_abnormal", ascending=False)
    )


def get_reaction_by_magnitude(
    df: pd.DataFrame,
    metric_type: str = "revenue",
    window_days: int = 1,
    bins: int = 5,
) -> pd.DataFrame:
    """Bucket revisions by pct_change magnitude and compute avg stock reaction."""
    filtered = df[
        (df["metric_type"] == metric_type)
        & (df["window_days"] == window_days)
        & df["pct_change"].notna()
    ].copy()

    filtered["magnitude_bucket"] = pd.cut(
        filtered["pct_change"].astype(float), bins=bins, precision=1
    )
    return (
        filtered.groupby("magnitude_bucket", observed=True)["abnormal_return"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "avg_abnormal", "count": "n"})
    )


def get_market_cap_tiers(df: pd.DataFrame) -> pd.DataFrame:
    """Assign market cap tiers and return average reaction by tier."""
    filtered = df[df["window_days"] == 1].copy()
    filtered["market_cap_usd"] = filtered["market_cap_usd"].astype(float)

    conditions = [
        filtered["market_cap_usd"] < 2e9,
        filtered["market_cap_usd"].between(2e9, 10e9),
        filtered["market_cap_usd"].between(10e9, 200e9),
        filtered["market_cap_usd"] > 200e9,
    ]
    choices = ["Small-cap (<$2B)", "Mid-cap ($2-10B)", "Large-cap ($10-200B)", "Mega-cap (>$200B)"]
    filtered["cap_tier"] = pd.Series(
        pd.Categorical(
            [choices[next((i for i, c in enumerate(conditions) if c.iloc[j]), 0)]
             for j in range(len(filtered))],
            categories=choices,
            ordered=True,
        )
    ) if not filtered.empty else None

    return (
        filtered.groupby("cap_tier", observed=True)["abnormal_return"]
        .agg(["mean", "count"])
        .reset_index()
    )


def validate_analytics(df: pd.DataFrame) -> bool:
    """Sanity-check the analytics output."""
    assert not df.empty, "Dataset is empty"
    assert df["event_id"].nunique() > 0, "No events found"
    assert df["metric_type"].isin(["revenue", "eps", "operating_margin"]).all(), "Unknown metric types"
    print(f"Validation passed: {df['event_id'].nunique()} events, {df['metric_id'].nunique()} metrics")
    return True
