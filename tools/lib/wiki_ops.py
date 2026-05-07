"""Wiki operations: reading, writing, indexing"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class WikiOps:
    """Handle wiki file operations, indexing, and backlink management"""

    def __init__(self, wiki_root: str = "./wiki"):
        self.wiki_root = Path(wiki_root)
        self.concepts_dir = self.wiki_root / "concepts"
        self.meta_dir = self.wiki_root / "_meta"
        self.index_path = self.wiki_root / "INDEX.md"
        self.summaries_path = self.meta_dir / "summaries.json"
        self.backlinks_path = self.meta_dir / "backlinks.json"

        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def read_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Parse frontmatter from markdown content

        Args:
            content: Markdown content with optional YAML frontmatter

        Returns:
            Tuple of (frontmatter_dict, body_content)
        """
        if not content.startswith("---"):
            return {}, content

        lines = content.split("\n")
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx is None:
            return {}, content

        fm_text = "\n".join(lines[1:end_idx])
        body = "\n".join(lines[end_idx + 1:]).lstrip()

        # Simple YAML parsing (no external dependency)
        fm = {}
        for line in fm_text.split("\n"):
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            # Handle lists
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip() for v in val[1:-1].split(",")]
            # Handle booleans
            elif val.lower() in ("true", "false"):
                val = val.lower() == "true"
            fm[key] = val
        return fm, body

    def write_frontmatter(self, fm: Dict, body: str) -> str:
        """Create markdown content with frontmatter

        Args:
            fm: Frontmatter dictionary
            body: Body content

        Returns:
            Complete markdown content
        """
        fm_lines = ["---"]
        for key, val in fm.items():
            if isinstance(val, list):
                val = "[" + ", ".join(str(v) for v in val) + "]"
            fm_lines.append(f"{key}: {val}")
        fm_lines.append("---")
        fm_lines.append("")

        return "\n".join(fm_lines) + body

    def get_article_path(self, slug: str) -> Path:
        filename = slug.lower().replace(" ", "-").replace("_", "-")
        filename = re.sub(r"[^a-z0-9\-]", "", filename)
        filename = re.sub(r"\-+", "-", filename).strip("-")
        return self.concepts_dir / f"{filename}.md"

    def write_article(self, slug: str, title: str, body: str, tags: List[str], sources: List[str], related: List[str], article_type: str = "concept") -> Path:
        path = self.get_article_path(slug)

        fm = {
            "title": title,
            "type": article_type,
            "created": datetime.now().isoformat(timespec="seconds"),
            "updated": datetime.now().isoformat(timespec="seconds"),
            "tags": tags,
            "summary": body.split("\n")[0][:150],
            "sources": sources,
            "related": related,
        }

        content = self.write_frontmatter(fm, body)
        path.write_text(content, encoding="utf-8")
        logger.info(f"Wrote article: {path}")
        return path

    def update_article(self, slug: str, new_body: str, new_sources: List[str], new_tags: List[str]) -> Path:
        """Merge new content into an existing article, preserving frontmatter."""
        result = self.read_article(slug)
        if not result:
            raise ValueError(f"Article not found: {slug}")

        fm, _ = result
        fm["updated"] = datetime.now().isoformat(timespec="seconds")

        existing_tags = fm.get("tags", [])
        if isinstance(existing_tags, str):
            existing_tags = [t.strip() for t in existing_tags.strip("[]").split(",") if t.strip()]
        fm["tags"] = list(dict.fromkeys(existing_tags + new_tags))  # dedup, preserve order

        existing_sources = fm.get("sources", [])
        if isinstance(existing_sources, str):
            existing_sources = [existing_sources]
        fm["sources"] = list(dict.fromkeys(existing_sources + new_sources))

        fm["summary"] = new_body.split("\n")[0][:150]

        path = self.get_article_path(slug)
        path.write_text(self.write_frontmatter(fm, new_body), encoding="utf-8")
        logger.info(f"Updated article: {path}")
        return path

    def read_article(self, slug: str) -> Optional[Tuple[Dict, str]]:
        """Read article by slug

        Args:
            slug: Article slug

        Returns:
            Tuple of (frontmatter, body) or None if not found
        """
        path = self.get_article_path(slug)
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8")
        return self.read_frontmatter(content)

    def list_articles(self) -> List[str]:
        """List all article slugs in wiki

        Returns:
            List of article file paths
        """
        return [f.stem for f in self.concepts_dir.glob("*.md")]

    def extract_wikilinks(self, content: str) -> List[str]:
        """Extract [[WikiLink]] references from markdown

        Args:
            content: Markdown content

        Returns:
            List of referenced slugs
        """
        matches = re.findall(r"\[\[([^\]]+)\]\]", content)
        return matches

    def rebuild_backlinks(self) -> Dict[str, List[str]]:
        """Scan all articles and rebuild backlinks index

        Returns:
            Dict mapping article slug -> list of articles that link to it
        """
        backlinks = {}
        articles = self.list_articles()

        for slug in articles:
            backlinks[slug] = []

        # Scan each article for wikilinks
        for slug in articles:
            result = self.read_article(slug)
            if not result:
                continue
            fm, body = result
            links = self.extract_wikilinks(body)
            for link in links:
                link_slug = link.lower().replace(" ", "-").replace("_", "-")
                if link_slug in backlinks:
                    if slug not in backlinks[link_slug]:
                        backlinks[link_slug].append(slug)

        self.backlinks_path.write_text(json.dumps(backlinks, indent=2), encoding="utf-8")
        logger.info(f"Rebuilt backlinks: {len(backlinks)} articles")
        return backlinks

    def rebuild_summaries(self) -> Dict[str, str]:
        """Rebuild summary cache from all articles

        Returns:
            Dict mapping article slug -> summary
        """
        summaries = {}
        articles = self.list_articles()

        for slug in articles:
            result = self.read_article(slug)
            if not result:
                continue
            fm, body = result
            summary = fm.get("summary", body.split("\n")[0][:150])
            summaries[slug] = summary

        self.summaries_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
        logger.info(f"Rebuilt summaries: {len(summaries)} articles")
        return summaries

    def load_summaries(self) -> Dict[str, str]:
        """Load summary cache

        Returns:
            Dict mapping article slug -> summary
        """
        if not self.summaries_path.exists():
            return {}
        return json.loads(self.summaries_path.read_text(encoding="utf-8"))

    def load_backlinks(self) -> Dict[str, List[str]]:
        """Load backlinks index

        Returns:
            Dict mapping article slug -> list of articles that link to it
        """
        if not self.backlinks_path.exists():
            return {}
        return json.loads(self.backlinks_path.read_text(encoding="utf-8"))

    def build_index(self) -> str:
        articles = self.list_articles()
        summaries = self.load_summaries()

        lines = ["# Wiki Index\n"]
        lines.append(f"*Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d')}*\n")
        lines.append(f"**Articoli totali: {len(articles)}**\n")

        if not articles:
            lines.append("\n*Nessun articolo ancora. Esegui `compile.py --new` per iniziare.*\n")
            return "\n".join(lines)

        # Group by type
        by_type: Dict[str, List[str]] = {}
        for slug in sorted(articles):
            result = self.read_article(slug)
            article_type = "concept"
            if result:
                fm, _ = result
                article_type = fm.get("type", "concept")
            by_type.setdefault(article_type, []).append(slug)

        for article_type, slugs in sorted(by_type.items()):
            lines.append(f"\n## {article_type.capitalize()}\n")
            for slug in slugs:
                summary = summaries.get(slug, "")
                line = f"- [[{slug}]]"
                if summary:
                    line += f" — {summary}"
                lines.append(line)

        return "\n".join(lines)

    def write_index(self):
        """Write index.md to wiki root"""
        content = self.build_index()
        self.index_path.write_text(content, encoding="utf-8")
        logger.info(f"Wrote index: {self.index_path}")
