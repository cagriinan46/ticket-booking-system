variable "aws_region" {
  description = "the aws region we will be working in"
  default     = "eu-central-1"
}

variable "vpc_name" {
  description = "the name of the vpc"
  default     = "bilet-vpc"
}

variable "vpc_cidr" {
  description = "vpc main ip block"
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "availability zones to be used"
  default     = ["eu-central-1a", "eu-central-1b"]
}

variable "public_subnets" {
  description = "public subnets ip blocks"
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  description = "private subnets ip blocks"
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "db_password" {
  description = "database password"
  type        = string
  sensitive   = true
}

variable "iyzico_api_key" { type = string }
variable "iyzico_secret_key" { type = string }
variable "sender_mail" { type = string }
variable "sender_app_password" { type = string }
variable "oauth2_secret_key" { type = string }