locals {
  app_name_dashed = "${var.customer}-${var.environment}"
  #
  aws_profile = "${var.customer}-${var.environment}"
  #
  tags = {
    application_name = local.app_name_dashed
    environment      = var.environment
    provisioner      = "terraform"
  }
}