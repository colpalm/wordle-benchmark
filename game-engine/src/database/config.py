"""Database configuration for different environments."""

import os
from abc import ABC, abstractmethod
from typing import Optional


class DatabaseConfig(ABC):
    """Base database configuration class."""

    @property
    @abstractmethod
    def database_url(self) -> str:
        """Return the database connection URL."""
        pass

    @property
    def echo_sql(self) -> bool:
        """Whether to echo SQL statements for debugging."""
        return False


class LocalDevConfig(DatabaseConfig):
    """
    Local development database configuration.
    
    For running the full application locally during development.
    Assumes a persistent PostgreSQL database is already running.
    """

    def __init__(self, database_url: Optional[str] = None):
        self._database_url = database_url

    @property
    def database_url(self) -> str:
        if self._database_url:
            return self._database_url

        # Default local PostgreSQL setup
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'postgres')
        database = os.getenv('DB_NAME', 'wordle_benchmark_dev')

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    @property
    def echo_sql(self) -> bool:
        return os.getenv('DB_ECHO_SQL', 'false').lower() == 'true'


class ProductionConfig(DatabaseConfig):
    """Production database configuration."""

    def __init__(self, database_url: Optional[str] = None):
        self._database_url = database_url

    @property
    def database_url(self) -> str:
        if self._database_url:
            return self._database_url

        # Production should always use an explicit environment variable
        url = os.getenv('DATABASE_URL')
        if not url:
            raise ValueError(
                "DATABASE_URL environment variable is required for production"
            )
        return url

    @property
    def echo_sql(self) -> bool:
        # Never echo SQL in production unless explicitly enabled
        return os.getenv('DB_ECHO_SQL', 'false').lower() == 'true'


class AnalysisConfig(DatabaseConfig):
    """Analysis environment database configuration."""

    def __init__(self, database_url: Optional[str] = None):
        self._database_url = database_url

    @property
    def database_url(self) -> str:
        if self._database_url:
            return self._database_url

        # Analysis environment setup
        host = os.getenv('ANALYSIS_DB_HOST', 'localhost')
        port = os.getenv('ANALYSIS_DB_PORT', '5432')
        user = os.getenv('ANALYSIS_DB_USER', 'postgres')
        password = os.getenv('ANALYSIS_DB_PASSWORD', 'postgres')
        database = os.getenv('ANALYSIS_DB_NAME', 'wordle_benchmark_analysis')

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    @property
    def echo_sql(self) -> bool:
        return os.getenv('ANALYSIS_DB_ECHO_SQL', 'false').lower() == 'true'


