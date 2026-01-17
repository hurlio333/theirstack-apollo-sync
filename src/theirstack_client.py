import logging
from datetime import datetime, timedelta
from typing import List

import requests

from .config import Config
from .models import Company

logger = logging.getLogger(__name__)

# TheirStack API returns max 25 results per page
PAGE_SIZE = 25


class TheirStackClient:
    """Client for TheirStack API."""

    def __init__(self, config: Config):
        self.base_url = config.theirstack_base_url
        self.lookback_days = config.sync_lookback_days
        self.headers = {
            "Authorization": f"Bearer {config.theirstack_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def search_companies_by_technology(
        self,
        technology_slug: str,
        limit: int = 200,
    ) -> List[Company]:
        """
        Search for companies that recently added a technology, with pagination.

        Fetches companies where the specified technology was first detected
        within the lookback period, sorted by most recent detection first.

        Args:
            technology_slug: Technology identifier (e.g., "apollo-io")
            limit: Total maximum results to return (will paginate to get all)

        Returns:
            List of Company objects with tech detection dates, newest first
        """
        url = f"{self.base_url}/companies/search"

        # Calculate date range - only get companies that added tech recently
        lookback_date = (datetime.now() - timedelta(days=self.lookback_days)).strftime("%Y-%m-%d")

        all_companies = []
        page = 0

        while len(all_companies) < limit:
            payload = {
                "company_technology_slug_or": [technology_slug],
                "expand_technology_slugs": [technology_slug],
                "tech_filters": {
                    # Only companies where this tech was FIRST detected after lookback date
                    "first_date_found_gte": lookback_date,
                },
                "order_by": [{"desc": True, "field": "first_date_found"}],
                "limit": PAGE_SIZE,
                "page": page,
            }

            logger.debug(f"TheirStack request page {page}: {payload}")

            response = requests.post(
                url, json=payload, headers=self.headers, timeout=30
            )

            if response.status_code != 200:
                logger.error(f"TheirStack API error: {response.status_code} - {response.text}")

            response.raise_for_status()

            data = response.json()
            page_data = data.get("data", [])

            if not page_data:
                # No more results
                logger.debug(f"No more results at page {page}")
                break

            for company_data in page_data:
                name = company_data.get("name", "")
                domain = company_data.get("domain", "")

                # Extract the tech detection date from expanded technology details
                tech_added_date = None
                technologies = company_data.get("technologies", [])
                for tech in technologies:
                    if tech.get("slug") == technology_slug:
                        tech_added_date = tech.get("first_date_found")
                        break

                if name and domain:
                    all_companies.append(
                        Company(
                            name=name,
                            domain=domain,
                            source="theirstack",
                            discovered_at=tech_added_date,
                        )
                    )

            logger.info(f"Page {page}: fetched {len(page_data)} companies (total: {len(all_companies)})")

            # Stop if we got fewer than a full page (no more results)
            if len(page_data) < PAGE_SIZE:
                break

            page += 1

        # Trim to requested limit
        all_companies = all_companies[:limit]

        logger.info(f"TheirStack returned {len(all_companies)} companies that added {technology_slug} in last {self.lookback_days} days")
        return all_companies
