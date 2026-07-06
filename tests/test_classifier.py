import pytest

from app.schemas import DocumentType
from app.services.classifier import detect_document_type


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("договор_47.pdf", DocumentType.contract),
        ("Договор поставки №12.docx", DocumentType.contract),
        ("contract_2025.pdf", DocumentType.contract),
        ("спецификация_к_договору.pdf", DocumentType.specification),
        ("Спецификация №1.docx", DocumentType.specification),
        ("specification.pdf", DocumentType.specification),
        ("счет_на_оплату.pdf", DocumentType.invoice),
        ("Счёт №105 от 01.03.2025.pdf", DocumentType.invoice),
        ("invoice_105.pdf", DocumentType.invoice),
        ("акт_приемки.pdf", DocumentType.act),
        ("акты выполненных работ.pdf", DocumentType.act),
        ("УПД_2025_03.pdf", DocumentType.act),
        ("upd_47.jpg", DocumentType.act),
        ("контракт_поставки.pdf", DocumentType.contract),
        ("scan_0041.jpg", None),
        ("photo.png", None),
        ("фактура.pdf", None),
    ],
)
def test_detect_document_type(filename, expected):
    assert detect_document_type(filename) == expected
