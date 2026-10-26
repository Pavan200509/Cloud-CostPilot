terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enabling APIs is usually free. Only enable what we may need.
resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "bigquery.googleapis.com",
    "run.googleapis.com",
    "aiplatform.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

# Runtime identity for read-only discovery (no create/delete VM permissions).
resource "google_service_account" "cloudops" {
  account_id   = "cloudops-runtime"
  display_name = "CloudOps runtime (read-only)"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "viewer" {
  project = var.project_id
  role    = "roles/compute.viewer"
  member  = "serviceAccount:${google_service_account.cloudops.email}"
}

resource "google_project_iam_member" "browser" {
  project = var.project_id
  role    = "roles/browser"
  member  = "serviceAccount:${google_service_account.cloudops.email}"
}

# Optional — small demo dataset only. Free tier usually covers tiny usage.
resource "google_bigquery_dataset" "cloudops" {
  count       = var.enable_bigquery ? 1 : 0
  dataset_id  = "cloudops"
  location    = var.region
  description = "CloudOps metrics (optional)"
  depends_on  = [google_project_service.apis]
}

resource "google_bigquery_table" "resource_metrics" {
  count      = var.enable_bigquery ? 1 : 0
  dataset_id = google_bigquery_dataset.cloudops[0].dataset_id
  table_id   = "resource_metrics"
  schema = jsonencode([
    { name = "resource_id", type = "STRING", mode = "REQUIRED" },
    { name = "name", type = "STRING", mode = "NULLABLE" },
    { name = "project_id", type = "STRING", mode = "NULLABLE" },
    { name = "machine_type", type = "STRING", mode = "NULLABLE" },
    { name = "cpu_utilization_pct", type = "FLOAT", mode = "NULLABLE" },
    { name = "memory_utilization_pct", type = "FLOAT", mode = "NULLABLE" },
    { name = "disk_utilization_pct", type = "FLOAT", mode = "NULLABLE" },
    { name = "observed_at", type = "TIMESTAMP", mode = "NULLABLE" }
  ])
}

output "runtime_service_account" {
  value = google_service_account.cloudops.email
}

output "note" {
  value = "Defaults avoid BigQuery/Cloud Run creation. Use local Docker (mock mode) for ₹0 demos."
}