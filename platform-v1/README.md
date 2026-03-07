# CloudHelm V1 (Supabase)

CloudHelm is a web platform to orchestrate requirements, suggest cloud architecture, estimate monthly cost, and generate Terraform modules.

## Stack

- Backend: FastAPI (Python 3.12)
- Frontend: GitHub Pages static site (`/frontend`)
- Database: Supabase Postgres (primary)
- Auth: GitHub OAuth + admin approval gate
- Runtime: Docker Compose (app service)

## Quick Start

1. Clone and enter folder:

```bash
git clone https://github.com/Joao19921/CloudHelm.git
cd CloudHelm/platform-v1
```

2. Create `.env`:

```bash
cp .env.example .env
```

3. Fill required env vars in `.env`:

- `DATABASE_URL` (Supabase connection string with `sslmode=require`)
- `SECRET_KEY`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GITHUB_REDIRECT_URI`
- `GITHUB_ADMIN_LOGINS`
- `FRONTEND_PUBLIC_URL`
- `CORS_ORIGINS`

4. Run:

```bash
docker compose up --build
```

Windows PowerShell (if `docker` is not in PATH):

```powershell
& "C:\Program Files\Docker\Docker\resources\bin\docker.exe" compose up --build
```

5. Open backend locally:

- App: `http://localhost:8000`
- Backoffice: `http://localhost:8000/backoffice`
- Health: `http://localhost:8000/health`

## Frontend on GitHub Pages

- Static frontend files are in `../frontend`.
- Configure `frontend/config.js`:
  - `API_BASE_URL`: public backend URL
  - `FRONTEND_HOME_URL`: GitHub Pages root URL
  - `FRONTEND_BACKOFFICE_URL`: GitHub Pages backoffice URL
- Workflow `.github/workflows/github-pages.yml` publishes automatically on push to `main`.

## GitHub OAuth Setup

Create a GitHub OAuth App and configure:

- Homepage URL: `http://localhost:8000`
- Authorization callback URL: `http://localhost:8000/api/auth/github/callback`

For production:

- GitHub callback must point to your backend callback endpoint.
- Set backend env `FRONTEND_PUBLIC_URL` to your GitHub Pages URL so token redirect returns to frontend.

## Main Features

- Requirement intake (text/audio)
- Automatic transcription endpoint
- Provider selection (`aws`, `gcp`, `azure`, `auto`)
- Architecture/cost/terraform orchestration
- Cloud catalog sync and provider ranking
- Backoffice for:
  - LLM provider/model/API key control (internal only)
  - User approval and access revocation

## Web Routes

- `GET /` main application
- `GET /backoffice` admin backoffice
- `GET /health` service health
- `GET /docs` Swagger UI
- `GET /openapi.json` OpenAPI schema

GitHub Pages frontend routes:

- `/` (index.html)
- `/backoffice.html`

## API Overview

- Auth:
  - `GET /api/auth/github/url`
  - `GET /api/auth/github/callback`
  - `GET /api/auth/session`
- Demands:
  - `POST /api/demands`
  - `GET /api/demands`
  - `POST /api/demands/{demand_id}/orchestrate`
  - `POST /api/demands/transcribe`
- Catalog:
  - `POST /api/catalog/sync`
  - `GET /api/catalog/items`
  - `GET /api/catalog/summary`
- Backoffice:
  - `GET /api/backoffice/users`
  - `POST /api/backoffice/users/{user_id}/approve`
  - `POST /api/backoffice/users/{user_id}/revoke`
  - `GET /api/backoffice/llm-config`
  - `PUT /api/backoffice/llm-config`

## Notes

- If you need local-only fallback, use:
  - `DATABASE_URL=sqlite:///./cloudhelm.db`
- Full operational guide:
  - [docs/RUN_ANYWHERE.md](./docs/RUN_ANYWHERE.md)
