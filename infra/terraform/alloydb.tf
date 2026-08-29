resource "google_alloydb_cluster" "k_scm_alloydb" {
  cluster_id = var.cluster_id
  location   = var.region
  network_config {
    network = google_compute_network.k_scm_vpc.id
  }

  encryption_config {
    kms_key_name = google_kms_crypto_key.alloydb_cmek.id
  }

  initial_user {
    password = var.alloydb_initial_password
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_alloydb_instance" "k_scm_primary" {
  cluster       = google_alloydb_cluster.k_scm_alloydb.name
  instance_id   = "${var.cluster_id}-primary"
  instance_type = "PRIMARY"

  machine_config {
    cpu_count = 2
  }

  depends_on = [google_alloydb_cluster.k_scm_alloydb]
}
