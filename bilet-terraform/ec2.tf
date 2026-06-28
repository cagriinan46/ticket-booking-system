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

  git clone --branch ${var.app_branch} --single-branch https://github.com/cagriinan46/ticket-booking-system.git /home/ec2-user/app
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
  OPENWEATHER_API_KEY="${var.openweather_api_key}"
  GEMINI_API_KEY="${var.gemini_api_key}"
  OLLAMA_HOST="http://${aws_instance.ollama_server.private_ip}:11434"
  OLLAMA_MODEL="${var.ollama_model}"
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

  command -v curl >/dev/null 2>&1 || dnf install -y curl-minimal

  OLLAMA_URL="http://${aws_instance.ollama_server.private_ip}:11434"
  OLLAMA_MODEL="${var.ollama_model}"

  echo "Waiting for Ollama model to be ready: $OLLAMA_MODEL"

  for i in $(seq 1 180); do
    if curl -s "$OLLAMA_URL/api/tags" | grep -q "$OLLAMA_MODEL"; then
      echo "Ollama model is ready: $OLLAMA_MODEL"
      break
    fi

    if [ "$i" -eq 180 ]; then
      echo "Ollama model was not ready after 30 minutes. Exiting."
      exit 1
    fi

    echo "Still waiting for Ollama model: $OLLAMA_MODEL"
    sleep 10
  done

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

  git clone --branch ${var.app_branch} --single-branch https://github.com/cagriinan46/ticket-booking-system.git /home/ec2-user/app
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
  OPENWEATHER_API_KEY="${var.openweather_api_key}"
  GEMINI_API_KEY="${var.gemini_api_key}"
  OLLAMA_HOST="http://${aws_instance.ollama_server.private_ip}:11434"
  OLLAMA_MODEL="${var.ollama_model}"
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

resource "aws_instance" "ollama_server" {
  ami                    = "ami-014f11e8c26ed3e15"
  instance_type          = var.ollama_instance_type
  subnet_id              = module.vpc.private_subnets[0]
  vpc_security_group_ids = [aws_security_group.ollama_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = <<-EOF
  #!/bin/bash
  set -e

  exec > >(tee /var/log/ollama-user-data.log | logger -t ollama-user-data -s 2>/dev/console) 2>&1

  MODEL="${var.ollama_model}"

  echo "Starting Ollama setup"
  echo "Target model: $MODEL"

  export HOME=/root
  export PATH=/usr/local/bin:/usr/bin:/bin:$PATH

  dnf update -y
  command -v curl >/dev/null 2>&1 || dnf install -y curl-minimal

  curl -fsSL https://ollama.com/install.sh | sh

  mkdir -p /etc/systemd/system/ollama.service.d

  cat <<'EOT' > /etc/systemd/system/ollama.service.d/override.conf
  [Service]
  Environment="OLLAMA_HOST=0.0.0.0:11434"
  Environment="HOME=/usr/share/ollama"
  EOT

  systemctl daemon-reload
  systemctl enable ollama
  systemctl restart ollama

  echo "Waiting for Ollama API..."

  for i in $(seq 1 60); do
    if curl -s http://localhost:11434/api/tags >/dev/null; then
      echo "Ollama API is ready"
      break
    fi

    if [ "$i" -eq 60 ]; then
      echo "Ollama API did not become ready"
      exit 1
    fi

    sleep 5
  done

  echo "Cleaning possible broken partial model files"
  rm -rf /usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library/qwen2.5 || true
  find /usr/share/ollama/.ollama/models/blobs -type f -name "*partial*" -delete || true

  echo "Pulling model through Ollama API: $MODEL"

  for attempt in $(seq 1 3); do
    echo "Model pull attempt $attempt"

    if curl -sS --fail --max-time 1800 http://localhost:11434/api/pull \
      -H "Content-Type: application/json" \
      -d "{\"name\":\"$MODEL\",\"stream\":false}"; then
      echo "Model pull succeeded"
      break
    fi

    echo "Model pull failed on attempt $attempt"

    rm -rf /usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library/qwen2.5 || true
    find /usr/share/ollama/.ollama/models/blobs -type f -name "*partial*" -delete || true

    sleep 15

    if [ "$attempt" -eq 3 ]; then
      echo "Model pull failed after 3 attempts"
      exit 1
    fi
  done

  echo "Checking installed models"

  if ! curl -s http://localhost:11434/api/tags | grep -q "$MODEL"; then
    echo "Model is still missing after pull: $MODEL"
    curl -s http://localhost:11434/api/tags
    exit 1
  fi

  echo "Warming up model"

  curl -sS --fail --max-time 600 http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$MODEL\",\"prompt\":\"OK\",\"stream\":false,\"keep_alive\":\"30m\",\"options\":{\"num_predict\":1}}"

  echo "Ollama server hazir! Model: $MODEL" > /home/ec2-user/ollama-status.txt
  echo "Ollama setup completed successfully"
  EOF

  tags = {
    Name = "Ticket-Ollama-Server"
  }
}