variable "project_name" {
  type = string
}

variable "provider" {
  type = string
}

resource "terraform_data" "network" {
  input = {
    name     = "${var.project_name}-network"
    provider = var.provider
  }
}

output "network_id" {
  value = terraform_data.network.id
}
