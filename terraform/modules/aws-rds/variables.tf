variable "identifier" {
  description = "Nome identificador da instância RDS"
  type        = string
}

variable "engine" {
  description = "Engine do banco de dados (postgres, mysql, mariadb, sqlserver)"
  type        = string
  validation {
    condition     = contains(["postgres", "mysql", "mariadb", "sqlserver"], var.engine)
    error_message = "Engine deve ser postgres, mysql, mariadb ou sqlserver."
  }
}

variable "engine_version" {
  description = "Versão do engine"
  type        = string
}

variable "parameter_group_family" {
  description = "Familia do parameter group (ex: postgres15, mysql8.0)"
  type        = string
}

variable "instance_class" {
  description = "Classe da instância (ex: db.t4g.micro, db.r6i.xlarge)"
  type        = string
}

variable "allocated_storage" {
  description = "Storage inicial em GB"
  type        = number
  validation {
    condition     = var.allocated_storage >= 20
    error_message = "Storage mínimo é 20 GB."
  }
}

variable "max_allocated_storage" {
  description = "Storage máximo para auto-scaling em GB"
  type        = number
}

variable "storage_type" {
  description = "Tipo de storage (gp3, gp2, io1, io2)"
  type        = string
  default     = "gp3"
}

variable "storage_encrypted" {
  description = "Criptografar storage"
  type        = bool
  default     = true
}

variable "iops" {
  description = "IOPS para io1/io2"
  type        = number
  default     = 3000
}

variable "database_name" {
  description = "Nome do database inicial"
  type        = string
}

variable "master_username" {
  description = "Usuário master do database"
  type        = string
  sensitive   = true
}

variable "master_password" {
  description = "Senha do usuário master"
  type        = string
  sensitive   = true
}

variable "db_port" {
  description = "Porta do database"
  type        = number
  default     = 5432 # PostgreSQL default
}

variable "db_subnet_ids" {
  description = "IDs das subnets para DB Subnet Group"
  type        = list(string)
  validation {
    condition     = length(var.db_subnet_ids) >= 2
    error_message = "Mínimo 2 subnets são obrigatórias."
  }
}

variable "vpc_security_group_ids" {
  description = "IDs dos security groups"
  type        = list(string)
}

variable "multi_az" {
  description = "Deploy em múltiplas AZs"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Dias de retenção de backups"
  type        = number
  default     = 30
}

variable "backup_window" {
  description = "Janela de backup (UTC, ex: 03:00-04:00)"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Janela de manutenção (ex: sun:04:00-sun:05:00)"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "publicly_accessible" {
  description = "Permitir acesso público"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Proteção contra exclusão"
  type        = bool
  default     = true
}

variable "skip_final_snapshot" {
  description = "Pular snapshot final ao deletar"
  type        = bool
  default     = false
}

variable "environment" {
  description = "Ambiente (dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "parameters" {
  description = "Parâmetros customizados para parameter group"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags para aplicar em todos os recursos"
  type        = map(string)
  default     = {}
}

variable "enable_iam_database_authentication" {
  description = "Habilitar autenticação IAM"
  type        = bool
  default     = true
}

variable "enable_storage_autoscaling" {
  description = "Habilitar auto-scaling de storage"
  type        = bool
  default     = true
}

variable "enable_enhanced_monitoring" {
  description = "Habilitar enhanced monitoring"
  type        = bool
  default     = true
}

variable "monitoring_interval" {
  description = "Intervalo de monitoramento (0, 1, 5, 10, 15, 30, 60)"
  type        = number
  default     = 60
}

variable "performance_insights_enabled" {
  description = "Habilitar Performance Insights"
  type        = bool
  default     = true
}

variable "performance_insights_retention_days" {
  description = "Dias de retenção do Performance Insights"
  type        = number
  default     = 7
}

variable "enabled_cloudwatch_logs_exports" {
  description = "Tipos de logs para exportar (postgresql, error, general, slowquery)"
  type        = list(string)
  default     = []
}

variable "enable_db_proxy" {
  description = "Habilitar RDS Proxy para connection pooling"
  type        = bool
  default     = false
}

variable "enable_cloudwatch_alarms" {
  description = "Habilitar CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alarm_sns_topic_arn" {
  description = "ARN do tópico SNS para alertas"
  type        = string
  default     = ""
}

variable "cpu_threshold" {
  description = "Threshold de CPU em % para alerta"
  type        = number
  default     = 80
}

variable "storage_threshold" {
  description = "Threshold de storage livre em GB para alerta"
  type        = number
  default     = 10
}

variable "max_connections_threshold" {
  description = "Threshold de conexões para alerta"
  type        = number
  default     = 80
}
