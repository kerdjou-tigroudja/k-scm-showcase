resource "google_compute_network" "k_scm_vpc" {
  name                    = "k-scm-vpc-${var.environment}"
  auto_create_subnetworks = false
}

resource "google_compute_global_address" "private_ip_alloc" {
  name          = "k-scm-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.k_scm_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.k_scm_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}
