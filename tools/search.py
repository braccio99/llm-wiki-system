#!/usr/bin/env python3
"""Search the wiki"""

import json
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
import yaml

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.search_engine import SearchEngine

# Load config
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

console = Console()


@click.command()
@click.argument("query")
@click.option("--top", type=int, default=10, help="Number of results")
@click.option("--json", is_flag=True, help="Output as JSON")
def search(query: str, top: int, json_flag: bool):
    """Search wiki articles

    QUERY: Search terms
    """

    console.print(f"[bold blue]🔎 Wiki Search[/bold blue]")
    console.print(f"Query: {query}\n")

    # Initialize search engine
    search_engine = SearchEngine(wiki_root=config["paths"]["wiki"])

    # Search
    results = search_engine.search(query, top_k=top)

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    if json_flag:
        # Output as JSON
        json_results = [
            {"slug": slug, "score": float(score), "snippet": snippet}
            for slug, score, snippet in results
        ]
        click.echo(json.dumps(json_results, indent=2))
    else:
        # Output as table
        table = Table(title=f"Search Results ({len(results)})")
        table.add_column("Article", style="cyan")
        table.add_column("Score", style="magenta")
        table.add_column("Snippet", style="white")

        for slug, score, snippet in results:
            table.add_row(slug, f"{score:.3f}", snippet)

        console.print(table)


if __name__ == "__main__":
    search()
