locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = "CloudShop Enterprise"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
