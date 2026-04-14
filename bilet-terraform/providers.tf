terraform {
  backend "s3" {
    bucket       = "bilet-tf-state"
    key          = "vpc/terraform.tfstate"
    region       = "eu-central-1"
    profile      = "cagan"
    use_lockfile = true
    encrypt      = true
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "cagan"
}