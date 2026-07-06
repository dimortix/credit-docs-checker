import re

from app.schemas import DocumentType

# contract проверяем последним, иначе "спецификация_к_договору" уйдет в договор;
# короткие токены (акт/act/упд) - через lookaround, чтобы не ловить их внутри слов (contract, фактура)
_PATTERNS: list[tuple[DocumentType, re.Pattern[str]]] = [
    (DocumentType.specification, re.compile(r"специфик|specification|(?<![a-z])spec(?![a-z])")),
    (DocumentType.invoice, re.compile(r"счет|invoice|(?<![a-z])bill(?![a-z])")),
    (
        DocumentType.act,
        re.compile(
            r"(?<![а-яa-z])акт(?:ы|а|ов|у|е)?(?![а-яa-z])|(?<![а-яa-z])упд(?![а-яa-z])"
            r"|(?<![a-zа-я])acts?(?![a-z])|(?<![a-zа-я])upd(?![a-z])"
        ),
    ),
    (DocumentType.contract, re.compile(r"договор|контракт|contract")),
]


def normalize_filename(filename: str) -> str:
    return filename.lower().replace("ё", "е")


def detect_document_type(filename: str) -> DocumentType | None:
    name = normalize_filename(filename)
    for doc_type, pattern in _PATTERNS:
        if pattern.search(name):
            return doc_type
    return None
