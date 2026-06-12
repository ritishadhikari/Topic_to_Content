variable "aws_region" {
  description = "The AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "The base name for all your AWS resources"
  type        = string
  default     = "khudse-kubernetes"
}

variable "instance_type" {
  description = "The EC2 instance type (Hardware Profile)"
  type        = string
  default     = "t3a.medium"
}