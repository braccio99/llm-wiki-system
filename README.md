# LLM Wiki System

A personal knowledge base powered by Claude. Drop raw documents in, ask questions, get a structured and interlinked wiki maintained by the LLM.

**Core principle**: you provide the sources in `raw/`, the LLM compiles and maintains the wiki, you ask the questions.

---

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/braccio99/llm-wiki-system.git
cd llm-wiki-system

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API key
cp .env.example .env
# Open .env and add your ANTHROPIC_API_KEY
```

---

## Configuration

Edit `config.yaml` to set up your wiki:

```yaml
wiki:
  name: "My Wiki"
  description: "What this wiki is about"
  language: "english"   # or "italian"
```

---

## Usage

### 1. Add source documents

Drop any `.md` or `.txt` files into `raw/` (or its subdirectories):

```
raw/
  papers/     ← research papers
  web/        ← markdown from Obsidian Web Clipper
  books/      ← book excerpts
  notes/      ← personal notes
```

### 2. Compile into wiki

```bash
# Process only new/modified files
python tools/compile.py --new

# Reprocess everything
python tools/compile.py --all
```

Each file generates an article in `wiki/concepts/` with YAML frontmatter, tags, and backlinks.

### 3. Ask questions

```bash
# Plain answer
python tools/query.py "What is the difference between X and Y?"

# Save output
python tools/query.py "Explain concept Z" --save

# Generate Marp slides
python tools/query.py "Explain concept Z" --format marp --save

# Generate matplotlib chart
python tools/query.py "Visualize relationships between A and B" --format chart --save

# Use more context documents
python tools/query.py "Complex question" --top 10
```

### 4. Search

```bash
python tools/search.py "keyword"

# JSON output (for scripting)
python tools/search.py "keyword" --json
```

### 5. Health checks

```bash
python tools/lint.py all              # run all checks
python tools/lint.py orphans          # articles with no backlinks
python tools/lint.py summaries        # missing summaries
python tools/lint.py inconsistencies  # contradictions between articles
python tools/lint.py suggest          # suggest new articles to write
```

---

## Dashboard

A local web UI to manage the wiki without using the terminal.

```bash
cd dashboard
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8000` in your browser.

Features: upload files, compile, query, search, lint, chat with the wiki.

---

## Typical workflow

```bash
# Drop sources into raw/
python tools/compile.py --new       # → creates/updates wiki/concepts/
python tools/query.py "Your question" --save  # → saves answer to outputs/qa/
python tools/lint.py all            # → finds gaps, orphans, suggests new topics
```

---

## Directory structure

```
raw/              ← Your source documents (append-only)
wiki/
  INDEX.md        ← Master index, auto-updated on every compile
  concepts/       ← Generated articles
  _meta/          ← Backlinks and summaries index
outputs/          ← Generated Q&A, slides, charts
tools/            ← CLI tools (compile, query, lint, search)
dashboard/        ← Web UI
config.yaml       ← System configuration
.env              ← API key (never commit this)
AGENTS.md         ← Operational rules for the LLM agent
```

---

## Obsidian integration

1. File → Open vault → select this directory
2. Recommended plugins: **Marp** (slides), **Dataview**, **Graph View**
3. `wiki/INDEX.md` is the entry point; `[[WikiLinks]]` navigate between articles

---

## Key files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Operational rules for the LLM — read before every session |
| `config.yaml` | System configuration (model, language, paths) |
| `wiki/INDEX.md` | Master index, auto-updated |
| `.env` | Anthropic API key (never commit) |

---

## Token monitoring

Every command prints token stats at the end:
- `cache_read_input_tokens` — tokens served from cache (not billed)

To use a more powerful model for complex queries:

```bash
# In config.yaml
model: "claude-opus-4-7"

# Or via environment variable
LLM_MODEL=claude-opus-4-7 python tools/query.py "Complex question"
```
