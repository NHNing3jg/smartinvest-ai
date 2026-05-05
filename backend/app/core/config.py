import os
from pathlib import Path
from urllib.parse import quote_plus


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent
DB_ENV_VARS = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")


class DatabaseConfigError(RuntimeError):
    """Raised when required database configuration is missing or invalid."""


def _load_dotenv_files() -> None:
    env_paths = (BACKEND_ROOT / ".env", PROJECT_ROOT / ".env")

    try:
        from dotenv import load_dotenv
    except ImportError:
        for env_path in env_paths:
            _load_env_file(env_path)
        return

    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
            continue

        key, value = stripped_line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")

        if key and key not in os.environ:
            os.environ[key] = value


class Settings:
    def __init__(self) -> None:
        _load_dotenv_files()

        self.DB_HOST = os.getenv("DB_HOST")
        self.DB_PORT = os.getenv("DB_PORT")
        self.DB_NAME = os.getenv("DB_NAME")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")

    @property
    def db_host(self) -> str | None:
        return self.DB_HOST

    @property
    def db_port(self) -> int | None:
        if not self.DB_PORT:
            return None

        try:
            return int(self.DB_PORT)
        except ValueError as exc:
            raise DatabaseConfigError("DB_PORT must be an integer.") from exc

    @property
    def db_name(self) -> str | None:
        return self.DB_NAME

    @property
    def db_user(self) -> str | None:
        return self.DB_USER

    @property
    def db_password(self) -> str | None:
        return self.DB_PASSWORD

    @property
    def DATABASE_URL(self) -> str:
        self.require_database_settings()

        username = quote_plus(str(self.DB_USER))
        password = quote_plus(str(self.DB_PASSWORD))
        host = str(self.DB_HOST)
        port = str(self.DB_PORT)
        database = str(self.DB_NAME)

        return (
            f"postgresql+psycopg2://{username}:{password}"
            f"@{host}:{port}/{database}"
        )

    def missing_database_variables(self) -> list[str]:
        return [variable for variable in DB_ENV_VARS if not getattr(self, variable)]

    def require_database_settings(self) -> None:
        missing_variables = self.missing_database_variables()
        if missing_variables:
            missing = ", ".join(missing_variables)
            raise DatabaseConfigError(
                f"Missing required database environment variables: {missing}."
            )

        _ = self.db_port


settings = Settings()
