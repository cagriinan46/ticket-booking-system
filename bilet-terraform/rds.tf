resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "ticket-rds-subnet-group"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "Ticket DB Subnet Group"
  }
}

resource "aws_db_instance" "ticket_postgres" {
  identifier        = "ticket-system-db"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  db_name  = "ticket_db"
  username = "db_admin"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible = false
  skip_final_snapshot = true

  tags = {
    Project     = "Ticket-Web-App"
    Environment = "Dev"
  }
}

output "rds_endpoint" {
  description = "database connection address"
  value       = aws_db_instance.ticket_postgres.endpoint
}