variable "cluster_name" {
  description = "Nome do cluster EKS"
  type        = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+$", var.cluster_name))
    error_message = "Nome do cluster deve conter apenas letras, números, hífens e underscores."
  }
}

variable "kubernetes_version" {
  description = "Versão do Kubernetes"
  type        = string
  default     = "1.29"
}

variable "vpc_id" {
  description = "ID da VPC onde o cluster será criado"
  type        = string
}

variable "subnet_ids" {
  description = "IDs das subnets para o cluster (mínimo 2 em AZs diferentes)"
  type        = list(string)
  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "Pelo menos 2 subnets são obrigatórias."
  }
}

variable "endpoint_private_access" {
  description = "Habilitar acesso privado ao endpoint da API"
  type        = bool
  default     = true
}

variable "endpoint_public_access" {
  description = "Habilitar acesso público ao endpoint da API"
  type        = bool
  default     = true
}

variable "enabled_cluster_log_types" {
  description = "Tipos de logs para habilitar no CloudWatch"
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
}

variable "node_groups" {
  description = "Configuração dos node groups"
  type = map(object({
    desired_size    = number
    min_size        = number
    max_size        = number
    max_unavailable = number
    instance_types  = list(string)
    disk_size       = number
    capacity_type   = string
    labels          = map(string)
  }))
  default = {
    general = {
      desired_size    = 2
      min_size        = 1
      max_size        = 10
      max_unavailable = 1
      instance_types  = ["t3.medium"]
      disk_size       = 20
      capacity_type   = "ON_DEMAND"
      labels = {
        workload = "general"
      }
    }
  }
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Tags para aplicar em todos os recursos"
  type        = map(string)
  default     = {}
}

variable "enable_irsa" {
  description = "Habilitar IRSA (IAM Roles for Service Accounts)"
  type        = bool
  default     = true
}

variable "enable_cluster_autoscaling" {
  description = "Habilitar auto-scaling de cluster"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Dias de retenção para logs do CloudWatch"
  type        = number
  default     = 7
}

variable "create_launch_template" {
  description = "Criar launch template customizado para nodes"
  type        = bool
  default     = false
}

variable "ami_id" {
  description = "AMI ID customizada (deixe vazio para usar padrão)"
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "Tipo de instância (se criar launch template)"
  type        = string
  default     = "t3.medium"
}

variable "volume_size" {
  description = "Tamanho do volume EBS em GB"
  type        = number
  default     = 20
}

variable "volume_type" {
  description = "Tipo de volume EBS"
  type        = string
  default     = "gp3"
}

variable "volume_encrypted" {
  description = "Criptografar volumes EBS"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Habilitar CloudWatch detailed monitoring"
  type        = bool
  default     = false
}

variable "user_data" {
  description = "Script de user data para nodes"
  type        = string
  default     = ""
}
