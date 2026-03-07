from typing import Any


def build_terraform_modules(provider: str) -> dict[str, Any]:
    provider_block = {
        "aws": 'provider "aws" {\n  region = var.region\n}\n',
        "gcp": 'provider "google" {\n  project = var.project_id\n  region  = var.region\n}\n',
        "azure": 'provider "azurerm" {\n  features {}\n}\n',
    }[provider]

    modules = {
        "network": (
            f'{provider_block}'
            'module "network" {\n'
            '  source = "./modules/network"\n'
            '  project_name = var.project_name\n'
            "}\n"
        ),
        "compute": (
            'module "compute" {\n'
            '  source = "./modules/compute"\n'
            "  provider = var.provider\n"
            "  app_name = var.project_name\n"
            "}\n"
        ),
        "database": (
            'module "database" {\n'
            '  source = "./modules/database"\n'
            "  provider = var.provider\n"
            "  db_name = \"antigravity\"\n"
            "}\n"
        ),
        "observability": (
            'module "observability" {\n'
            '  source = "./modules/observability"\n'
            "  provider = var.provider\n"
            "}\n"
        ),
        "security": (
            'module "security" {\n'
            '  source = "./modules/security"\n'
            "  provider = var.provider\n"
            "}\n"
        ),
    }

    return {
        "provider": provider,
        "modules": modules,
    }
