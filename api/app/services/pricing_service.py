"""
Cloud pricing and architecture intelligence.

The pricing estimator consumes normalized catalog records collected from the
official provider price APIs in cloud_catalog_service.py. When the catalog has
no usable match for a component, it falls back to explicit baseline rates so the
orchestration flow remains deterministic in local development.
"""

from dataclasses import dataclass
from typing import Any

from app.models.cloud_catalog_item import CloudCatalogItem
from app.schemas.pricing import PricingEstimateRequest


SUPPORTED_PROVIDERS = {"aws", "gcp", "azure", "oci"}


@dataclass(frozen=True)
class ComponentRule:
    name: str
    keywords: tuple[str, ...]
    quantity_field: str


COMPONENT_RULES = (
    ComponentRule("compute", ("compute", "ec2", "virtual machine", "vm", "instance"), "compute_units"),
    ComponentRule("database", ("rds", "sql", "database", "mysql", "postgres"), "database_units"),
    ComponentRule("cache", ("redis", "cache", "memorystore", "elasticache"), "cache_units"),
    ComponentRule("storage", ("storage", "s3", "object", "bucket", "block volume"), "storage_gb"),
    ComponentRule("network", ("cdn", "cloudfront", "front door", "load balancer", "data transfer"), "data_transfer_gb"),
    ComponentRule("observability", ("logging", "monitoring", "cloudwatch", "log analytics"), "observability_gb"),
)


FALLBACK_RATES: dict[str, dict[str, dict[str, Any]]] = {
    "aws": {
        "compute": {"service": "Amazon EC2", "display_name": "EC2 On-Demand baseline", "unit": "Hrs", "price": 0.0416},
        "database": {"service": "Amazon RDS", "display_name": "RDS MySQL baseline", "unit": "Hrs", "price": 0.032},
        "cache": {"service": "Amazon ElastiCache", "display_name": "Redis small node", "unit": "Hrs", "price": 0.027},
        "storage": {"service": "Amazon S3", "display_name": "S3 Standard Storage", "unit": "GB-Mo", "price": 0.023},
        "network": {"service": "Amazon CloudFront", "display_name": "CloudFront transfer baseline", "unit": "GB", "price": 0.085},
        "observability": {"service": "Amazon CloudWatch", "display_name": "CloudWatch Logs ingestion", "unit": "GB", "price": 0.5},
    },
    "gcp": {
        "compute": {"service": "Compute Engine", "display_name": "E2 shared core baseline", "unit": "Hrs", "price": 0.0335},
        "database": {"service": "Cloud SQL", "display_name": "Cloud SQL MySQL baseline", "unit": "Hrs", "price": 0.041},
        "cache": {"service": "Memorystore", "display_name": "Redis basic tier", "unit": "Hrs", "price": 0.035},
        "storage": {"service": "Cloud Storage", "display_name": "Standard Storage", "unit": "GB-Mo", "price": 0.02},
        "network": {"service": "Cloud CDN", "display_name": "Cloud CDN transfer baseline", "unit": "GB", "price": 0.085},
        "observability": {"service": "Cloud Logging", "display_name": "Log ingestion", "unit": "GB", "price": 0.5},
    },
    "azure": {
        "compute": {"service": "Virtual Machines", "display_name": "Virtual Machine B2s baseline", "unit": "1 Hour", "price": 0.052},
        "database": {"service": "SQL Database", "display_name": "SQL Database baseline", "unit": "1 Hour", "price": 0.051},
        "cache": {"service": "Cache for Redis", "display_name": "Redis Basic baseline", "unit": "1 Hour", "price": 0.0149},
        "storage": {"service": "Storage", "display_name": "Storage LRS baseline", "unit": "1 GB/Month", "price": 0.0184},
        "network": {"service": "Azure Front Door", "display_name": "Front Door transfer baseline", "unit": "1 GB", "price": 0.087},
        "observability": {"service": "Monitor", "display_name": "Log Analytics ingestion", "unit": "1 GB", "price": 0.5},
    },
    "oci": {
        "compute": {"service": "Compute", "display_name": "OCI Compute baseline", "unit": "OCPU Hour", "price": 0.0255},
        "database": {"service": "Database", "display_name": "OCI Database baseline", "unit": "OCPU Hour", "price": 0.1613},
        "cache": {"service": "Cache", "display_name": "OCI cache baseline", "unit": "Hour", "price": 0.03},
        "storage": {"service": "Storage", "display_name": "OCI Object Storage baseline", "unit": "GB Month", "price": 0.0255},
        "network": {"service": "Networking", "display_name": "OCI outbound transfer baseline", "unit": "GB", "price": 0.0085},
        "observability": {"service": "Observability", "display_name": "OCI logging baseline", "unit": "GB", "price": 0.05},
    },
}


SIZE_MULTIPLIERS = {"small": 1.0, "medium": 2.5, "large": 6.0}


def build_pricing_request_from_text(raw_input: str) -> PricingEstimateRequest:
    text = raw_input.lower()
    workload_size = "small"
    if any(term in text for term in ("alta escala", "large", "enterprise", "milhoes", "milhões", "1000", "10000")):
        workload_size = "large"
    elif any(term in text for term in ("media escala", "média escala", "medium", "centenas", "500")):
        workload_size = "medium"

    multiplier = SIZE_MULTIPLIERS[workload_size]
    return PricingEstimateRequest(
        workload_size=workload_size,
        compute_units=max(1, round(multiplier)),
        database_units=1 if any(term in text for term in ("banco", "database", "sql", "dados")) else 0,
        cache_units=1 if any(term in text for term in ("cache", "redis", "sessao", "sessão")) else 0,
        storage_gb=round(100 * multiplier),
        data_transfer_gb=round(100 * multiplier),
        observability_gb=round(20 * multiplier),
    )


def estimate_infrastructure_costs(
    catalog_items: list[CloudCatalogItem] | list[dict[str, Any]] | None,
    request: PricingEstimateRequest,
) -> dict[str, Any]:
    providers = [provider.lower() for provider in request.providers if provider.lower() in SUPPORTED_PROVIDERS]
    if not providers:
        providers = ["aws", "gcp", "azure", "oci"]

    normalized_items = [_normalize_catalog_item(item) for item in catalog_items or []]
    estimates = {provider: _estimate_provider(provider, normalized_items, request) for provider in providers}

    return {
        "currency": "USD",
        "monthly_estimate": {
            provider: {"min": value["min"], "max": value["max"], "total": value["monthly_total"]}
            for provider, value in estimates.items()
        },
        "providers": estimates,
        "assumptions": {
            "workload_size": request.workload_size,
            "monthly_hours": request.monthly_hours,
            "compute_units": request.compute_units,
            "database_units": request.database_units,
            "cache_units": request.cache_units,
            "storage_gb": request.storage_gb,
            "data_transfer_gb": request.data_transfer_gb,
            "observability_gb": request.observability_gb,
        },
        "notes": [
            "Valores calculados a partir do catalogo sincronizado das APIs oficiais quando ha correspondencia de SKU.",
            "Fallbacks sao usados por componente quando o catalogo local ainda nao tem dados suficientes.",
            "Estimativa nao inclui impostos, descontos privados, Savings Plans, reservas ou compromissos empresariais.",
        ],
    }


def _normalize_catalog_item(item: CloudCatalogItem | dict[str, Any]) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    return {
        "id": item.id,
        "provider": item.provider,
        "service": item.service,
        "display_name": item.display_name,
        "price": item.price,
        "currency": item.currency,
        "unit": item.unit,
        "source": item.source,
    }


def _estimate_provider(provider: str, catalog_items: list[dict[str, Any]], request: PricingEstimateRequest) -> dict[str, Any]:
    provider_items = [item for item in catalog_items if item.get("provider") == provider and item.get("currency", "USD") == "USD"]
    components = []
    used_fallback = False

    for rule in COMPONENT_RULES:
        quantity = float(getattr(request, rule.quantity_field))
        if quantity <= 0:
            continue

        matched = _find_catalog_match(provider_items, rule)
        if matched:
            component = _build_component(rule.name, matched, quantity, request.monthly_hours)
        else:
            used_fallback = True
            fallback = FALLBACK_RATES[provider][rule.name]
            component = _build_fallback_component(rule.name, fallback, quantity, request.monthly_hours)
        components.append(component)

    total = round(sum(component["monthly_cost"] for component in components), 2)
    return {
        "provider": provider,
        "currency": "USD",
        "monthly_total": total,
        "min": round(total * 0.85, 2),
        "max": round(total * 1.25, 2),
        "components": components,
        "used_fallback": used_fallback,
        "sources": sorted({component["source"] for component in components}),
    }


def _find_catalog_match(items: list[dict[str, Any]], rule: ComponentRule) -> dict[str, Any] | None:
    candidates = []
    for item in items:
        searchable = f"{item.get('service', '')} {item.get('display_name', '')} {item.get('unit', '')}".lower()
        if any(keyword in searchable for keyword in rule.keywords):
            candidates.append(item)
    if not candidates:
        return None
    return min(candidates, key=lambda item: float(item.get("price") or 0))


def _build_component(name: str, item: dict[str, Any], quantity: float, monthly_hours: int) -> dict[str, Any]:
    unit = item.get("unit", "Unit")
    unit_price = float(item.get("price") or 0)
    billable_quantity = _billable_quantity(unit=unit, quantity=quantity, monthly_hours=monthly_hours)
    return {
        "component": name,
        "catalog_item_id": item.get("id"),
        "service": item.get("service", name),
        "display_name": item.get("display_name", name),
        "unit": unit,
        "unit_price": unit_price,
        "quantity": billable_quantity,
        "monthly_cost": round(unit_price * billable_quantity, 2),
        "source": item.get("source", "catalog"),
    }


def _build_fallback_component(name: str, item: dict[str, Any], quantity: float, monthly_hours: int) -> dict[str, Any]:
    unit = item["unit"]
    unit_price = float(item["price"])
    billable_quantity = _billable_quantity(unit=unit, quantity=quantity, monthly_hours=monthly_hours)
    return {
        "component": name,
        "catalog_item_id": None,
        "service": item["service"],
        "display_name": item["display_name"],
        "unit": unit,
        "unit_price": unit_price,
        "quantity": billable_quantity,
        "monthly_cost": round(unit_price * billable_quantity, 2),
        "source": "fallback-baseline",
    }


def _billable_quantity(unit: str, quantity: float, monthly_hours: int) -> float:
    normalized = unit.lower()
    if "hour" in normalized or "hrs" in normalized or normalized == "hr" or "ocpu" in normalized:
        return quantity * monthly_hours
    return quantity


class CloudPricingService:
    """Compatibility facade for older imports."""

    estimate_infrastructure_costs = staticmethod(estimate_infrastructure_costs)
