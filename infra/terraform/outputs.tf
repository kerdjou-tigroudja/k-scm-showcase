output "alloydb_cluster_id" {
  description = "ID of the AlloyDB cluster"
  value       = google_alloydb_cluster.k_scm_alloydb.id
}

output "alloydb_primary_ip" {
  description = "Private IP of the AlloyDB primary instance"
  value       = google_alloydb_instance.k_scm_primary.ip_address
}

output "kms_alloydb_key_id" {
  description = "KMS Key ID for AlloyDB CMEK"
  value       = google_kms_crypto_key.alloydb_cmek.id
}

output "service_account_email" {
  description = "Email of the dedicated K-SCM Service Account"
  value       = google_service_account.kerdjou_scm_sa.email
}

output "rag_staging_bucket" {
  description = "Name of the CMEK-encrypted GCS staging bucket"
  value       = google_storage_bucket.rag_staging.name
}
