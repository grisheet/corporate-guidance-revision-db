# Corporate Guidance Revision Database

A production-quality analytics platform for tracking and analyzing corporate financial guidance updates. The system tracks every company guidance revision focused on revenue, EPS, and operating margins, normalizes the revisions, stores them in PostgreSQL, and analyzes how stocks historically reacted to those changes across multiple event windows.

## Features

- **End-to-end ETL Pipeline**: Ingests 217+ guidance events, calculates 415+ metrics, generates 1085+ analytical window rows
- **PostgreSQL Database**: Full relational schema with 6 core tables, managed by Alembic migrations
- **Interactive Dashboard**: Plotly/Dash web app with filters, tabs, and real-time callbacks
- **Event Study Analysis**: 0, 1, 3, 5, and 20-day stock reaction windows
- **58 Automated Tests**: Comprehensive test suite covering pipeline, analytics, and dashboard
- **Docker Support**: Containerized deployment ready

## Project Structure

```
corporate-guidance-revision-db/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── src/
│   ├── __init__.py
│   ├── db.py
│   ├── models.py
│   ├── pipeline.py
│   ├── analytics.py
│   ├── seed_data.py
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py
│       ├── theme.py
│       ├── figures.py
│       └── callbacks.py
└── tests/
    ├── __init__.py
    ├── test_pipeline.py
    ├── test_analytics.py
    └── test_dashboard.py
```

## Data Model

| Table | Description |
|-------|-------------|
| `companies` | Ticker, name, sector, exchange, market cap |
| `guidance_events` | Announcement date, fiscal period, source type/URL |
| `guidance_metrics` | Prior vs. new guidance for revenue, EPS, margin |
| `source_documents` | Filing references and press release metadata |
| `price_history` | Daily OHLCV data per company |
| `benchmark_history` | Market index data for abnormal return calculations |

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16
- Docker & Docker Compose (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/grisheet/corporate-guidance-revision-db.git
cd corporate-guidance-revision-db

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Run database migrations
alembic upgrade head

# Seed with sample data
python -m src.seed_data

# Run the pipeline
python -m src.pipeline

# Launch the dashboard
python -m src.dashboard.app
```

### Docker Setup

```bash
docker-compose up --build
```

The dashboard will be available at http://localhost:8050

## Dashboard

The interactive dashboard answers:

- What changed in company guidance?
- Was the revision upward, downward, or reaffirmed?
- How large was the change in percentage and absolute terms?
- How did the stock react on day 0, 1, 5, and 20?
- How do reactions differ by sector, market cap, metric type, and revision magnitude?

### Dashboard Tabs

1. **Overview** - Summary statistics and revision distribution
2. **Revision Analysis** - Magnitude and direction of guidance changes
3. **Stock Reactions** - Price responses by event window
4. **Sector Comparison** - Cross-sector analysis
5. **Raw Data** - Filterable data table

## Running Tests

```bash
pytest tests/ -v
# 58 tests, all passing
```

## Tech Stack

- **Python 3.11** - ETL, analytics, and application logic
- **PostgreSQL 16** - Primary database
- **SQLAlchemy** - ORM and query building
- **Alembic** - Database migrations
- **Plotly / Dash** - Interactive visualization and web dashboard
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computations
- **Docker** - Containerization
- **pytest** - Test framework

## License

MIT
