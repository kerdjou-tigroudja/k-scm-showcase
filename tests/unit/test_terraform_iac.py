from pathlib import Path


def test_terraform_files_exist():
    tf_dir = Path("infra/terraform")
    assert tf_dir.exists(), "infra/terraform directory should exist"

    expected_files = [
        "providers.tf",
        "variables.tf",
        "kms.tf",
        "network.tf",
        "alloydb.tf",
        "storage.tf",
        "iam.tf",
        "vpc_sc.tf",
        "outputs.tf",
        "terraform.tfvars.example"
    ]

    for filename in expected_files:
        file_path = tf_dir / filename
        assert file_path.exists(), f"Expected terraform file {filename} to exist"
        assert file_path.stat().st_size > 0, f"File {filename} should not be empty"

def test_terraform_variables_content():
    var_file = Path("infra/terraform/variables.tf")
    content = var_file.read_text(encoding="utf-8")
    assert "kairosium-post-gscp-1" in content, "variables.tf should set default project to kairosium-post-gscp-1"
    assert "europe-west9" in content, "variables.tf should set region to europe-west9"
    assert "kerdjou-scm-sa" in content, "variables.tf should set default service account id to kerdjou-scm-sa"

def test_terraform_kms_cmek_config():
    kms_file = Path("infra/terraform/kms.tf")
    content = kms_file.read_text(encoding="utf-8")
    assert "k-scm-alloydb-key" in content, "kms.tf should define alloydb CMEK key"
    assert "k-scm-storage-key" in content, "kms.tf should define storage CMEK key"

def test_terraform_service_account():
    iam_file = Path("infra/terraform/iam.tf")
    content = iam_file.read_text(encoding="utf-8")
    assert "google_service_account" in content, "iam.tf should declare google_service_account resource"
    assert "roles/cloudkms.cryptoKeyEncrypterDecrypter" in content, "iam.tf should bind KMS encrypter/decrypter role"
