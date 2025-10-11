# --- Outputs for Project and Region ---
output "project_id" {
  description = "The ID of the GCP project."
  value       = var.project_id
}

output "region" {
  description = "The GCP region where resources are deployed."
  value       = var.region
}

# --- Outputs for GCS Buckets ---

output "bronze_bucket_name" {
  description = "The name of the GCS bucket for raw data (Bronze layer)."
  value       = google_storage_bucket.bronze_bucket.name
}

output "silver_bucket_name" {
  description = "The name of the GCS bucket for processed data (Silver layer)."
  value       = google_storage_bucket.silver_bucket.name
}

output "gold_bucket_name" {
  description = "The name of the GCS bucket for aggregated data (Gold layer)."
  value       = google_storage_bucket.gold_bucket.name
}

# --- Outputs for BigQuery Datasets ---

output "bronze_dataset_id" {
  description = "The ID of the BigQuery dataset for the Bronze layer."
  value       = google_bigquery_dataset.bronze_dataset.dataset_id
}

output "silver_dataset_id" {
  description = "The ID of the BigQuery dataset for the Silver layer."
  value       = google_bigquery_dataset.silver_dataset.dataset_id
}

output "gold_dataset_id" {
  description = "The ID of the BigQuery dataset for the Gold layer."
  value       = google_bigquery_dataset.gold_dataset.dataset_id
}

# --- Outputs for Service Account ---

output "pipeline_worker_service_account_email" {
  description = "The email address of the service account used by the Pipeline Worker."
  value       = google_service_account.pipeline_worker_sa.email
}
