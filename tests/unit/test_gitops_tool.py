import json
import os

import pytest

from app.tools.gitops_tool import (
    _apply_patch_to_repo,
    _sanitize_logs,
    _stage_remediation_inventory,
    _validate_remediation_branch,
    _validate_target_repository,
    submit_hitl_remediation_review,
    _has_unique_commits,
)


def test_submit_hitl_remediation_review_happy_path():
    from unittest.mock import patch
    with patch("app.tools.gitops_tool._has_unique_commits", return_value=True):
        raw_result = submit_hitl_remediation_review(
            repo_name="k-scm-mock-target-repository",
            branch_name="fix/compliance-madr-0001",
            patch_diff="- public_access_prevention = \"inherited\"\n+ public_access_prevention = \"enforced\"",
            adr_content="# [ADR-0001] Enforce CMEK & Public Access Prevention",
            compliance_summary="Fixed 4 critical non-compliance violations under EU AI Act & GDPR.",
        )
        result = json.loads(raw_result)

        assert "status" in result
        assert result["mode"] == "Human-in-the-Loop (Zero-Trust)"
        assert result["repository"] == "k-scm-mock-target-repository"
        assert result["remediation_branch"] == "fix/compliance-madr-0001"
        assert result["branch_readme_generated"] is True
        assert result["is_draft_pr_verified"] is True
        assert len(result["human_review_checklist"]) == 5
        assert "pull_request_url" in result


def test_apply_patch_to_repo():
    applied, msg, modified_files = _apply_patch_to_repo(
        "k-scm-mock-target-repository",
        "- public_access_prevention = \"inherited\"\n+ public_access_prevention = \"enforced\"",
    )
    assert isinstance(applied, bool)
    assert isinstance(msg, str)
    assert isinstance(modified_files, list)





def test_source_repository_read_only_protection():
    source_cwd = os.path.abspath(os.getcwd())
    with pytest.raises(PermissionError, match="strictly read-only"):
        _validate_target_repository("k-scm", repo_dir=source_cwd)


def test_forbidden_branch_rejection():
    with pytest.raises(ValueError, match="strictly disallowed"):
        _validate_remediation_branch("main")

    with pytest.raises(ValueError, match="strictly disallowed"):
        _validate_remediation_branch("master")


def test_stage_remediation_inventory_filtering(tmp_path):
    repo_dir = str(tmp_path)
    # Create git init in tmp_path
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)

    # Create allowed file and sensitive untracked file
    allowed_file = os.path.join(repo_dir, "README.md")
    sensitive_file = os.path.join(repo_dir, ".env.secret")

    with open(allowed_file, "w", encoding="utf-8") as f:
        f.write("# Test Readme")
    with open(sensitive_file, "w", encoding="utf-8") as f:
        f.write("SECRET_KEY=12345")

    staged = _stage_remediation_inventory(repo_dir, ["README.md"])
    assert "README.md" in staged or ".\\README.md" in staged
    assert ".env.secret" not in staged


def test_sanitize_logs():
    raw_logs = [
        "Checkout branch fix/compliance-001",
        "Header: Authorization: Bearer gho_1234567890secrettokenvalue",
        "GitHub PAT used: ghp_99999999999999999999",
    ]
    sanitized = _sanitize_logs(raw_logs)
    assert "gho_[REDACTED]" in sanitized[1] or "Bearer [REDACTED]" in sanitized[1]
    assert "ghp_[REDACTED]" in sanitized[2]
    assert "secrettokenvalue" not in sanitized[1]


def test_has_unique_commits_with_commits():
    from unittest.mock import patch
    with patch("app.tools.gitops_tool._run_git_cmd") as mock_run:
        # Mocking the first call: origin/main..HEAD -> returns count of 5
        mock_run.return_value = (0, "5\n")
        assert _has_unique_commits("dummy_dir", "fix/branch", "main") is True
        mock_run.assert_called_with(["git", "rev-list", "--count", "origin/main..HEAD"], cwd="dummy_dir", retries=1)


def test_has_unique_commits_no_commits():
    from unittest.mock import patch
    with patch("app.tools.gitops_tool._run_git_cmd") as mock_run:
        # Mocking the first call: origin/main..HEAD -> returns count of 0
        mock_run.return_value = (0, "0\n")
        assert _has_unique_commits("dummy_dir", "fix/branch", "main") is False


def test_has_unique_commits_fallback():
    from unittest.mock import patch
    with patch("app.tools.gitops_tool._run_git_cmd") as mock_run:
        # Mocking first call as failed (non-zero exit code), second as success with count 3
        mock_run.side_effect = [
            (1, "error"),
            (0, "3\n")
        ]
        assert _has_unique_commits("dummy_dir", "fix/branch", "main") is True
        assert mock_run.call_count == 2


def test_submit_hitl_remediation_review_no_unique_commits(tmp_path):
    import os
    repo_dir = str(tmp_path)
    # Create a dummy .git directory to simulate a real git repository
    os.makedirs(os.path.join(repo_dir, ".git"), exist_ok=True)

    from unittest.mock import patch
    with patch("app.tools.gitops_tool._has_unique_commits") as mock_has_unique, \
         patch("app.tools.gitops_tool._resolve_target_repo_dir") as mock_resolve_dir, \
         patch("app.tools.gitops_tool._validate_target_repository") as mock_validate_repo, \
         patch("app.tools.gitops_tool._validate_remediation_branch") as mock_validate_branch, \
         patch("app.tools.gitops_tool._run_git_cmd") as mock_run_git:

        mock_resolve_dir.return_value = repo_dir
        mock_validate_repo.return_value = None
        mock_validate_branch.return_value = None
        mock_run_git.return_value = (0, "Success")
        mock_has_unique.return_value = False

        raw_result = submit_hitl_remediation_review(
            repo_name="k-scm-mock-target-repository",
            branch_name="fix/compliance-madr-0001",
            patch_diff="- old = 1\n+ new = 1",
            adr_content="# ADR-0001",
            compliance_summary="Summary",
        )
        result = json.loads(raw_result)

        assert result["status"] == "pr_cancelled_no_commits"
        assert result["pushed_remote"] is False
        assert result["pull_request_url"] == ""
        assert "diagnostic" in result
        assert "0 net-new commits relative to main" in result["diagnostic"]

