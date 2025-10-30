import os
from typing import Optional


class Settings:
    """Application settings with code-defaults that can be overridden by env vars.

    Edit the defaults below when copying this MCP server to a new PingOne env.
    """

    # Hardcoded defaults (edit these values for your PingOne environment)
    PINGONE_CLIENT_ID: Optional[str] = None
    PINGONE_CLIENT_SECRET: Optional[str] = None
    PINGONE_ENV_ID: Optional[str] = None
    PINGONE_DECISION_ID: Optional[str] = None  # Back-compat
    PINGONE_DECISION_ENDPOINT_ID: Optional[str] = None  # Preferred

    # Token URL typically does not change except for regional differences
    PINGONE_TOKEN_URL: str = "https://auth.pingone.com/as/token"

    # API base for management/authorize calls (adjust TLD for your region)
    PINGONE_API_BASE: str = "https://api.pingone.com/v1"

    def with_env_overrides(self) -> "Settings":
        """Return a copy with environment variables applied as overrides."""
        clone = Settings()
        clone.PINGONE_CLIENT_ID = os.getenv("PINGONE_CLIENT_ID", self.PINGONE_CLIENT_ID)
        clone.PINGONE_CLIENT_SECRET = os.getenv("PINGONE_CLIENT_SECRET", self.PINGONE_CLIENT_SECRET)
        clone.PINGONE_ENV_ID = os.getenv("PINGONE_ENV_ID", self.PINGONE_ENV_ID)
        # Prefer DECISION_ENDPOINT_ID if present; otherwise DECISION_ID
        clone.PINGONE_DECISION_ENDPOINT_ID = os.getenv("PINGONE_DECISION_ENDPOINT_ID", self.PINGONE_DECISION_ENDPOINT_ID)
        clone.PINGONE_DECISION_ID = os.getenv("PINGONE_DECISION_ID", self.PINGONE_DECISION_ID)
        if not clone.PINGONE_DECISION_ENDPOINT_ID and clone.PINGONE_DECISION_ID:
            clone.PINGONE_DECISION_ENDPOINT_ID = clone.PINGONE_DECISION_ID
        clone.PINGONE_TOKEN_URL = os.getenv("PINGONE_TOKEN_URL", self.PINGONE_TOKEN_URL)
        clone.PINGONE_API_BASE = os.getenv("PINGONE_API_BASE", self.PINGONE_API_BASE)
        return clone


settings = Settings().with_env_overrides()
