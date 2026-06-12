# random token for cluster authentication
resource "random_password" "k3s_token" {
  length  = 32
  special = false
}

# virtual private cloud
resource "aws_vpc" "k3s_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.project_name}-vpc" }
}

# internet gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.k3s_vpc.id
  tags   = { Name = "${var.project_name}-igw" }
}

# public subnet with in the vpc
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.k3s_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project_name}-subnet" }
}

# create the route table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.k3s_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

# associate the route table
resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# the security group
resource "aws_security_group" "k3s_sg" {
  name        = "${var.project_name}-sg"
  description = "Allow inbound traffic for K3s, SSH, HTTP/HTTPS and Internal VPC"
  vpc_id      = aws_vpc.k3s_vpc.id

  # Allow all internal commununications between Master and Worker (Flannel, Kubelet etc.)
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.k3s_vpc.cidr_block]
  }

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP web traffic access
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS web traffic access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Kubernetes API
  ingress {
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # outboud traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# find latest Ubuntu Image
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}


# Control Plane (master node)
resource "aws_instance" "k3s_master" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = "k3s-cluster-key"
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.k3s_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              #  Install K3s as a Master Node with the generated token
              curl -sfL https://get.k3s.io | K3S_TOKEN=${random_password.k3s_token.result} sh -

              sleep 15
              chmod 644 /etc/rancher/k3s/k3s.yaml
              EOF

  tags = { Name = "${var.project_name}-master" }
}



# Data Plane (worker node)
resource "aws_instance" "k3s_worker" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = "k3s-cluster-key"
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.k3s_sg.id]

  depends_on = [aws_instance.k3s_master]

  user_data = <<-EOF
               #!/bin/bash
               # master node should boot up
               sleep 30
               
               # Install K3s as a worker node (agent)
               curl -sfL https://get.k3s.io | K3S_URL=https://${aws_instance.k3s_master.private_ip}:6443 K3S_TOKEN=${random_password.k3s_token.result} sh - 
               EOF
  tags      = { Name = "${var.project_name}-worker" }
}

# outputs for the master node
output "master_public_ip" {
  description = "The Public IP of the Master Node (Required for Kubectl and SSH)"
  value       = aws_instance.k3s_master.public_ip
}

# outputs for the worker node
output "worker_public_ip" {
  description = "The Public IP of the worker node"
  value       = aws_instance.k3s_worker.public_ip
}