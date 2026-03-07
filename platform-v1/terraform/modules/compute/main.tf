variable "app_name" {
  type = string
}

variable "provider" {
  type = string
}

variable "network_id" {
  type = string
}

resource "terraform_data" "compute" {
  input = {
    app_name   = var.app_name
    provider   = var.provider
    network_id = var.network_id
  }
}

output "endpoint" {
  value = "${var.app_name}.${var.provider}.local"
}
