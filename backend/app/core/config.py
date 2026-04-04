from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。"""

    app_name: str = "TauClear Graph Platform API"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change_me"
    graph_source: str = "mock"
    mock_data_file: str = "backend/data/mock_data.json"
    template_graph_file: str = "backend/data/template_graphs.json"
    molecule_descriptor_file: str = "data/molecule/molecule_descriptors.csv"
    molecule_fingerprint_file: str = "data/molecule/molecule_fingerprints.csv"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
