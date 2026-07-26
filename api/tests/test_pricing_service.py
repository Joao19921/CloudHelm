from app.schemas.pricing import PricingEstimateRequest
from app.services.pricing_service import estimate_infrastructure_costs


def test_estimate_uses_catalog_match_for_compute():
    catalog_items = [
        {
            "id": 1,
            "provider": "aws",
            "service": "Amazon EC2",
            "display_name": "EC2 t3.medium Linux",
            "price": 0.05,
            "currency": "USD",
            "unit": "Hrs",
            "source": "aws-pricing-api",
        }
    ]

    result = estimate_infrastructure_costs(
        catalog_items=catalog_items,
        request=PricingEstimateRequest(
            providers=["aws"],
            compute_units=2,
            database_units=0,
            cache_units=0,
            storage_gb=0,
            data_transfer_gb=0,
            observability_gb=0,
        ),
    )

    aws = result["providers"]["aws"]
    assert aws["monthly_total"] == 73.0
    assert aws["used_fallback"] is False
    assert aws["components"][0]["catalog_item_id"] == 1
    assert aws["components"][0]["source"] == "aws-pricing-api"


def test_estimate_falls_back_when_catalog_is_empty():
    result = estimate_infrastructure_costs(
        catalog_items=[],
        request=PricingEstimateRequest(
            providers=["oci"],
            compute_units=1,
            database_units=0,
            cache_units=0,
            storage_gb=10,
            data_transfer_gb=0,
            observability_gb=0,
        ),
    )

    oci = result["providers"]["oci"]
    assert oci["monthly_total"] > 0
    assert oci["used_fallback"] is True
    assert "fallback-baseline" in oci["sources"]
