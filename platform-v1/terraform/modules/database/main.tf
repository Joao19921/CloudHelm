variable "db_name" {
  type = string
}

variable "provider" {
  type = string
}

variable "network_id" {
  type = string
}

resource "terraform_data" "database" {
  input = {
    db_name    = var.db_name
    provider   = var.provider
    network_id = var.network_id
  }
}

output "endpoint" {
  value = "${var.db_name}.${var.provider}.db.local"
}
