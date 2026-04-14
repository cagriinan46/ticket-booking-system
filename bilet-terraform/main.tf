module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.6.0"

  name = var.vpc_name
  cidr = var.vpc_cidr

  azs             = var.azs
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway = true
  single_nat_gateway = true

  # This is a requirement for EC2 and databases to communicate using their names within AWS.
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Project     = "Ticket-Web-App"
    Environment = "Dev"
    ManagedBy   = "Terraform"
  }
}