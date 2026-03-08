output "db_instance_id" {
  description = "ID identificador do database"
  value       = aws_db_instance.main.id
}

output "db_instance_arn" {
  description = "ARN do database"
  value       = aws_db_instance.main.arn
}

output "db_instance_endpoint" {
  description = "Endpoint do database (host:port)"
  value       = aws_db_instance.main.endpoint
}

output "db_instance_address" {
  description = "Endereço do database"
  value       = aws_db_instance.main.address
}

output "db_instance_port" {
  description = "Porta do database"
  value       = aws_db_instance.main.port
}

output "db_instance_resource_id" {
  description = "Resource ID do database"
  value       = aws_db_instance.main.resource_id
}

output "db_instance_status" {
  description = "Status do database"
  value       = aws_db_instance.main.db_instance_status
}

output "db_name" {
  description = "Nome do database"
  value       = aws_db_instance.main.db_name
}

output "db_username" {
  description = "Usuário master"
  value       = aws_db_instance.main.username
}

output "db_engine" {
  description = "Engine do database"
  value       = aws_db_instance.main.engine
}

output "db_engine_version" {
  description = "Versão do engine"
  value       = aws_db_instance.main.engine_version
}

output "db_proxy_endpoint" {
  description = "Endpoint do RDS Proxy (se habilitado)"
  value       = var.enable_db_proxy ? aws_db_proxy.main[0].endpoint : null
}

output "db_parameter_group_id" {
  description = "ID do parameter group"
  value       = aws_db_parameter_group.main.id
}

output "db_subnet_group_id" {
  description = "ID do DB subnet group"
  value       = aws_db_subnet_group.main.id
}

output "secrets_manager_secret_arn" {
  description = "ARN do secret no Secrets Manager (se proxy habilitado)"
  value       = var.enable_db_proxy ? aws_secretsmanager_secret.db_credentials[0].arn : null
}

output "connection_string_psql" {
  description = "Connection string para psql"
  value = var.engine == "postgres" ? format(
    "psql -h %s -U %s -d %s -p %d",
    aws_db_instance.main.address,
    aws_db_instance.main.username,
    aws_db_instance.main.db_name,
    aws_db_instance.main.port
  ) : null
}

output "connection_string_mysql" {
  description = "Connection string para mysql"
  value = contains(["mysql", "mariadb"], var.engine) ? format(
    "mysql -h %s -u %s -p -P %d %s",
    aws_db_instance.main.address,
    aws_db_instance.main.username,
    aws_db_instance.main.port,
    aws_db_instance.main.db_name
  ) : null
}

output "jdbc_connection_string" {
  description = "JDBC URL para aplicações Java"
  value = format(
    "jdbc:%s://%s:%d/%s",
    var.engine == "postgres" ? "postgresql" : var.engine,
    aws_db_instance.main.address,
    aws_db_instance.main.port,
    aws_db_instance.main.db_name
  )
}
