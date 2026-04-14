resource "aws_security_group" "alb_sg" {
  name        = "ticket-alb-sg"
  description = "it receives incoming http requests from outside and passes them to the load balancer"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "https for everyone"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ticket-alb-sg"
    Environment = "Dev"
  }
}

resource "aws_security_group" "ec2_sg" {
  name        = "ticket-ec2-sg"
  description = "it only accepts traffic coming from the load balancer"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "http traffic only from alb"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ticket-ec2-sg"
    Environment = "Dev"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "ticket-rds-sg"
  description = "firewall for postgresql database"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "only database connections coming from our vpc"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}