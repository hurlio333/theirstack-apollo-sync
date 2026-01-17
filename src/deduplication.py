import logging
from typing import List, Set

from .models import Company
from .sheets_client import SheetsClient

logger = logging.getLogger(__name__)


class DeduplicationService:
    """
    Handles deduplication of companies.

    Strategy:
    1. Primary key: domain (normalized to lowercase)
    2. Source of truth: Google Sheets (persisted state)
    3. Apollo has built-in deduplication, but we dedupe beforehand
       to avoid unnecessary API calls
    """

    def __init__(self, sheets_client: SheetsClient):
        self.sheets = sheets_client
        self._existing_domains: Set[str] = None

    def _load_existing_domains(self) -> Set[str]:
        """Lazy load existing domains from sheet."""
        if self._existing_domains is None:
            self._existing_domains = self.sheets.get_existing_domains()
        return self._existing_domains

    def filter_new_companies(self, companies: List[Company]) -> List[Company]:
        """
        Filter out companies that already exist.

        Args:
            companies: List of companies to filter

        Returns:
            List of companies not already in the sheet
        """
        existing = self._load_existing_domains()

        new_companies = []
        seen_in_batch = set()  # Also dedupe within the batch

        for company in companies:
            domain_normalized = company.domain.lower().strip()

            if not domain_normalized:
                logger.debug(f"Skipping company without domain: {company.name}")
                continue

            if domain_normalized in existing:
                logger.debug(f"Skipping existing domain: {domain_normalized}")
                continue

            if domain_normalized in seen_in_batch:
                logger.debug(f"Skipping duplicate in batch: {domain_normalized}")
                continue

            seen_in_batch.add(domain_normalized)
            new_companies.append(company)

        logger.info(
            f"Deduplication: {len(companies)} input -> {len(new_companies)} new"
        )
        return new_companies
