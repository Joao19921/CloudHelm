# Rotas da API

Base URL de producao: `https://cloudhelm-platform.onrender.com`

Todas as rotas de negocio usam prefixo global `/api`, exceto UI server-side e healthcheck.

## Sistema

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| GET | `/health` | Nao | Healthcheck do Render. |
| GET | `/` | Nao | Pagina server-side simples do backend. |
| GET | `/backoffice` | Nao | Pagina server-side simples do backend. |

## Autenticacao

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | Nao | Cria usuario local. |
| POST | `/api/auth/login` | Nao | Autentica usuario local e retorna JWT. |
| GET | `/api/auth/github/url` | Nao | Retorna URL de login GitHub OAuth. |
| GET | `/api/auth/github/callback` | Nao | Recebe callback OAuth, cria/atualiza usuario e redireciona ao frontend. |
| GET | `/api/auth/session` | JWT | Retorna a sessao atual. |

## Demandas e orquestracao

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| GET | `/api/providers` | Nao | Lista provedores suportados. |
| GET | `/api/terraform/{provider}` | Nao | Retorna template Terraform do provedor. |
| POST | `/api/demands` | JWT | Cria demanda de infraestrutura. |
| GET | `/api/demands` | JWT | Lista demandas do usuario. |
| POST | `/api/demands/{demand_id}/orchestrate` | JWT | Gera analise, ranking, custos e sugestao Terraform; usa fallback deterministico se a IA externa estiver indisponivel. |
| POST | `/api/demands/transcribe` | JWT | Transcreve audio quando OpenAI estiver configurada. |

## Catalogo cloud

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| POST | `/api/catalog/sync` | JWT | Sincroniza catalogo AWS/GCP/Azure/OCI. |
| GET | `/api/catalog/items` | Nao | Lista itens do catalogo com filtros `provider`, `search` e `limit`. |
| GET | `/api/catalog/summary` | Nao | Resume quantidade de itens por provedor. |

## Custos

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| POST | `/api/pricing/estimate` | Nao | Estima custo mensal por provedor. |

## Backoffice

| Metodo | Rota | Auth | Descricao |
| --- | --- | --- | --- |
| GET | `/api/backoffice/users` | Admin JWT | Lista usuarios. |
| POST | `/api/backoffice/users/{user_id}/approve` | Admin JWT | Aprova usuario. |
| POST | `/api/backoffice/users/bulk-approve` | Admin JWT | Aprova usuarios em lote. |
| POST | `/api/backoffice/users/{user_id}/revoke` | Admin JWT | Revoga acesso. |
| POST | `/api/backoffice/users/{user_id}/role` | Admin JWT | Altera papel do usuario. |
| GET | `/api/backoffice/audit-logs` | Admin JWT | Lista eventos administrativos. |
| GET | `/api/backoffice/llm-config` | Admin JWT | Le configuracao de modelos. |
| PUT | `/api/backoffice/llm-config` | Admin JWT | Atualiza configuracao de modelos. |
