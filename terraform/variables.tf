variable "project_id" {
  type = string
  description = "The GCP project ID"
}

variable "region" {
  type = string
  description = "The primary GCP region for resources."
  default = "asia-southeast1"
}

variable "env" {
  type = string
  description = "The environment name (e.g., dev, staging, prod)."
  default = "dev"
}
