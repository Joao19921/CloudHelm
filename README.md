# CloudHelm

Official repository for the **CloudHelm** product.

## Structure

- `.agent/`: internal agents, skills, and orchestration workflows.
- `platform-v1/`: backend API (FastAPI), orchestration logic, auth/backoffice.
- `frontend/`: static frontend for GitHub Pages.

## Deployment Model

- Frontend: GitHub Pages (`frontend/`)
- Backend API: public FastAPI runtime (Render/Railway/Fly/etc.)
- Database: Supabase Postgres

## Setup Guides

- [`platform-v1/README.md`](platform-v1/README.md)
- [`platform-v1/docs/RUN_ANYWHERE.md`](platform-v1/docs/RUN_ANYWHERE.md)
