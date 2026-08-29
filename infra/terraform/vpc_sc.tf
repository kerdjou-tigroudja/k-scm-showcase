resource "google_access_context_manager_access_policy" "access_policy" {
  parent = "organizations/0"
  title  = "k_scm_sovereign_policy"
}

resource "google_access_context_manager_service_perimeter" "k_scm_perimeter" {
  parent         = "accessPolicies/${google_access_context_manager_access_policy.access_policy.name}"
  name           = "accessPolicies/${google_access_context_manager_access_policy.access_policy.name}/servicePerimeters/k_scm_perimeter"
  title          = "K-SCM Sovereign Security Perimeter"
  perimeter_type = "PERIMETER_TYPE_REGULAR"

  status {
    restricted_services = [
      "alloydb.googleapis.com",
      "storage.googleapis.com",
      "cloudkms.googleapis.com"
    ]
  }
}
