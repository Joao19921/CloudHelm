from typing import Any

from app.services.llm_service import LLMService
from app.services.pricing_service import build_pricing_request_from_text, estimate_infrastructure_costs
from app.services.terraform_service import build_terraform_modules


def _build_agent_tasks() -> list[dict[str, str]]:
    return [
        {"task": "Discovery and breakdown", "agent": "project-planner"},
        {"task": "Global coordination", "agent": "orchestrator"},
        {"task": "Backend and API design", "agent": "backend-specialist"},
        {"task": "Database modeling and backup strategy", "agent": "database-architect"},
        {"task": "UX/UI flow and premium layout", "agent": "frontend-specialist"},
        {"task": "Security and access controls", "agent": "security-auditor"},
        {"task": "Tests and quality gates", "agent": "test-engineer"},
        {"task": "Docker and deployment setup", "agent": "devops-engineer"},
    ]


def _build_architecture(raw_input: str, provider: str, ai: dict[str, Any]) -> dict[str, Any]:
    modules = [
        {
            "name": "Input Gateway",
            "role": "Receives transcript/text and validates request payload.",
            "calls": "Orchestration Engine",
            "returns": "request_id and normalized requirement package",
        },
        {
            "name": "Orchestration Engine",
            "role": "Breaks requirements into tasks and routes to specialist agents.",
            "calls": "Architecture, Cost, and Terraform modules",
            "returns": "consolidated architecture plan",
        },
        {
            "name": "Architecture Module",
            "role": "Builds scalable and HA-oriented service blueprint.",
            "calls": "Provider Mapping module",
            "returns": "service matrix and dependencies",
        },
        {
            "name": "Cost Module",
            "role": "Calculates monthly estimates from the synchronized official cloud pricing catalog.",
            "calls": "AWS Pricing, Azure Retail, GCP Billing, OCI Price List normalized catalog",
            "returns": "componentized cost ranges and provider recommendation",
        },
        {
            "name": "Terraform Generator",
            "role": "Builds modular IaC stubs by provider.",
            "calls": "Module template registry",
            "returns": "Terraform scripts per module",
        },
        {
            "name": "Audit and Auth",
            "role": "Handles login, authorship tracking, and action logs.",
            "calls": "Database",
            "returns": "access tokens and audit trail",
        },
    ]

    return {
        "provider_focus": provider,
        "input_excerpt": raw_input[:220],
        "availability_targets": {"rto_minutes": 15, "rpo_minutes": 15},
        "modules": modules,
        "agent_tasks": _build_agent_tasks(),
        "ai": ai,
    }


def _monthly_cost_midpoint(cost_range: dict[str, float]) -> float:
    return float(cost_range["min"] + cost_range["max"]) / 2.0


def _summary_index(summary: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    if not summary:
        return {}
    return {item["provider"].lower(): item for item in summary if item.get("provider")}


def _build_provider_ranking(
    costs: dict[str, Any],
    preferred_provider: str | None,
    catalog_summary: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    summary_map = _summary_index(catalog_summary)
    estimates = costs["monthly_estimate"]
    base_providers = [provider for provider in ("aws", "gcp", "azure", "oci") if provider in estimates]

    mids = {provider: _monthly_cost_midpoint(estimates[provider]) for provider in base_providers}
    max_mid = max(mids.values())
    min_mid = min(mids.values())
    spread = max(max_mid - min_mid, 0.0001)

    ranked = []
    for provider in base_providers:
        cost_efficiency = 1 - ((mids[provider] - min_mid) / spread)
        sla_score = 0.92 if provider in {"aws", "gcp"} else 0.9 if provider == "azure" else 0.88
        catalog_signal = 0.5
        if provider in summary_map:
            total_items = summary_map[provider].get("total", 0) or 0
            catalog_signal = min(1.0, total_items / 25)

        fallback_penalty = 0.08 if costs.get("providers", {}).get(provider, {}).get("used_fallback") else 0.0
        preference_bonus = 0.12 if preferred_provider and provider == preferred_provider else 0.0
        score = (cost_efficiency * 0.45) + (sla_score * 0.35) + (catalog_signal * 0.2) + preference_bonus - fallback_penalty

        ranked.append(
            {
                "provider": provider,
                "score": round(score, 4),
                "cost_mid_usd_month": round(mids[provider], 2),
                "cost_efficiency": round(cost_efficiency, 4),
                "sla_score": round(sla_score, 4),
                "catalog_signal": round(catalog_signal, 4),
                "preferred": provider == preferred_provider,
            }
        )

    ranked.sort(key=lambda row: row["score"], reverse=True)
    return {
        "recommended_provider": ranked[0]["provider"],
        "method": "weighted(cost=45%, sla=35%, catalog-signal=20%, preference-bonus=12%, fallback-penalty=8%)",
        "items": ranked,
    }


def orchestrate_demand(
    raw_input: str,
    provider: str,
    catalog_summary: list[dict[str, Any]] | None = None,
    catalog_items: list[Any] | None = None,
    llm_provider: str = "none",
    llm_api_key: str | None = None,
    llm_model: str | None = None,
) -> dict[str, Any]:
    pricing_request = build_pricing_request_from_text(raw_input)
    costs = estimate_infrastructure_costs(catalog_items=catalog_items, request=pricing_request)
    preferred_provider = provider if provider in {"aws", "gcp", "azure", "oci"} else None
    ranking = _build_provider_ranking(
        costs=costs,
        preferred_provider=preferred_provider,
        catalog_summary=catalog_summary,
    )
    selected_provider = provider if provider in {"aws", "gcp", "azure"} else ranking["recommended_provider"]
    if selected_provider == "oci":
        selected_provider = ranking["items"][1]["provider"] if len(ranking["items"]) > 1 else "aws"

    llm_result = LLMService.generate_brief(
        raw_input=raw_input,
        cloud_provider=selected_provider,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
    )

    ai_context = {
        "provider": llm_result.provider,
        "model": llm_result.model,
        "used_fallback": llm_result.used_fallback,
        "brief": llm_result.content,
    }

    architecture = _build_architecture(raw_input=raw_input, provider=selected_provider, ai=ai_context)
    terraform = build_terraform_modules(provider=selected_provider)
    return {
        "provider": selected_provider,
        "architecture": architecture,
        "costs": costs,
        "terraform": terraform,
        "ranking": ranking,
        "ai": ai_context,
    }
