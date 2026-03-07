# CloudHelm V1

Local-first V1 for requirement intake, cloud mapping, architecture preview, and Terraform generation.

## Stack

- Backend: FastAPI (Python)
- UI: Server-rendered HTML + Tailwind CDN
- Database: MySQL (Docker) with SQLite fallback
- Infra local: Docker Compose

## Run Local

1. Copy env:

```bash
cp .env.example .env
```

2. Start:

```bash
docker compose up --build
```

3. Open:

`http://localhost:8000`

## Complete Setup Guide

- [Run Anywhere Guide](./docs/RUN_ANYWHERE.md)
- Prereq check scripts:
  - `./scripts/check-prereqs.ps1` (Windows)
  - `./scripts/check-prereqs.sh` (Linux/macOS)

## Main Features (V1)

- Login/register with JWT
- Demand input (text/audio transcript as text payload)
- Cloud provider selection (AWS, GCP, Azure)
- Modular architecture and monthly cost view
- Terraform snippets per provider and module
- Cloud catalog sync (AWS/GCP seeded baseline + Azure retail API)
- Fuzzy icon matching and static JSON export (`dist_cloud_data/cloud_master_data.json`)
- Audio upload + automatic transcription endpoint
- Provider ranking engine (cost + SLA + catalog signal)
- Multi-LLM POC: choose GPT or Gemini by API key at orchestration time

## API Overview

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/demands`
- `POST /api/demands/transcribe`
- `POST /api/demands/{id}/orchestrate`
- `GET /api/demands`
- `GET /api/providers`
- `GET /api/terraform/{provider}`
- `POST /api/catalog/sync`
- `GET /api/catalog/items`
- `GET /api/catalog/summary`

## V1.1 Notes

- Automatic transcription uses OpenAI when `OPENAI_API_KEY` is configured.
- Without key, the system uses local fallback transcript text to keep flow running.
- Provider ranking is returned in orchestration response (`ranking` field).
- Orchestration accepts optional `llm_provider`, `llm_model`, and `llm_api_key`.

## Cloud Catalog Job

Daily sync job script:

`backend/jobs/alimentador.py`

Run manually inside the app container:

```bash
python jobs/alimentador.py
```
