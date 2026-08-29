variable "project_id" {
  description = "GCP Project ID for sovereign K-SCM infrastructure"
  type        = string
  default     = "kairosium-post-gscp-1"
}

variable "region" {
  description = "Sovereign GCP Region (SecNumCloud / S3NS compliant)"
  type        = string
  default     = "europe-west9"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "cluster_id" {
  description = "AlloyDB Cluster Identifier"
  type        = string
  default     = "k-scm-alloydb-cluster"
}

variable "database_name" {
  description = "AlloyDB database name for regulatory RAG"
  type        = string
  default     = "k_scm_rag"
}

variable "service_account_id" {
  description = "Service Account ID for K-SCM Agent"
  type        = string
  default     = "kerdjou-scm-sa"
}

variable "telemetry_dataset_id" {
  description = "BigQuery dataset ID for ADK Agent Analytics and Telemetry"
  type        = string
  default     = "adk_agent_analytics"
}

variable "telemetry_dataset_ttl_ms" {
  description = "Default table retention / TTL in milliseconds for telemetry dataset (30 days)"
  type        = number
  default     = 2592000000 # 30 days in ms
}

variable "alloydb_initial_password" {
  description = "Initial password for AlloyDB cluster root user (sensitive)"
  type        = string
  sensitive   = true
  default     = "ChangeMeSovereignPass123!"
}
