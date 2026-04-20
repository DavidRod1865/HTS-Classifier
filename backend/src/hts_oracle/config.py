"""
Application configuration — loaded from environment variables.

Uses pydantic-settings to validate ALL required config at startup.
If any required key is missing, the app crashes immediately with a
clear error message instead of failing later during a user request.

Usage:
    from hts_oracle.config import get_settings
    settings = get_settings()
    print(settings.openai_api_key)
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Required API keys (no defaults = must be set) ---
    openai_api_key: str
    anthropic_api_key: str

    # --- Database ---
    # Connection string for Postgres with pgvector extension.
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    # The "+asyncpg" part tells SQLAlchemy to use the async driver.
    database_url: str = "postgresql+asyncpg://localhost:5432/hts_oracle"

    # --- Model configuration ---
    # text-embedding-3-small: 1536 dims, plenty for ~8K codes
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Claude model for disambiguation when vector search confidence is low
    claude_model: str = "claude-haiku-4-5-20251001"

    # --- Classification thresholds ---
    # Above this score: return results directly, zero LLM calls (fast + cheap)
    # Below this score: ask Claude to pick the best match or request more info
    high_confidence_threshold: float = 0.65
    batch_confidence_threshold: float = 0.55

    # How many clarifying questions before giving up and showing best results
    max_clarifications: int = 3

    # --- Search tuning ---
    # Fetch more candidates than we need, then take the top results.
    search_candidates: int = 30  # Fetch this many from pgvector
    search_top_k: int = 10       # Return this many to the user

    # --- Server ---
    port: int = 8080
    environment: str = "development"  # "development" or "production"

    # CORS: which frontend URLs can call our API
    # In dev this is localhost:5173 (Vite). In prod it's your Vercel/Netlify URL.
    # Stored as a comma-separated string so pydantic-settings doesn't try to JSON-parse it.
    cors_origins: str = "https://hts-oracle.netlify.app,http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # --- pydantic-settings config ---
    # Tells pydantic to read from a .env file and strip whitespace from values
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),  # Checks both; .env.local takes priority
        env_file_encoding="utf-8",
        extra="ignore",  # Don't crash on unknown env vars
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    lru_cache means the .env file is read once at startup, and every call
    after that returns the same object. This is important for performance and consistency across the app.
    """
    return Settings()