# Fluxo do Sistema

## 1. Acesso inicial

1. Usuario abre `https://joao19921.github.io/CloudHelm/`.
2. Frontend carrega `frontend/config.js`.
3. Chamadas HTTP usam `API_BASE_URL=https://cloudhelm-platform.onrender.com`.
4. Backend responde `/health` para validacao operacional.

## 2. Login com GitHub

1. Frontend chama `/api/auth/github/url`.
2. Usuario autentica no GitHub OAuth App.
3. GitHub redireciona para `/api/auth/github/callback`.
4. Backend valida o codigo, cria/atualiza usuario e emite JWT.
5. Backend redireciona para o frontend com token.
6. Frontend armazena token e passa a chamar rotas protegidas.

## 3. Aprovacao administrativa

1. Logins configurados em `GITHUB_ADMIN_LOGINS` recebem permissao administrativa.
2. Admin acessa o backoffice no frontend.
3. Frontend chama rotas `/api/backoffice/*` com JWT.
4. Admin aprova, revoga, altera papel ou define acesso temporario de usuarios.

## 4. Catalogo cloud

1. Usuario autenticado chama `/api/catalog/sync`.
2. Backend consulta APIs/fontes de AWS, GCP, Azure e OCI quando disponiveis.
3. Se uma fonte falhar ou nao tiver credencial, o servico usa fallback.
4. Itens normalizados sao persistidos em `cloud_catalog_items`.
5. Frontend consulta `/api/catalog/items` e `/api/catalog/summary`.

## 5. Estimativa de custos

1. Frontend envia premissas para `/api/pricing/estimate`.
2. Backend le itens do catalogo por provedor.
3. `pricing_service` calcula componentes mensais: compute, database, cache, storage, data transfer e observability.
4. Resposta retorna total por provedor, intervalo minimo/maximo, fontes e premissas.

## 6. Orquestracao de demanda

1. Usuario cria demanda em `/api/demands`.
2. Usuario executa `/api/demands/{demand_id}/orchestrate`.
3. Backend combina dados da demanda, catalogo, heuristicas e modelos LLM opcionais.
4. Resposta inclui analise, ranking de provedores, custos estimados e Terraform sugerido.

## 7. Deploy

1. Push em `main` aciona GitHub Pages para `frontend/`.
2. Render faz auto deploy do backend usando `render.yaml` e `api/Dockerfile`.
3. Render injeta variaveis de ambiente e conecta no Supabase via `DATABASE_URL`.
4. Healthcheck `/health` confirma disponibilidade do backend.
