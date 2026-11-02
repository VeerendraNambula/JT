# LinkedIn-to-X Job Announcement Pipeline

A Python pipeline that collects LinkedIn job-announcement posts, identifies relevant opportunities, extracts structured job details with Google Gemini (or heuristic fallbacks), and drafts posts for X.

The project includes both a command-line workflow and a Streamlit interface.

## Workflow

1. **Ingest** posts from a JSON/CSV file or a public LinkedIn updates/search URL.
2. **Detect** whether a post is a job announcement.
3. **Parse** job details using Gemini when enabled, with heuristic fallback support.
4. **Match and prepare** relevant job information.
5. **Generate** a concise X-ready draft.
6. **Review and publish** interactively when publishing is explicitly enabled.

Publishing is opt-in; the CLI defaults to not publishing.

## Features

- JSON and CSV input support.
- Optional live collection from a LinkedIn URL or search query.
- Gemini-powered classification and extraction, with a no-LLM mode.
- Structured processing through separate ingestion, detection, parsing, and publishing modules.
- JSON output for generated drafts.
- Optional human confirmation before publishing to X.
- Streamlit-based interface with light/dark theme state.

## Technology stack

- Python 3.11+
- Streamlit
- Google GenAI SDK
- Pydantic Settings
- Click
- Playwright
- Tweepy
- Pandas

## Project structure

```text
JT/
├── src/
│   ├── app.py
│   ├── cli/
│   │   └── main.py
│   ├── config/
│   │   └── settings.py
│   ├── linkedin/
│   │   ├── ingest.py
│   │   ├── job_detector.py
│   │   ├── job_parser.py
│   │   └── ...
│   └── twitter/
│       ├── publisher.py
│       └── tweet_generator.py
├── .env.example
├── pyproject.toml
└── requirements.txt
```

## Setup

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and add the credentials you intend to use:

- `GEMINI_API_KEY` — optional; enables Gemini-based classification and parsing.
- `DEFAULT_MODEL` — Gemini model name (defaults to `gemini-2.5-flash`).
- `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` — required only for X publishing.

Never commit your real `.env` file or API credentials.

## Run the command-line pipeline

View available options:

```bash
python src/cli/main.py --help
```

Process an existing export without publishing:

```bash
python src/cli/main.py --input-file posts.json --output-file tweets_output.json --no-publish
```

The CLI also supports URL/search input, a post limit, LLM enable/disable, browser headful mode, and an interactive publishing confirmation.

## Run the Streamlit interface

```bash
streamlit run src/app.py
```

## Responsible use

Use only data you are authorized to access. Follow LinkedIn and X platform terms, respect rate limits and privacy, and review generated content before publishing. Automated publishing should remain disabled unless you explicitly configure credentials and enable it.
