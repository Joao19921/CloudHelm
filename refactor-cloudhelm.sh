#!/bin/bash

echo "Starting CloudHelm refactor..."

# Create new structure
mkdir -p api/routes
mkdir -p api/services
mkdir -p api/models
mkdir -p api/middleware
mkdir -p api/config
mkdir -p docs
mkdir -p infrastructure

# Move backend if exists
if [ -d "platform-v1" ]; then
  echo "Moving backend from platform-v1 to api"
  mv platform-v1/* api/
fi

# Move terraform and ansible
if [ -d "terraform" ]; then
  mv terraform infrastructure/
fi

if [ -d "ansible" ]; then
  mv ansible infrastructure/
fi

# Create API version structure placeholder
mkdir -p api/routes/auth
mkdir -p api/routes/users
mkdir -p api/routes/projects

# Create documentation files
touch docs/API_ROUTES.md
touch docs/ARCHITECTURE.md
touch docs/SYSTEM_FLOW.md
touch docs/MICROSERVICES.md

# Create config file
cat <<EOF > api/config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CloudHelm"
    API_VERSION: str = "v1"

settings = Settings()
EOF

# Create base router example
cat <<EOF > api/routes/auth.py
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login():
    return {"success": True}
EOF

# Create main API file if not exists
if [ ! -f "api/main.py" ]; then
cat <<EOF > api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import auth

app = FastAPI(title="CloudHelm API")

origins = [
    "http://localhost:5173",
    "https://joao19921.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
EOF
fi

echo "Refactor completed."
echo "Next step: review files and commit changes."
