# CloudHelm Deploy Gratuito

Arquitetura recomendada para MVP/demo:

- Frontend: GitHub Pages, publicando a pasta `frontend/`.
- Backend: Render Free, usando `render.yaml` e `api/Dockerfile`.
- Banco: Supabase Free Postgres, via `DATABASE_URL`.

## 1. Supabase

1. Crie um projeto no Supabase.
2. Copie a connection string Postgres em modo direto ou pooled.
3. Use formato compativel com SQLAlchemy/psycopg:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require
```

Use essa string como `DATABASE_URL` no Render.

## 2. GitHub OAuth

Crie um OAuth App no GitHub com:

```text
Homepage URL: https://joao19921.github.io/CloudHelm
Authorization callback URL: https://cloudhelm-platform-c7nv.onrender.com/api/auth/github/callback
```

Depois configure no Render:

```text
GITHUB_CLIENT_ID=<client id>
GITHUB_CLIENT_SECRET=<client secret>
GITHUB_REDIRECT_URI=https://cloudhelm-platform-c7nv.onrender.com/api/auth/github/callback
GITHUB_ADMIN_LOGINS=Joao19921
```

## 3. Render

Use o Blueprint do arquivo `render.yaml`.

Variaveis obrigatorias no Render:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require
FRONTEND_PUBLIC_URL=https://joao19921.github.io/CloudHelm
CORS_ORIGINS=https://joao19921.github.io,https://joao19921.github.io/CloudHelm,https://cloudhelm-platform-c7nv.onrender.com
GITHUB_CLIENT_ID=<client id>
GITHUB_CLIENT_SECRET=<client secret>
GITHUB_REDIRECT_URI=https://cloudhelm-platform-c7nv.onrender.com/api/auth/github/callback
GITHUB_ADMIN_LOGINS=Joao19921
```

Variaveis opcionais:

```text
OPENAI_API_KEY=<somente se quiser IA OpenAI por ambiente>
GEMINI_API_KEY=<somente se quiser Gemini por ambiente>
GCP_BILLING_API_KEY=<somente se quiser GCP Billing Catalog real>
```

O backend deve responder em:

```text
https://cloudhelm-platform-c7nv.onrender.com/health
```

## 4. GitHub Pages

O workflow `.github/workflows/github-pages.yml` ja publica `frontend/`.

No GitHub, confirme:

1. Settings > Pages.
2. Source: GitHub Actions.
3. Rode o workflow `Deploy Frontend to GitHub Pages`.

A URL esperada e:

```text
https://joao19921.github.io/CloudHelm/
```

## 5. Checklist de Validacao

1. Abra `https://cloudhelm-platform-c7nv.onrender.com/health` e confirme `{"status":"ok"}`.
2. Abra `https://joao19921.github.io/CloudHelm/`.
3. Clique em `Entrar com GitHub`.
4. Confirme retorno para o frontend com token.
5. No primeiro usuario/admin, acesse backoffice e aprove usuarios pendentes.
6. Sincronize catalogo cloud.
7. Orquestre uma demanda e confira arquitetura, ranking, custos e Terraform.

## Observacoes de Free Tier

- Render Free pode hibernar apos inatividade; o primeiro acesso pode ser lento.
- SQLite nao deve ser usado em Render Free, porque o filesystem nao e persistente.
- Supabase Free e suficiente para demo/MVP, mas deve ser monitorado para limites de projeto e conexoes.
