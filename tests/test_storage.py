import pytest

from app.services.check_service import safe_filename


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("договор_47.pdf", "договор_47.pdf"),
        ("../../../tmp/evil.pdf", "evil.pdf"),
        ("/etc/passwd", "passwd"),
        ("..\\..\\windows\\evil.docx", "evil.docx"),
        ("<script>alert(1)</script>.pdf", "script_.pdf"),
        ("файл\x00.pdf", "файл_.pdf"),
        ("", "unnamed"),
    ],
)
def test_safe_filename(raw, expected):
    assert safe_filename(raw) == expected
