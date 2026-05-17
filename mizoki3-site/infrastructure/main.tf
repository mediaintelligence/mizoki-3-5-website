# ==============================================================================
# MIZOKI3: AUTONOMOUS STRATEGIC INTELLIGENCE INFRASTRUCTURE
# Architecture: Zero-Trust VPC, Neptune TCKG, EKS Orchestration, MSK Event Bus
# ------------------------------------------------------------------------------
# Repo:  mizoki3-core-infrastructure
# Note:  Foundation-model ID is pinned below. Review/bump to the current
#        approved Claude model on Bedrock before applying to Production.
# ==============================================================================

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Environment = "Production-Fiduciary"
      System      = "MIZOKI3-Nexus"
    }
  }
}

# ------------------------------------------------------------------------------
# 1. THE FORTRESS (Zero-Trust VPC Network)
# All reasoning and memory occurs in strictly private subnets.
# ------------------------------------------------------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  name = "mizoki3-nexus-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false # High availability for enterprise SLAs
  enable_dns_hostnames = true
  enable_dns_support   = true
}

# ------------------------------------------------------------------------------
# 2. THE SUBSTRATE: Temporal-Causal Knowledge Graph (TCKG)
# AWS Neptune: Bi-Temporal Graph Database hosting entity and causal physics.
# ------------------------------------------------------------------------------
resource "aws_neptune_cluster" "tckg_substrate" {
  cluster_identifier                  = "mizoki3-tckg-cluster"
  engine                              = "neptune"
  engine_version                      = "1.3.0.0" # Graph + Vector capabilities
  backup_retention_period             = 35
  iam_database_authentication_enabled = true
  apply_immediately                   = true
  vpc_security_group_ids              = [aws_security_group.tckg_sg.id]
  neptune_subnet_group_name           = aws_neptune_subnet_group.tckg_subnets.name
  storage_encrypted                   = true
  kms_key_arn                         = aws_kms_key.mizoki_kms.arn
}

resource "aws_neptune_cluster_instance" "tckg_nodes" {
  count              = 2 # High Availability (1 Writer, 1 Reader)
  identifier         = "mizoki3-tckg-node-${count.index}"
  cluster_identifier = aws_neptune_cluster.tckg_substrate.id
  engine             = "neptune"
  instance_class     = "db.r6g.2xlarge" # Memory-optimized for heavy graph traversal
}

resource "aws_neptune_subnet_group" "tckg_subnets" {
  name       = "mizoki3-tckg-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

# ------------------------------------------------------------------------------
# 3. THE NERVOUS SYSTEM: Kafka Event Bus (Amazon MSK)
# Cross-domain updates (e.g., Counsel updates Capital instantly).
# ------------------------------------------------------------------------------
resource "aws_msk_serverless_cluster" "nexus_event_bus" {
  cluster_name = "mizoki3-nexus-bus"

  vpc_config {
    subnet_ids         = module.vpc.private_subnets
    security_group_ids = [aws_security_group.tckg_sg.id]
  }

  client_authentication {
    sasl {
      iam {
        enabled = true # Strict IAM authentication inside the VPC
      }
    }
  }
}

# ------------------------------------------------------------------------------
# 4. THE EXECUTION ENGINE: SRPVDAL Orchestration & Temporal.io
# AWS EKS hosting the LangGraph Multi-Agent framework.
# ------------------------------------------------------------------------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.16.0"

  cluster_name    = "mizoki3-srpvdal-orchestrator"
  cluster_version = "1.28"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  cluster_endpoint_public_access = false # No public internet access to the control plane

  eks_managed_node_groups = {
    agents = {
      min_size       = 3
      max_size       = 10
      desired_size   = 3
      instance_types = ["c6i.2xlarge"] # Compute-optimized for simulation physics
    }
  }
}

# ------------------------------------------------------------------------------
# 5. REASONING ISOLATION (Bedrock IAM)
# Limits agents strictly to an approved Claude model without data leaving the VPC.
# ------------------------------------------------------------------------------
resource "aws_iam_policy" "fiduciary_ai_policy" {
  name        = "MIZOKI3-Fiduciary-Bedrock-Policy"
  description = "Allows EKS LangGraph agents to reason via an approved Claude model securely"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Effect   = "Allow"
        Resource = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
      }
    ]
  })
}

resource "aws_kms_key" "mizoki_kms" {
  description             = "MIZOKI3 Master Fiduciary Encryption Key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_security_group" "tckg_sg" {
  name   = "mizoki3-internal-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [module.vpc.vpc_cidr_block] # Only internal VPC traffic allowed
  }
}
