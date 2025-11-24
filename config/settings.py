from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str  # Legacy - will be replaced by GOOGLE_API_KEY
    TAVILY_API_KEY: Optional[str] = None  # Legacy - ADK uses google_search
    JUDGE0_API_KEY: Optional[str] = None  # Optional - can use BuiltInCodeExecutor
    
    # Google ADK API Keys
    GOOGLE_API_KEY: Optional[str] = None  # Required for ADK/Gemini
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/interview_copilot"
    VECTOR_DB_PATH: str = "./data/vectordb"
    
    # Session Persistence
    SESSION_PERSISTENCE_ENABLED: bool = True
    SESSION_STORAGE_TYPE: str = "file"  # "file" or "sqlite"
    SESSION_STORAGE_PATH: str = "./data/sessions"
    SESSION_EXPIRATION_HOURS: int = 168  # 7 days default
    
    # LLM Settings (Legacy - OpenAI)
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    
    # ADK/Gemini Settings
    ADK_MODEL: str = "gemini-2.5-flash-lite"  # Default ADK model
    ADK_TEMPERATURE: float = 0.7
    ADK_RETRY_ATTEMPTS: int = 5
    ADK_RETRY_BASE: int = 7
    ADK_INITIAL_DELAY: int = 1
    
    # Redis (optional)
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    
    # Observability
    LOG_LEVEL: str = "INFO"
    METRICS_PORT: int = 8001
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env file

settings = Settings()