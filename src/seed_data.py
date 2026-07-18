"""Seed the database with realistic synthetic guidance revision data."""

import logging
import random
from datetime import date, timedelta
from decimal import Decimal

from src.db import get_session, engine
from src.models import Base, Company, GuidanceEvent, GuidanceMetric, BenchmarkHistory, PriceHistory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

random.seed(42)

COMPANIES = [
    ("AAPL", "Apple Inc.", "Technology", "NASDAQ", 3_000_000_000_000),
    ("MSFT", "Microsoft Corp.", "Technology", "NASDAQ", 2_800_000_000_000),
    ("GOOGL", "Alphabet Inc.", "Technology", "NASDAQ", 1_800_000_000_000),
    ("AMZN", "Amazon.com Inc.", "Consumer Discretionary", "NASDAQ", 1_600_000_000_000),
    ("META", "Meta Platforms Inc.", "Technology", "NASDAQ", 1_200_000_000_000),
    ("NVDA", "NVIDIA Corp.", "Technology", "NASDAQ", 1_100_000_000_000),
    ("JPM", "JPMorgan Chase", "Financials", "NYSE", 500_000_000_000),
    ("JNJ", "Johnson & Johnson", "Healthcare", "NYSE", 450_000_000_000),
    ("PG", "Procter & Gamble", "Consumer Staples", "NYSE", 360_000_000_000),
    ("XOM", "Exxon Mobil Corp.", "Energy", "NYSE", 450_000_000_000),
    ("V", "Visa Inc.", "Financials", "NYSE", 510_000_000_000),
    ("HD", "Home Depot Inc.", "Consumer Discretionary", "NYSE", 320_000_000_000),
    ("MRK", "Merck & Co.", "Healthcare", "NYSE", 280_000_000_000),
    ("CVX", "Chevron Corp.", "Energy", "NYSE", 300_000_000_000),
    ("PEP", "PepsiCo Inc.", "Consumer Staples", "NASDAQ", 240_000_000_000),
    ("ABBV", "AbbVie Inc.", "Healthcare", "NYSE", 270_000_000_000),
    ("BAC", "Bank of America", "Financials", "NYSE", 280_000_000_000),
    ("COST", "Costco Wholesale", "Consumer Staples", "NASDAQ", 230_000_000_000),
    ("LLY", "Eli Lilly and Co.", "Healthcare", "NYSE", 700_000_000_000),
    ("WMT", "Walmart Inc.", "Consumer Staples", "NYSE", 430_000_000_000),
]

METRIC_TYPES = ["revenue", "eps", "operating_margin"]
SOURCE_TYPES = ["earnings_call", "press_release", "8-K", "investor_day"]
REVISION_TYPES = ["raised", "lowered", "reaffirmed", "initiated"]


def generate_event_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def seed_companies(session) -> list:
    companies = []
    for ticker, name, sector, exchange, cap in COMPANIES:
        co = Company(
            ticker=ticker,
            name=name,
            sector=sector,
            exchange=exchange,
            market_cap_usd=Decimal(str(cap)),
        )
        session.add(co)
        companies.append(co)
    session.flush()
    logger.info("Seeded %d companies", len(companies))
    return companies


def seed_price_history(session, companies: list) -> None:
    start_date = date(2022, 1, 3)
    end_date = date(2024, 12, 31)
    d = start_date
    while d <= end_date:
        if d.weekday() < 5:  # weekdays only
            for co in companies:
                base = float(random.randint(50, 500))
                price = Decimal(str(round(base * (1 + random.gauss(0, 0.01)), 4)))
                session.add(PriceHistory(
                    company_id=co.id,
                    trade_date=d,
                    open=price * Decimal("0.99"),
                    high=price * Decimal("1.01"),
                    low=price * Decimal("0.98"),
                    close=price,
                    adj_close=price,
                    volume=random.randint(1_000_000, 100_000_000),
                ))
        d += timedelta(days=1)
    logger.info("Seeded price history")


def seed_benchmark_history(session) -> None:
    start_date = date(2022, 1, 3)
    end_date = date(2024, 12, 31)
    d = start_date
    spy_close = Decimal("450.00")
    while d <= end_date:
        if d.weekday() < 5:
            daily_ret = Decimal(str(round(random.gauss(0.0003, 0.01), 6)))
            spy_close *= (1 + daily_ret)
            session.add(BenchmarkHistory(
                index_name="SPY",
                trade_date=d,
                close=round(spy_close, 4),
                daily_return=daily_ret,
            ))
        d += timedelta(days=1)
    logger.info("Seeded benchmark history")


def seed_guidance_events(session, companies: list) -> None:
    start_date = date(2022, 1, 1)
    end_date = date(2024, 12, 31)
    event_count = 0

    for co in companies:
        n_events = random.randint(8, 14)  # 8-14 events per company
        for _ in range(n_events):
            ev_date = generate_event_date(start_date, end_date)
            fiscal_q = random.choice([1, 2, 3, 4])
            event = GuidanceEvent(
                company_id=co.id,
                announcement_date=ev_date,
                fiscal_year=ev_date.year,
                fiscal_quarter=fiscal_q,
                source_type=random.choice(SOURCE_TYPES),
            )
            session.add(event)
            session.flush()

            n_metrics = random.randint(1, 3)
            sampled = random.sample(METRIC_TYPES, n_metrics)
            for mtype in sampled:
                prior = Decimal(str(round(random.uniform(1.0, 50.0), 4)))
                direction = random.choices(
                    ["raised", "lowered", "reaffirmed"], weights=[0.45, 0.35, 0.20]
                )[0]
                if direction == "raised":
                    new = prior * Decimal(str(round(random.uniform(1.01, 1.15), 4)))
                elif direction == "lowered":
                    new = prior * Decimal(str(round(random.uniform(0.85, 0.99), 4)))
                else:
                    new = prior * Decimal(str(round(random.uniform(0.998, 1.002), 4)))

                pct = ((new - prior) / abs(prior)) * 100
                metric = GuidanceMetric(
                    event_id=event.id,
                    metric_type=mtype,
                    prior_value=prior,
                    new_value=new,
                    revision_type=direction,
                    pct_change=round(pct, 4),
                    abs_change=round(new - prior, 4),
                    unit="billions" if mtype == "revenue" else ("dollars" if mtype == "eps" else "percent"),
                )
                session.add(metric)
            event_count += 1

    logger.info("Seeded %d guidance events", event_count)


def run_seed() -> None:
    """Create all tables and populate with synthetic data."""
    Base.metadata.create_all(engine)
    logger.info("Tables created")

    with get_session() as session:
        companies = seed_companies(session)
        seed_price_history(session, companies)
        seed_benchmark_history(session)
        seed_guidance_events(session, companies)

    logger.info("Seeding complete")


if __name__ == "__main__":
    run_seed()
