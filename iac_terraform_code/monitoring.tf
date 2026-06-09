# helm package manager
provider "helm" {
    kubernetes {
        host = azurerm_kubernetes_cluster.khudse_aks.kube_config[0].host
        client_certificate = base64decode(azurerm_kubernetes_cluster.khudse_aks.kube_config[0].client_certificate)
        client_key = base64decode(azurerm_kubernetes_cluster.khudse_aks.kube_config[0].client_key)
        cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.khudse_aks.kube_config[0].cluster_ca_certificate)
    }
}


# monitoring stack deployment
resource "helm_release" "prometheus" {
    name = "prometheus-stack"
    repository = "https://prometheus-community.github.io/helm-charts"
    chart = "kube-prometheus-stack"
    namespace = "monitoring"
    create_namespace = true

    # ensuring the cluster exists before trying to install software onto it
    depends_on = [azurerm_kubernetes_cluster.khudse_aks]
}