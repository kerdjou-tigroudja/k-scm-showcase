resource "google_kms_key_ring" "k_scm_keyring" {
  name     = "k-scm-keyring-${var.environment}"
  location = var.region
}

resource "google_kms_crypto_key" "alloydb_cmek" {
  name            = "k-scm-alloydb-key"
  key_ring        = google_kms_key_ring.k_scm_keyring.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key" "storage_cmek" {
  name            = "k-scm-storage-key"
  key_ring        = google_kms_key_ring.k_scm_keyring.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}
