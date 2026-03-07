variable "provider" {
  type = string
}

variable "app_name" {
  type = string
}

resource "terraform_data" "security" {
  input = {
    provider = var.provider
    app_name = var.app_name
  }
}

output "security_profile" {
  value = "baseline-rbac-audit"
}
