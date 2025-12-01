from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: Optional[str] = None  # Legacy - optional, use GOOGLE_API_KEY instead
    TAVILY_API_KEY: Optional[str] = None  # Legacy - ADK uses google_search
    JUDGE0_API_KEY: Optional[str] = None  # Optional - can use BuiltInCodeExecutor
    
    # Google ADK API Keys (Preferred)
    GOOGLE_API_KEY: Optional[str] = None  # Required for ADK/Gemini - preferred over OpenAI
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/interview_copilot"
    VECTOR_DB_PATH: str = "./data/vectordb"
    
    # Session Persistence
    SESSION_PERSISTENCE_ENABLED: bool = True
    SESSION_STORAGE_TYPE: str = "file"  # "file", "sqlite", or "database" (PostgreSQL via ADK)
    SESSION_STORAGE_PATH: str = "./data/sessions"  # Path for file/sqlite, or DATABASE_URL for database
    SESSION_EXPIRATION_HOURS: int = 168  # 7 days default
    
    # LLM Settings (Legacy - OpenAI)
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    
    # ADK/Gemini Settings
    ADK_MODEL: str = "gemini-2.0-flash-exp"  # Supports tools/function calling
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