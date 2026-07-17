import logging
import hashlib
from typing import List
from playwright.sync_api import sync_playwright
from src.linkedin.ingest import LinkedInPost

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """
    Crawls live public LinkedIn pages (like company updates pages) using Playwright.
    Attempts to retrieve and parse the most recent posts.
    """
    @staticmethod
    def fetch_posts(url: str, limit: int = 5, headless: bool = True) -> List[LinkedInPost]:
        posts = []
        logger.info(f"Starting live LinkedIn crawl for URL: {url} (headless={headless})")
        
        import os
        import click
        user_data_dir = os.path.abspath(".playwright_user_data")
        
        try:
            with sync_playwright() as p:
                # Use launch_persistent_context to maintain browser sessions/cookies
                context = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=headless,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800}
                )
                page = context.new_page()
                
                # Navigate to the page
                logger.info("Navigating to URL...")
                page.goto(url, wait_until="load", timeout=45000)
                
                # In headful mode, wait for user validation (e.g. log in)
                if not headless:
                    click.echo("\n[*] Running in HEADFUL mode.")
                    click.echo("[*] If you see a login screen, please log in.")
                    click.echo("[*] Once logged in and the target page loads, press Enter in this terminal to continue processing...")
                    input()
                    
                page.wait_for_timeout(3000)
                
                # Inspect for redirection to login wall
                current_url = page.url.lower()
                if "login" in current_url or "signup" in current_url:
                    logger.warning("LinkedIn redirected to a login page. Try running the tool with the `--headful` flag to sign in and save session cookies.")
                    context.close()
                    return []
                
                # Scroll down twice to trigger loading of older updates
                logger.info("Scrolling page to load dynamic content...")
                for _ in range(2):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    page.wait_for_timeout(2000)
                
                # Resilient list of selectors for post updates
                card_selectors = [
                    ".org-update-card-single-update",
                    ".feed-shared-update-v2",
                    ".share-update-card",
                    "div.feed-shared-update",
                    "li.updates__list-item",
                    "article"
                ]
                
                cards = []
                for selector in card_selectors:
                    cards = page.query_selector_all(selector)
                    if cards:
                        logger.info(f"Found {len(cards)} post cards using selector '{selector}'")
                        break
                
                if not cards:
                    # Generic fallback: search for anything containing a data-urn (usually posts)
                    cards = page.query_selector_all("div[data-urn]")
                    if cards:
                        logger.info(f"Found {len(cards)} post cards using data-urn attributes")
                
                for idx, card in enumerate(cards[:limit]):
                    try:
                        # 1. Post ID / URN
                        urn = card.get_attribute("data-urn")
                        post_id = urn.split(":")[-1] if urn else None
                        
                        # 2. Text Content
                        text_el = None
                        text_selectors = [
                            ".feed-shared-text", 
                            ".feed-shared-update-v2__description-wrapper",
                            ".commentary",
                            ".share-update-card__description-text",
                            ".org-update-card-single-update__commentary",
                            ".feed-shared-update-v2__commentary"
                        ]
                        for ts in text_selectors:
                            text_el = card.query_selector(ts)
                            if text_el:
                                break
                        
                        text_content = text_el.inner_text().strip() if text_el else ""
                        
                        # Skip if there's no readable description
                        if not text_content:
                            continue
                            
                        # Generate fallback hash ID if URN is missing
                        if not post_id:
                            post_id = hashlib.md5(text_content.encode("utf-8")).hexdigest()[:10]
                        
                        # 3. Author Name
                        author_el = None
                        author_selectors = [
                            "span.feed-shared-actor__title",
                            ".org-update-actor__title",
                            ".share-update-card__actor-text",
                            "span.actor__name",
                            ".feed-shared-actor__name"
                        ]
                        for asel in author_selectors:
                            author_el = card.query_selector(asel)
                            if author_el:
                                break
                        author_name = author_el.inner_text().strip() if author_el else "Unknown Author"
                        
                        # 4. Post Direct URL
                        post_url = None
                        link_el = card.query_selector("a[href*='/feed/update/'], a[href*='/posts/']")
                        if link_el:
                            href = link_el.get_attribute("href")
                            if href:
                                post_url = f"https://www.linkedin.com{href}" if href.startswith("/") else href
                                
                        if not post_url:
                            post_url = f"https://www.linkedin.com/feed/update/{urn}" if urn else url
                            
                        # 5. Posted Date (Relative string)
                        date_el = None
                        date_selectors = [
                            ".feed-shared-actor__sub-text",
                            ".share-update-card__actor-subtext",
                            ".org-update-actor__sub-text"
                        ]
                        for dsel in date_selectors:
                            date_el = card.query_selector(dsel)
                            if date_el:
                                break
                        
                        raw_date = date_el.inner_text().strip() if date_el else "Recent"
                        # Clean relative time (split by dot bullets)
                        posted_date = raw_date.split("•")[0].strip() if "•" in raw_date else raw_date
                        
                        # 6. Author Profile URL
                        profile_el = card.query_selector("a[href*='/in/'], a[href*='/company/']")
                        author_profile_url = None
                        if profile_el:
                            href = profile_el.get_attribute("href")
                            if href:
                                author_profile_url = f"https://www.linkedin.com{href}" if href.startswith("/") else href
                        
                        posts.append(LinkedInPost(
                            post_id=post_id,
                            author_name=author_name,
                            author_profile_url=author_profile_url,
                            post_url=post_url,
                            text_content=text_content,
                            posted_date=posted_date
                        ))
                    except Exception as parse_err:
                        logger.error(f"Error parsing card #{idx}: {parse_err}")
                        
                context.close()
        except Exception as launch_err:
            logger.error(f"Error running Playwright crawler: {launch_err}")
            
        logger.info(f"Successfully scraped {len(posts)} posts from the live site.")
        return posts
