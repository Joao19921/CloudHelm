# CloudHelm - Proposed System Architecture

This document outlines the refactored, modern, and scalable architecture for the CloudHelm SaaS platform. The new design emphasizes a clear separation of concerns, maintainability, and cost-efficiency while adhering to industry best practices.

## 1. Guiding Principles

- **Separation of Concerns:** The frontend, backend, and infrastructure codebases are explicitly separated into distinct top-level directories (`frontend`, `api`, `infra`).
- **Modularity & Scalability:** The backend is structured by feature and versioned to allow for independent development and future expansion.
- **Developer Experience:** A standardized structure, modern tooling, and automated database migrations improve the development and onboarding process.
- **Production Ready:** Centralized configuration, structured error handling, and environment-aware settings make the platform robust and ready for deployment.
- **FinOps Mindset:** The architecture continues to leverage cost-effective solutions (GitHub Pages, Render's free/low-cost tiers) and avoids expensive managed services.

## 2. Proposed Folder Structure

The repository will be reorganized to clearly delineate the different parts of the system.

```
/
|-- .github/
|-- .vscode/
|-- api/                # NEW: All backend code
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py         # FastAPI app entry point
|   |   |-- config.py       # Centralized configuration
|   |   |-- deps.py         # FastAPI dependencies (e.g., get_current_user)
|   |   |-- middleware/     # Custom middleware
|   |   |   |-- error_handling.py
|   |   |-- models/         # SQLAlchemy models
|   |   |-- schemas/        # Pydantic schemas
|   |   |-- services/       # Business logic layer
|   |   |-- core/           # Core components (security, etc.)
|   |   |-- api_v1/         # NEW: Version 1 of the API
|   |       |-- __init__.py
|   |       |-- endpoints/    # NEW: Routers are now "endpoints"
|   |       |   |-- auth.py
|   |       |   |-- users.py
|   |       |   |-- projects.py
|   |       |-- router.py     # NEW: Includes all v1 endpoints
|   |-- migrations/       # NEW: Alembic for DB migrations
|   |-- tests/
|   |-- alembic.ini
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- .env.example
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |-- services/
|   |   |   `-- api.js      # NEW: Centralized API client
|   |   |-- App.jsx         # Or index.js if not using a framework
|   |   `-- main.jsx
|   |-- public/
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js    # Using Vite for a modern build process
|-- infra/                # NEW: All IaC
|   |-- terraform/
|   `-- ansible/
|-- docs/                 # NEW: Documentation
|   |-- ARCHITECTURE.md
|   |-- API_ROUTES.md
|   `-- SYSTEM_FLOW.md
|-- .gitignore
|-- render.yaml           # To be updated
`-- README.md
```

## 3. System Components & Flow

### 3.1. Frontend

- **Hosting:** Remains on **GitHub Pages** for a cost-effective, simple static hosting solution.
- **Framework:** The vanilla JavaScript will be restructured for a modern build tool like **Vite**. This is non-disruptive but allows for proper environment variable management (e.g., `import.meta.env.VITE_API_URL`) and future growth (e.g., introducing a framework like React).
- **API Communication:** A new centralized API service (`frontend/src/services/api.js`) will manage all `fetch` requests. It will use a single base URL from environment variables, eliminating hardcoded paths and routing inconsistencies.

### 3.2. Backend

- **Hosting:** Remains on **Render**, which offers a generous free tier for web services and PostgreSQL.
- **Framework:** **FastAPI** remains the framework of choice.
- **Structure:** The code is moved to `/api` and refactored into a modular, service-oriented architecture.
    - **`main.py`:** The main application entry point, responsible for creating the FastAPI app, adding middleware, and including the versioned API router.
    - **`api_v1/`:** A dedicated directory for version 1 of the API. This makes future upgrades (e.g., to `v2`) much cleaner.
    - **`endpoints/`:** Contains the API route handlers (previously `routers`), keeping them thin and focused on request/response handling.
    - **`services/`:** Contains the core business logic, extracted from the route handlers. This improves testability and reusability.
- **Database Migrations:** Manual SQL statements for schema changes will be replaced with **Alembic**, providing a robust, version-controlled migration system.

### 3.3. Database

- **Provider:** **Supabase** (PostgreSQL) remains the database provider. Its authentication features and managed PostgreSQL are a good fit for the project's scale and budget.

### 3.4. Infrastructure as Code (IaC)

- **Location:** All IaC (Terraform, Ansible) is consolidated into the `/infra` directory for clarity.
- **Usage:** No changes to the IaC strategy are proposed at this time, as it's already in place for potential future deployments beyond the free-tier services.

## 4. Key Improvements

- **API Versioning:** All backend routes will be prefixed with `/api/v1/`. This is a critical best practice for public-facing APIs.
- **Centralized Configuration:** Both frontend and backend will use environment variables (`.env` files and platform-native environment variable support) for configuration, removing hardcoded values.
- **Standardized Error Handling:** A custom middleware in FastAPI will catch all exceptions and format them into a consistent JSON response (`{ "success": false, "error": "..." }`), preventing generic 500 errors.
- **Authentication:** JWT usage will be standardized and enforced by FastAPI dependencies, ensuring protected routes are secure.
- **Documentation:** The `/docs` folder will serve as the single source of truth for architecture, API routes, and system flows. FastAPI's automatic Swagger/ReDoc generation will be the primary source for `API_ROUTES.md`.
