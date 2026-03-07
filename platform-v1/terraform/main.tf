terraform {
  required_version = ">= 1.5.0"
}

module "network" {
  source       = "./modules/network"
  project_name = var.project_name
  provider     = var.provider
}

module "compute" {
  source       = "./modules/compute"
  app_name     = var.project_name
  provider     = var.provider
  network_id   = module.network.network_id
}

module "database" {
  source       = "./modules/database"
  db_name      = "antigravity"
  provider     = var.provider
  network_id   = module.network.network_id
}

module "observability" {
  source   = "./modules/observability"
  provider = var.provider
  app_name = var.project_name
}

module "security" {
  source   = "./modules/security"
  provider = var.provider
  app_name = var.project_name
}
