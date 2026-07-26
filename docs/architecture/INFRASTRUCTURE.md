# Arquitetura de infraestrutura

## Estado atual — produção

```mermaid
flowchart TB
    Browser[Usuário / navegador]
    Pages[GitHub Pages\nFrontend estático]
    Render[Render\nContainer Docker + FastAPI]
    Supabase[(Supabase Postgres\nDATABASE_URL + TLS)]
    GitHub[GitHub OAuth]
    Catalogs[APIs de preços\nAWS · GCP · Azure · OCI]
    AI[OpenAI / Gemini\nOpcional]

    Browser -->|HTTPS| Pages
    Browser -->|REST/JSON + JWT| Render
    Render -->|SQLAlchemy / psycopg| Supabase
    Render -->|OAuth callback| GitHub
    Render -->|HTTPS| Catalogs
    Render -.->|HTTPS, se habilitado| AI
```

Runtime e responsabilidades:

- GitHub Actions publica `frontend/` no GitHub Pages.
- Render executa `api/Dockerfile`, faz deploy automático de `main` e verifica `/health`.
- Supabase mantém o Postgres gerenciado; SQLite é somente local.
- Segredos e URLs são variáveis de ambiente do Render.

## Estado-alvo — provisionamento em cloud

Os playbooks em `infrastructure/ansible/` e módulos Terraform descrevem uma topologia alternativa para execução em AWS, Azure ou GCP. Ela não substitui o deployment atual sem uma migração explícita.

```mermaid
flowchart TB
    Internet((Internet)) --> WAF[Load Balancer / WAF]
    WAF --> K8s[Kubernetes gerenciado\nEKS / AKS / GKE]
    K8s --> API[Deployment CloudHelm API\nréplicas horizontais]
    API --> DB[(Banco gerenciado\nRDS / Azure SQL / Cloud SQL)]
    API --> Secrets[Secret Manager / Key Vault]
    API --> Logs[Monitoring + Logs]
    API --> Providers[APIs AWS / GCP / Azure / OCI]
    K8s --> Storage[(Object / block storage)]
```

Requisitos de evolução: ingress/TLS, secret manager, backup e restore testados, observabilidade, autoscaling, migrations controladas e política de rede. A extração para workers de catálogo/LLM deve ocorrer somente quando houver necessidade de escala ou isolamento.
