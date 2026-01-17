import logging
import sys

from dotenv import load_dotenv

from .apollo_client import ApolloClient
from .config import Config
from .deduplication import DeduplicationService
from .sheets_client import SheetsClient
from .theirstack_client import TheirStackClient


def setup_logging(level: str) -> logging.Logger:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("theirstack-sync")


def main() -> int:
    """Main sync orchestration."""
    # Load .env file if present (for local development)
    load_dotenv()

    # Load configuration
    try:
        config = Config.from_env()
    except KeyError as e:
        print(f"Missing required environment variable: {e}")
        return 1

    logger = setup_logging(config.log_level)
    logger.info("Starting TheirStack to Apollo sync")

    try:
        # Initialize clients
        theirstack = TheirStackClient(config)
        sheets = SheetsClient(config)
        apollo = ApolloClient(config)
        dedup = DeduplicationService(sheets)

        logger.info(f"Fetching up to {config.sync_max_companies} companies that added Apollo.io in last {config.sync_lookback_days} days")

        # Fetch companies from TheirStack (sorted by most recent tech detection)
        companies = theirstack.search_companies_by_technology(
            technology_slug="apollo-io",
            limit=config.sync_max_companies,
        )
        logger.info(f"Found {len(companies)} companies from TheirStack")

        if not companies:
            logger.info("No companies found. Exiting.")
            return 0

        # Deduplicate against existing data in sheet
        new_companies = dedup.filter_new_companies(companies)
        logger.info(f"{len(new_companies)} companies are new (not in sheet)")

        if not new_companies:
            logger.info("All companies already processed. Exiting.")
            return 0

        # Write to Google Sheets
        sheets.append_companies(new_companies)
        logger.info(f"Added {len(new_companies)} companies to Google Sheets")

        # Add to Apollo list
        result = apollo.bulk_create_accounts(
            companies=new_companies,
            list_id=config.apollo_list_id,
        )
        logger.info(
            f"Apollo sync complete: {result['created']} created, "
            f"{result['existing']} already existed"
        )

        logger.info("Sync completed successfully")
        return 0

    except Exception as e:
        logger.exception(f"Sync failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
