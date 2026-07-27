# CI/CD

O repositorio usa GitHub Actions para validar backend e frontend antes de publicar mudancas na branch `main`.

## Workflows

- `CI`: executa testes do backend FastAPI, compilacao dos modulos Python e validacao de sintaxe dos arquivos JavaScript do frontend.
- `Backend Automated Tests`: valida o backend quando arquivos em `api/**` mudam.
- `Deploy Frontend to GitHub Pages`: publica o diretorio `frontend/` no GitHub Pages quando o frontend muda.

## Variaveis de CI

Os workflows usam valores seguros de teste para `SECRET_KEY`, `DATABASE_URL`, `GITHUB_REDIRECT_URI`, `GITHUB_CLIENT_ID` e `GITHUB_CLIENT_SECRET`. Segredos reais nao devem ser colocados nos arquivos YAML.

## Deploy de producao

- Backend: Render faz deploy automatico a partir da branch `main`.
- Frontend: GitHub Pages publica os arquivos estaticos em `frontend/`.
- Banco: Supabase PostgreSQL e configurado no Render via `DATABASE_URL`.
