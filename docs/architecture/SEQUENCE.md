# Diagramas de sequência — CloudHelm

## Login GitHub OAuth

```plantuml
@startuml CloudHelm-Login
autonumber
actor Usuario as U
participant "Frontend" as FE
participant "API FastAPI" as API
participant "GitHub OAuth" as GH
database "Supabase Postgres" as DB

U -> FE: Seleciona "Entrar com GitHub"
FE -> API: GET /api/auth/github/url
API --> FE: URL OAuth
FE -> GH: Autoriza aplicação
GH -> API: GET /api/auth/github/callback?code=...
API -> GH: Troca code por token
GH --> API: Identidade do usuário
API -> DB: Cria/atualiza usuário
DB --> API: Usuário e papel
API --> FE: Redirect com JWT
FE -> API: GET /api/auth/session\nAuthorization: Bearer JWT
API --> FE: Sessão (papel/status)
@enduml
```

## Orquestração de demanda

```plantuml
@startuml CloudHelm-Orchestration
autonumber
actor Usuario as U
participant "Frontend" as FE
participant "API / Demands" as API
database "Supabase Postgres" as DB
participant "Catalog Service" as CAT
participant "Pricing Service" as PRICE
participant "LLM Service" as LLM

U -> FE: Envia descrição da infraestrutura
FE -> API: POST /api/demands
API -> DB: Persiste demanda
DB --> API: demand_id
API --> FE: Demanda criada
U -> FE: Solicita orquestração
FE -> API: POST /api/demands/{id}/orchestrate
API -> DB: Carrega demanda e configurações
DB --> API: Dados da demanda
API -> CAT: Lê resumo e itens do catálogo
CAT -> DB: Consulta cloud_catalog_items
DB --> CAT: Itens normalizados
CAT --> API: Catálogo disponível
API -> PRICE: Estima componentes por provedor
PRICE --> API: Custos, intervalo e fontes
API -> LLM: Gera briefing (se configurado)
alt LLM disponível
  LLM --> API: Briefing arquitetural
else Sem chave ou erro
  LLM --> API: Fallback determinístico
end
API -> DB: Registra auditoria/resultado quando aplicável
API --> FE: Ranking + arquitetura + custos + Terraform
FE --> U: Exibe recomendação
@enduml
```

## Regras de falha relevantes

- Falha de um catálogo não interrompe a estimativa: o componente usa baseline determinístico.
- Falha ou ausência de credencial de LLM não interrompe a orquestração.
- Indisponibilidade do Postgres impede operações autenticadas e persistentes; o healthcheck deve sinalizar a degradação.
