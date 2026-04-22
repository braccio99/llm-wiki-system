"""BM25 search engine for wiki articles"""

import logging
import re
from pathlib import Path
from typing import List, Tuple, Optional
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class SearchEngine:
    """BM25-based search engine for wiki articles"""

    STOPWORDS = {
        # English
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "for",
        "from", "he", "in", "is", "it", "its", "of", "on", "or", "that",
        "the", "to", "was", "will", "with", "you", "she", "we",
        "they", "this", "these", "those", "what", "which", "who",
        # Italian
        "il", "lo", "la", "gli", "le", "un", "uno", "una",
        "di", "da", "in", "con", "su", "per", "tra", "fra",
        "del", "della", "dello", "dei", "degli", "delle",
        "al", "alla", "allo", "ai", "agli", "alle",
        "dal", "dalla", "dallo", "dai", "dagli", "dalle",
        "nel", "nella", "nello", "nei", "negli", "nelle",
        "sul", "sulla", "sullo", "sui", "sugli", "sulle",
        "questo", "questa", "questi", "queste",
        "quello", "quella", "quelli", "quelle",
        "sono", "essere", "avere", "anche", "però", "quindi",
        "come", "quando", "dove", "perché", "non", "si", "ci", "ne",
    }

    def __init__(self, wiki_root: str = "./wiki", k1: float = 1.5, b: float = 0.75):
        """Initialize search engine

        Args:
            wiki_root: Root directory of wiki
            k1: BM25 parameter (term frequency saturation)
            b: BM25 parameter (length normalization)
        """
        self.wiki_root = Path(wiki_root)
        self.concepts_dir = self.wiki_root / "concepts"
        self.k1 = k1
        self.b = b
        self.bm25 = None
        self.documents = {}  # slug -> content
        self.tokenized_docs = None
        self._index_articles()

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text for search

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        tokens = re.findall(r"[a-z0-9àáèéìíòóùúâêîôûäëïöü]+", text.lower())
        tokens = [t for t in tokens if t not in self.STOPWORDS and len(t) > 2]
        return tokens

    def _index_articles(self):
        """Index all articles in wiki"""
        self.documents = {}
        articles = []

        if not self.concepts_dir.exists():
            logger.warning(f"Concepts directory not found: {self.concepts_dir}")
            return

        for article_file in self.concepts_dir.glob("*.md"):
            slug = article_file.stem
            content = article_file.read_text(encoding="utf-8")
            # Remove frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].lstrip()
            self.documents[slug] = content
            articles.append(content)

        if articles:
            self.tokenized_docs = [self.tokenize(doc) for doc in articles]
            self.bm25 = BM25Okapi(self.tokenized_docs, k1=self.k1, b=self.b)
            logger.info(f"Indexed {len(articles)} articles")
        else:
            logger.warning("No articles found to index")
            self.tokenized_docs = []

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float, str]]:
        """Search for articles matching query

        Args:
            query: Search query
            top_k: Number of top results to return

        Returns:
            List of (slug, score, snippet) tuples
        """
        if not self.bm25 or not self.documents:
            logger.warning("No articles indexed yet")
            return []

        tokens = self.tokenize(query)
        if not tokens:
            logger.warning(f"Query '{query}' has no valid tokens after filtering")
            return []

        # Get BM25 scores
        scores = self.bm25.get_scores(tokens)

        # Create list of (slug, score) and sort
        results = []
        slugs = list(self.documents.keys())
        for i, score in enumerate(scores):
            if score > 0:
                results.append((slugs[i], score))

        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_k]

        # Add snippets
        final_results = []
        for slug, score in results:
            content = self.documents[slug]
            # Extract first 200 chars as snippet
            snippet = content.replace("\n", " ")[:200].strip()
            if not snippet.endswith("..."):
                snippet += "..."
            final_results.append((slug, score, snippet))

        return final_results

    def search_json(self, query: str, top_k: int = 10) -> str:
        """Search and return results as JSON string

        Args:
            query: Search query
            top_k: Number of top results

        Returns:
            JSON string with results
        """
        import json
        results = self.search(query, top_k)
        json_results = [
            {"slug": slug, "score": float(score), "snippet": snippet}
            for slug, score, snippet in results
        ]
        return json.dumps(json_results, indent=2)
