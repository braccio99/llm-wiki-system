#!/usr/bin/env python3
"""Q&A against the wiki"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
import yaml

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.claude_client import ClaudeClient
from lib.wiki_ops import WikiOps
from lib.search_engine import SearchEngine
from lib.wiki_log import log_event

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

# Load config
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)


def find_relevant_docs(client: ClaudeClient, wiki_ops: WikiOps, query: str, top_k: int = 5) -> list:
    """Use Claude to identify relevant documents from wiki index"""
    summaries = wiki_ops.load_summaries()
    if not summaries:
        return []

    # Create concise index for Claude
    index_text = "Available documents:\n"
    for slug, summary in list(summaries.items())[:50]:  # Limit to keep context reasonable
        index_text += f"- {slug}: {summary}\n"

    prompt = f"""Given this query and list of available documents, identify which 2-5 documents are most relevant to answer the question.

Query: {query}

{index_text}

Return a JSON array of document slugs, e.g.: ["slug1", "slug2"]
Return ONLY valid JSON array, no explanation."""

    response = client.chat(prompt, temperature=0.7, max_tokens=500)

    try:
        slugs = json.loads(response)
        return slugs if isinstance(slugs, list) else []
    except json.JSONDecodeError:
        # Try to extract array from response
        import re
        match = re.search(r"\[.*\]", response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return []


@click.command()
@click.argument("query")
@click.option("--format", type=click.Choice(["md", "marp", "chart"]), default="md",
              help="Output format")
@click.option("--save", is_flag=True, help="Save output to file")
@click.option("--top", type=int, default=5, help="Number of relevant documents to use")
@click.option("--raw", is_flag=True, help="Print answer only, no status messages")
def query_wiki(query: str, format: str, save: bool, top: int, raw: bool):
    """Ask a question against the wiki

    QUERY: Your question
    """

    if not raw:
        console.print(f"[bold blue]❓ Wiki Query[/bold blue]")
        console.print(f"Question: {query}\n")

    # Initialize
    client = ClaudeClient(model=config["llm"]["model"])
    wiki_ops = WikiOps(config["paths"]["wiki"])

    # Find relevant documents
    if not raw:
        console.print("[cyan]Finding relevant documents...[/cyan]")
    relevant_slugs = find_relevant_docs(client, wiki_ops, query, top_k=top)

    if not relevant_slugs:
        if not raw:
            console.print("[yellow]No relevant documents found[/yellow]")
        return

    # Read relevant documents
    context_docs = []
    for slug in relevant_slugs:
        result = wiki_ops.read_article(slug)
        if result:
            fm, body = result
            content = f"# {fm.get('title', slug)}\n\n{body}"
            context_docs.append(content)

    if not context_docs:
        if not raw:
            console.print("[red]Could not read any relevant documents[/red]")
        return

    if not raw:
        console.print(f"[cyan]Using {len(context_docs)} documents as context[/cyan]")

    # Generate answer based on format
    if format == "marp":
        system_prompt = """You are an expert at creating educational slide presentations.
Create a Marp-formatted slide deck (markdown with marp directives) that answers the user's question.
Use proper marp syntax with --- to separate slides.
Include speaker notes with > at the start of lines."""

        answer_prompt = f"""Based on these documents, create a Marp slide presentation to answer: {query}

Documents:
{chr(10).join(context_docs)}"""

    elif format == "chart":
        system_prompt = """You are an expert at data visualization.
Generate Python matplotlib code to create insightful charts based on the provided information.
Return valid Python code that uses matplotlib to visualize the data.
The code should be executable as-is."""

        answer_prompt = f"""Based on these documents, generate matplotlib code to visualize data relevant to: {query}

Documents:
{chr(10).join(context_docs)}

Generate complete, executable Python code using matplotlib."""

    else:  # markdown
        system_prompt = """You are a knowledgeable researcher providing detailed answers.
Cite sources by referencing [[WikiLink]] format for related documents.
Structure answers clearly with headers and bullet points."""

        answer_prompt = f"""Based on these documents, provide a detailed answer to: {query}

Documents:
{chr(10).join(context_docs)}"""

    # Generate response
    if not raw:
        console.print("[cyan]Generating answer...[/cyan]")
    answer = client.chat(answer_prompt, system=system_prompt, max_tokens=4096, temperature=0.7)

    if raw:
        print(answer)
    else:
        console.print("\n[bold green]Answer:[/bold green]\n")
        console.print(answer)

    # Save if requested
    if save:
        output_dir = Path(config["paths"][f"outputs_{format}"])
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if format == "chart":
            output_path = output_dir / f"chart_{timestamp}.py"
        elif format == "marp":
            output_path = output_dir / f"slides_{timestamp}.md"
        else:
            output_path = output_dir / f"answer_{timestamp}.md"

        output_path.write_text(answer, encoding="utf-8")
        console.print(f"\n[green]✅ Saved to: {output_path}[/green]")

    # Print stats
    stats = client.get_stats()
    if not raw:
        console.print(f"\n[dim]Tokens: {stats['input_tokens']} in, {stats['output_tokens']} out[/dim]")

    log_event(
        "query",
        f"- question: {query}\n"
        f"- format: {format} (saved={save})\n"
        f"- context docs: {len(context_docs)} ({', '.join(relevant_slugs)})\n"
        f"- tokens: {stats['input_tokens']} in / {stats['output_tokens']} out"
    )


if __name__ == "__main__":
    query_wiki()
