from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CloudHelm"
    API_VERSION: str = "v1"

settings = Settings()
