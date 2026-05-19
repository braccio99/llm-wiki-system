#!/usr/bin/env python3
"""Compile raw documents into wiki articles"""

import os
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from rich.progress import Progress
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


def get_raw_index() -> dict:
    """Load or create raw/_index.json to track processed files"""
    raw_dir = Path(config["paths"]["raw"])
    index_path = raw_dir / "_index.json"

    if index_path.exists():
        return json.loads(index_path.read_text())
    return {}


def save_raw_index(index: dict):
    """Save raw file index"""
    raw_dir = Path(config["paths"]["raw"])
    index_path = raw_dir / "_index.json"
    index_path.write_text(json.dumps(index, indent=2))


def get_new_files(raw_index: dict) -> list:
    """Get list of new or modified files in raw/"""
    raw_dir = Path(config["paths"]["raw"])
    new_files = []

    # Scan raw directory
    for file_path in raw_dir.glob("**/*"):
        if file_path.name.startswith("_") or file_path.is_dir():
            continue
        if file_path.suffix not in [".md", ".txt"]:
            continue

        rel_path = str(file_path.relative_to(raw_dir))
        mtime = os.path.getmtime(file_path)

        if rel_path not in raw_index or raw_index[rel_path].get("mtime", 0) < mtime:
            new_files.append((rel_path, file_path, mtime))

    return new_files


def find_matching_article(client, wiki_ops: WikiOps, new_data: dict) -> str | None:
    """Return slug of existing article that covers the same concept, or None."""
    summaries = wiki_ops.load_summaries()
    if not summaries:
        return None

    # Exact slug hit — no API call needed
    if new_data.get("slug") in summaries:
        return new_data["slug"]

    index_text = "\n".join(
        f"- {slug}: {summary}" for slug, summary in list(summaries.items())[:60]
    )

    prompt = f"""Does this new content overlap significantly with any existing wiki article?

New content:
- Title: {new_data.get('title')}
- Summary: {new_data.get('summary')}
- Tags: {new_data.get('tags')}

Existing articles:
{index_text}

If there is significant conceptual overlap with one existing article, return ONLY its slug.
If the content is distinct enough to deserve a new article, return "new".
Return ONLY the slug or the word "new". No explanation."""

    response = client.chat(prompt, temperature=0.1, max_tokens=50).strip().strip('"').strip("'")
    return response if response != "new" and response in summaries else None


def merge_article_content(client, existing_body: str, new_body: str, title: str) -> str:
    """Use Claude to merge new information into an existing article body."""
    prompt = f"""You are updating the wiki article "{title}" with new information.

Existing article body:
{existing_body}

New information to integrate:
{new_body}

Rules:
1. Preserve all existing information that remains accurate.
2. Add new facts, data points, or perspectives from the new source.
3. If there are contradictions, keep the more detailed or recent version.
4. Expand or update existing sections — do not just append a new section at the end.
5. Keep the article concise and well-structured with markdown headers.

Return ONLY the updated article body. No frontmatter, no title heading."""

    return client.chat(prompt, temperature=0.3, max_tokens=2000)


def extract_article_data(client, file_path: Path) -> dict:
    """Use Claude to extract article data from raw document"""
    content = file_path.read_text(encoding="utf-8")

    prompt = f"""Analyze this document and extract structured data for a wiki article.

Document content:
---
{content[:3000]}
---

Return a JSON object with:
{{
    "title": "Main concept/title",
    "slug": "concept-slug-kebab-case",
    "type": "concept",
    "summary": "One sentence summary (max 150 chars)",
    "tags": ["tag1", "tag2"],
    "body": "2-3 paragraph summary of key points"
}}

Slug must be lowercase kebab-case (hyphens, no underscores).
Type must be one of: concept, topic, person, paper, guideline.
Return ONLY valid JSON, no markdown code blocks."""

    response = client.chat(prompt, temperature=0.7, max_tokens=1000)

    try:
        # Try to parse JSON from response
        data = json.loads(response)
        return data
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        import re
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return data
            except:
                pass
        logger.warning(f"Failed to parse Claude response for {file_path}")
        return None


@click.command()
@click.option("--all", is_flag=True, help="Recompile all files in raw/")
@click.option("--new", is_flag=True, default=True, help="Compile only new/modified files")
@click.option("--max-files", type=int, default=None, help="Max files to process")
def compile_wiki(all: bool, new: bool, max_files: int):
    """Compile raw documents into wiki articles"""

    console.print("[bold blue]🔨 LLM Wiki Compiler[/bold blue]")

    # Initialize
    client = get_llm_client(config)
    wiki_ops = WikiOps(config["paths"]["wiki"])

    # Get files to process
    raw_index = get_raw_index() if not all else {}
    files_to_process = get_new_files(raw_index) if not all else []

    if all:
        raw_dir = Path(config["paths"]["raw"])
        for file_path in raw_dir.glob("**/*"):
            if not file_path.is_dir() and file_path.suffix in [".md", ".txt"] and not file_path.name.startswith("_"):
                rel_path = str(file_path.relative_to(raw_dir))
                mtime = os.path.getmtime(file_path)
                files_to_process.append((rel_path, file_path, mtime))

    if not files_to_process:
        console.print("[yellow]ℹ️ No new files to compile[/yellow]")
        return

    if max_files:
        files_to_process = files_to_process[:max_files]

    console.print(f"[cyan]Found {len(files_to_process)} files to compile[/cyan]")

    # Process files
    processed = 0
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing...", total=len(files_to_process))

        for rel_path, file_path, mtime in files_to_process:
            progress.update(task, description=f"[cyan]Processing {file_path.name}...")

            try:
                data = extract_article_data(client, file_path)
                if not data:
                    progress.update(task, advance=1)
                    continue

                match = find_matching_article(client, wiki_ops, data)

                if match:
                    # Merge into existing article
                    existing = wiki_ops.read_article(match)
                    existing_body = existing[1] if existing else ""
                    merged_body = merge_article_content(client, existing_body, data.get("body", ""), data.get("title", match))
                    article_path = wiki_ops.update_article(
                        slug=match,
                        new_body=merged_body,
                        new_sources=[f"raw/{rel_path}"],
                        new_tags=data.get("tags", []),
                    )
                    console.print(f"  [blue]↺ Updated:[/blue] {match}")
                else:
                    # Create new article
                    article_path = wiki_ops.write_article(
                        slug=data.get("slug", file_path.stem),
                        title=data.get("title", "Untitled"),
                        body=data.get("body", ""),
                        tags=data.get("tags", []),
                        sources=[f"raw/{rel_path}"],
                        related=[],
                        article_type=data.get("type", "concept"),
                    )
                    console.print(f"  [green]✚ Created:[/green] {data.get('slug', file_path.stem)}")

                # Update raw index
                raw_index[rel_path] = {"mtime": mtime, "article": str(article_path)}
                processed += 1

            except Exception as e:
                console.print(f"[red]❌ Error processing {file_path}: {e}[/red]")
                logger.exception(f"Error processing {file_path}")

            progress.update(task, advance=1)

    # Save raw index
    save_raw_index(raw_index)

    # Rebuild wiki metadata
    console.print("[cyan]Rebuilding wiki index and metadata...[/cyan]")
    wiki_ops.rebuild_summaries()
    wiki_ops.rebuild_backlinks()
    wiki_ops.write_index()

    # Print stats
    stats = client.get_stats()
    console.print(f"\n[bold green]✅ Compilation complete![/bold green]")
    console.print(f"  Processed: {processed} files")
    console.print(f"  Tokens used: {stats['input_tokens']} input, {stats['output_tokens']} output")
    if stats['cache_read_input_tokens'] > 0:
        console.print(f"  Cache hits: {stats['cache_read_input_tokens']} tokens read from cache")

    log_event(
        "ingest",
        f"- files processed: {processed}/{len(files_to_process)}\n"
        f"- tokens: {stats['input_tokens']} in / {stats['output_tokens']} out"
    )


if __name__ == "__main__":
    compile_wiki()
