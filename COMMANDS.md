# 📋 Quick Command Reference

Copy-paste these commands to use your wiki system.

---

## 🔨 Compilation (Ingest Documents)

```bash
# Compile new/modified files in raw/
python tools/compile.py --new

# Recompile everything
python tools/compile.py --all

# Compile only the first 10 files (safer for large batches)
python tools/compile.py --new --max-files 10

# See all options
python tools/compile.py --help
```

---

## ❓ Q&A (Ask Questions)

```bash
# Ask a simple question
python tools/query.py "Your question here?"

# Save answer to outputs/qa/
python tools/query.py "Your question?" --save

# Generate Marp slides and save
python tools/query.py "Create a presentation on topic X" --format marp --save

# Generate matplotlib visualization code and save
python tools/query.py "Visualize the data about topic Y" --format chart --save

# Use specific number of documents for context
python tools/query.py "Question?" --top 10

# See all options
python tools/query.py --help
```

---

## 🔎 Search

```bash
# Search for articles
python tools/search.py "search query"

# Get top 20 results instead of default 10
python tools/search.py "query" --top 20

# Get results as JSON (for scripting)
python tools/search.py "query" --json

# See all options
python tools/search.py --help
```

---

## 🧹 Linting (Health Checks)

```bash
# Run all health checks
python tools/lint.py all

# Find orphaned articles (no incoming links)
python tools/lint.py orphans

# Find articles missing summaries
python tools/lint.py summaries

# Check for inconsistencies between related articles
python tools/lint.py inconsistencies

# Get suggestions for new article topics
python tools/lint.py suggest

# See all options
python tools/lint.py --help
```

---

## 🌊 Typical Workflow

```bash
# Day 1: Add documents and compile
cp ~/Documents/article1.md raw/
cp ~/Documents/article2.md raw/
python tools/compile.py --new

# Day 2: Ask questions
python tools/query.py "What's the relationship between topic A and B?" --save

# Day 3: Health check
python tools/lint.py all

# Day 4: Generate presentation
python tools/query.py "Create slides on topic C" --format marp --save

# Day 5: Expand
python tools/compile.py --new
python tools/search.py "recent additions"
```

---

## 🎯 Common Queries

```bash
# Get an overview of a topic
python tools/query.py "Give me an overview of [topic]"

# Compare concepts
python tools/query.py "Compare [concept A] vs [concept B]"

# Find connections
python tools/query.py "How do [A], [B], and [C] relate?"

# Extract key points
python tools/query.py "What are the 5 most important points about [topic]?"

# Create summary
python tools/query.py "Summarize everything I know about [topic]" --save

# Learn step by step
python tools/query.py "Explain [topic] as if I were a beginner"
```

---

## 🎨 Output Generation

```bash
# Generate educational slides
python tools/query.py "Create a lecture on [topic]" --format marp --save

# Generate charts
python tools/query.py "Create a visualization showing [data relationship]" --format chart --save

# Save Q&A as markdown article
python tools/query.py "Deep dive into [topic]" --format md --save
```

---

## 🔧 Configuration

Edit `config.yaml` for:

```yaml
# Switch to a more capable model (for complex questions)
llm:
  model: "claude-opus-4-6"

# Adjust creativity vs accuracy (0.0-1.0)
llm:
  temperature: 0.5  # Lower = more accurate, Higher = more creative

# Change search behavior
search:
  top_k: 15  # Return more results by default
```

---

## 🐍 Python Scripting

Use the libraries in your own Python code:

```python
from tools.lib import ClaudeClient, WikiOps, SearchEngine

# Initialize
client = ClaudeClient(model="claude-opus-4-6")
wiki = WikiOps(wiki_root="./wiki")
search = SearchEngine(wiki_root="./wiki")

# Search
results = search.search("your query", top_k=5)
for slug, score, snippet in results:
    print(f"{slug}: {score:.3f} - {snippet}")

# Read an article
fm, body = wiki.read_article("article_slug")
print(fm["title"])
print(body)

# Ask Claude with context
answer = client.chat_with_context(
    "Your question?",
    context_documents=[body],
    system="You are a helpful assistant"
)
print(answer)
```

---

## 📊 View Stats

All commands print token usage statistics:

```
Tokens: 1234 in, 567 out
```

Monitor these to optimize your workflow.

---

## 🆘 Help

```bash
# Get help for any command
python tools/compile.py --help
python tools/query.py --help
python tools/search.py --help
python tools/lint.py --help
```

See [CLAUDE.md](CLAUDE.md) for detailed documentation.

---

## 💡 Pro Tips

1. **Batch process**: Use `--max-files` to process documents safely
2. **Monitor caching**: Look for `cache_read_input_tokens` to verify prompt caching is working
3. **Use Obsidian**: Open folder as vault to browse articles with backlinks
4. **Custom scripts**: Create Python scripts in `tools/` for automated workflows
5. **Regular linting**: Run `python tools/lint.py all` weekly to maintain quality

---

**Ready to build your knowledge base!** 🚀
