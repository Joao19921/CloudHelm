# AWS RDS Module

Módulo Terraform reutilizável para provisionar instâncias Amazon RDS (Relational Database Service) com suporte a PostgreSQL, MySQL, MariaDB e SQL Server.

## Características

- ✅ **Multi-engine support**: PostgreSQL, MySQL, MariaDB, SQL Server
- ✅ **Multi-AZ deployment** para alta disponibilidade
- ✅ **Auto-scaling de storage** automático
- ✅ **RDS Proxy** para connection pooling
- ✅ **Secrets Manager integration** para gestão de credenciais
- ✅ **Enhanced Monitoring** com CloudWatch
- ✅ **Performance Insights** para análise
- ✅ **CloudWatch Alarms** pré-configurados
- ✅ **IAM Database Authentication**
- ✅ **Backup e restore** com retenção configurável
- ✅ **Encryption** de storage e em trânsito
- ✅ **Parameter Groups** customizável

## Usando o Módulo

### Exemplo Básico PostgreSQL

```hcl
module "postgres" {
  source = "../../modules/aws-rds"

  identifier               = "cloudhelm-postgres"
  engine                   = "postgres"
  engine_version           = "15.3"
  parameter_group_family   = "postgres15"
  instance_class           = "db.t4g.micro"
  allocated_storage        = 20
  max_allocated_storage    = 100
  database_name            = "cloudhelm"
  master_username          = "admin"
  master_password          = var.db_password
  
  db_subnet_ids           = aws_subnet.private[*].id
  vpc_security_group_ids  = [aws_security_group.rds.id]
  
  multi_az                = true
  backup_retention_days   = 30
  environment             = "production"

  tags = {
    Project     = "CloudHelm"
    Environment = "Production"
  }
}
```

### Exemplo MySQL com RDS Proxy

```hcl
module "mysql" {
  source = "../../modules/aws-rds"

  identifier               = "cloudhelm-mysql"
  engine                   = "mysql"
  engine_version           = "8.0.33"
  parameter_group_family   = "mysql8.0"
  instance_class           = "db.r6i.large"
  allocated_storage        = 100
  max_allocated_storage    = 500
  storage_type             = "gp3"
  iops                     = 5000
  database_name            = "appdb"
  master_username          = "dbadmin"
  master_password          = var.db_password
  
  db_subnet_ids           = aws_subnet.private[*].id
  vpc_security_group_ids  = [aws_security_group.rds.id]
  
  # RDS Proxy para connection pooling
  enable_db_proxy         = true
  
  # Monitoramento
  enable_enhanced_monitoring = true
  monitoring_interval        = 60
  performance_insights_enabled = true
  
  # Logs
  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]
  
  # Alertas
  enable_cloudwatch_alarms  = true
  alarm_sns_topic_arn      = aws_sns_topic.alerts.arn
  
  tags = {
    Project     = "CloudHelm"
    Environment = "Production"
    Backup      = "daily"
  }
}
```

### Exemplo com Parâmetros Customizados

```hcl
module "postgres_custom" {
  source = "../../modules/aws-rds"

  identifier               = "cloudhelm-postgres-custom"
  engine                   = "postgres"
  engine_version           = "15.3"
  parameter_group_family   = "postgres15"
  instance_class           = "db.r6i.xlarge"
  allocated_storage        = 500
  max_allocated_storage    = 2000
  database_name            = "analytics"
  master_username          = "admin"
  master_password          = var.db_password
  
  db_subnet_ids           = aws_subnet.private[*].id
  vpc_security_group_ids  = [aws_security_group.rds.id]

  # Parâmetros customizados
  parameters = {
    "max_connections"           = "500"
    "shared_buffers"            = "262144" # 2GB
    "effective_cache_size"      = "1048576" # 8GB
    "maintenance_work_mem"      = "65536" # 512MB
    "random_page_cost"          = "1.1"
    "effective_io_concurrency" = "200"
    "work_mem"                 = "8192" # 64MB
    "log_min_duration_statement" = "1000" # Log queries > 1s
  }

  # Logs detalhados
  enabled_cloudwatch_logs_exports = ["postgresql"]
}
```

## Variáveis

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `identifier` | string | - | **Obrigatório**. Nome da instância |
| `engine` | string | - | **Obrigatório**. postgres\|mysql\|mariadb\|sqlserver |
| `engine_version` | string | - | **Obrigatório**. Versão (ex: 15.3) |
| `parameter_group_family` | string | - | **Obrigatório**. Familia (ex: postgres15) |
| `instance_class` | string | - | **Obrigatório**. Tipo (ex: db.t4g.micro) |
| `allocated_storage` | number | - | **Obrigatório**. Storage inicial (GB) |
| `max_allocated_storage` | number | - | **Obrigatório**. Storage máximo (GB) |
| `database_name` | string | - | **Obrigatório**. Nome do database |
| `master_username` | string | - | **Obrigatório**. Usuário admin |
| `master_password` | string | - | **Obrigatório**. Senha admin |
| `db_subnet_ids` | list(string) | - | **Obrigatório**. Subnets (mín. 2) |
| `vpc_security_group_ids` | list(string) | - | **Obrigatório**. Security groups |
| `storage_encrypted` | bool | `true` | Criptografar storage |
| `multi_az` | bool | `true` | Multi-AZ deployment |
| `backup_retention_days` | number | `30` | Dias de retenção |
| `enable_db_proxy` | bool | `false` | Habilitar RDS Proxy |
| `enable_enhanced_monitoring` | bool | `true` | Enhanced monitoring |
| `performance_insights_enabled` | bool | `true` | Performance Insights |

## Outputs

| Output | Descrição |
|--------|-----------|
| `db_instance_endpoint` | Endpoint do database (host:port) |
| `db_instance_address` | Endereço do host |
| `db_instance_port` | Porta do database |
| `db_proxy_endpoint` | Endpoint do RDS Proxy |
| `connection_string_psql` | String de conexão para psql |
| `connection_string_mysql` | String de conexão para mysql |
| `jdbc_connection_string` | JDBC URL para Java |
| `secrets_manager_secret_arn` | ARN do secret no Secrets Manager |

## Usando RDS Proxy

RDS Proxy melhora performance com connection pooling automático:

```hcl
# Terraform
module "db" {
  source = "../../modules/aws-rds"
  
  # ... outras configs ...
  
  enable_db_proxy = true
}

# Aplicação conecta ao proxy ao invés do database
# Conexão: module.db.db_proxy_endpoint
```

## CloudWatch Alarms

Alarms pré-configurados são criados automaticamente:

- **CPU > 80%**: Aviso de processamento alto
- **Free Storage < 10GB**: Aviso de espaço baixo
- **Conexões > threshold**: Aviso de conexões excessivas

Configure o SNS topic para receber notificações:

```hcl
module "db" {
  # ...
  enable_cloudwatch_alarms = true
  alarm_sns_topic_arn      = "arn:aws:sns:region:account:topic-name"
}
```

## IAM Database Authentication

Ao invés de senhas, use IAM roles para autenticar:

```bash
# Gerar authentication token
aws rds generate-db-auth-token \
  --hostname cloudhelm-postgres.xxxxx.rds.amazonaws.com \
  --port 5432 \
  --region us-east-1 \
  --username iamuser

# Conectar com token
PGPASSWORD="token" psql -h hostname -U iamuser -d dbname -p 5432 --set="sslmode=require"
```

## Boas Práticas

1. **Senhas**: Use Terraform variables e terraform.tfvars (não commitado)
2. **Backup**: Manter backup_retention_days >= 7
3. **Multi-AZ**: Sempre habilitar em produção
4. **Proxy**: Usar RDS Proxy para aplicações com muitas conexões
5. **Monitoramento**: Habilitar Enhanced Monitoring e Performance Insights
6. **Storage**: Usar gp3 para melhor custo-benefício
7. **Parametrização**: Customizar parameters para workload específico
8. **Patching**: Deixar AWS fazer patching automático

## Exemplo: Backup e Restore

```bash
# Criar snapshot manual
aws rds create-db-snapshot \
  --db-instance-identifier cloudhelm-postgres \
  --db-snapshot-identifier cloudhelm-postgres-backup-20240307

# Restaurar de snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier cloudhelm-postgres-restored \
  --db-snapshot-identifier cloudhelm-postgres-backup-20240307 \
  --db-instance-class db.t4g.micro
```

## Troubleshooting

### Database não responde
```bash
# Verificar status
aws rds describe-db-instances \
  --db-instance-identifier cloudhelm-postgres \
  --query 'DBInstances[0].DBInstanceStatus'

# Ver events
aws rds describe-events \
  --source-identifier cloudhelm-postgres \
  --source-type db-instance
```

### Conexão recusada
- Verificar security group: porta aberta?
- Verificar subnet: database acessível de dentro da VPC?
- Verificar credenciais: usuário e senha corretos?

### Performance degradada
- Verificar CPU/Memory no CloudWatch
- Verificar slow query logs
- Usar Performance Insights para análise
- Considerar instance class maior

## Requisitos

- Terraform >= 1.0
- AWS Credentials configuradas
- AWS CLI >= 2.0

## Licença

CloudHelm © 2024 - MIT License
