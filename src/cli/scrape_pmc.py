import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from services.repositories import JsonFolderPaperRepository
from services.pmc_scraper_service import PmcScraperService

def main() -> None:

    search_url = "https://pmc.ncbi.nlm.nih.gov/search/?term=mental+health"
    max_articles = 50
    output_folder = "pmc_articles"

    repository = JsonFolderPaperRepository(output_folder)
    scraper_service = PmcScraperService(repository)

    summary = scraper_service.scrape_and_store(
        search_url=search_url,
        max_articles=max_articles,
        target_sections=("Results", "Discussion"),
    )


    print("\nCLI SUMMARY")
    print("=" * 60)
    print(f"Collected URLs: {summary['collected_urls']}")
    print(f"Successfully scraped & stored: {summary['successful']}")
    print(f"Skipped (no target sections): {summary['skipped_no_target_sections']}")
    print(f"Failed: {summary['failed']}")
    print(f"Output folder: {output_folder}/")
    print("=" * 60)


if __name__ == "__main__":
    main()

