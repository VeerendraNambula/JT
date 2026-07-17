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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("jt.cli")

@click.command()
@click.option(
    "--input-file", "-i",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the raw LinkedIn posts JSON or CSV file"
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
def main(input_file: str, output_file: str, use_llm: bool):
    """
    LinkedIn-to-X Job Parser & Tweet Generator Pipeline.
    
    Ingests LinkedIn posts from JSON or CSV, identifies job announcements,
    extracts details (using Gemini LLM or heuristics), and generates optimized tweets.
    """
    click.echo("==================================================")
    click.echo("   LinkedIn-to-X Job Announcement CLI Pipeline   ")
    click.echo("==================================================")
    
    # 1. Ingest
    click.echo(f"[*] Ingesting posts from: {input_file}")
    try:
        posts = ingest_raw_posts(input_file)
        click.echo(f"[+] Successfully loaded {len(posts)} posts.")
    except Exception as e:
        click.echo(f"[ERROR] Failed to read input file: {e}", err=True)
        return
        
    # 2. Initialize Components
    detector = JobDetector(use_llm=use_llm)
    parser = JobParser()
    tweeter = TweetGenerator()
    
    # Inform user of status
    api_key_status = "Available" if os.getenv("GEMINI_API_KEY") else "Not configured (Using Heuristics)"
    click.echo(f"[*] Gemini API Key: {api_key_status}")
    click.echo(f"[*] LLM Processing: {'Enabled' if use_llm and os.getenv('GEMINI_API_KEY') else 'Disabled/Fallback'}")
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
            
            result = ProcessingResult(
                post=post,
                is_job=True,
                job_details=details,
                tweet_text=tweet
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
