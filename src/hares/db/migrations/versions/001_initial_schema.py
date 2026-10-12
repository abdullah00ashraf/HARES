"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-12 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create official_domains table
    op.create_table(
        "official_domains",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("entity_name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("verified_owner", sa.String(length=255), nullable=False),
        sa.Column("quarterly_review_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
    )
    op.create_index("ix_official_domains_domain", "official_domains", ["domain"], unique=True)

    # 2. Create threat_campaigns table
    op.create_table(
        "threat_campaigns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("lure_type", sa.String(length=50), nullable=False),
        sa.Column("target_entity_spoofed", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("total_submissions", sa.Integer(), server_default="1", nullable=False),
        sa.Column("first_detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_threat_campaigns_lure_type", "threat_campaigns", ["lure_type"])
    op.create_index("ix_threat_campaigns_status", "threat_campaigns", ["status"])

    # 3. Create threat_indicators table
    op.create_table(
        "threat_indicators",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=True),
        sa.Column("indicator_type", sa.String(length=50), nullable=False),
        sa.Column("raw_indicator", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.String(length=512), nullable=False),
        sa.Column("verdict", sa.String(length=20), nullable=False),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["threat_campaigns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_threat_indicators_normalized_value", "threat_indicators", ["normalized_value"])

    # 4. Create triage_audit_log table
    op.create_table(
        "triage_audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("citizen_user_hash", sa.String(length=64), nullable=False),
        sa.Column("payload_type", sa.String(length=20), nullable=False),
        sa.Column("triage_verdict", sa.String(length=20), nullable=False),
        sa.Column("rule_triggered", sa.String(length=100), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("ix_triage_audit_log_citizen_user_hash", "triage_audit_log", ["citizen_user_hash"])
    op.create_index("ix_triage_audit_log_created_at", "triage_audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("triage_audit_log")
    op.drop_table("threat_indicators")
    op.drop_table("threat_campaigns")
    op.drop_table("official_domains")
