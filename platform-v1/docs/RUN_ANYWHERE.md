# CloudHelm V1 - Run Anywhere (Supabase First)

## 1) Mandatory prerequisites

- Git 2.40+
- Docker Desktop 4.29+ (Compose v2 enabled)
- Free port: `8000`
- A Supabase project (Free tier works for POC)

## 2) Clone and bootstrap

```bash
git clone https://github.com/Joao19921/CloudHelm.git
cd CloudHelm/platform-v1
cp .env.example .env
```

Windows PowerShell:

```powershell
git clone https://github.com/Joao19921/CloudHelm.git
cd CloudHelm/platform-v1
Copy-Item .env.example .env
```

## 3) Configure environment (`.env`)

Required:

- `APP_NAME=CloudHelm`
- `SECRET_KEY=<strong-random-secret>`
- `ACCESS_TOKEN_EXPIRE_MINUTES=120`
- `DATABASE_URL=postgresql+psycopg://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require`
- `GITHUB_CLIENT_ID=<github-oauth-client-id>`
- `GITHUB_CLIENT_SECRET=<github-oauth-client-secret>`
- `GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback`
- `GITHUB_ADMIN_LOGINS=<your_github_login>`
- `FRONTEND_PUBLIC_URL=http://localhost:8000`
- `CORS_ORIGINS=http://localhost:8000`

Optional:

- `OPENAI_API_KEY=`
- `GEMINI_API_KEY=`
- `OPENAI_CHAT_MODEL=gpt-4o-mini`
- `GEMINI_MODEL=gemini-1.5-flash`
- `TRANSCRIBE_MODEL=whisper-1`

## 4) Run with Docker

```bash
docker compose up --build
```

Windows PowerShell (if `docker` is not in PATH):

```powershell
& "C:\Program Files\Docker\Docker\resources\bin\docker.exe" compose up --build
```

Access:

- App: `http://localhost:8000`
- Backoffice: `http://localhost:8000/backoffice`
- Health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## 5) GitHub OAuth configuration

In GitHub OAuth App:

- Homepage URL: `http://localhost:8000`
- Callback URL: `http://localhost:8000/api/auth/github/callback`

For production:

- Set `GITHUB_REDIRECT_URI` to your backend callback URL.
- Set `FRONTEND_PUBLIC_URL` to your GitHub Pages URL.
- Include your GitHub Pages domain in `CORS_ORIGINS`.

## 6) First functional flow

1. Login with GitHub on `/`.
2. If pending approval, access `/backoffice` with admin user.
3. Approve users in Backoffice.
4. Set internal LLM provider/model/key in Backoffice.
5. Create demand and run orchestration in main app.

## 6.1) Frontend on GitHub Pages

1. Configure `frontend/config.js`:
  - `API_BASE_URL=https://<your-backend-domain>`
  - `FRONTEND_HOME_URL=https://<user>.github.io/<repo>/`
  - `FRONTEND_BACKOFFICE_URL=https://<user>.github.io/<repo>/backoffice.html`
2. Push to `main`.
3. GitHub Actions workflow `github-pages.yml` publishes automatically.
4. Access:
  - `https://<user>.github.io/<repo>/`
  - `https://<user>.github.io/<repo>/backoffice.html`

## 7) Without Docker (fallback)

Inside `platform-v1/backend`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 8) Troubleshooting

- `GitHub OAuth not configured`:
  - Fill `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`.
- DB connection error:
  - Validate Supabase `DATABASE_URL`, password, project ref, and `sslmode=require`.
- `open //./pipe/docker_engine: Access is denied`:
  - Open PowerShell as Administrator and validate `docker info`.
- Port 8000 busy:
  - Change compose mapping to `8001:8000`.

## 9) API route list

- `GET /api/auth/github/url`
- `GET /api/auth/github/callback`
- `GET /api/auth/session`
- `POST /api/demands`
- `GET /api/demands`
- `POST /api/demands/{demand_id}/orchestrate`
- `POST /api/demands/transcribe`
- `POST /api/catalog/sync`
- `GET /api/catalog/items`
- `GET /api/catalog/summary`
- `GET /api/backoffice/users`
- `POST /api/backoffice/users/{user_id}/approve`
- `POST /api/backoffice/users/{user_id}/revoke`
- `GET /api/backoffice/llm-config`
- `PUT /api/backoffice/llm-config`
