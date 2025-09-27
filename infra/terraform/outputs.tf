# --- Outputs cho GCS Buckets ---

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

# --- Outputs cho BigQuery Datasets ---

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

# --- Outputs cho Service Account (Rất quan trọng!) ---

output "pipeline_service_account_email" {
  description = "The email address of the service account used by the ETL pipeline."
  value       = google_service_account.service_account.email
}
