terraform {
  backend "s3" {
    bucket = "rootmos-terraform"
    key = "mdu-schema"
    region = "eu-central-1"
  }

  required_providers {
    aws = {
      # https://registry.terraform.io/providers/hashicorp/aws/latest
      source  = "hashicorp/aws"
      version = "~> 6.28"
    }
  }
}

provider "aws" {
  region = "eu-central-1"

  default_tags {
    tags = {
      App = var.app
      GitRepo = var.git-repo
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
