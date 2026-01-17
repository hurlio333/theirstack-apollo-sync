import logging
from typing import List, Set

import gspread

from .config import Config
from .models import Company

logger = logging.getLogger(__name__)


class SheetsClient:
    """Client for Google Sheets API."""

    def __init__(self, config: Config):
        self.gc = gspread.service_account_from_dict(config.google_service_account)
        self.spreadsheet = self.gc.open_by_key(config.google_sheet_id)
        self.worksheet = self.spreadsheet.worksheet(config.google_sheet_name)

    def get_existing_domains(self) -> Set[str]:
        """
        Get all domains already in the sheet.

        Returns:
            Set of domain strings (lowercase)
        """
        values = self.worksheet.get_all_values()

        if not values:
            return set()

        # Skip header row, get domain column (index 1)
        domains = set()
        for row in values[1:]:
            if len(row) > 1 and row[1]:
                domains.add(row[1].lower().strip())

        logger.debug(f"Found {len(domains)} existing domains in sheet")
        return domains

    def append_companies(self, companies: List[Company]) -> None:
        """
        Append companies to the sheet.

        Args:
            companies: List of Company objects to add
        """
        if not companies:
            return

        # Ensure header exists
        existing = self.worksheet.get_all_values()
        if not existing:
            self.worksheet.append_row(
                ["Company Name", "Domain", "Source", "Tech Added Date"],
                value_input_option="RAW",
            )

        # Prepare rows
        rows = [
            [c.name, c.domain, c.source, c.discovered_at or ""]
            for c in companies
        ]

        # Batch append
        self.worksheet.append_rows(rows, value_input_option="RAW")
        logger.info(f"Appended {len(rows)} rows to Google Sheet")
