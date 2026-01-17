import logging
from typing import List

import requests

from .config import Config
from .models import Company

logger = logging.getLogger(__name__)


class TheirStackClient:
    """Client for TheirStack API."""

    def __init__(self, config: Config):
        self.base_url = config.theirstack_base_url
        self.headers = {
            "Authorization": f"Bearer {config.theirstack_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def search_companies_by_technology(
        self,
        technology_slug: str,
        limit: int = 25,
    ) -> List[Company]:
        """
        Search for companies that use a technology, sorted by most recent detection.

        Args:
            technology_slug: Technology identifier (e.g., "apollo-io")
            limit: Maximum results to return (max 25 for free plan)

        Returns:
            List of Company objects with tech detection dates
        """
        url = f"{self.base_url}/companies/search"

        payload = {
            "company_technology_slug_or": [technology_slug],
            "expand_technology_slugs": [technology_slug],  # Get detailed tech info
            "order_by": [{"desc": True, "field": "first_date_found"}],  # Most recent first
            "limit": limit,
            "page": 0,
        }

        logger.debug(f"TheirStack request: {payload}")

        response = requests.post(
            url, json=payload, headers=self.headers, timeout=30
        )

        if response.status_code != 200:
            logger.error(f"TheirStack API error: {response.status_code} - {response.text}")

        response.raise_for_status()

        data = response.json()
        companies = []

        for company_data in data.get("data", []):
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
                companies.append(
                    Company(
                        name=name,
                        domain=domain,
                        source="theirstack",
                        discovered_at=tech_added_date,
                    )
                )

        logger.info(f"TheirStack returned {len(companies)} companies")
        return companies
