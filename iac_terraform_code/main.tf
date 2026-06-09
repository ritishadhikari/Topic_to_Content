# resource group
resource "azurerm_resource_group" "khudse_rg" {
    name = var.resource_group_name
    location = var.location
}

# kubernetes cluster
resource "azurerm_kubernetes_cluster" "khudse_aks" {
    name = var.cluster_name
    location = azurerm_resource_group.khudse_rg.location
    resource_group_name = azurerm_resource_group.khudse_rg.name
    dns_prefix = var.dns_prefix

    # worker nodes
    default_node_pool {
        name = "default"
        node_count = var.node_count
        vm_size = var.vm_size
    }

    # cluster authentication
    identity {
        type = "SystemAssigned"
    }

    # internal routing topology
    network_profile {
        network_plugin = "kubenet"
    }
}
