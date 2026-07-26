# Servicos e Limites de Contexto

CloudHelm hoje roda como um monolito modular FastAPI. Nao ha microsservicos separados em producao. A separacao atual e por dominios internos, o que reduz custo operacional e ainda permite extrair servicos no futuro.

## Servico frontend

- Local: `frontend/`.
- Deploy: GitHub Pages.
- Tipo: estatico.
- Responsabilidades: interface, navegacao, consumo da API e armazenamento client-side do token JWT.

## Servico backend

- Local: `api/`.
- Deploy: Render Docker.
- Tipo: API HTTP FastAPI.
- Responsabilidades: autenticacao, autorizacao, backoffice, demandas, catalogo, custos e integracoes externas.

## Banco de dados

- Provider: Supabase Postgres.
- Acesso: `DATABASE_URL` via SQLAlchemy/psycopg.
- Responsabilidades: usuarios, demandas, configuracoes, auditoria e catalogo cloud normalizado.

## Modulos internos do backend

| Modulo | Local | Responsabilidade |
| --- | --- | --- |
| Auth | `api/app/api_v1/endpoints/auth.py` | Login local, GitHub OAuth e sessao. |
| Backoffice | `api/app/api_v1/endpoints/backoffice.py` | Administracao de usuarios e configuracoes. |
| Demands | `api/app/api_v1/endpoints/demands.py` | Demandas, transcricao e orquestracao. |
| Catalog | `api/app/api_v1/endpoints/catalog.py` | Sincronizacao e leitura do catalogo cloud. |
| Pricing | `api/app/api_v1/endpoints/pricing.py` | Estimativa de custos por provedor. |

## Quando extrair microsservicos

Extrair somente quando houver necessidade real de escala, isolamento ou ciclo de deploy independente. Candidatos futuros:

- Worker de sincronizacao de catalogo cloud.
- Worker de processamento LLM/transcricao.
- Servico dedicado de billing/FinOps.
