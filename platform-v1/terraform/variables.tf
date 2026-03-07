variable "provider" {
  type        = string
  description = "Cloud provider: aws, gcp, azure"
  validation {
    condition     = contains(["aws", "gcp", "azure"], var.provider)
    error_message = "Provider must be one of: aws, gcp, azure."
  }
}

variable "project_name" {
  type        = string
  description = "Project logical name."
}
