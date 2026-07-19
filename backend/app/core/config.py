from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central app configuration. Values are read from environment variables
    or a .env file — never hardcode secrets here.
    """

    database_url: str = "postgresql://datapilot:datapilot@localhost:5432/datapilot"

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    llm_provider: str = "groq"
    groq_api_key: str = ""

    embedding_backend: str = "hashing"  # "hashing" (default, offline) or "sentence-transformers"
    chroma_persist_dir: str = "./chroma_store"

    # Comma-separated list of allowed frontend origins for CORS.
    # Local dev origins are always included; add your deployed Vercel URL here
    # (as an env var in Render's dashboard) once you deploy — e.g.
    # ALLOWED_ORIGINS=https://your-app.vercel.app
    allowed_origins: str = ""

    upload_dir: str = "./uploaded_files"
    max_upload_mb: int = 25

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
