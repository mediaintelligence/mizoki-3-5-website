# ==============================================================================
# MIZOKI3: AUTONOMOUS STRATEGIC INTELLIGENCE INFRASTRUCTURE
# Cloud:        Google Cloud Platform
# Architecture: Zero-Trust VPC · SRPVDAL cells on Cloud Run · BigQuery + Neo4j
#               TCKG · Pub/Sub Nexus bus · Vertex AI reasoning isolation
# ------------------------------------------------------------------------------
# Repo:  mizoki3-core-infrastructure
# Note:  Reasoning is pinned to CURRENT-generation Claude models on Vertex AI.
#        Older / deprecated model generations are intentionally excluded — see
#        var.approved_claude_models below.
# ==============================================================================

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

# ------------------------------------------------------------------------------
# VARIABLES
# ------------------------------------------------------------------------------
variable "project_id" {
  description = "GCP project hosting the MIZOKI3 Nexus."
  type        = string
  default     = "mizoki3-prod"
}

variable "region" {
  description = "Primary GCP region for all regional resources."
  type        = string
  default     = "us-central1"
}

variable "approved_claude_models" {
  description = <<-EOT
    Current-generation Claude models approved for MIZOKI3 reasoning on Vertex AI.
    Update this list as Anthropic ships newer models. Deprecated / older
    generations (e.g. claude-3.x) must NEVER be added — reasoning isolation
    depends on this list staying current.
  EOT
  type        = list(string)
  default = [
    "claude-opus-4-7",   # Primary  — most capable
    "claude-opus-4-6",   # Fallback
    "claude-sonnet-4-6", # High-throughput tier
  ]
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_project" "current" {}

# ------------------------------------------------------------------------------
# 1. THE FORTRESS (Zero-Trust VPC Network)
# All reasoning and memory run in a private subnet. No public ingress; egress
# is NAT-only so cells can reach Google APIs without an external address.
# ------------------------------------------------------------------------------
resource "google_compute_network" "nexus_vpc" {
  name                    = "mizoki3-nexus-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "private_subnet" {
  name                     = "mizoki3-private-subnet"
  ip_cidr_range            = "10.0.1.0/24"
  region                   = var.region
  network                  = google_compute_network.nexus_vpc.id
  private_ip_google_access = true # Reach Google APIs without a public IP
}

resource "google_compute_router" "nexus_router" {
  name    = "mizoki3-nexus-router"
  region  = var.region
  network = google_compute_network.nexus_vpc.id
}

resource "google_compute_router_nat" "nexus_nat" {
  name                               = "mizoki3-nexus-nat"
  router                             = google_compute_router.nexus_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# Perimeter firewall — internal VPC traffic only; explicit public-ingress deny.
resource "google_compute_firewall" "allow_internal" {
  name      = "mizoki3-allow-internal"
  network   = google_compute_network.nexus_vpc.id
  direction = "INGRESS"
  priority  = 1000
  allow { protocol = "all" }
  source_ranges = ["10.0.0.0/16"] # Only internal VPC traffic
}

resource "google_compute_firewall" "deny_public_ingress" {
  name      = "mizoki3-deny-public-ingress"
  network   = google_compute_network.nexus_vpc.id
  direction = "INGRESS"
  priority  = 2000
  deny { protocol = "all" }
  source_ranges = ["0.0.0.0/0"]
}

# ------------------------------------------------------------------------------
# 2. THE SUBSTRATE: Temporal-Causal Knowledge Graph (TCKG)
# Neo4j (causal graph physics) + BigQuery (unified analytical store) + GCS.
# All three encrypted with the customer-managed fiduciary key.
# ------------------------------------------------------------------------------
resource "google_compute_instance" "tckg_neo4j" {
  name         = "mizoki3-tckg-neo4j"
  machine_type = "n2-highmem-8" # Memory-optimized for heavy graph traversal
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "projects/cos-cloud/global/images/family/cos-stable"
      size  = 200
    }
    kms_key_self_link = google_kms_crypto_key.mizoki_key.id
  }

  network_interface {
    subnetwork = google_compute_subnetwork.private_subnet.id
    # No access_config block => no external/public IP
  }

  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  depends_on = [google_kms_crypto_key_iam_member.service_agents]
}

resource "google_bigquery_dataset" "tckg_unified" {
  dataset_id    = "mizoki3_unified"
  friendly_name = "MIZOKI3 Unified TCKG Dataset"
  location      = "US"

  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.mizoki_key.id
  }

  depends_on = [google_kms_crypto_key_iam_member.service_agents]
}

resource "google_storage_bucket" "nexus_artifacts" {
  name                        = "${var.project_id}-nexus-artifacts"
  location                    = "US"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  encryption {
    default_kms_key_name = google_kms_crypto_key.mizoki_key.id
  }

  versioning { enabled = true }

  depends_on = [google_kms_crypto_key_iam_member.service_agents]
}

# ------------------------------------------------------------------------------
# 3. THE NERVOUS SYSTEM: Pub/Sub Event Bus
# Cross-domain updates (e.g. Counsel updates Capital instantly).
# ------------------------------------------------------------------------------
resource "google_pubsub_topic" "nexus_event_bus" {
  name         = "mizoki3-nexus-bus"
  kms_key_name = google_kms_crypto_key.mizoki_key.id

  depends_on = [google_kms_crypto_key_iam_member.service_agents]
}

resource "google_pubsub_subscription" "nexus_subscription" {
  name                       = "mizoki3-nexus-sub"
  topic                      = google_pubsub_topic.nexus_event_bus.id
  ack_deadline_seconds       = 30
  message_retention_duration = "604800s" # 7-day replay window
}

# ------------------------------------------------------------------------------
# 4. THE EXECUTION ENGINE: SRPVDAL Orchestration on Cloud Run
# 32 FastAPI cells run as Cloud Run services; the orchestrator cell is shown
# here. Ingress is internal-only — no public route to the reasoning loop.
# ------------------------------------------------------------------------------
resource "google_service_account" "cell_runtime" {
  account_id   = "mizoki3-cell-runtime"
  display_name = "MIZOKI3 Cloud Run cell runtime"
}

resource "google_cloud_run_v2_service" "srpvdal_orchestrator" {
  name     = "mizoki3-srpvdal-orchestrator"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY" # No public internet to the brain

  template {
    service_account = google_service_account.cell_runtime.email

    scaling {
      min_instance_count = 1
      max_instance_count = 100
    }

    vpc_access {
      network_interfaces {
        network    = google_compute_network.nexus_vpc.id
        subnetwork = google_compute_subnetwork.private_subnet.id
      }
      egress = "ALL_TRAFFIC"
    }

    containers {
      image = "gcr.io/${var.project_id}/cell-orchestrator:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
    }
  }
}

# ------------------------------------------------------------------------------
# 5. REASONING ISOLATION (Vertex AI)
# Cells reason via CURRENT-generation Claude models on Vertex AI. Prompts and
# enterprise data never leave the project; older model generations are not
# permitted. Reasoning calls target Vertex publisher endpoints, e.g.:
#   publishers/anthropic/models/claude-opus-4-7
# ------------------------------------------------------------------------------
resource "google_project_iam_custom_role" "vertex_reasoning" {
  role_id     = "mizoki3VertexReasoning"
  title       = "MIZOKI3 Vertex Reasoning"
  description = "Allows Cloud Run cells to invoke approved Claude models on Vertex AI."
  permissions = [
    "aiplatform.endpoints.predict",
    "aiplatform.endpoints.get",
  ]
}

resource "google_project_iam_member" "cell_vertex_binding" {
  project = var.project_id
  role    = google_project_iam_custom_role.vertex_reasoning.id
  member  = "serviceAccount:${google_service_account.cell_runtime.email}"
}

# Approved-model allowlist — cells read this at boot and refuse any model
# (older generation or otherwise) that is not on the list.
resource "google_secret_manager_secret" "approved_models" {
  secret_id = "mizoki3-approved-claude-models"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "approved_models_v" {
  secret      = google_secret_manager_secret.approved_models.id
  secret_data = jsonencode(var.approved_claude_models)
}

# ------------------------------------------------------------------------------
# 6. FIDUCIARY ENCRYPTION (Cloud KMS)
# One customer-managed key with 90-day rotation encrypts the graph disk,
# BigQuery, GCS, and the Pub/Sub bus. Service agents are granted decrypt rights.
# ------------------------------------------------------------------------------
resource "google_kms_key_ring" "mizoki_ring" {
  name     = "mizoki3-fiduciary-ring"
  location = var.region
}

resource "google_kms_crypto_key" "mizoki_key" {
  name            = "mizoki3-master-key"
  key_ring        = google_kms_key_ring.mizoki_ring.id
  rotation_period = "7776000s" # 90-day rotation

  lifecycle {
    prevent_destroy = true
  }
}

# Grant each Google service agent encrypt/decrypt on the fiduciary key.
resource "google_kms_crypto_key_iam_member" "service_agents" {
  for_each = {
    compute  = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
    storage  = "serviceAccount:service-${data.google_project.current.number}@gs-project-accounts.iam.gserviceaccount.com"
    pubsub   = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
    bigquery = "serviceAccount:bq-${data.google_project.current.number}@bigquery-encryption.iam.gserviceaccount.com"
  }
  crypto_key_id = google_kms_crypto_key.mizoki_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
}

# ------------------------------------------------------------------------------
# OUTPUTS
# ------------------------------------------------------------------------------
output "orchestrator_url" {
  description = "Internal URL of the SRPVDAL orchestrator cell."
  value       = google_cloud_run_v2_service.srpvdal_orchestrator.uri
}

output "approved_claude_models" {
  description = "Claude models currently approved for reasoning. No older generations."
  value       = var.approved_claude_models
}
