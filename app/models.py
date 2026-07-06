import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.schemas import CheckStatus, DocumentType, IssueLevel, Program


class Check(Base):
    __tablename__ = "checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program: Mapped[Program] = mapped_column(Enum(Program, name="program"), nullable=False)
    status: Mapped[CheckStatus] = mapped_column(
        Enum(CheckStatus, name="check_status"), nullable=False, default=CheckStatus.check_in_progress
    )
    status_label: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="check", cascade="all, delete-orphan", order_by="Document.id"
    )
    issues: Mapped[list["Issue"]] = relationship(
        back_populates="check", cascade="all, delete-orphan", order_by="Issue.id"
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("checks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    detected_type: Mapped[DocumentType | None] = mapped_column(
        Enum(DocumentType, name="document_type"), nullable=True
    )
    size_kb: Mapped[int] = mapped_column(nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    check: Mapped[Check] = relationship(back_populates="documents")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("checks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    level: Mapped[IssueLevel] = mapped_column(Enum(IssueLevel, name="issue_level"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    check: Mapped[Check] = relationship(back_populates="issues")
