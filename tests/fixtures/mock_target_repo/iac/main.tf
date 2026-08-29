# Non-compliant Terraform infrastructure for testing K-SCM static audit

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# VIOLATION 1: GCS Bucket with missing CMEK encryption & inherited public access
resource "google_storage_bucket" "unsecured_data_bucket" {
  name          = "${var.project_id}-unsecured-customer-data"
  location      = var.region
  force_destroy = true

  # Missing public_access_prevention = "enforced"
  # Missing encryption block with kms_key_name (CMEK)
}

# VIOLATION 2: IAM policy granting public access to storage bucket
resource "google_storage_bucket_iam_binding" "public_read_binding" {
  bucket = google_storage_bucket.unsecured_data_bucket.name
  role   = "roles/storage.objectViewer"
  members = [
    "allUsers"
  ]
}

# VIOLATION 3: Compute Firewall allowing unrestricted SSH access from 0.0.0.0/0
resource "google_compute_firewall" "allow_ssh_all" {
  name    = "allow-ssh-unrestricted"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "3389"]
  }

  source_ranges = ["0.0.0.0/0"]
}

# VIOLATION 4: Vertex AI Dataset missing CMEK encryption key
resource "google_vertex_ai_dataset" "ai_training_dataset" {
  display_name        = "customer-behavior-ml-dataset"
  metadata_schema_uri = "gs://google-cloud-aiplatform/schema/dataset/metadata/tabular_1.0.0.yaml"
  region              = var.region

  # Missing encryption_spec { kms_key_name = ... }
}
