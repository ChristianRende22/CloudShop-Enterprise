terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# WAFv2 con scope CLOUDFRONT debe crearse SIEMPRE en us-east-1, sin importar
# la region del resto de la infraestructura. Se usa este provider aliaseado
# solo para el WebACL (ver waf.tf).
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
