resource "aws_sqs_queue" "ticket_queue" {
  name                      = "ticket-order-queue"
  delay_seconds             = 0
  max_message_size          = 262144 # 256 KB
  message_retention_seconds = 345600 # 4 Days

  receive_wait_time_seconds = 10 # long polling

  tags = {
    Project     = "Ticket-Web-App"
    Environment = "Dev"
    ManagedBy   = "Terraform"
  }
}

output "sqs_queue_url" {
  description = "ticket order queue url"
  value       = aws_sqs_queue.ticket_queue.id
}