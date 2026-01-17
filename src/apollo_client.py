import logging
from typing import Dict, List

import requests

from .config import Config
from .models import Company

logger = logging.getLogger(__name__)


class ApolloClient:
    """Client for Apollo.io API."""

    def __init__(self, config: Config):
        self.base_url = config.apollo_base_url
        self.api_key = config.apollo_api_key
        self.list_id = config.apollo_list_id

    def bulk_create_accounts(
        self,
        companies: List[Company],
        list_id: str = None,
    ) -> Dict[str, int]:
        """
        Bulk create accounts in Apollo and add to a list.

        Args:
            companies: List of Company objects
            list_id: Apollo list ID to add accounts to (uses config default if None)

        Returns:
            Dict with 'created' and 'existing' counts
        """
        if not companies:
            return {"created": 0, "existing": 0}

        list_id = list_id or self.list_id
        url = f"{self.base_url}/accounts/bulk_create"

        # Prepare accounts payload
        accounts = [
            {
                "name": company.name,
                "domain": company.domain,
                "account_list_ids": [list_id],
            }
            for company in companies
        ]

        # Process in batches of 100 (Apollo limit)
        created = 0
        existing = 0

        for i in range(0, len(accounts), 100):
            batch = accounts[i : i + 100]

            payload = {
                "api_key": self.api_key,
                "accounts": batch,
            }

            logger.debug(f"Apollo batch {i // 100 + 1}: {len(batch)} accounts")

            response = requests.post(url, json=payload, timeout=60)

            logger.debug(f"Apollo response status: {response.status_code}")
            logger.debug(f"Apollo response: {response.text[:500]}")

            response.raise_for_status()

            result = response.json()
            batch_created = len(result.get("new_accounts", []))
            batch_existing = len(result.get("existing_accounts", []))

            created += batch_created
            existing += batch_existing

            logger.debug(
                f"Batch result: {batch_created} created, {batch_existing} existing"
            )

        logger.info(
            f"Apollo sync complete: {created} created, {existing} already existed"
        )
        return {"created": created, "existing": existing}
