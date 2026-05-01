resource "aws_lb" "ticket_alb" {
  name               = "ticket-app-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = module.vpc.public_subnets

  tags = {
    Project     = "Ticket-Web-App"
    Environment = "Dev"
    ManagedBy   = "Terraform"
  }
}

resource "aws_lb_target_group" "ticket_tg" {
  name     = "ticket-target-group"
  port     = 80
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30
  }
}

resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.ticket_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ticket_tg.arn
  }
}

resource "aws_lb_target_group_attachment" "backend_attachment" {
  target_group_arn = aws_lb_target_group.ticket_tg.arn
  target_id        = aws_instance.producer_api.id
  port             = 8000
}

output "alb_dns_name" {
  description = "the url address where the ticket website is published"
  value       = aws_lb.ticket_alb.dns_name
}