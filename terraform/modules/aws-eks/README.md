# AWS EKS Cluster Module

Módulo Terraform reutilizável para provisionar clusters Amazon EKS (Elastic Kubernetes Service) com configurações enterprise-grade.

## Características

- ✅ **Cluster EKS completo** com versão customizável
- ✅ **Node Groups flexíveis** com scaling automático
- ✅ **IRSA** (IAM Roles for Service Accounts) para pods com permissões
- ✅ **Launch Templates** para customização avançada de nodes
- ✅ **CloudWatch Logging** integrado
- ✅ **OIDC Provider** para autenticação
- ✅ **Security best practices** (IMDSv2, encryption, etc)
- ✅ **Auto Scaling** com Cluster Autoscaler support

## Usando o Módulo

### Exemplo Básico

```hcl
module "eks" {
  source = "../../modules/aws-eks"

  cluster_name       = "cloudhelm-prod"
  kubernetes_version = "1.29"
  vpc_id             = aws_vpc.main.id
  subnet_ids         = aws_subnet.private[*].id
  environment        = "production"

  tags = {
    Project     = "CloudHelm"
    Environment = "Production"
    Managed_by  = "Terraform"
  }
}
```

### Exemplo com Node Groups Customizado

```hcl
module "eks" {
  source = "../../modules/aws-eks"

  cluster_name = "cloudhelm-staging"
  vpc_id       = aws_vpc.main.id
  subnet_ids   = aws_subnet.private[*].id

  node_groups = {
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
    gpu = {
      desired_size    = 1
      min_size        = 0
      max_size        = 5
      max_unavailable = 1
      instance_types  = ["g4dn.xlarge"]
      disk_size       = 50
      capacity_type   = "SPOT"
      labels = {
        workload = "gpu"
      }
    }
  }

  enable_irsa                = true
  enable_cluster_autoscaling = true
}
```

### Exemplo com Launch Template Customizado

```hcl
module "eks" {
  source = "../../modules/aws-eks"

  cluster_name = "cloudhelm-custom"
  vpc_id       = aws_vpc.main.id
  subnet_ids   = aws_subnet.private[*].id

  create_launch_template = true
  instance_type          = "t3.large"
  volume_size            = 50
  volume_encrypted       = true
  enable_monitoring      = true

  user_data = base64encode(file("${path.module}/user_data.sh"))
}
```

## Variáveis

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `cluster_name` | string | - | **Obrigatório**. Nome do cluster |
| `kubernetes_version` | string | `1.29` | Versão do Kubernetes |
| `vpc_id` | string | - | **Obrigatório**. ID da VPC |
| `subnet_ids` | list(string) | - | **Obrigatório**. IDs das subnets (mín. 2) |
| `endpoint_private_access` | bool | `true` | Acesso privado à API |
| `endpoint_public_access` | bool | `true` | Acesso público à API |
| `node_groups` | map(object) | Veja defaults | Configuração de node groups |
| `environment` | string | `dev` | dev, staging, prod |
| `tags` | map(string) | `{}` | Tags para recursos |
| `enable_irsa` | bool | `true` | Habilitar IRSA |
| `enable_cluster_autoscaling` | bool | `true` | Habilitar auto-scaling |
| `create_launch_template` | bool | `false` | Usar launch template customizado |

## Outputs

| Output | Tipo | Descrição |
|--------|------|-----------|
| `cluster_id` | string | ID do cluster |
| `cluster_arn` | string | ARN do cluster |
| `cluster_endpoint` | string | Endpoint da API |
| `cluster_version` | string | Versão do Kubernetes |
| `cluster_security_group_id` | string | Security group do cluster |
| `node_groups` | map | Informações de node groups |
| `oidc_provider_arn` | string | ARN do OIDC Provider |
| `configure_kubectl` | string | Comando para configurar kubectl |

## Usar IRSA para Pods

Uma vez criado o cluster com IRSA habilitado, você pode criar service accounts com permissões específicas:

```hcl
# 1. Criar política IAM
resource "aws_iam_policy" "pod_policy" {
  name = "cloudhelm-pod-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = "*"
    }]
  })
}

# 2. Criar role com trust policy OIDC
resource "aws_iam_role" "pod_role" {
  name = "cloudhelm-pod-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = module.eks.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(module.eks.oidc_issuer_url, "https://", "")}:sub" = "system:serviceaccount:default:cloudhelm-sa"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "pod_policy" {
  policy_arn = aws_iam_policy.pod_policy.arn
  role       = aws_iam_role.pod_role.name
}
```

Depois, no Kubernetes:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cloudhelm-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/cloudhelm-pod-role
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloudhelm-app
spec:
  serviceAccountName: cloudhelm-sa
  containers:
  - name: app
    image: cloudhelm:latest
```

## Cluster Autoscaler

Se `enable_cluster_autoscaling = true`, os node groups são automaticamente taggados para funcionar com o Cluster Autoscaler.

Instale o Cluster Autoscaler:

```bash
helm repo add autoscaling https://kubernetes.github.io/autoscaling
helm install cluster-autoscaler autoscaling/cluster-autoscaler \
  --namespace kube-system \
  --set awsRegion=us-east-1 \
  --set autoDiscovery.clusterName=cloudhelm-prod
```

## Boas Práticas

1. **Subnets**: Use pelo menos 2 subnets em AZs diferentes para Alta Disponibilidade
2. **Node Groups**: Separe workloads (general, gpu, compute) em node groups diferentes
3. **Logging**: Habilite todos os tipos de log para auditoria (padrão)
4. **IRSA**: Sempre use IRSA ao invés de credentials EC2 para pods
5. **Scaling**: Configure min_size > 0 para garantir disponibilidade
6. **Versão do K8s**: Atualize versão regularmente (1x por trimestre)

## Troubleshooting

### Cluster não responde
```bash
# Verificar status
aws eks describe-cluster --name cloudhelm-prod --query 'cluster.status'

# Ver logs
aws logs tail /aws/eks/cloudhelm-prod/cluster --follow
```

### Node não está pronto
```bash
# Verificar nodes
kubectl get nodes

# Describe node problemático
kubectl describe node <node-name>

# Check node logs via Systems Manager
aws ssm start-session --target <instance-id>
```

## Requisitos

- Terraform >= 1.0
- AWS CLI >= 2.0
- kubectl >= 1.24
- aws-iam-authenticator

## Licença

CloudHelm © 2024 - MIT License
