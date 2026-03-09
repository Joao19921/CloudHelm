output "cluster_id" {
  description = "ID do cluster EKS"
  value       = aws_eks_cluster.main.id
}

output "cluster_arn" {
  description = "ARN do cluster EKS"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "Endpoint da API do cluster EKS"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_version" {
  description = "Versão do Kubernetes do cluster"
  value       = aws_eks_cluster.main.version
}

output "cluster_certificate_authority_data" {
  description = "Certificate Authority do cluster (base64)"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "cluster_platform_version" {
  description = "Plataforma version do cluster"
  value       = aws_eks_cluster.main.platform_version
}

output "cluster_security_group_id" {
  description = "Security group ID do cluster"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "node_groups" {
  description = "Informações dos node groups"
  value = {
    for k, v in aws_eks_node_group.main : k => {
      id           = v.id
      arn          = v.arn
      status       = v.status
      version      = v.version
      capacity_type = v.capacity_type
    }
  }
}

output "oidc_provider_arn" {
  description = "ARN do OIDC Provider para IRSA"
  value       = var.enable_irsa ? aws_iam_openid_connect_provider.main[0].arn : null
}

output "oidc_issuer_url" {
  description = "URL do OIDC Issuer"
  value       = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

output "configure_kubectl" {
  description = "Comando para configurar kubectl"
  value       = "aws eks update-kubeconfig --region ${data.aws_caller_identity.current.account} --name ${aws_eks_cluster.main.name}"
}

# Data source para obter informações da conta
data "aws_caller_identity" "current" {}
