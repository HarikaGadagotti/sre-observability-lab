terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_container_cluster" "primary" {
  name             = "sre-lab"
  location         = var.region
  enable_autopilot = true
  deletion_protection = false
}

resource "google_artifact_registry_repository" "images" {
  repository_id = "orders"
  format        = "DOCKER"
  location      = var.region
}

output "cluster_name" { value = google_container_cluster.primary.name }
