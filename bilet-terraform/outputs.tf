output "vpc_id" {
  description = "the id of the created vpc"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "public subnet ids"
  value       = module.vpc.public_subnets
}

output "private_subnet_ids" {
  description = "private subnet ids"
  value       = module.vpc.private_subnets
}

output "ollama_private_ip" {
  description = "Private IP address of the Ollama server"
  value       = aws_instance.ollama_server.private_ip
}

output "ollama_host" {
  description = "Ollama host URL for backend"
  value       = "http://${aws_instance.ollama_server.private_ip}:11434"
}