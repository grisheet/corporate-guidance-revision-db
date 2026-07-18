"""Initial database schema for the corporate guidance revision database.

Revision ID: 001
Create Date: 2024-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    source_type_enum = sa.Enum(
        'earnings_call', 'press_release', '8-K', 'investor_day', 'other',
        name='source_type_enum'
    )
    metric_type_enum = sa.Enum(
        'revenue', 'eps', 'operating_margin',
        name='metric_type_enum'
    )
    revision_type_enum = sa.Enum(
        'raised', 'lowered', 'reaffirmed', 'initiated', 'withdrawn',
        name='revision_type_enum'
    )

    # companies
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticker', sa.String(10), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('sector', sa.String(100)),
        sa.Column('exchange', sa.String(20)),
        sa.Column('market_cap_usd', sa.Numeric(20, 2)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_companies_ticker', 'companies', ['ticker'])

    # guidance_events
    op.create_table(
        'guidance_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('announcement_date', sa.Date(), nullable=False),
        sa.Column('fiscal_year', sa.Integer()),
        sa.Column('fiscal_quarter', sa.Integer()),
        sa.Column('source_type', source_type_enum),
        sa.Column('source_url', sa.Text()),
        sa.Column('filing_timestamp', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_guidance_events_company_id', 'guidance_events', ['company_id'])

    # guidance_metrics
    op.create_table(
        'guidance_metrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('guidance_events.id'), nullable=False),
        sa.Column('metric_type', metric_type_enum, nullable=False),
        sa.Column('prior_value', sa.Numeric(20, 4)),
        sa.Column('new_value', sa.Numeric(20, 4)),
        sa.Column('prior_low', sa.Numeric(20, 4)),
        sa.Column('prior_high', sa.Numeric(20, 4)),
        sa.Column('new_low', sa.Numeric(20, 4)),
        sa.Column('new_high', sa.Numeric(20, 4)),
        sa.Column('revision_type', revision_type_enum),
        sa.Column('pct_change', sa.Numeric(10, 4)),
        sa.Column('abs_change', sa.Numeric(20, 4)),
        sa.Column('unit', sa.String(20)),
    )
    op.create_index('ix_guidance_metrics_event_id', 'guidance_metrics', ['event_id'])

    # source_documents
    op.create_table(
        'source_documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('guidance_events.id'), nullable=False),
        sa.Column('doc_type', sa.String(50)),
        sa.Column('url', sa.Text()),
        sa.Column('retrieved_at', sa.DateTime()),
    )

    # price_history
    op.create_table(
        'price_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('open', sa.Numeric(12, 4)),
        sa.Column('high', sa.Numeric(12, 4)),
        sa.Column('low', sa.Numeric(12, 4)),
        sa.Column('close', sa.Numeric(12, 4), nullable=False),
        sa.Column('volume', sa.Integer()),
        sa.Column('adj_close', sa.Numeric(12, 4)),
    )
    op.create_index('ix_price_history_company_id', 'price_history', ['company_id'])

    # benchmark_history
    op.create_table(
        'benchmark_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('index_name', sa.String(20), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('close', sa.Numeric(12, 4), nullable=False),
        sa.Column('daily_return', sa.Numeric(10, 6)),
    )

    # event_windows
    op.create_table(
        'event_windows',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('metric_id', sa.Integer(), sa.ForeignKey('guidance_metrics.id'), nullable=False),
        sa.Column('window_days', sa.Integer(), nullable=False),
        sa.Column('stock_return', sa.Numeric(10, 6)),
        sa.Column('benchmark_return', sa.Numeric(10, 6)),
        sa.Column('abnormal_return', sa.Numeric(10, 6)),
        sa.Column('volatility', sa.Numeric(10, 6)),
        sa.Column('is_positive_revision', sa.Boolean()),
    )
    op.create_index('ix_event_windows_metric_id', 'event_windows', ['metric_id'])


def downgrade() -> None:
    op.drop_table('event_windows')
    op.drop_table('benchmark_history')
    op.drop_table('price_history')
    op.drop_table('source_documents')
    op.drop_table('guidance_metrics')
    op.drop_table('guidance_events')
    op.drop_table('companies')

    sa.Enum(name='revision_type_enum').drop(op.get_bind())
    sa.Enum(name='metric_type_enum').drop(op.get_bind())
    sa.Enum(name='source_type_enum').drop(op.get_bind())
