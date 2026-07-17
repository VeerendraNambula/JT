import json
import logging
import os
import click
from dotenv import load_dotenv

# Load env variables from .env file if available
load_dotenv()

from src.linkedin.ingest import ingest_raw_posts, ProcessingResult
from src.linkedin.job_detector import JobDetector
from src.linkedin.job_parser import JobParser
from src.twitter.tweet_generator import TweetGenerator
from src.twitter.publisher import XPublisher
from src.linkedin.scraper import LinkedInScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("jt.cli")

@click.command()
@click.option(
    "--input-file", "-i",
    required=False,
    default=None,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the raw LinkedIn posts JSON or CSV file"
)
@click.option(
    "--url", "-u",
    required=False,
    default=None,
    help="Direct URL to a public LinkedIn company or user profile updates page to scrape live"
)
@click.option(
    "--output-file", "-o",
    default="tweets_output.json",
    type=click.Path(dir_okay=False, writable=True),
    help="Path to write the processed tweets JSON output"
)
@click.option(
    "--use-llm/--no-llm",
    default=True,
    help="Enable or disable LLM-based classification/parsing (falls back to heuristics if disabled or if API key is missing)"
)
@click.option(
    "--publish/--no-publish",
    default=False,
    help="Enable interactive human-in-the-loop publishing to X/Twitter (requires Twitter credentials)"
)
@click.option(
    "--headful",
    is_flag=True,
    default=False,
    help="Launch browser in headful mode to log in manually and bypass bot protections"
)
@click.option(
    "--limit", "-l",
    default=15,
    type=int,
    help="Maximum number of posts to scrape and process from the live site"
)
def main(input_file: str, url: str, output_file: str, use_llm: bool, publish: bool, headful: bool, limit: int):
    """
    LinkedIn-to-X Job Parser & Tweet Generator Pipeline.
    
    Ingests LinkedIn posts from JSON or CSV, identifies job announcements,
    extracts details (using Gemini LLM or heuristics), and generates optimized tweets.
    """
    click.echo("==================================================")
    click.echo("   LinkedIn-to-X Job Announcement CLI Pipeline   ")
    click.echo("==================================================")
    
    # 1. Ingest Validation
    if not input_file and not url:
        click.echo("[ERROR] Please provide either --input-file (-i) or --url (-u) to run the pipeline.", err=True)
        return

    # 2. Initialize Components
    detector = JobDetector(use_llm=use_llm)
    parser = JobParser()
    tweeter = TweetGenerator()
    publisher = XPublisher()

    posts = []
    if url:
        click.echo(f"[*] Fetching live posts from LinkedIn URL: {url} (headless={not headful}, target_jobs={limit})")
        try:
            # Pass the job detector callback to filter posts on-the-fly and keep scrolling until target is met
            posts = LinkedInScraper.fetch_posts(
                url, 
                limit=limit, 
                headless=not headful,
                job_detector_cb=detector.is_job_opening,
                target_jobs=limit
            )
            if not posts:
                click.echo("[WARNING] No job posts matching the official email criteria were found on the live feed.")
                return
            click.echo(f"[+] Successfully gathered {len(posts)} job posts from the live site.")
        except Exception as e:
            click.echo(f"[ERROR] Live crawl failed: {e}", err=True)
            return
    else:
        click.echo(f"[*] Ingesting posts from local file: {input_file}")
        try:
            posts = ingest_raw_posts(input_file)
            click.echo(f"[+] Successfully loaded {len(posts)} posts.")
        except Exception as e:
            click.echo(f"[ERROR] Failed to read input file: {e}", err=True)
            return
    
    # Inform user of status
    api_key_status = "Available" if os.getenv("GEMINI_API_KEY") else "Not configured (Using Heuristics)"
    click.echo(f"[*] Gemini API Key: {api_key_status}")
    click.echo(f"[*] LLM Processing: {'Enabled' if use_llm and os.getenv('GEMINI_API_KEY') else 'Disabled/Fallback'}")
    click.echo(f"[*] X/Twitter Publisher Configured: {publisher.is_configured()}")
    if publish and not publisher.is_configured():
        click.echo("[WARNING] Twitter/X credentials are not fully configured. Publishing will be skipped.", err=True)
    click.echo("--------------------------------------------------")
    
    results = []
    job_count = 0
    
    # 3. Process each post
    for idx, post in enumerate(posts, 1):
        click.echo(f"Processing post {idx}/{len(posts)} (ID: {post.post_id})...")
        
        # Check if job opening
        is_job = detector.is_job_opening(post)
        
        if is_job:
            job_count += 1
            click.echo("  --> [DETECTED] Job Announcement!")
            
            # Parse details
            details = parser.parse_job_details(post)
            click.echo(f"  --> [PARSED] Role: '{details.role}' | Company: '{details.company}'")
            
            # Generate tweet
            tweet = tweeter.generate_tweet(details)
            click.echo(f"  --> [TWEET GENERATED] Length: {len(tweet)} chars (X simulated len: {tweeter.get_x_length(tweet)})")
            click.echo("      ---------- Tweet Draft ----------")
            click.echo(f"\n{tweet}\n")
            click.echo("      --------------------------------")
            
            # Interactive publishing logic (human-in-the-loop)
            tweet_id = None
            if publish and publisher.is_configured():
                if click.confirm("Do you want to publish this tweet to X?", default=False):
                    click.echo("[*] Publishing tweet to X...")
                    tweet_id = publisher.publish_tweet(tweet)
                    if tweet_id:
                        click.echo(f"[+] Successfully posted to X! Tweet ID: {tweet_id}")
                    else:
                        click.echo("[-] Failed to post tweet to X.", err=True)
                else:
                    click.echo("[*] Publishing skipped by user.")
                    
            result = ProcessingResult(
                post=post,
                is_job=True,
                job_details=details,
                tweet_text=tweet,
                tweet_id=tweet_id
            )
        else:
            click.echo("  --> [SKIPPED] Non-job post.")
            result = ProcessingResult(
                post=post,
                is_job=False
            )
            
        results.append(result)
        click.echo("--------------------------------------------------")
        
    # 4. Save results
    click.echo(f"[*] Exporting results to: {output_file}")
    try:
        # Convert Pydantic objects to dicts
        serializable_results = [res.model_dump() for res in results]
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        click.echo("[+] Export completed successfully.")
    except Exception as e:
        click.echo(f"[ERROR] Failed to save results to file: {e}", err=True)
        
    click.echo("\n=================== Summary ======================")
    click.echo(f" Total posts processed: {len(posts)}")
    click.echo(f" Job openings found:   {job_count}")
    click.echo(f" Posts skipped:        {len(posts) - job_count}")
    click.echo("==================================================")

if __name__ == "__main__":
    main()
