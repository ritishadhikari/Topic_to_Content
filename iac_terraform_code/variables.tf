# base azure settings
variable "resource_group_name" {
    type = string
    description = "The name of the Azure Resource Group"
    default = "khudse-rg"
}

variable "location" {
    type = string
    description = "The Azure region to deploy into"
    default="East US"  # the cheapest cluster
}

# kubernetes cluster settings
variable "cluster_name" {
    type = string
    description = "The name of the AKS cluster"
    default = "khudse-cluster"
}

variable "dns_prefix" {
    type = string
    description = "DNS prefix for the AKS cluster"
    default = "khudse-dns"
}

variable "node_count" {
    type = number
    description = "The number of worker nodes"
    default = 1
}

variable "vm_size" {
    type = string
    description = "The size of the Virtual Machine."
    default = "Standard_B2s"  # 2 vCPU and 4 GB RAM 

}