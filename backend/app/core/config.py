from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
_BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_ROOT_ENV if _ROOT_ENV.exists() else _BACKEND_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "portfolio123"
    neo4j_database: str = "neo4j"

    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    graph_node_limit: int = 80
    graph_node_limit_complete: int = 500
    cypher_timeout_seconds: float = 5.0
    sector_exposure_min_percent: float = 40.0

    disclaimer: str = "Synthetic data. Estimated exposure only. Not investment advice."


settings = Settings()
