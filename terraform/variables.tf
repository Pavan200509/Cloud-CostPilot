variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type    = string
  default = "asia-south1"
}

variable "enable_bigquery" {
  type        = bool
  default     = false
  description = "Create BigQuery dataset. Keep false for ₹0 local-only demos."
}

variable "enable_cloud_run" {
  type        = bool
  default     = false
  description = "Create Cloud Run placeholder service. Keep false unless deploying."
}