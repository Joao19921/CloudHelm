# AWS EKS Cluster Module
# Reutilizável para diferentes projetos e ambientes

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# IAM Role para EKS Cluster
resource "aws_iam_role" "eks_cluster_role" {
  name = "${var.cluster_name}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, { Name = "${var.cluster_name}-eks-cluster-role" })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name            = var.cluster_name
  role_arn        = aws_iam_role.eks_cluster_role.arn
  version         = var.kubernetes_version
  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = var.endpoint_private_access
    endpoint_public_access  = var.endpoint_public_access
  }

  enabled_cluster_log_types = var.enabled_cluster_log_types

  tags = merge(var.tags, { Name = var.cluster_name })

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
}

# IAM Role para Node Groups
resource "aws_iam_role" "eks_nodegroup_role" {
  name = "${var.cluster_name}-eks-nodegroup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, { Name = "${var.cluster_name}-eks-nodegroup-role" })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodegroup_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodegroup_role.name
}

resource "aws_iam_role_policy_attachment" "eks_ssm_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = aws_iam_role.eks_nodegroup_role.name
}

# Launch Template para customização de nodes
resource "aws_launch_template" "eks_node" {
  count           = var.create_launch_template ? 1 : 0
  name_prefix     = "${var.cluster_name}-node-"
  image_id        = var.ami_id
  instance_type   = var.instance_type
  
  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = var.volume_size
      volume_type           = var.volume_type
      delete_on_termination = true
      encrypted             = var.volume_encrypted
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  monitoring {
    enabled = var.enable_monitoring
  }

  tag_specifications {
    resource_type = "instance"
    tags          = merge(var.tags, { Name = "${var.cluster_name}-node" })
  }

  user_data = base64encode(var.user_data)

  lifecycle {
    create_before_destroy = true
  }
}

# EKS Node Group
resource "aws_eks_node_group" "main" {
  for_each        = var.node_groups
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-${each.key}"
  node_role_arn   = aws_iam_role.eks_nodegroup_role.arn
  subnet_ids      = var.subnet_ids
  disk_size       = each.value.disk_size
  capacity_type   = each.value.capacity_type
  instance_types  = each.value.instance_types
  desired_size    = each.value.desired_size
  max_size        = each.value.max_size
  min_size        = each.value.min_size
  max_unavailable = each.value.max_unavailable

  labels = merge(
    { Environment = var.environment },
    each.value.labels
  )

  dynamic "launch_template" {
    for_each = var.create_launch_template ? [1] : []
    content {
      id      = aws_launch_template.eks_node[0].id
      version = aws_launch_template.eks_node[0].latest_version_number
    }
  }

  tags = merge(var.tags, { Name = "${var.cluster_name}-${each.key}-nodegroup" })

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_ssm_policy,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# OIDC Provider para IRSA (IAM Roles for Service Accounts)
data "tls_certificate" "main" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "main" {
  count             = var.enable_irsa ? 1 : 0
  client_id_list    = ["sts.amazonaws.com"]
  thumbprint_list   = [data.tls_certificate.main.certificates[0].sha1_fingerprint]
  url               = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

# CloudWatch Log Group para EKS
resource "aws_cloudwatch_log_group" "eks_cluster" {
  count             = var.enable_cluster_autoscaling ? 1 : 0
  name              = "/aws/eks/${var.cluster_name}/cluster"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, { Name = "${var.cluster_name}-logs" })
}

# Auto Scaling tags para Cluster Autoscaler
resource "aws_autoscaling_group_tag" "cluster_autoscaler_enabled" {
  for_each              = var.enable_cluster_autoscaling ? aws_eks_node_group.main : {}
  autoscaling_group_name = each.value.resources[0].autoscaling_groups[0].name

  tag {
    key                 = "k8s.io/cluster-autoscaler/${var.cluster_name}"
    value               = "owned"
    propagate_at_launch = true
  }
}
