#### terraform variables

variable "environment" {}
variable "customer" {}
variable "region" {}

#Name for the lambda excecution role
variable "lambda_role_name" {
  type    = string
  default = "lambda_role_name"
}

#Map with the lambda funtions to be deployed
variable "lambda_deploy" {
  type    = map(any)
  default = {}
}

#Region where are the main aws services
variable "main_region" {
  type    = string
  default = "us-east-1"
}

#Map of tags to add to all created resources
variable "default_tags" {
  type    = map(string)
  default = {}
}

variable "aws_account" {
  type = string
}

######### python variables

variable "SENDER" {
  type = string
}

variable "RECIPIENTS" {
  type = string
}

variable "lambda_defaults" {
  type = map(string)
}
