"""
ADK Tools for Static Compliance Audit of Terraform IaC and Python Source Code.
"""

import ast
import json
import re
from pathlib import Path


def _extract_hcl_resource_blocks(content: str) -> list[tuple[str, str, str, int]]:
    """Extracts HCL resource blocks from Terraform content using brace matching.

    Returns:
        List of tuples: (resource_type, resource_name, body_text, start_line)
    """
    blocks = []
    pattern = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{')

    for match in pattern.finditer(content):
        res_type = match.group(1)
        res_name = match.group(2)
        start_line = content[:match.start()].count("\n") + 1

        # Brace matching for block body
        start_idx = match.end() - 1
        depth = 0
        end_idx = -1

        for i in range(start_idx, len(content)):
            char = content[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break

        if end_idx != -1:
            body = content[start_idx + 1:end_idx]
            blocks.append((res_type, res_name, body, start_line))

    return blocks


def _is_ignored_path(path: Path) -> bool:
    """Helper to check if a path belongs to tests, fixtures, or virtual environments."""
    ignored = {"tests", "fixtures", ".venv", ".git", ".pytest_cache"}
    return any(part in ignored for p in [path] for part in p.parts)


def _resolve_tf_files(file_path: str) -> list[Path]:
    """Helper to resolve .tf files strictly confined to the requested target directory/file."""
    path = Path(file_path).resolve() if Path(file_path).is_absolute() else (Path.cwd() / file_path).resolve()

    if path.is_file() and path.suffix == ".tf":
        if not _is_ignored_path(path):
            return [path]
    if path.is_dir():
        files = [f for f in path.glob("**/*.tf") if not _is_ignored_path(f)]
        if files:
            return sorted(files)

    # Fallback for relative path without cwd prefix if path does not exist directly
    raw_path = Path(file_path)
    if raw_path.is_file() and raw_path.suffix == ".tf" and not _is_ignored_path(raw_path):
        return [raw_path]
    if raw_path.is_dir():
        files = [f for f in raw_path.glob("**/*.tf") if not _is_ignored_path(f)]
        if files:
            return sorted(files)


    return []


def _resolve_py_files(file_path: str) -> list[Path]:
    """Helper to resolve .py files strictly confined to the requested target directory/file."""
    path = Path(file_path).resolve() if Path(file_path).is_absolute() else (Path.cwd() / file_path).resolve()

    if path.is_file() and path.suffix == ".py":
        if not _is_ignored_path(path):
            return [path]
    if path.is_dir():
        files = [f for f in path.glob("**/*.py") if not _is_ignored_path(f)]
        if files:
            return sorted(files)

    # Fallback for relative path without cwd prefix if path does not exist directly
    raw_path = Path(file_path)
    if raw_path.is_file() and raw_path.suffix == ".py" and not _is_ignored_path(raw_path):
        return [raw_path]
    if raw_path.is_dir():
        files = [f for f in raw_path.glob("**/*.py") if not _is_ignored_path(f)]
        if files:
            return sorted(files)


    return []


def parse_terraform_iac(file_path: str = ".") -> str:
    """Parses and performs static compliance audit on Terraform IaC files (.tf) or directories.

    Identifies security vulnerabilities and regulatory non-compliance under EU AI Act and GDPR,
    such as public GCS buckets, missing CMEK encryption, open firewall ports (SSH/RDP), and public IAM bindings.

    Args:
        file_path: Path to a .tf/.py file or target repository directory (default: '.').

    Returns:
        JSON string containing the audit report with detected violations, line numbers, and regulatory tags.
    """
    tf_files = _resolve_tf_files(file_path)

    if not tf_files:
        return json.dumps({
            "status": "error",
            "message": f"No .tf files found at path: {file_path}",
            "violations": []
        }, indent=2)

    violations = []

    for tf_file in tf_files:
        try:
            content = tf_file.read_text(encoding="utf-8")
            resource_blocks = _extract_hcl_resource_blocks(content)

            for res_type, res_name, res_body, start_line in resource_blocks:
                # Strip single-line comments (# and //) to avoid false negative matches from comments
                clean_body = re.sub(r'(#|//).*', '', res_body)

                # 1. Audit google_storage_bucket
                if res_type == "google_storage_bucket":
                    if "kms_key_name" not in clean_body and "encryption" not in clean_body:
                        violations.append({
                            "file": str(tf_file),
                            "line": start_line,
                            "resource_type": res_type,
                            "resource_name": res_name,
                            "severity": "HIGH",
                            "rule_id": "KSCM-TF-CMEK-01",
                            "description": f"Storage bucket '{res_name}' is missing Cloud KMS CMEK encryption.",
                            "regulatory_category": "GDPR Article 32 (Security of Processing), SecNumCloud CMEK"
                        })

                    if 'public_access_prevention = "enforced"' not in clean_body:
                        violations.append({
                            "file": str(tf_file),
                            "line": start_line,
                            "resource_type": res_type,
                            "resource_name": res_name,
                            "severity": "HIGH",
                            "rule_id": "KSCM-TF-GCS-02",
                            "description": f"Storage bucket '{res_name}' does not enforce 'public_access_prevention = \"enforced\"'.",
                            "regulatory_category": "GDPR Article 32 / Data Leakage Prevention"
                        })

                # 2. Audit google_storage_bucket_iam_binding / google_storage_bucket_iam_member
                elif res_type.startswith("google_storage_bucket_iam_"):
                    if '"allUsers"' in clean_body or '"allAuthenticatedUsers"' in clean_body:
                        violations.append({
                            "file": str(tf_file),
                            "line": start_line,
                            "resource_type": res_type,
                            "resource_name": res_name,
                            "severity": "CRITICAL",
                            "rule_id": "KSCM-TF-IAM-01",
                            "description": f"Public IAM binding granting access to allUsers/allAuthenticatedUsers in '{res_name}'.",
                            "regulatory_category": "GDPR Article 32 / Zero-Trust Public Exposure"
                        })

                # 3. Audit google_compute_firewall
                elif res_type == "google_compute_firewall":
                    if '"0.0.0.0/0"' in clean_body and ("22" in clean_body or "3389" in clean_body):
                        violations.append({
                            "file": str(tf_file),
                            "line": start_line,
                            "resource_type": res_type,
                            "resource_name": res_name,
                            "severity": "HIGH",
                            "rule_id": "KSCM-TF-NET-01",
                            "description": f"Firewall rule '{res_name}' opens administrative SSH/RDP ports to 0.0.0.0/0.",
                            "regulatory_category": "EU AI Act Article 15 (Cybersecurity) / SecNumCloud Network Isolation"
                        })

                # 4. Audit google_vertex_ai_dataset
                elif res_type == "google_vertex_ai_dataset":
                    if "encryption_spec" not in clean_body or "kms_key_name" not in clean_body:
                        violations.append({
                            "file": str(tf_file),
                            "line": start_line,
                            "resource_type": res_type,
                            "resource_name": res_name,
                            "severity": "HIGH",
                            "rule_id": "KSCM-TF-AI-01",
                            "description": f"Vertex AI dataset '{res_name}' missing CMEK encryption spec.",
                            "regulatory_category": "EU AI Act Article 10 (Data & Governance) & GDPR Article 32"
                        })

                # 5. Audit google_alloydb_cluster / google_alloydb_instance
                elif res_type in ("google_alloydb_cluster", "google_alloydb_instance"):
                    if "kms_key_name" not in clean_body and "encryption_config" not in clean_body:
                        violations.append({
                            "file": str(tf_file),
                            "line": start_line,
                            "resource_type": res_type,
                            "resource_name": res_name,
                            "severity": "HIGH",
                            "rule_id": "KSCM-TF-CMEK-02",
                            "description": f"AlloyDB resource '{res_name}' is missing Cloud KMS CMEK encryption config.",
                            "regulatory_category": "GDPR Article 32 (Security of Processing) & SecNumCloud CMEK"
                        })

        except Exception as e:
            violations.append({
                "file": str(tf_file),
                "line": 1,
                "resource_type": "unknown",
                "resource_name": "parse_error",
                "severity": "LOW",
                "rule_id": "KSCM-TF-ERR-01",
                "description": f"Error parsing file {tf_file}: {e}",
                "regulatory_category": "Syntax/Parser Error"
            })

    return json.dumps({
        "status": "success",
        "scanned_path": str(file_path),
        "total_files_scanned": len(tf_files),
        "total_violations": len(violations),
        "violations": violations
    }, indent=2)


def parse_python_source(file_path: str = ".") -> str:
    """Parses and performs AST static compliance audit on Python source files (.py) or directories.

    Detects hardcoded secrets/credentials, unencrypted disk storage of PII personal data (GDPR),
    and unmonitored AI/LLM model execution lacking safety guardrails (EU AI Act).

    Args:
        file_path: Path to a .tf/.py file or target repository directory (default: '.').

    Returns:
        JSON string containing the AST audit report with detected violations and regulatory classifications.
    """
    py_files = _resolve_py_files(file_path)

    if not py_files:
        return json.dumps({
            "status": "error",
            "message": f"No .py files found at path: {file_path}",
            "violations": []
        }, indent=2)

    violations = []
    secret_keywords = {"password", "secret", "api_key", "private_key", "token", "sk-proj"}

    for py_file in py_files:
        try:
            source_code = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source_code, filename=str(py_file))

            reported_ai_lines = set()
            reported_secret_lines = set()

            # AST Visitor for Code Audit
            for node in ast.walk(tree):
                # Check Assign for Hardcoded Secrets
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        var_name = ""
                        if isinstance(target, ast.Name):
                            var_name = target.id
                        elif isinstance(target, ast.Attribute):
                            var_name = target.attr

                        if any(kw in var_name.lower() for kw in secret_keywords):
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                if not any(abs(node.lineno - prev) <= 3 for prev in reported_secret_lines):
                                    reported_secret_lines.add(node.lineno)
                                    violations.append({
                                        "file": str(py_file),
                                        "line": node.lineno,
                                        "node_type": "Assign",
                                        "symbol": var_name,
                                        "severity": "CRITICAL",
                                        "rule_id": "KSCM-PY-SEC-01",
                                        "description": f"Hardcoded credential/secret in variable '{var_name}'.",
                                        "regulatory_category": "GDPR Article 32 (Security) & SecNumCloud Secret Hygiene"
                                    })

                # Check Call for File Writing (PII Risk) & AI Model Execution
                if isinstance(node, ast.Call):
                    # Check open() calls for unencrypted disk write
                    if isinstance(node.func, ast.Name) and node.func.id == "open":
                        mode_arg = None
                        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                            mode_arg = node.args[1].value
                        else:
                            for kw in node.keywords:
                                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                                    mode_arg = kw.value.value

                        if mode_arg and any(m in str(mode_arg) for m in ["w", "a", "x"]):
                            # File opened for writing
                            file_target = ""
                            if len(node.args) >= 1 and isinstance(node.args[0], ast.Constant):
                                file_target = str(node.args[0].value)

                            violations.append({
                                "file": str(py_file),
                                "line": node.lineno,
                                "node_type": "Call",
                                "symbol": "open",
                                "severity": "HIGH",
                                "rule_id": "KSCM-PY-PII-01",
                                "description": f"Unencrypted local file write operation targeting '{file_target}'. Potential PII leak.",
                                "regulatory_category": "GDPR Article 32 & Article 5 (Storage Limitation & Integrity)"
                            })

                    # Check AI Model calls (GenerativeModel, generate_content, etc.)
                    is_ai_call = False
                    symbol = getattr(node.func, "attr", getattr(node.func, "id", "AI_Call"))
                    if symbol in ("GenerativeModel", "generate_content", "predict"):
                        is_ai_call = True

                    if is_ai_call:
                        if not any(abs(node.lineno - prev) <= 5 for prev in reported_ai_lines):
                            reported_ai_lines.add(node.lineno)
                            violations.append({
                                "file": str(py_file),
                                "line": node.lineno,
                                "node_type": "Call",
                                "symbol": symbol,
                                "severity": "HIGH",
                                "rule_id": "KSCM-PY-AI-01",
                                "description": "High-risk AI model call detected without risk management, guardrails, or compliance logging.",
                                "regulatory_category": "EU AI Act Article 15 (Accuracy, Robustness & Cybersecurity) & Article 14 (Human Oversight)"
                            })

        except SyntaxError as se:
            violations.append({
                "file": str(py_file),
                "line": se.lineno or 1,
                "node_type": "SyntaxError",
                "symbol": "syntax_error",
                "severity": "LOW",
                "rule_id": "KSCM-PY-ERR-01",
                "description": f"Python syntax error in file {py_file}: {se.msg}",
                "regulatory_category": "Syntax Error"
            })
        except Exception as e:
            violations.append({
                "file": str(py_file),
                "line": 1,
                "node_type": "Exception",
                "symbol": "parser_exception",
                "severity": "LOW",
                "rule_id": "KSCM-PY-ERR-02",
                "description": f"Failed to parse AST for file {py_file}: {e}",
                "regulatory_category": "Parser Error"
            })

    return json.dumps({
        "status": "success",
        "scanned_path": str(file_path),
        "total_files_scanned": len(py_files),
        "total_violations": len(violations),
        "violations": violations
    }, indent=2)
