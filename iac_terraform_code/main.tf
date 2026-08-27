# random token for cluster authentication
resource "random_password" "k3s_token" {
  length  = 32
  special = false
}

# virtual private cloud
resource "aws_vpc" "khudse_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.project_name}-vpc" }
}

# internet gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.khudse_vpc.id
  tags   = { Name = "${var.project_name}-igw" }
}

# public subnet with in the vpc
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.khudse_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project_name}-subnet" }
}

# By default, AWS creates a hidden, internal-only route table for your VPC that says: "If a server is trying to talk to another server inside the 10.0.0.0/16 network, allow it. If it tries to talk to anything else, drop the traffic."
# This block overrides that default behavior. It explicitly tells your network: "If a server asks to connect to an IP address that isn't inside our private network (0.0.0.0/0), don't drop the traffic—forward it out the Internet Gateway door."
# create the route table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.khudse_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

# associate the route table
resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id  # who gets the rules
  route_table_id = aws_route_table.public_rt.id  # what rules apply
}

# the security group
resource "aws_security_group" "khudse_sg" {
  name        = "${var.project_name}-sg"
  description = "Allow inbound traffic for K3s, SSH, HTTP/HTTPS and Internal VPC"
  vpc_id      = aws_vpc.khudse_vpc.id

  # Allow all internal commununications between Master and Worker (Flannel, Kubelet etc.)
  # specially for the internal servers living inside the private AWS network, allowing constantly talk among them each other
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"  # allows all protocols - TCP, UDP, ICMP, etc
    cidr_blocks = [aws_vpc.khudse_vpc.cidr_block]  # all the ip address can access within the VPC
  }

  # SSH access
  ingress {
    from_port   = 22  # all ports has the connectivity to and from
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # allows traffic from anywhere on the internet
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
    cidr_blocks = ["0.0.0.0/0"]  # allows to manage clusters remotely from local laptop using kubectl
  }

  # If a hacker on the public internet (0.0.0.0/0) tries to access a sensitive internal Kubernetes port on your server (like port 2379), AWS checks the rules:
  # Does the hacker match aws_vpc.khudse_vpc.cidr_block? No.
  # Does the hacker match 0.0.0.0/0 on port 80? No.
  # Does the hacker match 0.0.0.0/0 on port 22? No.
  # Because no rule matches, the traffic is dropped. The hacker is kept out, but your worker nodes can still communicate on port 2379 because they match the first internal rule.

  # outbound traffic
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
  key_name               = "k3s-cluster-key"  # required for ssh and scp purpose to the nodes
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.khudse_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              #  Install K3s as a Master Node with the generated token
              # Requires for locking the master node with the worker node
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
  vpc_security_group_ids = [aws_security_group.khudse_sg.id]

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