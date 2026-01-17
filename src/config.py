import os
import json
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration loaded from environment variables."""

    # Required fields (no defaults) - must come first
    theirstack_api_key: str
    apollo_api_key: str
    apollo_list_id: str
    google_service_account: dict
    google_sheet_id: str

    # Optional fields (with defaults)
    theirstack_base_url: str = "https://api.theirstack.com/v1"
    apollo_base_url: str = "https://api.apollo.io/api/v1"
    google_sheet_name: str = "Sheet1"
    sync_max_companies: int = 200  # Total companies to fetch (paginated)
    sync_lookback_days: int = 30  # How far back to look for new tech installations
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        google_sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "{}")

        return cls(
            theirstack_api_key=os.environ["THEIRSTACK_API_KEY"],
            apollo_api_key=os.environ["APOLLO_API_KEY"],
            apollo_list_id=os.environ["APOLLO_LIST_ID"],
            google_service_account=json.loads(google_sa_json),
            google_sheet_id=os.environ["GOOGLE_SHEET_ID"],
            google_sheet_name=os.environ.get("GOOGLE_SHEET_NAME", "Sheet1"),
            sync_max_companies=int(os.environ.get("SYNC_MAX_COMPANIES", "200")),
            sync_lookback_days=int(os.environ.get("SYNC_LOOKBACK_DAYS", "30")),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )
