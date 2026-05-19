#!/usr/bin/env python3
"""Lint and health checks for wiki"""

import logging
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
import yaml

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.llm_client import get_llm_client
from lib.wiki_ops import WikiOps
from lib.wiki_log import log_event

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

# Load config
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)


def check_orphans(wiki_ops: WikiOps):
    """Find articles with no incoming backlinks"""
    backlinks = wiki_ops.load_backlinks()
    articles = wiki_ops.list_articles()

    orphans = [slug for slug in articles if not backlinks.get(slug, [])]

    if orphans:
        console.print(f"\n[yellow]Orphaned articles ({len(orphans)}):[/yellow]")
        for slug in orphans[:10]:  # Show first 10
            console.print(f"  - {slug}")
        if len(orphans) > 10:
            console.print(f"  ... and {len(orphans) - 10} more")
    else:
        console.print("[green]✅ No orphaned articles[/green]")


def check_missing_summaries(wiki_ops: WikiOps):
    """Find articles missing summaries"""
    summaries = wiki_ops.load_summaries()
    articles = wiki_ops.list_articles()

    missing = [slug for slug in articles if slug not in summaries or not summaries[slug]]

    if missing:
        console.print(f"\n[yellow]Articles missing summaries ({len(missing)}):[/yellow]")
        for slug in missing[:10]:
            console.print(f"  - {slug}")
        if len(missing) > 10:
            console.print(f"  ... and {len(missing) - 10} more")
        console.print("\n[cyan]Regenerating summaries...[/cyan]")
        wiki_ops.rebuild_summaries()
        console.print("[green]✅ Summaries regenerated[/green]")
    else:
        console.print("[green]✅ All articles have summaries[/green]")


def check_inconsistencies(wiki_ops: WikiOps, client):
    """Use Claude to find contradictions in related articles"""
    articles = wiki_ops.list_articles()

    if not articles:
        console.print("[yellow]No articles to check[/yellow]")
        return

    # Sample a few related articles
    console.print("[cyan]Checking for inconsistencies...[/cyan]")

    # Get backlinks to find related articles
    backlinks = wiki_ops.load_backlinks()
    checked = 0

    for slug in articles[:5]:  # Check first 5 articles
        related = backlinks.get(slug, [])
        if not related:
            continue

        # Read articles
        main_result = wiki_ops.read_article(slug)
        if not main_result:
            continue

        main_fm, main_body = main_result
        context = f"Main article: {slug}\n{main_body[:1000]}\n\n"

        for rel_slug in related[:3]:  # Check first 3 related
            rel_result = wiki_ops.read_article(rel_slug)
            if rel_result:
                rel_fm, rel_body = rel_result
                context += f"Related article: {rel_slug}\n{rel_body[:1000]}\n\n"

        # Ask Claude to check
        prompt = f"""Check these related wiki articles for contradictions, inconsistencies, or missing connections.

{context}

If you find issues, list them briefly. Otherwise, say "No issues found"."""

        response = client.chat(prompt, temperature=0.3, max_tokens=500)

        if "no issues" not in response.lower():
            console.print(f"\n[yellow]Potential issues in {slug}:[/yellow]")
            console.print(response)

        checked += 1

    if checked == 0:
        console.print("[dim]No related articles to check[/dim]")


def suggest_articles(wiki_ops: WikiOps, client):
    """Suggest new article topics based on gaps in wiki"""
    summaries = wiki_ops.load_summaries()

    if not summaries:
        console.print("[yellow]Wiki is empty, start by adding documents[/yellow]")
        return

    # Create summary of what exists
    topics = "\n".join([f"- {slug}: {summary[:80]}" for slug, summary in list(summaries.items())[:20]])

    prompt = f"""Based on this wiki of {len(summaries)} articles, suggest 5 new article topics that would:
1. Fill gaps in knowledge
2. Connect related concepts
3. Provide foundational understanding

Current articles (sample):
{topics}

Suggest NEW topics not already in the list. Return as numbered list with brief explanations."""

    console.print("[cyan]Generating suggestions...[/cyan]")
    response = client.chat(prompt, temperature=0.8, max_tokens=1000)

    console.print(f"\n[bold]Suggested new articles:[/bold]")
    console.print(response)


@click.group()
def lint():
    """Wiki health checks and linting"""
    pass


@lint.command()
def orphans():
    """Find orphaned articles"""
    wiki_ops = WikiOps(config["paths"]["wiki"])
    console.print("[bold blue]🔍 Checking for orphaned articles[/bold blue]")
    check_orphans(wiki_ops)
    log_event("lint", "- check: orphans")


@lint.command()
def summaries():
    """Check for missing summaries"""
    wiki_ops = WikiOps(config["paths"]["wiki"])
    console.print("[bold blue]🔍 Checking article summaries[/bold blue]")
    check_missing_summaries(wiki_ops)
    log_event("lint", "- check: summaries")


@lint.command()
def inconsistencies():
    """Check for inconsistencies in related articles"""
    console.print("[bold blue]🔍 Checking for inconsistencies[/bold blue]")
    client = get_llm_client(config)
    wiki_ops = WikiOps(config["paths"]["wiki"])
    check_inconsistencies(wiki_ops, client)
    stats = client.get_stats()
    console.print(f"\n[dim]Tokens: {stats['input_tokens']} in, {stats['output_tokens']} out[/dim]")
    log_event("lint", f"- check: inconsistencies\n- tokens: {stats['input_tokens']} in / {stats['output_tokens']} out")


@lint.command()
def suggest():
    """Suggest new article topics"""
    console.print("[bold blue]💡 Suggesting new articles[/bold blue]")
    client = get_llm_client(config)
    wiki_ops = WikiOps(config["paths"]["wiki"])
    suggest_articles(wiki_ops, client)
    stats = client.get_stats()
    console.print(f"\n[dim]Tokens: {stats['input_tokens']} in, {stats['output_tokens']} out[/dim]")
    log_event("lint", f"- check: suggest\n- tokens: {stats['input_tokens']} in / {stats['output_tokens']} out")


@lint.command(name="all")
def check_all():
    """Run all checks"""
    console.print("[bold blue]🔍 Running all health checks[/bold blue]\n")
    client = get_llm_client(config)
    wiki_ops = WikiOps(config["paths"]["wiki"])

    console.print("[cyan]1. Checking for orphaned articles...[/cyan]")
    check_orphans(wiki_ops)

    console.print("\n[cyan]2. Checking summaries...[/cyan]")
    check_missing_summaries(wiki_ops)

    console.print("\n[cyan]3. Checking for inconsistencies...[/cyan]")
    check_inconsistencies(wiki_ops, client)

    console.print("\n[cyan]4. Suggesting new articles...[/cyan]")
    suggest_articles(wiki_ops, client)

    stats = client.get_stats()
    console.print(f"\n[bold green]✅ Health check complete[/bold green]")
    console.print(f"[dim]Tokens: {stats['input_tokens']} in, {stats['output_tokens']} out[/dim]")
    log_event("lint", f"- check: all (orphans, summaries, inconsistencies, suggest)\n- tokens: {stats['input_tokens']} in / {stats['output_tokens']} out")


if __name__ == "__main__":
    lint()
