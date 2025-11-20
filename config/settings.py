from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    TAVILY_API_KEY: Optional[str] = None
    JUDGE0_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/interview_copilot"
    VECTOR_DB_PATH: str = "./data/vectordb"
    
    # LLM Settings
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    
    # Redis (optional)
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    
    # Observability
    LOG_LEVEL: str = "INFO"
    METRICS_PORT: int = 8001
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env file

settings = Settings()