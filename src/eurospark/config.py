from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    supabase_url: str
    supabase_key: str
    langsmith_api_key: str = ""
    langsmith_tracing: bool = False
    database_uri: str = ""           # only needed on Render for PostgresSaver

settings = Settings()