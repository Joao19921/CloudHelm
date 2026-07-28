import io
import json
import os
import zipfile
from datetime import datetime, timezone

import requests

from app.repositories.catalog_repository import replace_provider_items


SERVICE_ICONS = {
    "aws": {
        "compute": "/static/icons/cloud/aws-ec2.svg",
        "database": "/static/icons/cloud/aws-rds.svg",
        "cache": "/static/icons/cloud/aws-elasticache.svg",
        "storage": "/static/icons/cloud/aws-s3.svg",
        "observability": "/static/icons/cloud/aws-cloudwatch.svg",
        "default": "/static/icons/cloud/aws-logo.svg",
    },
    "azure": {
        "compute": "/static/icons/cloud/azure-vm.svg",
        "database": "/static/icons/cloud/azure-sql.svg",
        "cache": "/static/icons/cloud/azure-redis.svg",
        "storage": "/static/icons/cloud/azure-storage.svg",
        "observability": "/static/icons/cloud/azure-monitor.svg",
        "default": "/static/icons/cloud/azure-vm.svg",
    },
    "gcp": {
        "compute": "/static/icons/cloud/gcp-compute.svg",
        "database": "/static/icons/cloud/gcp-sql.svg",
        "storage": "/static/icons/cloud/gcp-storage.svg",
        "observability": "/static/icons/cloud/gcp-observability.svg",
        "default": "/static/icons/cloud/gcp-compute-alt.svg",
    },
    "oci": {"default": "/static/icons/cloud/oci.svg"},
}


class CloudMasterEngine:
    def __init__(self):
        self.output_path = "dist_cloud_data"
        self.icon_dir = "app/static/icons"
        self.data_file = f"{self.output_path}/cloud_master_data.json"
        os.makedirs(self.icon_dir, exist_ok=True)
        os.makedirs(self.output_path, exist_ok=True)

    def download_all_icons(self) -> int:
        url = "https://github.com/awslabs/aws-icons-for-plantuml/archive/refs/heads/master.zip"
        try:
            response = requests.get(url, timeout=45)
            response.raise_for_status()
        except requests.RequestException:
            return 0

        written = 0
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for file_name in archive.namelist():
                if not file_name.endswith(".svg"):
                    continue
                base = os.path.basename(file_name)
                if not base:
                    continue
                with open(os.path.join(self.icon_dir, base), "wb") as out:
                    out.write(archive.read(file_name))
                written += 1
        return written

    def get_smart_icon(self, service_name: str, provider: str = "") -> str:
        normalized = f"{service_name} {provider}".lower()
        icon_set = SERVICE_ICONS.get(provider.lower(), {})
        keywords = {
            "compute": ("compute", "ec2", "virtual machine", "vm", "instance"),
            "database": ("database", "rds", "sql", "postgres", "mysql"),
            "cache": ("cache", "redis", "elasticache", "memorystore"),
            "storage": ("storage", "s3", "bucket", "object"),
            "observability": ("cloudwatch", "logging", "monitor", "log analytics"),
        }
        for category, terms in keywords.items():
            if any(term in normalized for term in terms) and category in icon_set:
                return icon_set[category]
        return icon_set.get("default", "/static/icons/generic.svg")
    def fetch_azure_data(self, limit: int = 20) -> list[dict]:
        filters = "serviceName eq 'Virtual Machines' or serviceName eq 'SQL Database'"
        url = "https://prices.azure.com/api/retail/prices"
        items: list[dict] = []
        next_url: str | None = f"{url}?$filter={filters}"

        while next_url and len(items) < limit:
            try:
                payload = requests.get(next_url, timeout=30).json()
            except requests.RequestException:
                break
            raw_items = payload.get("Items", [])
            for item in raw_items:
                price = item.get("retailPrice")
                if price is None:
                    continue
                items.append(
                    {
                        "provider": "azure",
                        "service": item.get("serviceName", "Unknown"),
                        "display_name": item.get("productName", item.get("serviceName", "Unknown")),
                        "region": item.get("armRegionName"),
                        "price": float(price),
                        "currency": item.get("currencyCode", "USD"),
                        "unit": item.get("unitOfMeasure", "Unit"),
                        "icon": self.get_smart_icon(item.get("serviceName", "Generic"), "azure"),
                        "source": "azure-retail-api",
                    }
                )
                if len(items) >= limit:
                    break
            next_url = payload.get("NextPageLink")

        return items

    def fetch_aws_data(self, limit: int = 20) -> list[dict]:
        seeded = [
            ("Amazon EC2", "EC2 On-Demand Baseline", 0.0116, "Hrs"),
            ("Amazon RDS", "RDS MySQL Baseline", 0.0320, "Hrs"),
            ("Amazon ElastiCache", "Redis Small Node", 0.0270, "Hrs"),
            ("Amazon S3", "S3 Standard Storage", 0.0230, "GB-Mo"),
            ("Amazon CloudWatch", "CloudWatch Logs Ingestion", 0.50, "GB"),
        ]
        try:
            import boto3
            client = boto3.client("pricing", region_name="us-east-1")
            response = client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
                    {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                    {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
                ],
                MaxResults=min(limit, 100),
            )
            items = []
            price_list = response.get("PriceList", [])
            for price_str in price_list:
                price_data = json.loads(price_str)
                product = price_data.get("product", {})
                attributes = product.get("attributes", {})

                terms = price_data.get("terms", {}).get("OnDemand", {})
                if not terms:
                    continue
                offer = list(terms.values())[0]
                price_dimensions = offer.get("priceDimensions", {})
                if not price_dimensions:
                    continue
                dimension = list(price_dimensions.values())[0]

                price_per_unit = list(dimension.get("pricePerUnit", {}).values())[0]
                unit = dimension.get("unit", "Hrs")

                service = attributes.get("servicecode", "Amazon EC2")
                instance_type = attributes.get("instanceType", "General")
                display_name = f"EC2 {instance_type} ({attributes.get('vcpu', 'N/A')} vCPUs, {attributes.get('memory', 'N/A')})"

                items.append(
                    {
                        "provider": "aws",
                        "service": service,
                        "display_name": display_name,
                        "region": attributes.get("regionCode", "us-east-1"),
                        "price": float(price_per_unit),
                        "currency": "USD",
                        "unit": unit,
                        "icon": self.get_smart_icon(service, "aws"),
                        "source": "aws-pricing-api",
                    }
                )
                if len(items) >= limit:
                    break
            if items:
                return items
        except Exception:
            pass

        return [
            {
                "provider": "aws",
                "service": svc,
                "display_name": name,
                "region": "us-east-1",
                "price": float(price),
                "currency": "USD",
                "unit": unit,
                "icon": self.get_smart_icon(svc, "aws"),
                "source": "seeded-baseline",
            }
            for svc, name, price, unit in seeded[:limit]
        ]

    def fetch_gcp_data(self, limit: int = 20) -> list[dict]:
        seeded = [
            ("Compute Engine", "E2 Shared Core Baseline", 0.0084, "Hrs"),
            ("Cloud SQL", "Cloud SQL MySQL Baseline", 0.0410, "Hrs"),
            ("Cloud Storage", "Standard Storage", 0.0200, "GB-Mo"),
            ("Memorystore", "Redis Basic Tier", 0.0350, "Hrs"),
            ("Cloud Logging", "Log Ingestion", 0.50, "GB"),
        ]

        from app.core.config import settings
        api_key = settings.gcp_billing_api_key

        if api_key:
            try:
                services_url = f"https://cloudbilling.googleapis.com/v1/services?key={api_key}"
                resp = requests.get(services_url, timeout=15)
                if resp.status_code == 200:
                    services = resp.json().get("services", [])
                    items = []
                    for svc in services:
                        svc_id = svc.get("serviceId")
                        svc_name = svc.get("displayName")

                        if svc_name not in ["Compute Engine", "Cloud Storage", "Cloud SQL"]:
                            continue

                        skus_url = f"https://cloudbilling.googleapis.com/v1/services/{svc_id}/skus?key={api_key}"
                        skus_resp = requests.get(skus_url, timeout=15)
                        if skus_resp.status_code != 200:
                            continue

                        skus = skus_resp.json().get("skus", [])
                        for sku in skus:
                            pricing_info = sku.get("pricingInfo", [])
                            if not pricing_info:
                                continue

                            pricing_expression = pricing_info[0].get("pricingExpression", {})
                            tiered_rates = pricing_expression.get("tieredRates", [])
                            if not tiered_rates:
                                continue

                            unit = pricing_expression.get("usageUnit", "Unit")
                            unit_price = tiered_rates[0].get("unitPrice", {})
                            nanos = unit_price.get("nanos", 0)
                            units = int(unit_price.get("units", 0))
                            price_val = units + (nanos / 1e9)

                            regions = sku.get("serviceRegions", ["us-central1"])
                            region = regions[0] if regions else "us-central1"

                            items.append(
                                {
                                    "provider": "gcp",
                                    "service": svc_name,
                                    "display_name": sku.get("description", sku.get("name")),
                                    "region": region,
                                    "price": float(price_val),
                                    "currency": "USD",
                                    "unit": unit,
                                    "icon": self.get_smart_icon(svc_name, "gcp"),
                                    "source": "gcp-billing-api",
                                }
                            )
                            if len(items) >= limit:
                                break
                        if len(items) >= limit:
                            break
                    if items:
                        return items
            except Exception:
                pass

        return [
            {
                "provider": "gcp",
                "service": svc,
                "display_name": name,
                "region": "us-central1",
                "price": float(price),
                "currency": "USD",
                "unit": unit,
                "icon": self.get_smart_icon(svc, "gcp"),
                "source": "seeded-baseline",
            }
            for svc, name, price, unit in seeded[:limit]
        ]

    def fetch_oci_data(self, limit: int = 20) -> list[dict]:
        url = "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/"
        try:
            resp = requests.get(url, timeout=20)
            if resp.status_code != 200:
                return []

            raw_items = resp.json().get("items", [])
            items = []
            for item in raw_items:
                localizations = item.get("currencyCodeLocalizations", [])

                usd_localization = None
                for loc in localizations:
                    if loc.get("currencyCode") == "USD":
                        usd_localization = loc
                        break

                if not usd_localization:
                    continue

                prices = usd_localization.get("prices", [])
                if not prices:
                    continue

                price_val = None
                for price in prices:
                    if price.get("model") == "PAY_AS_YOU_GO":
                        price_val = price.get("value")
                        break

                if price_val is None:
                    continue

                service = item.get("serviceCategory", "General")
                display_name = item.get("displayName", "OCI Product")
                metric = item.get("metricName", "Unit")

                items.append(
                    {
                        "provider": "oci",
                        "service": service,
                        "display_name": display_name,
                        "region": "global",
                        "price": float(price_val),
                        "currency": "USD",
                        "unit": metric,
                        "icon": self.get_smart_icon(service, "oci"),
                        "source": "oci-retail-api",
                    }
                )
                if len(items) >= limit:
                    break
            return items
        except Exception:
            return []

    def collect(self, providers: list[str], limit_per_provider: int) -> dict[str, list[dict]]:
        self.download_all_icons()
        data: dict[str, list[dict]] = {}
        for provider in providers:
            if provider == "azure":
                data[provider] = self.fetch_azure_data(limit_per_provider)
            elif provider == "aws":
                data[provider] = self.fetch_aws_data(limit_per_provider)
            elif provider == "gcp":
                data[provider] = self.fetch_gcp_data(limit_per_provider)
            elif provider == "oci":
                data[provider] = self.fetch_oci_data(limit_per_provider)
        return data

    def export_flat_json(self, provider_data: dict[str, list[dict]]) -> str:
        merged = []
        for provider_items in provider_data.values():
            merged.extend(provider_items)
        content = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total": len(merged),
            "items": merged,
        }
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(content, file, indent=2, ensure_ascii=False)
        return self.data_file

    def sync_database(self, db, providers: list[str], limit_per_provider: int) -> tuple[dict[str, int], str]:
        provider_data = self.collect(providers=providers, limit_per_provider=limit_per_provider)
        synced: dict[str, int] = {}
        for provider, items in provider_data.items():
            synced[provider] = replace_provider_items(db=db, provider=provider, items=items)
        exported_file = self.export_flat_json(provider_data=provider_data)
        return synced, exported_file
