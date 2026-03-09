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
