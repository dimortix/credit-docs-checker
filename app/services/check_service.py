import re
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models import Check, Document, Issue
from app.schemas import STATUS_LABELS, Program
from app.services.classifier import detect_document_type
from app.services.validator import FileInfo, build_reason, resolve_status, validate_files

_UNSAFE_CHARS = re.compile(r"[\x00-\x1f<>:\"/\\|?*]")


class UploadedFile:
    def __init__(self, name: str, size_bytes: int, content: bytes | None):
        self.name = name
        self.size_bytes = size_bytes
        # content is None, если файл не прошел валидацию и на диск не сохраняется
        self.content = content


def safe_filename(name: str) -> str:
    # защита от path traversal и инъекций: отрезаем путь и опасные символы
    base = Path(name.replace("\\", "/")).name
    cleaned = _UNSAFE_CHARS.sub("_", base).strip()
    return cleaned or "unnamed"


def extract_document_data(files: list[FileInfo]) -> dict:
    # TODO: сюда подключается AI-модуль извлечения реквизитов из содержимого документов;
    # пока структура возвращается с пустыми значениями (соответствует формату ответа ТЗ)
    return {"contractor": None, "amount": None, "date": None, "subject": None}


def _store_files(
    files: list[UploadedFile], storage_dir: Path
) -> list[tuple[UploadedFile, str | None]]:
    storage_dir.mkdir(parents=True, exist_ok=True)
    result: list[tuple[UploadedFile, str | None]] = []
    for index, f in enumerate(files):
        if f.content is None:
            result.append((f, None))
            continue
        # префикс индексом гарантирует уникальность при одинаковых именах в пакете
        stored_path = storage_dir / f"{index:03d}_{safe_filename(f.name)}"
        stored_path.write_bytes(f.content)
        result.append((f, str(stored_path)))
    return result


async def run_check(
    session: AsyncSession,
    program: Program,
    files: list[UploadedFile],
    settings: Settings,
) -> Check:
    check_id = uuid.uuid4()

    file_infos = [
        FileInfo(
            name=f.name,
            size_bytes=f.size_bytes,
            detected_type=detect_document_type(f.name),
        )
        for f in files
    ]

    issues = validate_files(
        file_infos,
        program,
        allowed_extensions=settings.allowed_extensions_set,
        max_file_size_bytes=settings.max_file_size_bytes,
    )
    status = resolve_status(issues)

    stored = _store_files(files, Path(settings.upload_dir) / str(check_id))

    documents = [
        Document(
            name=safe_filename(f.name),
            detected_type=info.detected_type,
            size_kb=(f.size_bytes + 1023) // 1024 if f.size_bytes else 0,
            stored_path=stored_path or "",
        )
        for (f, stored_path), info in zip(stored, file_infos)
    ]

    check = Check(
        id=check_id,
        program=program,
        status=status,
        status_label=STATUS_LABELS[status],
        reason=build_reason(issues, status),
        extracted=extract_document_data(file_infos),
        documents=documents,
        issues=[Issue(level=i.level, message=i.message) for i in issues],
    )
    session.add(check)
    await session.commit()
    await session.refresh(check, attribute_names=["documents", "issues"])
    return check
