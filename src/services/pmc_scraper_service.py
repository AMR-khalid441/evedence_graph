from __future__ import annotations

from datetime import datetime
import time
import uuid
from typing import Iterable, List, Optional, Sequence, Tuple

from playwright.sync_api import sync_playwright, Page

from domain import Paper, Section
from services.interfaces import PaperRepository


class PmcScraperService:
    """
    Service that crawls PMC search results, scrapes target sections,
    and persists them via a `PaperRepository`.

    It preserves the existing behavior and JSON shape from `scrapping_service.py.py`,
    with the business rule that each stored paper must have at least one of the
    target sections (e.g. "Results" or "Discussion").
    """

    def __init__(self, repository: PaperRepository) -> None:
        self._repository = repository

    # =========================================================
    # STEP 1 — Crawl PMC Search Pages (Multi-Page Safe)
    # =========================================================
    def crawl_article_urls(self, search_url: str, max_articles: int = 50) -> List[str]:
        """
        Crawl PMC search results across multiple pages and collect article URLs.

        This mirrors the existing `crawl_pmc_article_urls` function.
        """
        all_urls: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page_number = 1

            while len(all_urls) < max_articles:
                print(f"\n--- Visiting search page {page_number} ---")

                page.goto(
                    f"{search_url}&page={page_number}",
                    wait_until="networkidle",
                    timeout=30000,
                )

                page.wait_for_selector("div.docsum-wrap", timeout=20000)

                results = page.query_selector_all("div.docsum-wrap")

                if not results:
                    print("No more results found.")
                    break

                for result in results:
                    link_element = result.query_selector("a.docsum-link")

                    if link_element:
                        href = link_element.get_attribute("href")

                        if href:
                            if href.startswith("/"):
                                full_url = f"https://www.ncbi.nlm.nih.gov{href}"
                            else:
                                full_url = href

                            if full_url not in all_urls:
                                all_urls.append(full_url)
                                print(f"Collected {len(all_urls)}: {full_url}")

                            if len(all_urls) >= max_articles:
                                break

                page_number += 1
                time.sleep(1)

            browser.close()

        print(f"\nTotal URLs collected: {len(all_urls)}")
        return all_urls[:max_articles]

    # =========================================================
    # STEP 2 — Scrape a Single Article into a Paper
    # =========================================================
    def _scrape_single(
        self,
        page: Page,
        url: str,
        target_sections: Sequence[str] = ("Results", "Discussion"),
    ) -> Optional[Paper]:
        """
        Scrape the given article URL for the target sections.

        Returns a `Paper` if at least one target section is found with text,
        otherwise returns None and the caller should treat this as "skipped".
        """
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        try:
            doc_title = page.locator("h1").inner_text().strip()
        except Exception:
            doc_title = "Unknown Article Title"

        sections: List[Section] = []

        for section_name in target_sections:
            h2 = page.locator("h2.pmc_sec_title").filter(has_text=section_name)

            if h2.count() == 0:
                print(f"Warning: {section_name} not found.")
                continue

            section_element = h2.locator("xpath=..")
            paragraphs = section_element.locator("p")

            full_text_parts: List[str] = []

            for i in range(paragraphs.count()):
                text = paragraphs.nth(i).inner_text().strip()
                if text:
                    full_text_parts.append(text)

            if full_text_parts:
                section = Section(
                    title=section_name,
                    order=len(sections),
                    text="\n\n".join(full_text_parts),
                )
                sections.append(section)

        # Business rule: skip articles that don't have any of the target sections.
        if not sections:
            print(f"No valid target sections found for {url}")
            return None

        paper = Paper(
            doc_id=str(uuid.uuid4()),
            doc_title=doc_title,
            source_url=url,
            created_at=datetime.today().strftime("%Y-%m-%d"),
            sections=sections,
        )
        return paper

    # =========================================================
    # STEP 3 — Orchestrate Crawl + Scrape + Store
    # =========================================================
    def scrape_and_store(
        self,
        search_url: str,
        max_articles: int = 50,
        target_sections: Sequence[str] = ("Results", "Discussion"),
    ) -> dict:
        """
        High-level orchestration:
        - crawl article URLs
        - scrape each one for target sections
        - persist resulting papers via the repository

        Returns a summary dictionary useful for CLI or API responses.
        """
        print("=" * 60)
        print("STEP 1: Collecting Article URLs")
        print("=" * 60)

        article_urls = self.crawl_article_urls(search_url, max_articles)

        if not article_urls:
            print("No articles found.")
            return {
                "collected_urls": 0,
                "successful": 0,
                "skipped_no_target_sections": 0,
                "failed": 0,
            }

        print("\n" + "=" * 60)
        print("STEP 2: Scraping Articles")
        print("=" * 60)

        successful = 0
        skipped_no_target_sections = 0
        failed = 0

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for idx, url in enumerate(article_urls, 1):
                print(f"\n[{idx}/{len(article_urls)}] Scraping: {url}")

                try:
                    paper = self._scrape_single(page, url, target_sections=target_sections)

                    if paper is not None:
                        self._repository.save(paper)
                        successful += 1
                    else:
                        skipped_no_target_sections += 1

                    time.sleep(1.5)  # be polite

                except Exception as e:
                    print(f"Error: {e}")
                    failed += 1

            browser.close()

        summary = {
            "collected_urls": len(article_urls),
            "successful": successful,
            "skipped_no_target_sections": skipped_no_target_sections,
            "failed": failed,
        }

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Collected URLs: {summary['collected_urls']}")
        print(f"Successfully scraped & stored: {summary['successful']}")
        print(f"Skipped (no target sections): {summary['skipped_no_target_sections']}")
        print(f"Failed: {summary['failed']}")
        print("=" * 60)

        return summary

