# The HF Daily Briefer

A website that automatically generates daily reports on trending models and datasets from [HuggingFace](https://huggingface.co). Each day, a scheduler picks a random trending item, sends its metadata to an LLM, and publishes a grounded summary with 5 project ideas.

All summaries are derived strictly from HuggingFace metadata — no hallucinated features or capabilities.

## How It Works

1. **Heroku Scheduler** triggers `flask generate-report` once per day
2. The command fetches trending models and datasets from the HuggingFace API
3. Items that have already been featured are filtered out (no duplicates)
4. A random unused item is selected and its metadata is sent to an Ollama-compatible LLM
5. The LLM generates a title, summary, and 5 project ideas grounded in the metadata
6. The report is saved to PostgreSQL and displayed on the website

## Tech Stack

- **Backend**: Flask + Jinja2 templates
- **Database**: SQLite (local) / PostgreSQL (Heroku)
- **LLM**: Ollama via OpenAI-compatible API
- **HuggingFace**: `huggingface_hub` library
- **Deployment**: Heroku with Gunicorn

## Local Setup

```bash
# Clone and install
git clone <repo-url>
cd daily-huggingface-report
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Ollama URL, API key, model, and HF token

# Run the web server (SQLite database is created automatically)
flask run

# Generate a report
flask generate-report
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Database connection string | `sqlite:///hf_daily.db` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `OLLAMA_URL` | Ollama server base URL | `http://localhost:11434` |
| `OLLAMA_API_KEY` | Ollama API key | `ollama` |
| `OLLAMA_MODEL` | Model name to use | `llama3` |
| `HUGGINGFACE_TOKEN` | HuggingFace API token (optional) | None |

## Heroku Deployment

```bash
# Create app and add-ons
heroku create
heroku addons:create heroku-postgresql:essential-0
heroku addons:create scheduler:standard

# Set config vars
heroku config:set OLLAMA_URL=https://your-ollama-server.com
heroku config:set OLLAMA_API_KEY=your-key
heroku config:set OLLAMA_MODEL=llama3
heroku config:set HUGGINGFACE_TOKEN=hf_xxx
heroku config:set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Deploy
git push heroku main

# Configure Heroku Scheduler (in dashboard)
# Add job: flask generate-report
# Frequency: Daily

# Seed first report
heroku run flask generate-report
```

## Project Structure

```
daily-huggingface-report/
├── app.py                    # Flask app factory and routes
├── config.py                 # Environment variable configuration
├── models.py                 # SQLAlchemy Report model
├── extensions.py             # Flask-SQLAlchemy instance
├── cli.py                    # flask generate-report CLI command
├── services/
│   ├── huggingface.py        # HuggingFace trending API integration
│   └── llm.py                # Ollama LLM integration and prompt
├── templates/
│   ├── base.html             # Base layout
│   ├── index.html            # Report listing
│   ├── post.html             # Report detail with HF link
│   └── about.html            # About page
├── static/
│   └── style.css             # Custom styles
├── Procfile                  # Heroku process definition
├── runtime.txt               # Python version
├── requirements.txt          # Dependencies
└── .env.example              # Environment variable template
```

## Created By

**Nicholas E. Johnson**
- [nejohnson2.com](https://www.nejohnson2.com)
- [github.com/nejohnson2](https://github.com/nejohnson2)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
