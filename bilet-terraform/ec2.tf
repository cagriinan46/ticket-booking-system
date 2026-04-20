resource "aws_iam_role" "ec2_role" {
  name = "ticket-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "sqs_full_access" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

resource "aws_iam_role_policy_attachment" "ses_full_access" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSESFullAccess"
}

resource "aws_iam_role_policy_attachment" "ssm_policy_attach" {
  role       = aws_iam_role.ec2_role.name 
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ticket-ec2-instance-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_instance" "producer_api" {
  ami                    = "ami-014f11e8c26ed3e15"
  instance_type          = "t3.micro"
  subnet_id              = module.vpc.private_subnets[0]
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = <<-EOF
  #!/bin/bash
  dnf update -y
  dnf install -y python3-pip git

  git clone https://github.com/cagriinan46/ticket-booking-system.git /home/ec2-user/app
  cd /home/ec2-user/app/bilet-backend
  
  python3 -m venv venv
  ./venv/bin/pip install -r requirements.txt

  cat <<'EOT' > /home/ec2-user/app/bilet-backend/.env
  DATABASE_URL="postgresql://db_admin:${var.db_password}@${aws_db_instance.ticket_postgres.address}:5432/ticket_db"
  SQS_URL="${aws_sqs_queue.ticket_queue.url}"
  IYZICO_API_KEY="${var.iyzico_api_key}"
  IYZICO_SECRET_KEY="${var.iyzico_secret_key}"
  IYZICO_BASE_URL="sandbox-api.iyzipay.com"
  SENDER_MAIL="${var.sender_mail}"
  SENDER_APP_PASSWORD="${var.sender_app_password}"
  OAUTH2_SECRET_KEY="${var.oauth2_secret_key}"
  EOT

  cat <<'EOT' > /etc/systemd/system/ticket-producer.service
  [Unit]
  Description=Ticket Producer API Service
  After=network.target

  [Service]
  EnvironmentFile=/home/ec2-user/app/bilet-backend/.env
  User=ec2-user
  WorkingDirectory=/home/ec2-user/app/bilet-backend
  ExecStart=/home/ec2-user/app/bilet-backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
  Restart=always

  [Install]
  WantedBy=multi-user.target
  EOT

  echo "Producer API hazir!" > /home/ec2-user/status.txt

  chown -R ec2-user:ec2-user /home/ec2-user/app

  systemctl daemon-reload
  systemctl enable ticket-producer
  systemctl start ticket-producer
  EOF

  tags = { Name = "Ticket-Producer-API" }
}

resource "aws_instance" "consumer_worker" {
  ami                    = "ami-014f11e8c26ed3e15"
  instance_type          = "t3.micro"
  subnet_id              = module.vpc.private_subnets[1]
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = <<-EOF
  #!/bin/bash
  dnf update -y
  dnf install -y python3-pip git

  git clone https://github.com/cagriinan46/ticket-booking-system.git /home/ec2-user/app
  cd /home/ec2-user/app/bilet-backend
  
  python3 -m venv venv
  ./venv/bin/pip install -r requirements.txt

  cat <<'EOT' > /home/ec2-user/app/bilet-backend/.env
  DATABASE_URL="postgresql://db_admin:${var.db_password}@${aws_db_instance.ticket_postgres.address}:5432/ticket_db"
  SQS_URL="${aws_sqs_queue.ticket_queue.url}"
  IYZICO_API_KEY="${var.iyzico_api_key}"
  IYZICO_SECRET_KEY="${var.iyzico_secret_key}"
  IYZICO_BASE_URL="sandbox-api.iyzipay.com"
  SENDER_MAIL="${var.sender_mail}"
  SENDER_APP_PASSWORD="${var.sender_app_password}"
  OAUTH2_SECRET_KEY="${var.oauth2_secret_key}"
  EOT

  cat <<'EOT' > /etc/systemd/system/ticket-consumer.service
  [Unit]
  Description=Ticket Consumer Worker Service
  After=network.target

  [Service]
  EnvironmentFile=/home/ec2-user/app/bilet-backend/.env
  User=ec2-user
  WorkingDirectory=/home/ec2-user/app/bilet-backend
  ExecStart=/home/ec2-user/app/bilet-backend/venv/bin/python worker.py
  Restart=always

  [Install]
  WantedBy=multi-user.target
  EOT
  
  echo "Worker hazir!" > /home/ec2-user/status.txt

  chown -R ec2-user:ec2-user /home/ec2-user/app

  systemctl daemon-reload
  systemctl enable ticket-consumer
  systemctl start ticket-consumer
  EOF

  tags = { Name = "Ticket-Worker-Consumer" }
}