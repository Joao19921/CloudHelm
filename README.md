# CloudHelm

CloudHelm e uma plataforma web para planejar infraestrutura cloud, comparar custos entre provedores e gerar uma base inicial de arquitetura/Terraform a partir de demandas do usuario.

## Estrutura do repositorio

- `.agent/`: materiais internos de agentes e regras operacionais.
- `.github/`: workflows de CI/CD, incluindo publicacao do frontend no GitHub Pages.
- `api/`: backend FastAPI, modelos, schemas, servicos, repositorios e Dockerfile.
- `docs/`: documentacao de arquitetura, rotas, fluxo e deploy.
- `frontend/`: frontend estatico publicado no GitHub Pages.
- `infrastructure/`: modulos e exemplos Terraform/Ansible.

## Stack atual

- Frontend: HTML/CSS/JavaScript estatico.
- Backend: FastAPI + SQLAlchemy + Pydantic.
- Banco: Supabase Postgres em producao; SQLite apenas para desenvolvimento local.
- Deploy: GitHub Pages para frontend e Render Docker para backend.
- Integracoes: GitHub OAuth, OpenAI/Gemini opcionais, catalogos de precos AWS/GCP/Azure/OCI com fallback.

## URLs de producao

- Frontend: `https://joao19921.github.io/CloudHelm/`
- Backend: `https://cloudhelm-platform.onrender.com`
- Healthcheck: `https://cloudhelm-platform.onrender.com/health`

## Documentacao principal

- `docs/ARCHITECTURE.md`: arquitetura atual da aplicacao.
- `docs/API_ROUTES.md`: rotas publicas e protegidas da API.
- `docs/SYSTEM_FLOW.md`: fluxo funcional ponta a ponta.
- `docs/DEPLOYMENT_FREE.md`: deploy gratuito com GitHub Pages, Render e Supabase.
- `docs/TESTING.md`: orientacoes de teste.
- `docs/FRONTEND_PERFORMANCE.md`: responsividade e performance do frontend.

## Execucao local do backend

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

No Windows PowerShell, ative a venv com `.venv\\Scripts\\Activate.ps1`.

## Observacoes de versionamento

- `api/.env` nunca deve ser commitado.
- Bancos locais (`*.db`, `*.sqlite`) nao devem entrar no Git.
- Exportacoes geradas pelo catalogo (`api/dist_cloud_data/`) sao artefatos runtime.

## CI/CD

- GitHub Actions valida backend e frontend em `main`; detalhes em `docs/CI_CD.md`.
