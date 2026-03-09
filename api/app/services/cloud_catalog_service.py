import io
import json
import os
import zipfile
from datetime import datetime, timezone

import requests
from thefuzz import fuzz, process

from app.repositories.catalog_repository import replace_provider_items


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

    def get_smart_icon(self, service_name: str) -> str:
        all_icons = [f for f in os.listdir(self.icon_dir) if f.endswith(".svg")]
        if not all_icons:
            return "/static/icons/generic.svg"
        result = process.extractOne(service_name, all_icons, scorer=fuzz.token_set_ratio)
        if not result:
            return "/static/icons/generic.svg"
        match, score = result[0], result[1]
        if score > 50:
            return f"/static/icons/{match}"
        return "/static/icons/generic.svg"

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
                        "icon": self.get_smart_icon(item.get("serviceName", "Generic")),
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
        return [
            {
                "provider": "aws",
                "service": svc,
                "display_name": name,
                "region": "us-east-1",
                "price": float(price),
                "currency": "USD",
                "unit": unit,
                "icon": self.get_smart_icon(svc),
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
        return [
            {
                "provider": "gcp",
                "service": svc,
                "display_name": name,
                "region": "us-central1",
                "price": float(price),
                "currency": "USD",
                "unit": unit,
                "icon": self.get_smart_icon(svc),
                "source": "seeded-baseline",
            }
            for svc, name, price, unit in seeded[:limit]
        ]

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
