from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = ""
    JWT_SECRET: str = ""
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    DEBUG: bool = False
    ANALYTICS_ENABLED: bool = False
    R2_ACCESS_KEY: str = ""
    R2_SECRET_KEY: str = ""
    R2_BUCKET: str = ""
    R2_ENDPOINT: str = ""
    WORDPRESS_GRAPHQL_URL: str | None = None


settings = Settings()
