resource "google_bigquery_dataset" "adk_agent_analytics" {
  dataset_id                  = var.telemetry_dataset_id
  friendly_name               = "ADK Agent Analytics & Telemetry"
  description                 = "Sovereign BigQuery dataset for K-SCM agent telemetry, token usage, and FinOps audit logs."
  location                    = var.region
  default_table_expiration_ms = var.telemetry_dataset_ttl_ms

  labels = {
    environment = var.environment
    service     = "k-scm"
    governance  = "f08-telemetry"
  }
}
