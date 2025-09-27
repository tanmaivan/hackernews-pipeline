terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "~> 7.4"
    }
  }

  backend "gcs" {
    bucket = "hn-pipeline-dev-tfstate"
    prefix = "terraform/state"
  }
}
