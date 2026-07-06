from app.schemas import CheckStatus, DocumentType, IssueLevel, Program
from app.services.classifier import detect_document_type
from app.services.validator import FileInfo, resolve_status, validate_files

ALLOWED = {"pdf", "docx", "jpg", "jpeg", "png"}
MAX_SIZE = 20 * 1024 * 1024


def make_file(name, size=100 * 1024):
    return FileInfo(name=name, size_bytes=size, detected_type=detect_document_type(name))


def run(files, program):
    issues = validate_files(files, program, ALLOWED, MAX_SIZE)
    return resolve_status(issues), issues


def test_federal_full_package_approved():
    files = [
        make_file("договор_47.pdf"),
        make_file("спецификация.pdf"),
        make_file("счет_105.pdf"),
        make_file("акт_приемки.pdf"),
    ]
    status, issues = run(files, Program.federal)
    assert status == CheckStatus.approved
    assert issues == []


def test_regional_full_package_approved():
    files = [make_file("договор.pdf"), make_file("счет.pdf"), make_file("упд.pdf")]
    status, issues = run(files, Program.regional)
    assert status == CheckStatus.approved
    assert issues == []


def test_federal_missing_specification_rejected():
    files = [make_file("договор.pdf"), make_file("счет.pdf"), make_file("акт.pdf")]
    status, issues = run(files, Program.federal)
    assert status == CheckStatus.rejected
    assert any(
        i.level == IssueLevel.error and "спецификация" in i.message for i in issues
    )


def test_invalid_extension_rejected():
    files = [
        make_file("договор.exe"),
        make_file("спецификация.pdf"),
        make_file("счет.pdf"),
        make_file("акт.pdf"),
    ]
    status, issues = run(files, Program.federal)
    assert status == CheckStatus.rejected
    assert any(
        i.level == IssueLevel.error and "Недопустимый формат" in i.message for i in issues
    )


def test_oversized_file_rejected():
    files = [
        make_file("договор.pdf", size=MAX_SIZE + 1),
        make_file("счет.pdf"),
        make_file("акт.pdf"),
    ]
    status, issues = run(files, Program.regional)
    assert status == CheckStatus.rejected
    assert any(i.level == IssueLevel.error and "превышает" in i.message for i in issues)


def test_unrecognized_file_is_warning_only():
    files = [
        make_file("договор.pdf"),
        make_file("счет.pdf"),
        make_file("акт.pdf"),
        make_file("scan_0041.jpg"),
    ]
    status, issues = run(files, Program.regional)
    assert status == CheckStatus.approved
    warnings = [i for i in issues if i.level == IssueLevel.warning]
    assert len(warnings) == 1
    assert "scan_0041.jpg" in warnings[0].message


def test_unrecognized_file_detected_types_present():
    files = [make_file("scan_0041.jpg")]
    assert files[0].detected_type is None
    status, _ = run(files, Program.regional)
    assert status == CheckStatus.rejected


def test_empty_package_rejected_with_all_missing():
    status, issues = run([], Program.federal)
    assert status == CheckStatus.rejected
    missing = [i for i in issues if "Отсутствует обязательный документ" in i.message]
    assert len(missing) == 4


def test_empty_file_rejected():
    files = [
        make_file("договор.pdf", size=0),
        make_file("счет.pdf"),
        make_file("акт.pdf"),
    ]
    status, issues = run(files, Program.regional)
    assert status == CheckStatus.rejected
    assert any(i.level == IssueLevel.error and "пустой" in i.message for i in issues)


def test_regional_does_not_require_specification():
    files = [make_file("договор.pdf"), make_file("счет.pdf"), make_file("акт.pdf")]
    _, issues = run(files, Program.regional)
    assert not any("спецификация" in i.message for i in issues)


def test_duplicate_types_count_once():
    files = [
        make_file("договор_1.pdf"),
        make_file("договор_2.pdf"),
        make_file("счет.pdf"),
        make_file("акт.pdf"),
    ]
    status, _ = run(files, Program.regional)
    assert status == CheckStatus.approved
    assert {f.detected_type for f in files} == {
        DocumentType.contract,
        DocumentType.invoice,
        DocumentType.act,
    }
