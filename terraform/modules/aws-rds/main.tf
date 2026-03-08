# AWS RDS Module
# Reutilizável para PostgreSQL, MySQL, MariaDB, SQL Server

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.identifier}-subnet-group"
  subnet_ids = var.db_subnet_ids

  tags = merge(var.tags, { Name = "${var.identifier}-subnet-group" })
}

# DB Parameter Group
resource "aws_db_parameter_group" "main" {
  family = var.parameter_group_family
  name   = "${var.identifier}-params"

  dynamic "parameter" {
    for_each = var.parameters
    content {
      name  = parameter.key
      value = parameter.value
    }
  }

  tags = merge(var.tags, { Name = "${var.identifier}-params" })

  lifecycle {
    create_before_destroy = true
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier     = var.identifier
  db_name        = var.environment == "production" ? var.database_name : "${var.database_name}_${var.environment}"
  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class
  
  allocated_storage     = var.allocated_storage
  storage_type          = var.storage_type
  storage_encrypted     = var.storage_encrypted
  iops                  = var.iops
  
  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = var.vpc_security_group_ids
  parameter_group_name            = aws_db_parameter_group.main.name
  publicly_accessible             = var.publicly_accessible
  
  username               = var.master_username
  password               = var.master_password
  port                   = var.db_port
  
  multi_az               = var.multi_az
  backup_retention_period = var.backup_retention_days
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window
  copy_tags_to_snapshot  = true
  
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.identifier}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  enabled_cloudwatch_logs_exports = var.enabled_cloudwatch_logs_exports
  
  enable_iam_database_authentication = var.enable_iam_database_authentication
  enable_storage_autoscaling        = var.enable_storage_autoscaling
  max_allocated_storage             = var.max_allocated_storage
  
  deletion_protection = var.deletion_protection
  
  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_retention_period = var.performance_insights_retention_days
  
  monitoring_interval             = var.enable_enhanced_monitoring ? var.monitoring_interval : 0
  monitoring_role_arn             = var.enable_enhanced_monitoring ? aws_iam_role.monitoring_role[0].arn : null
  enable_performance_insights     = var.performance_insights_enabled
  
  tags = merge(var.tags, { Name = var.identifier })

  depends_on = [aws_db_subnet_group.main, aws_db_parameter_group.main]

  lifecycle {
    ignore_changes = [password]
  }
}

# Enhanced Monitoring IAM Role
resource "aws_iam_role" "monitoring_role" {
  count = var.enable_enhanced_monitoring ? 1 : 0
  name  = "${var.identifier}-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "monitoring.rds.amazonaws.com"
      }
    }]
  })

  tags = merge(var.tags, { Name = "${var.identifier}-monitoring-role" })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring_policy" {
  count      = var.enable_enhanced_monitoring ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  role       = aws_iam_role.monitoring_role[0].name
}

# Optional: DB Proxy para connection pooling
resource "aws_db_proxy" "main" {
  count                  = var.enable_db_proxy ? 1 : 0
  name                   = "${var.identifier}-proxy"
  engine_family          = upper(var.engine)
  auth {
    auth_scheme = "SECRETS"
    secret_arn  = aws_secretsmanager_secret.db_credentials[0].arn
  }
  role_arn               = aws_iam_role.proxy_role[0].arn
  db_subnet_group_names  = [aws_db_subnet_group.main.name]
  target_db_resource_identifier = [aws_db_instance.main.arn]
  require_tls            = true
  max_idle_connections_percent = 50
  connection_borrow_timeout    = 120
  
  tags = merge(var.tags, { Name = "${var.identifier}-proxy" })
}

# Secrets Manager for DB credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  count                   = var.enable_db_proxy ? 1 : 0
  name                    = "${var.identifier}-credentials"
  description             = "RDS credentials for ${var.identifier}"
  recovery_window_in_days = 7

  tags = merge(var.tags, { Name = "${var.identifier}-credentials" })
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  count         = var.enable_db_proxy ? 1 : 0
  secret_id     = aws_secretsmanager_secret.db_credentials[0].id
  secret_string = jsonencode({
    username = var.master_username
    password = var.master_password
    dbname   = aws_db_instance.main.db_name
    engine   = var.engine
    host     = aws_db_instance.main.endpoint
    port     = var.db_port
  })
}

# DB Proxy IAM Role
resource "aws_iam_role" "proxy_role" {
  count = var.enable_db_proxy ? 1 : 0
  name  = "${var.identifier}-proxy-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "rds.amazonaws.com"
      }
    }]
  })

  tags = merge(var.tags, { Name = "${var.identifier}-proxy-role" })
}

resource "aws_iam_role_policy" "proxy_secrets_policy" {
  count = var.enable_db_proxy ? 1 : 0
  name  = "${var.identifier}-proxy-secrets-policy"
  role  = aws_iam_role.proxy_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ]
      Resource = aws_secretsmanager_secret.db_credentials[0].arn
    }]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.identifier}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.cpu_threshold
  alarm_description   = "Alert when RDS CPU exceeds ${var.cpu_threshold}%"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "database_storage" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.identifier}-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.storage_threshold * 1024 * 1024 * 1024
  alarm_description   = "Alert when free storage < ${var.storage_threshold}GB"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  count               = var.enable_cloudwatch_alarms ? 1 : 0
  alarm_name          = "${var.identifier}-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.max_connections_threshold
  alarm_description   = "Alert when connections exceed ${var.max_connections_threshold}"
  alarm_actions       = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }
}
