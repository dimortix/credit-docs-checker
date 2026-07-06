import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Program(StrEnum):
    federal = "federal"
    regional = "regional"


class CheckStatus(StrEnum):
    approved = "approved"
    rejected = "rejected"
    check_in_progress = "check_in_progress"


class DocumentType(StrEnum):
    contract = "contract"
    specification = "specification"
    invoice = "invoice"
    act = "act"


class IssueLevel(StrEnum):
    error = "error"
    warning = "warning"


STATUS_LABELS: dict[CheckStatus, str] = {
    CheckStatus.approved: "Можно заявлять в банк",
    CheckStatus.rejected: "Нельзя заявлять в банк",
    CheckStatus.check_in_progress: "Проверка выполняется",
}

REQUIRED_DOCUMENTS: dict[Program, set[DocumentType]] = {
    Program.federal: {
        DocumentType.contract,
        DocumentType.specification,
        DocumentType.invoice,
        DocumentType.act,
    },
    Program.regional: {
        DocumentType.contract,
        DocumentType.invoice,
        DocumentType.act,
    },
}

DOCUMENT_TYPE_TITLES: dict[DocumentType, str] = {
    DocumentType.contract: "договор",
    DocumentType.specification: "спецификация",
    DocumentType.invoice: "счёт",
    DocumentType.act: "акт/УПД",
}


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    level: IssueLevel
    message: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    detected_type: DocumentType | None
    size_kb: int


class CheckResult(BaseModel):
    check_id: uuid.UUID
    status: CheckStatus
    status_label: str
    reason: str | None
    issues: list[IssueOut]
    documents: list[DocumentOut]
    extracted: dict | None
    checked_at: datetime


class CheckListItem(BaseModel):
    check_id: uuid.UUID
    checked_at: datetime
    program: Program
    status: CheckStatus
    documents_count: int
