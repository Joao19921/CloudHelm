import re
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
        {"task": "Application and infrastructure foundation UX/UI", "agent": "super-agent-ux-ui-frontend"},
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
            "returns": "consolidated architectural foundation",
        },
        {
            "name": "Architecture Module",
            "role": "Documents the application and infrastructure foundation for the selected cloud reference.",
            "calls": "Provider Mapping module",
            "returns": "service matrix and dependencies",
        },
        {
            "name": "Cost Module",
            "role": "Calculates monthly estimates from the synchronized official cloud pricing catalog.",
            "calls": "AWS Pricing, Azure Retail, GCP Billing, OCI Price List normalized catalog",
            "returns": "componentized reference cost ranges for planning",
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



def _build_product_artifacts(raw_input: str, provider: str, costs: dict[str, Any]) -> dict[str, Any]:
    """Create explainable artifacts for business and technical review."""
    normalized = raw_input.lower()
    user_match = re.search(r"(\d[\d.,]*)\s*(?:mil|k)?\s*(?:usuários|usuarios|users)", normalized)
    scale = user_match.group(0) if user_match else "a definir"
    objectives = [
        "Traduzir o desafio de negócio em componentes e responsabilidades técnicas.",
        f"Estabelecer uma infraestrutura de referência em {provider.upper()}.",
        "Criar uma base rastreável para validação, evolução e implementação.",
    ]
    non_functional = []
    for keywords, label in [
        (("disponibilidade", "alta disponibilidade", "ha", "sla"), "Disponibilidade e continuidade"),
        (("segurança", "seguranca", "lgpd", "compliance", "gdpr"), "Segurança e conformidade"),
        (("escala", "usuários", "usuarios", "users", "pico"), "Escalabilidade e capacidade"),
        (("latência", "latencia", "tempo real", "performance"), "Performance e latência"),
        (("backup", "rto", "rpo", "desastre"), "Recuperação e proteção de dados"),
    ]:
        if any(keyword in normalized for keyword in keywords):
            non_functional.append(label)
    if not non_functional:
        non_functional = ["Disponibilidade", "Segurança", "Escalabilidade", "Observabilidade"]
    decisions = [
        {"service": "Entrada e API", "purpose": "Receber solicitações e expor contratos da aplicação.", "why": "Cria um limite claro entre usuários, integrações e domínio.", "alternative": "API Gateway gerenciado ou ingress do cluster."},
        {"service": "Compute gerenciado", "purpose": "Executar os serviços da aplicação com escala controlada.", "why": "Reduz a carga operacional inicial e deixa a capacidade explícita.", "alternative": "Kubernetes quando houver necessidade comprovada de controle fino."},
        {"service": "Dados e persistência", "purpose": "Armazenar dados transacionais com política de backup definida.", "why": "Separa o estado da aplicação e permite evoluir disponibilidade por etapas.", "alternative": "Banco serverless ou distribuído quando o padrão justificar."},
        {"service": "Observabilidade", "purpose": "Acompanhar saúde, erros, latência e comportamento da solução.", "why": "Permite validar a arquitetura em operação, não apenas no diagrama.", "alternative": "Stack centralizada integrada por OpenTelemetry."},
    ]
    tradeoffs = [
        {"decision": "Compute gerenciado vs. Kubernetes", "benefit": "Menor complexidade operacional e time-to-value.", "cost": "Menos controle de runtime e portabilidade específica.", "when": "Começar gerenciado; migrar quando houver evidência."},
        {"decision": "Redundância multi-zona", "benefit": "Maior disponibilidade e recuperação automática.", "cost": "Aumenta custo de compute, dados e operação.", "when": "Aplicar aos componentes críticos conforme SLA e RTO/RPO."},
        {"decision": "Cache distribuído", "benefit": "Reduz latência e pressão no banco.", "cost": "Adiciona invalidação, consistência e operação.", "when": "Introduzir após identificar leituras repetidas ou gargalos."},
    ]
    risks = [
        {"severity": "alta", "title": "Requisitos de recuperação ainda não confirmados", "detail": "RTO, RPO, backup e disaster recovery precisam de valores aprovados.", "mitigation": "Validar metas e testar restauração antes do go-live."},
        {"severity": "média", "title": "Observabilidade pode ficar para depois", "detail": "Sem métricas, logs e traces não há como validar a base em operação.", "mitigation": "Definir sinais mínimos e alertas junto com o primeiro deploy."},
        {"severity": "média", "title": "Dependências externas não detalhadas", "detail": "Integrações, limites de terceiros e contratos podem alterar o desenho.", "mitigation": "Mapear sistemas externos, SLAs, autenticação e estratégias de falha."},
    ]
    plan = [
        {"step": "Validar contexto", "description": "Confirmar atores, jornadas, regras de negócio, escala e metas de qualidade.", "owner": "Produto + Engenharia"},
        {"step": "Fechar contratos", "description": "Definir APIs, eventos, dados, integrações e fronteiras dos componentes.", "owner": "Arquitetura + Backend"},
        {"step": "Provisionar fundação", "description": "Criar rede, identidade, compute, dados, secrets e observabilidade mínima.", "owner": "Plataforma + DevOps"},
        {"step": "Validar operação", "description": "Executar testes de carga, falha, backup, segurança e custo.", "owner": "QA + SRE"},
    ]
    discovery = {
        "business_questions": ["Qual problema e impacto financeiro estamos tratando?", "Quem usa, decide e opera a solução?", "Quais indicadores definem sucesso?", "Qual prazo, orçamento e custo de falha?"],
        "identified_signals": ["Contexto técnico informado" if any(term in normalized for term in ("api", "aplicacao", "aplicação", "sistema")) else "Contexto técnico ainda incompleto", "Escala " + scale, "Cloud de referência " + provider.upper()],
        "gaps": ["Objetivos de negócio e KPIs", "Orçamento e prazo aprovados", "Atores, integrações e regras de negócio", "SLA, RTO, RPO e requisitos de compliance"],
        "assumptions": ["A solução começa com uma base evolutiva e decisões revisáveis.", "Valores de custo são referências de planejamento, não proposta comercial."]
    }
    architecture_options = [
        {"name": "Monólito modular + Clean/Hexagonal", "fit": "Recomendação inicial", "benefit": "Entrega rápida, baixo custo e fronteiras claras para evoluir.", "tradeoff": "Módulos ainda compartilham ciclo de deploy e runtime."},
        {"name": "Microsserviços", "fit": "Usar com evidência", "benefit": "Escala e autonomia por domínio.", "tradeoff": "Aumenta observabilidade, operação, testes distribuídos e custo."},
        {"name": "Event-driven / Serverless", "fit": "Para fluxos assíncronos", "benefit": "Desacoplamento e escala sob demanda.", "tradeoff": "Consistência, rastreabilidade e debugging ficam mais complexos."}
    ]
    security = [
        {"area": "Identidade", "baseline": "OAuth/OIDC, JWT de curta duração, RBAC e MFA para operações sensíveis."},
        {"area": "Proteção", "baseline": "TLS, criptografia em repouso, gestão de secrets, WAF e rate limit."},
        {"area": "Governança", "baseline": "Logs de auditoria, OWASP, retenção definida e revisão de acesso."}
    ]
    platform = {
        "devops": ["CI com lint, testes, análise de dependências e segurança", "CD por ambientes: desenvolvimento, homologação e produção", "Deploy canário ou blue-green quando o risco justificar", "Rollback automatizado e IaC versionada"],
        "observability": ["Métricas de negócio e técnicas", "Logs estruturados e correlação por request-id", "Tracing distribuído com OpenTelemetry", "SLO, alertas acionáveis e runbooks"],
        "data": ["Modelo de dados e relacionamentos validados no domínio", "Índices e estratégia de crescimento definidos por volume", "Backup testado, retenção e restauração", "Particionamento somente quando a carga justificar"],
        "apis": ["REST como padrão inicial; gRPC para comunicação interna de alto volume", "Versionamento de contratos e documentação OpenAPI", "Webhooks e eventos para integrações assíncronas", "Autenticação, idempotência e rate limit por contrato"]
    }
    delivery = {
        "team": [{"role": "Produto + Negócio", "count": "1-2", "phase": "descoberta e priorização"}, {"role": "Arquitetura + Tech Lead", "count": "1-2", "phase": "fundação e decisões"}, {"role": "Backend + Frontend", "count": "2-5", "phase": "MVP e evolução"}, {"role": "QA + DevOps/SRE", "count": "1-2", "phase": "qualidade, deploy e operação"}],
        "timeline": ["Descoberta e requisitos", "Fundação arquitetural", "MVP com critérios de aceite", "Homologação e produção", "Evolução orientada por métricas"],
        "cost_note": "Sem prazo, equipe e volume confirmados, apresentar faixas e atualizar após a descoberta."
    }
    support = ["Definir SLA e SLO por jornada crítica", "Operar incidentes com severidade, comunicação e postmortem", "Manter plano de capacidade e custos", "Reservar ciclo para dívida técnica e atualizações", "Revisar riscos e arquitetura a cada evolução"]
    extended = {"discovery": discovery, "architecture_options": architecture_options, "security_baseline": security, "platform_blueprint": platform, "delivery_estimate": delivery, "support_model": support, "next_steps": ["Responder as lacunas de descoberta", "Validar a alternativa arquitetural com produto e engenharia", "Detalhar contratos, dados e integrações", "Transformar a base validada em backlog e ADRs"], "engineering_principles": ["Simplicidade antes de complexidade", "Baixo acoplamento e alta coesão", "Segurança e observabilidade desde o início", "Escalar por evidência", "Custo, prazo e qualidade como decisões conjuntas"]}
    return {**extended, "executive_summary": {"interpretation": raw_input[:500], "scale": scale, "objectives": objectives, "non_functional_requirements": non_functional, "provider_reference": provider.upper(), "confidence_note": "Base inicial para validação humana; decisões críticas dependem de requisitos confirmados."}, "service_decisions": decisions, "tradeoffs": tradeoffs, "risks": risks, "implementation_plan": plan, "cost_scope": list((costs.get("monthly_estimate") or {}).keys())}

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
    selected_provider = provider if provider in {"aws", "gcp", "azure", "oci"} else ranking["recommended_provider"]

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
    artifacts = _build_product_artifacts(raw_input=raw_input, provider=selected_provider, costs=costs)
    return {
        "provider": selected_provider,
        "architecture": architecture,
        "costs": costs,
        "terraform": terraform,
        "ranking": ranking,
        "ai": ai_context,
        **artifacts,
    }