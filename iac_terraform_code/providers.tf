# plugins download
terraform {
    required_providers {
        azurerm = {
            source = "hashicorp/azurerm"
            version = "~> 4.76"
        }
        helm = {
            source = "hashicorp/helm"
            version = "~>3.0" 
        }
    }
}

# provider activation
provider "azurerm" {
    features {}
    # version 4 requirements
    subscription_id="18a1f27f-edf5-495e-9acb-753c93335294"
}