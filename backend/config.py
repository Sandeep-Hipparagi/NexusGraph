"""Configuration module for NexusGraph."""

from functools import lru_cache
from typing import Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """NexusGraph configuration settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    falkordb_password: Optional[str] = None
    falkordb_username: Optional[str] = None

    app_env: str = "development"
    default_tenant_id: str = "acme_corp"
    openai_api_key: Optional[str] = None

    # LLM Settings (OpenAI, Gemini, Groq, Ollama compatible)
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: str = "gpt-4o"

    @property
    def effective_llm_key(self) -> Optional[str]:
        return self.llm_api_key or self.openai_api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

    @property
    def falkordb_url(self) -> str:
        """Return the redis/bolt URL for FalkorDB."""
        if self.falkordb_password:
            auth = f":{self.falkordb_password}@"
            if self.falkordb_username:
                auth = f"{self.falkordb_username}:{self.falkordb_password}@"
            return f"redis://{auth}{self.falkordb_host}:{self.falkordb_port}"
        return f"redis://{self.falkordb_host}:{self.falkordb_port}"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
