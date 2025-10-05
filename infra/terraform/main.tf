# --- Provider configuration ---
resource "google_project_service" "required_apis" {
  for_each = toset([
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "secretmanager.googleapis.com",
    "dataproc.googleapis.com"
  ])
  project = var.project_id
  service = each.key

  disable_on_destroy = false

}

# --- Naming conventions ---
locals {
  resource_prefix = "hn-${var.env}"
}

# --- Buckets ---
resource "google_storage_bucket" "bronze_bucket" {
  name          = "${local.resource_prefix}-bronze-bucket"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30
    }
  }

}

resource "google_storage_bucket" "silver_bucket" {
  name = "${local.resource_prefix}-silver-bucket"
  location = var.region
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "gold_bucket" {
  name = "${local.resource_prefix}-gold-bucket"
  location = var.region
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "code_bucket" {
  name = "${local.resource_prefix}-code-bucket"
  location = var.region
  uniform_bucket_level_access = true
  force_destroy = true
  versioning {
    enabled = true
  }

}

# --- BigQuery Datasets ---
resource "google_bigquery_dataset" "bronze_dataset" {
  dataset_id = "${replace(local.resource_prefix, "-", "_")}_bronze"
  location   = var.region
  friendly_name = "Bronze Dataset"
  description = "Raw data from Hacker News API"
  default_partition_expiration_ms = 30 * 24 * 3600 * 1000 # 30 days
}

resource "google_bigquery_dataset" "silver_dataset" {
  dataset_id = "${replace(local.resource_prefix, "-", "_")}_silver"
  location   = var.region
  friendly_name = "Silver Dataset"
  description = "Cleansed and standardized data from Bronze Dataset"
}

resource "google_bigquery_dataset" "gold_dataset" {
  dataset_id = "${replace(local.resource_prefix, "-", "_")}_gold"
  location   = var.region
  friendly_name = "Gold Dataset"
  description = "Aggregated and business-ready data from Silver Dataset"
}

# --- Artifact Registry for Docker Images ---
resource "google_artifact_registry_repository" "hackernews_docker_repo" {
    location = var.region
    repository_id = "hackernews-docker-repo"
    description = "Docker repository for Hacker News data pipeline"
    format = "DOCKER"
}

# --- Service Account for the Pipeline Worker ---
resource "google_service_account" "pipeline_worker_sa" {
  account_id   = "${local.resource_prefix}-pipeline-worker-sa"
  display_name = "Service Account for Hacker News Pipeline Worker"
}

# --- IAM Bindings for Service Account ---
resource "google_storage_bucket_iam_member" "bronzer_writer" {
  bucket = google_storage_bucket.bronze_bucket.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.pipeline_worker_sa.member
}

resource "google_storage_bucket_iam_member" "silver_writer" {
  bucket = google_storage_bucket.silver_bucket.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.pipeline_worker_sa.member
}

resource "google_storage_bucket_iam_member" "gold_writer" {
  bucket = google_storage_bucket.gold_bucket.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.pipeline_worker_sa.member
}

resource "google_storage_bucket_iam_member" "code_writer" {
  bucket = google_storage_bucket.code_bucket.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.pipeline_worker_sa.member
}

resource "google_project_iam_member" "bigquery_user" {
  project = var.project_id
  role = "roles/bigquery.user"
  member = google_service_account.pipeline_worker_sa.member
}

resource "google_project_iam_member" "bigquery_data_editor" {
  project = var.project_id
  role = "roles/bigquery.dataEditor"
  member = google_service_account.pipeline_worker_sa.member
}

resource "google_artifact_registry_repository_iam_member" "pipeline_runner_repo_reader" {
    location = var.region
    repository = google_artifact_registry_repository.hackernews_docker_repo.name
    role = "roles/artifactregistry.reader"
    member = google_service_account.pipeline_worker_sa.member
}

resource "google_project_iam_member" "vm_instance_user" {
    project = var.project_id
    role = "roles/compute.instanceUser"
    member = google_service_account.pipeline_worker_sa.member

}
