import json
import logging
import sys

import click
from flask import current_app
from flask.cli import with_appcontext

from extensions import db
from models import Report
from services.huggingface import fetch_trending_item, fetch_readme
from services.llm import generate_report

logger = logging.getLogger(__name__)


def register_commands(app):
    @app.cli.command("generate-report")
    @with_appcontext
    def generate_report_command():
        """Fetch a trending HF item and generate a daily report."""
        # Enable logging so LLM output is visible in the console
        logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

        try:
            # Get already-used item names to avoid duplicates
            used_names = {
                r.item_name for r in db.session.query(Report.item_name).all()
            }

            click.echo("Fetching trending item from HuggingFace...")
            metadata = fetch_trending_item(
                token=current_app.config.get("HUGGINGFACE_TOKEN"),
                used_names=used_names,
            )
            click.echo(f"Selected: {metadata['id']} ({metadata['type']})")

            # Fetch the README for this specific repo
            click.echo(f"Fetching README for {metadata['id']}...")
            readme = fetch_readme(
                repo_id=metadata["id"],
                item_type=metadata["type"],
                token=current_app.config.get("HUGGINGFACE_TOKEN"),
            )
            if readme:
                metadata["readme"] = readme
                click.echo(f"README fetched ({len(readme)} chars)")
            else:
                click.echo("README not available, continuing with metadata only")

            click.echo("=== Metadata sent to LLM ===")
            click.echo(json.dumps(metadata, indent=2, default=str))

            click.echo("Generating report via LLM...")
            result = generate_report(
                metadata=metadata,
                ollama_url=current_app.config["OLLAMA_URL"],
                api_key=current_app.config["OLLAMA_API_KEY"],
                model=current_app.config["OLLAMA_MODEL"],
            )

            click.echo("=== Final Report ===")
            click.echo(f"Title: {result['title']}")
            click.echo(f"Summary: {result['summary'][:200]}...")
            click.echo("Ideas:")
            for i, idea in enumerate(result["ideas"], 1):
                click.echo(f"  {i}. {idea}")

            report = Report(
                title=result["title"],
                item_name=metadata["id"],
                item_type=metadata["type"],
                summary=result["summary"],
                ideas=json.dumps(result["ideas"]),
                metadata_json=json.dumps(metadata, default=str),
            )
            db.session.add(report)
            db.session.commit()

            click.echo(f"\nReport saved: {report.title} (ID: {report.id})")

        except Exception as e:
            click.echo(f"Error generating report: {e}", err=True)
            sys.exit(1)
