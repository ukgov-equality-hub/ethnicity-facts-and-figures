
terraform {
  required_version = ">= 1.6.2"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.23"
    }
  }

  backend "s3" {}
}

provider "aws" {
  region = var.aws_region // no alias is provided so will be used as default

  default_tags {
    tags = {
      Service = var.service_name
      Environment = var.environment
    }
  }
}

provider "aws" { // This us-east-1 provider is needed for CloudFront (which we might use in future)
  region = "us-east-1"
  alias = "us-east-1"

  default_tags {
    tags = {
      Service = var.service_name
      Environment = var.environment
    }
  }
}
