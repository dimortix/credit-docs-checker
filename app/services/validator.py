from dataclasses import dataclass
from pathlib import PurePosixPath

from app.schemas import (
    DOCUMENT_TYPE_TITLES,
    REQUIRED_DOCUMENTS,
    CheckStatus,
    DocumentType,
    IssueLevel,
    Program,
)


@dataclass(frozen=True)
class FileInfo:
    name: str
    size_bytes: int
    detected_type: DocumentType | None


@dataclass(frozen=True)
class IssueItem:
    level: IssueLevel
    message: str


def get_extension(filename: str) -> str:
    return PurePosixPath(filename).suffix.lstrip(".").lower()


def validate_files(
    files: list[FileInfo],
    program: Program,
    allowed_extensions: set[str],
    max_file_size_bytes: int,
) -> list[IssueItem]:
    issues: list[IssueItem] = []

    for file in files:
        ext = get_extension(file.name)
        if ext not in allowed_extensions:
            issues.append(
                IssueItem(
                    IssueLevel.error,
                    f"Недопустимый формат файла «{file.name}»: "
                    f"разрешены только {', '.join(sorted(e.upper() for e in allowed_extensions))}",
                )
            )
        if file.size_bytes > max_file_size_bytes:
            max_mb = max_file_size_bytes // (1024 * 1024)
            issues.append(
                IssueItem(IssueLevel.error, f"Размер файла «{file.name}» превышает {max_mb} МБ")
            )
        elif file.size_bytes == 0:
            issues.append(
                IssueItem(IssueLevel.error, f"Файл «{file.name}» пустой")
            )
        if file.detected_type is None:
            issues.append(
                IssueItem(IssueLevel.warning, f"Не удалось определить тип документа: «{file.name}»")
            )

    present_types = {f.detected_type for f in files if f.detected_type is not None}
    for required in sorted(REQUIRED_DOCUMENTS[program], key=lambda t: t.value):
        if required not in present_types:
            issues.append(
                IssueItem(
                    IssueLevel.error,
                    f"Отсутствует обязательный документ: {DOCUMENT_TYPE_TITLES[required]}",
                )
            )

    return issues


def resolve_status(issues: list[IssueItem]) -> CheckStatus:
    if any(issue.level == IssueLevel.error for issue in issues):
        return CheckStatus.rejected
    return CheckStatus.approved


def build_reason(issues: list[IssueItem], status: CheckStatus) -> str | None:
    if status == CheckStatus.approved:
        return None
    errors = [issue.message for issue in issues if issue.level == IssueLevel.error]
    return ". ".join(errors) if errors else None
