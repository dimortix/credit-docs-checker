"""initial

Revision ID: 0001
Revises:
Create Date: 2026-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program",
            sa.Enum("federal", "regional", name="program"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("approved", "rejected", "check_in_progress", name="check_status"),
            nullable=False,
        ),
        sa.Column("status_label", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("extracted", postgresql.JSONB(), nullable=True),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "check_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("checks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column(
            "detected_type",
            sa.Enum("contract", "specification", "invoice", "act", name="document_type"),
            nullable=True,
        ),
        sa.Column("size_kb", sa.Integer(), nullable=False),
        sa.Column("stored_path", sa.String(length=1024), nullable=False),
    )
    op.create_index("ix_documents_check_id", "documents", ["check_id"])
    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "check_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("checks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "level",
            sa.Enum("error", "warning", name="issue_level"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
    )
    op.create_index("ix_issues_check_id", "issues", ["check_id"])


def downgrade() -> None:
    op.drop_table("issues")
    op.drop_table("documents")
    op.drop_table("checks")
    sa.Enum(name="issue_level").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="document_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="check_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="program").drop(op.get_bind(), checkfirst=True)
