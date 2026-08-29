resource "google_service_account" "kerdjou_scm_sa" {
  account_id   = var.service_account_id
  display_name = "K-SCM Sovereign Compliance Mesh Service Account"
  description  = "Service account for K-SCM ADK agents, RAG querying, and telemetry"
}

resource "google_kms_crypto_key_iam_binding" "alloydb_kms_binding" {
  crypto_key_id = google_kms_crypto_key.alloydb_cmek.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members       = ["serviceAccount:${google_service_account.kerdjou_scm_sa.email}"]
}

resource "google_project_iam_member" "alloydb_client" {
  project = var.project_id
  role    = "roles/alloydb.client"
  member  = "serviceAccount:${google_service_account.kerdjou_scm_sa.email}"
}

resource "google_project_iam_member" "trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.kerdjou_scm_sa.email}"
}

# Minimal IAM: Job execution permission at project level
resource "google_project_iam_member" "bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.kerdjou_scm_sa.email}"
}

# Minimal IAM: Dataset-scoped Data Editor permission strictly restricted to telemetry dataset
resource "google_bigquery_dataset_iam_member" "bq_analytics_dataset_editor" {
  dataset_id = google_bigquery_dataset.adk_agent_analytics.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.kerdjou_scm_sa.email}"
}
