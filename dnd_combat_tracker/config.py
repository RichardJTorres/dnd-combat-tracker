from pydantic_settings import BaseSettings

VALID_PROVIDERS = {"claude", "gemini", "openai", "ollama"}


class Settings(BaseSettings):
    database_url: str = "sqlite:///./dnd_combat_tracker.db"
    port: int = 8000

    # AI provider API keys
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
