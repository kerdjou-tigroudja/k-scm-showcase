import json
from pathlib import Path

from app.tools.static_audit_tool import parse_python_source, parse_terraform_iac


def test_parse_terraform_iac_mock_repo():
    fixture_path = Path("tests/fixtures/mock_target_repo/iac")
    assert fixture_path.exists(), "Terraform fixture directory must exist"

    raw_result = parse_terraform_iac(str(fixture_path))
    result = json.loads(raw_result)

    assert result["status"] == "success"
    assert result["total_violations"] >= 4

    rule_ids = [v["rule_id"] for v in result["violations"]]
    assert "KSCM-TF-CMEK-01" in rule_ids
    assert "KSCM-TF-GCS-02" in rule_ids
    assert "KSCM-TF-IAM-01" in rule_ids
    assert "KSCM-TF-NET-01" in rule_ids
    assert "KSCM-TF-AI-01" in rule_ids


def test_parse_python_source_mock_repo():
    fixture_path = Path("tests/fixtures/mock_target_repo/src")
    assert fixture_path.exists(), "Python fixture directory must exist"

    raw_result = parse_python_source(str(fixture_path))
    result = json.loads(raw_result)

    assert result["status"] == "success"
    assert result["total_violations"] >= 3

    rule_ids = [v["rule_id"] for v in result["violations"]]
    assert "KSCM-PY-SEC-01" in rule_ids
    assert "KSCM-PY-PII-01" in rule_ids
    assert "KSCM-PY-AI-01" in rule_ids


def test_explicit_fixture_file_is_scanned():
    target = Path("tests/fixtures/mock_target_repo/iac/main.tf")
    assert target.exists(), "Terraform fixture file must exist"

    result = json.loads(parse_terraform_iac(str(target)))

    assert result["status"] == "success"
    assert result["total_files_scanned"] == 1


def test_nested_fixture_directory_stays_ignored(tmp_path: Path):
    root = tmp_path / "repo"
    kept = root / "main.tf"
    hidden = root / "fixtures" / "hidden.tf"
    hidden.parent.mkdir(parents=True)
    body = 'resource "google_storage_bucket" "open" {}\n'
    kept.write_text(body, encoding="utf-8")
    hidden.write_text(body, encoding="utf-8")

    result = json.loads(parse_terraform_iac(str(root)))

    assert result["status"] == "success"
    assert result["total_files_scanned"] == 1
    assert all(
        not str(item["file"]).endswith("hidden.tf") for item in result["violations"]
    )
