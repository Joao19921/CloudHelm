variable "provider" {
  type = string
}

variable "app_name" {
  type = string
}

resource "terraform_data" "observability" {
  input = {
    provider = var.provider
    app_name = var.app_name
  }
}

output "monitoring_stack" {
  value = "monitoring-${var.provider}"
}
