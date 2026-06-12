# plugins download
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# provider activation
provider "aws" {
  region = var.aws_region
}