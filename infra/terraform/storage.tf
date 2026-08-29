resource "google_storage_bucket" "rag_staging" {
  name                        = "k-scm-rag-staging-${var.project_id}"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_cmek.id
  }

  versioning {
    enabled = true
  }
}
