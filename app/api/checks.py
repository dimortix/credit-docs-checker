import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import Settings, get_settings
from app.database import get_session
from app.models import Check, Document
from app.schemas import CheckListItem, CheckResult, Program
from app.services.check_service import UploadedFile, run_check

router = APIRouter(prefix="/api/checks", tags=["checks"])


def _to_result(check: Check) -> CheckResult:
    return CheckResult(
        check_id=check.id,
        status=check.status,
        status_label=check.status_label,
        reason=check.reason,
        issues=check.issues,
        documents=check.documents,
        extracted=check.extracted,
        checked_at=check.checked_at,
    )


@router.post("", response_model=CheckResult, status_code=status.HTTP_201_CREATED)
async def create_check(
    files: list[UploadFile] = File(default=[]),
    program: Program = Form(...),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> CheckResult:
    if not files:
        raise HTTPException(status_code=400, detail="Не передано ни одного файла")
    if len(files) > settings.max_files_per_check:
        raise HTTPException(
            status_code=400,
            detail=f"Слишком много файлов: максимум {settings.max_files_per_check} за одну проверку",
        )

    uploaded: list[UploadedFile] = []
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Файл без имени недопустим")
        if len(file.filename) > settings.max_filename_length:
            raise HTTPException(
                status_code=400,
                detail=f"Слишком длинное имя файла (максимум {settings.max_filename_length} символов)",
            )
        # файлы сверх лимита размера в память и на диск не грузим, только фиксируем ошибку
        if file.size is not None and file.size > settings.max_file_size_bytes:
            uploaded.append(UploadedFile(name=file.filename, size_bytes=file.size, content=None))
            continue
        content = await file.read()
        size_bytes = len(content)
        if size_bytes > settings.max_file_size_bytes:
            content = None
        uploaded.append(
            UploadedFile(name=file.filename, size_bytes=size_bytes, content=content)
        )

    check = await run_check(session, program, uploaded, settings)
    return _to_result(check)


@router.get("", response_model=list[CheckListItem])
async def list_checks(session: AsyncSession = Depends(get_session)) -> list[CheckListItem]:
    stmt = (
        select(Check, func.count(Document.id))
        .outerjoin(Document)
        .group_by(Check.id)
        .order_by(Check.checked_at.desc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        CheckListItem(
            check_id=check.id,
            checked_at=check.checked_at,
            program=check.program,
            status=check.status,
            documents_count=count,
        )
        for check, count in rows
    ]


@router.get("/{check_id}", response_model=CheckResult)
async def get_check(
    check_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> CheckResult:
    stmt = (
        select(Check)
        .where(Check.id == check_id)
        .options(selectinload(Check.documents), selectinload(Check.issues))
    )
    check = (await session.execute(stmt)).scalar_one_or_none()
    if check is None:
        raise HTTPException(status_code=404, detail="Проверка не найдена")
    return _to_result(check)
