from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- AWS ---
    AWS_REGION: str = Field(
        default="us-east-2",
        description="AWS region for all services.",
    )

    # --- AgentCore Memory ---
    AGENTCORE_MEMORY_ID: str = Field(
        default="",
        description="Bedrock AgentCore Memory resource ID for user preferences.",
    )

    # --- Google Places API ---
    GOOGLE_PLACES_API_KEY: str = Field(
        default="",
        description="API key for Google Places API (New).",
    )

    # --- OpenRouteService API ---
    OPEN_ROUTE_SERVICE_API_KEY: str = Field(
        default="",
        description="API key for OpenRouteService (routing, geocoding).",
    )

    # --- Bedrock Prompt Management ---
    BEDROCK_PROMPT_ID: str = Field(
        default="",
        description="Bedrock Prompt Management prompt identifier for the agent scope prompt.",
    )
    PROMPT_CACHE_TTL_SECONDS: int = Field(
        default=300,
        description="TTL in seconds for the prompt text cache.",
    )


settings = Settings()
