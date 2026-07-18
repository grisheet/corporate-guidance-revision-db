"""SQLAlchemy ORM models for the guidance revision database."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, Numeric, Date, DateTime, Boolean, Integer,
    ForeignKey, Text, Enum as SAEnum, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    exchange: Mapped[Optional[str]] = mapped_column(String(20))
    market_cap_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    events: Mapped[list["GuidanceEvent"]] = relationship(back_populates="company")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="company")


class GuidanceEvent(Base):
    __tablename__ = "guidance_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    announcement_date: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_year: Mapped[Optional[int]] = mapped_column(Integer)
    fiscal_quarter: Mapped[Optional[int]] = mapped_column(Integer)
    source_type: Mapped[Optional[str]] = mapped_column(
        SAEnum("earnings_call", "press_release", "8-K", "investor_day", "other", name="source_type_enum")
    )
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    filing_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    company: Mapped[Company] = relationship(back_populates="events")
    metrics: Mapped[list["GuidanceMetric"]] = relationship(back_populates="event")
    source_documents: Mapped[list["SourceDocument"]] = relationship(back_populates="event")


class GuidanceMetric(Base):
    __tablename__ = "guidance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("guidance_events.id"), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(
        SAEnum("revenue", "eps", "operating_margin", name="metric_type_enum"), nullable=False
    )
    prior_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4))
    new_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4))
    prior_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4))
    prior_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4))
    new_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4))
    new_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4))
    revision_type: Mapped[Optional[str]] = mapped_column(
        SAEnum("raised", "lowered", "reaffirmed", "initiated", "withdrawn", name="revision_type_enum")
    )
    pct_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    abs_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4))
    unit: Mapped[Optional[str]] = mapped_column(String(20))  # millions, billions, percent

    event: Mapped[GuidanceEvent] = relationship(back_populates="metrics")
    window_data: Mapped[list["EventWindow"]] = relationship(back_populates="metric")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("guidance_events.id"), nullable=False)
    doc_type: Mapped[Optional[str]] = mapped_column(String(50))
    url: Mapped[Optional[str]] = mapped_column(Text)
    retrieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    event: Mapped[GuidanceEvent] = relationship(back_populates="source_documents")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    high: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    low: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    close: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[Optional[int]] = mapped_column(Integer)
    adj_close: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))

    company: Mapped[Company] = relationship(back_populates="price_history")


class BenchmarkHistory(Base):
    __tablename__ = "benchmark_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    index_name: Mapped[str] = mapped_column(String(20), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    daily_return: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))


class EventWindow(Base):
    __tablename__ = "event_windows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("guidance_metrics.id"), nullable=False, index=True)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 0, 1, 3, 5, 20
    stock_return: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    benchmark_return: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    abnormal_return: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    volatility: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    is_positive_revision: Mapped[Optional[bool]] = mapped_column(Boolean)

    metric: Mapped[GuidanceMetric] = relationship(back_populates="window_data")
