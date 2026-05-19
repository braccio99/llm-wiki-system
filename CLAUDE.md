# LLM Wiki System - Claude Code Instructions

This is a **personal knowledge base system** powered by any LLM (local or cloud). The LLM maintains and operates the wiki. Your role is primarily to:
1. Feed in raw documents (via Obsidian Web Clipper or direct uploads)
2. Ask questions against the wiki
3. Request linting/health checks
4. Iterate and expand the knowledge base

---

## Supported LLM Providers

Set `provider` in `config.yaml` → `llm.provider`:

| Provider | Value | Needs key? | Default base_url |
|---|---|---|---|
| Anthropic Claude | `anthropic` | Yes — `ANTHROPIC_API_KEY` | (SDK default) |
| Ollama (local) | `ollama` | No | `http://localhost:11434/v1` |
| LM Studio (local) | `lmstudio` | No | `http://localhost:1234/v1` |
| vLLM (local/remote) | `vllm` | No locally | `http://localhost:8000/v1` |
| OpenAI | `openai` | Yes — `OPENAI_API_KEY` | `https://api.openai.com/v1` |
| Groq, Together, etc. | `openai-compatible` | Yes — `LLM_API_KEY` | set `llm.base_url` |

Quick switch examples in `config.yaml`:
```yaml
# Local Ollama
llm:
  provider: "ollama"
  model: "llama3.2"

# LM Studio (uses whatever model is loaded)
llm:
  provider: "lmstudio"
  model: "local-model"

# vLLM
llm:
  provider: "vllm"
  model: "mistralai/Mistral-7B-Instruct-v0.2"

# Groq
llm:
  provider: "openai-compatible"
  model: "llama-3.3-70b-versatile"
  base_url: "https://api.groq.com/openai/v1"
  api_key: null  # reads LLM_API_KEY from .env
```

---

## System Architecture

```
raw/              → Raw source documents (articles, PDFs, etc.)
   ↓
compile.py        → Ingest raw/ and create or update wiki articles via Claude
   ↓
wiki/concepts/    → Compiled markdown articles (frontmatter + body)
   ↓
query.py          → Q&A against wiki
lint.py           → Health checks and gap detection
search.py         → BM25 search over wiki
   ↓
outputs/          → Generated slides, charts, Q&A results
   ↓
Obsidian          → View everything as a vault
```

---

## Quick Start

### 1. Setup (one-time)

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Add Your First Document

```bash
# Create or download a markdown/text file and put it in raw/
# For example: raw/my-article.md

# Compile it into wiki
python tools/compile.py --new
```

This will:
- Read all files in `raw/`
- Send each to Claude for analysis
- Extract: title, slug, summary, tags, body
- **Create** a new article in `wiki/concepts/`, or **update** an existing one if the concept is already covered
- Update indexes and backlinks

### 3. Ask Questions

```bash
# Basic question
python tools/query.py "What do you know about topic X?"

# Generate slides
python tools/query.py "Create a slide presentation about topic X" --format marp --save

# Generate visualizations
python tools/query.py "Visualize the relationships between concepts A, B, C" --format chart --save
```

### 4. Keep Wiki Healthy

```bash
# Find orphaned articles
python tools/lint.py orphans

# Check for inconsistencies
python tools/lint.py inconsistencies

# Get suggestions for new articles
python tools/lint.py suggest

# Run all checks
python tools/lint.py all
```

### 5. Search

```bash
# Search for articles
python tools/search.py "your search query"

# Get results as JSON (useful for programmatic access)
python tools/search.py "query" --json
```

---

## Article Format

Every article in `wiki/concepts/` must have YAML frontmatter:

```markdown
---
title: "Concept Name"
created: "2026-04-16T14:30:00"
updated: "2026-04-16T14:30:00"
tags: [tag1, tag2]
summary: "One-line description (max 150 chars)"
sources: [raw/original-article.md]
related: [[related-article-1]], [[related-article-2]]
---

## Article Body

Start writing the actual content here. Use [[WikiLink]] syntax to reference other articles.

The first paragraph becomes the summary if not specified in frontmatter.
```

### WikiLink Syntax
- `[[article-slug]]` → Links to another article
- Links are bidirectional (backlinks are auto-maintained)
- See `wiki/INDEX.md` for a complete index with all articles

---

## Workflow Example: Building a Knowledge Base

### Day 1: Ingest Raw Data
```bash
# Drop some markdown/text files into raw/
# (Use Obsidian Web Clipper to get markdown from the web)
python tools/compile.py --new
# → Creates articles in wiki/concepts/
# → Updates existing articles if related content was already present
# → Generates wiki/INDEX.md
```

### Day 2: Ask Questions
```bash
python tools/query.py "Compare supervised vs unsupervised learning" --save

# Output saved to: outputs/qa/answer_20260416_143000.md
```

### Day 3: Find Gaps
```bash
python tools/lint.py all
# → Finds orphaned articles
# → Spots inconsistencies
# → Suggests new topics to write about
```

### Day 4: Generate Visualizations
```bash
python tools/query.py "Create a mind map of neural network architectures" \
  --format marp --save
# → Creates slides in outputs/slides/
# → View in Obsidian with Marp plugin
```

### Day 5: Expand
```bash
# Add more raw documents
python tools/compile.py --new
python tools/lint.py all
```

---

## Configuration

Edit `config.yaml` to change:
- **Wiki identity**: name, description, language
- **LLM model** (default: haiku-4.5, set to claude-opus-4-7 for higher quality)
- **Temperature** (0.3 for factual, 0.8 for creative)
- **Batch sizes** for compilation
- **Search parameters** (BM25 k1, b, top_k)
- **Output directories and formats**

---

## File Structure Reference

```
LLM WIKI/
├── raw/                              # Your source documents (append-only)
│   └── _index.json                  # Auto-generated tracking of processed files
│
├── wiki/                            # The compiled knowledge base
│   ├── INDEX.md                    # Main index of all articles
│   ├── _meta/
│   │   ├── summaries.json          # Quick lookup of summaries
│   │   └── backlinks.json          # Graph of article relationships
│   └── concepts/
│       ├── machine-learning.md
│       ├── neural-networks.md
│       └── ...
│
├── outputs/                         # Generated content
│   ├── qa/answer_*.md              # Q&A results
│   ├── slides/slides_*.md          # Marp presentations
│   └── charts/chart_*.py           # Matplotlib visualization code
│
├── tools/
│   ├── compile.py                  # Ingest raw/ → wiki/ (create or update)
│   ├── query.py                    # Q&A against wiki
│   ├── lint.py                     # Health checks
│   ├── search.py                   # Search engine
│   └── lib/
│       ├── claude_client.py        # LLM API wrapper (with caching)
│       ├── wiki_ops.py             # Wiki operations
│       ├── wiki_log.py             # Append-only activity log
│       └── search_engine.py        # BM25 search
│
├── config.yaml                      # System configuration
├── AGENTS.md                        # Operational rules for the LLM agent
├── requirements.txt                 # Python dependencies
├── .env                            # API keys (keep secret!)
└── CLAUDE.md                       # This file
```

---

## Advanced Usage

### Using Claude as a Tool Within Your Own Script

```python
from tools.lib import ClaudeClient, WikiOps, SearchEngine

# Initialize
client = ClaudeClient()
wiki = WikiOps()
search = SearchEngine()

# Search
results = search.search("your query", top_k=5)
print(results)  # → [("slug", 0.95, "snippet"), ...]

# Read articles
fm, body = wiki.read_article("slug")
print(fm["title"])

# Ask Claude with context
answer = client.chat_with_context(
    "Your question",
    context_documents=[body],
    system="You are a helpful assistant"
)
```

### Scripting Workflows

```python
#!/usr/bin/env python3
# tools/my_workflow.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from lib import ClaudeClient, WikiOps

wiki = WikiOps()
client = ClaudeClient()

for slug in wiki.list_articles():
    result = wiki.read_article(slug)
    if result:
        fm, body = result
        # Process...
```

---

## Obsidian Integration

1. **Open folder as vault**: File → Open vault → select this directory
2. **Recommended plugins**:
   - **Marp**: View slide presentations (outputs/slides/)
   - **Dataview**: Query wiki metadata dynamically
   - **Graph View**: Visualize article connections (built-in)
   - **Backlinks**: See which articles reference each other (built-in)

3. **Usage**: Navigate the wiki like any Obsidian vault, click `[[WikiLink]]` to jump between articles

---

## Tips & Tricks

### Batch Processing Many Documents
```bash
# Compile all files at once
python tools/compile.py --all

# Or limit to 10 files per run to avoid huge context
python tools/compile.py --new --max-files 10
```

### Re-generate Summaries After Editing
```bash
# Edit articles manually in Obsidian, then update summaries:
python tools/lint.py summaries
```

### Use Higher Quality Model for Complex Queries
```bash
# Edit config.yaml: set model to "claude-opus-4-7"
# Or via environment variable:
export LLM_MODEL=claude-opus-4-7
python tools/query.py "Complex philosophical question"
```

### Monitor Token Usage
All tools print token statistics. For large queries, look for:
- `cache_read_input_tokens`: tokens you didn't pay for (cache hits!)
- High cache hit = prompt caching is working

---

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
- Create `.env` file with `ANTHROPIC_API_KEY=sk-...`
- Or set environment variable: `export ANTHROPIC_API_KEY=sk-...`

### Articles not getting created
- Check `raw/` has .md or .txt files
- Check Claude response isn't truncated: look at compile.py logs
- Try with a simpler document first

### Search returns no results
- Wiki might be empty; run `python tools/compile.py --new` first
- Search looks for tokens > 2 chars, removes stopwords
- Try shorter, more specific queries

### Obsidian showing broken links
- Run `python tools/lint.py all` to check for orphans
- Rebuild indexes: `python tools/compile.py --new` (even with 0 new files)

---

## Philosophy

This system is designed so that:
1. **LLM does the hard work**: Writing, organizing, maintaining the wiki
2. **You do the thinking**: Ask good questions, feed in good sources, decide what matters
3. **Obsidian is the view**: Everything is markdown, everything is linkable
4. **Iteration compounds**: Each query, lint check, and new document improves the whole base

The goal is a living, evolving knowledge base that gets smarter as you use it.

---

## Next Steps

1. Configure `config.yaml` with your wiki name and domain
2. Add your first raw document: `raw/my-article.md`
3. Compile: `python tools/compile.py --new`
4. Explore: open `wiki/INDEX.md` or open in Obsidian
5. Ask questions: `python tools/query.py "What do you know?"`
6. Iterate: lint, suggest, expand, refine
