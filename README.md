# 📚 LLM Wiki System

A personal knowledge base system powered by Claude that compiles raw documents into an organized, interconnected wiki.

**Vision**: Raw data → LLM-driven compilation → searchable, queryable knowledge base → Obsidian frontend

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Add a document to raw/
# (download an article, save as raw/article.md)

# 4. Compile into wiki
python tools/compile.py --new

# 5. Ask a question
python tools/query.py "What do you know about [topic]?"

# 6. Open in Obsidian
# File → Open vault → select this directory
```

---

## 🎯 What It Does

| Operation | Command | Output |
|-----------|---------|--------|
| **Ingest documents** | `python tools/compile.py --new` | Articles in `wiki/concepts/` |
| **Ask questions** | `python tools/query.py "question"` | Markdown answer with sources |
| **Generate slides** | `python tools/query.py "topic" --format marp --save` | Marp presentation in `outputs/slides/` |
| **Visualize data** | `python tools/query.py "chart topic" --format chart --save` | Matplotlib code in `outputs/charts/` |
| **Search wiki** | `python tools/search.py "query"` | BM25 ranked results |
| **Health checks** | `python tools/lint.py all` | Orphaned articles, suggestions, inconsistencies |

---

## 📁 Directory Structure

```
raw/                    # Your source documents
wiki/
  ├── _index.md        # Auto-generated index of all articles
  └── concepts/        # Individual articles (created by LLM)
outputs/
  ├── qa/              # Q&A results
  ├── slides/          # Marp presentations
  └── charts/          # Matplotlib visualizations
tools/
  ├── compile.py       # Ingest documents
  ├── query.py         # Q&A engine
  ├── lint.py          # Health checks
  ├── search.py        # Search engine
  └── lib/             # Shared libraries
```

---

## 🧠 How It Works

1. **Ingest**: Drop markdown/text files in `raw/`
2. **Compile**: Claude reads raw files, extracts structure, creates wiki articles with:
   - Title, summary, tags
   - Body content
   - Backlinks to related articles
3. **Index**: Auto-generates `wiki/_index.md` + metadata indexes
4. **Query**: Ask Claude questions against the indexed wiki
5. **Output**: Generate markdown, slides (Marp), or charts (matplotlib)
6. **Maintain**: Linting detects orphans, inconsistencies, suggests new topics
7. **View**: Open in Obsidian for seamless browsing and editing

---

## 🔧 Configuration

Edit `config.yaml` to customize:
- **LLM model** (default: claude-haiku-4-5-20251001)
- **Temperature** for creativity vs. accuracy
- **Batch sizes** for compilation
- **Output formats** and paths

---

## 📖 Full Documentation

See **[CLAUDE.md](CLAUDE.md)** for:
- Detailed usage examples
- Article format specifications
- Advanced features and scripting
- Troubleshooting guide
- Obsidian integration tips

---

## 🚀 Example Workflow

```bash
# Day 1: Ingest articles about machine learning
python tools/compile.py --new
# → Creates articles in wiki/concepts/

# Day 2: Ask a complex question
python tools/query.py "Compare supervised vs unsupervised learning" --save
# → Saves answer to outputs/qa/

# Day 3: Find gaps in knowledge
python tools/lint.py all
# → Suggests new articles, finds inconsistencies

# Day 4: Generate a presentation
python tools/query.py "Create a lecture on neural networks" --format marp --save
# → Saves slides to outputs/slides/, view in Obsidian

# Day 5: Keep building
# Repeat: add more documents, ask more questions, maintain quality
```

---

## 🔐 Security

- **API Keys**: Keep `ANTHROPIC_API_KEY` in `.env` (never commit)
- **Local Only**: No web search or external API calls (all data stays local)
- **.gitignore**: Configured to exclude `.env` and credentials

---

## 📊 Features

✅ **Automatic compilation** - Claude extracts structure from raw documents  
✅ **Bidirectional backlinks** - Auto-maintained [[WikiLink]] references  
✅ **Smart search** - BM25 full-text search over all articles  
✅ **Q&A engine** - Ask questions, get answers with sources  
✅ **Multiple outputs** - Markdown, Marp slides, matplotlib charts  
✅ **Health checks** - Lint for orphaned articles, inconsistencies, gaps  
✅ **Obsidian native** - Works as a standard markdown vault  
✅ **Prompt caching** - Efficient token usage with Claude API  

---

## 🎓 Use Cases

- **Research**: Build a knowledge base on any research topic
- **Learning**: Create a personal study wiki
- **Documentation**: Auto-compile internal docs into searchable wiki
- **Content creation**: Generate articles, slides, visualizations from research
- **Knowledge synthesis**: Get answers by querying across your sources

---

## 🛠️ Stack

- **Python 3.8+**
- **Claude API** (claude-haiku-4.5 default, any model supported)
- **Anthropic SDK** (with prompt caching)
- **BM25** for search
- **Click** for CLI
- **Obsidian** as frontend

---

## 📝 License

This is your personal knowledge base system. Modify and extend it freely.

---

## ❓ Questions?

See [CLAUDE.md](CLAUDE.md) for comprehensive documentation and troubleshooting.

Start with: `python tools/compile.py --help`
