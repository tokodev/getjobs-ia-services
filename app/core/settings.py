from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str = "redis://localhost:6379/0"
    
    LITELLM_URL: str = "http://localhost:4000"
    LITELLM_API_KEY: str = "sk-litellm-getjobs-2026-master-key"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/getjobs?schema=public"
    
    # LangSmith
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "getjobs-ia-services"
    
    # BullMQ Queues
    BULLMQ_QUEUE_NAME: str = "cv-extraction"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
