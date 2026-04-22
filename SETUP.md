# 🚀 Setup Guide - LLM Wiki System

Your LLM Wiki System is **ready to use**! Follow these steps to get started.

---

## Step 1: Install Python Dependencies

```bash
# From the LLM WIKI directory
pip install -r requirements.txt
```

This installs:
- `anthropic` - Claude API client
- `click` - CLI framework
- `rich` - Beautiful terminal output
- `rank-bm25` - Search engine
- `pyyaml` - Configuration
- Other utilities

---

## Step 2: Configure API Access

### Option A: Environment Variable

```bash
# Linux/macOS
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=sk-ant-...
```

### Option B: .env File (Recommended)

```bash
# Copy the template
cp .env.example .env

# Edit .env with your API key
# Windows: notepad .env
# Linux/macOS: nano .env
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Step 3: Test the System (Optional)

A sample document is already in `raw/example_article.md`. Test the compilation:

```bash
# See available options
python tools/compile.py --help

# Compile the example article
python tools/compile.py --new
```

You should see:
- Progress bar for processing
- New article created in `wiki/concepts/`
- Index and metadata files generated

---

## Step 4: Start Using

### Add Your Own Documents

1. Find articles, PDFs, or web content you want to analyze
2. Convert to markdown (use **Obsidian Web Clipper** for web articles)
3. Drop files in `raw/` directory
4. Run: `python tools/compile.py --new`

### Ask Questions

```bash
python tools/query.py "Your question here?"
```

### Generate Slides

```bash
python tools/query.py "Topic for presentation" --format marp --save
```

### Search the Wiki

```bash
python tools/search.py "search terms"
```

### Check Wiki Health

```bash
python tools/lint.py all
```

---

## Step 5: Open in Obsidian (Optional)

For the best experience, open the wiki in Obsidian:

1. **Download Obsidian**: https://obsidian.md
2. **Open Vault**: File → Open vault as folder
3. **Select**: The `LLM WIKI` directory
4. **Explore**: Browse articles, click links, view graph
5. **Recommended plugins**:
   - **Marp** (for viewing generated slides)
   - **Dataview** (for dynamic queries)
   - Graph View (built-in, already available)

---

## Common Commands

```bash
# Compile new documents
python tools/compile.py --new

# Ask a question and save the answer
python tools/query.py "Your question?" --save

# Search for articles
python tools/search.py "search query"

# Check wiki health
python tools/lint.py all

# Get help on any command
python tools/compile.py --help
python tools/query.py --help
python tools/search.py --help
python tools/lint.py --help
```

---

## Configuration

The system is configured via `config.yaml`. You can:

- **Change the LLM model**: Set `model: claude-opus-4-6` for higher quality
- **Adjust temperature**: Lower (0.3) for accuracy, higher (0.8) for creativity
- **Customize paths**: Modify output directories
- **Tune search**: Adjust BM25 parameters

Example:
```yaml
llm:
  model: "claude-opus-4-6"  # Switch to Opus for complex tasks
  temperature: 0.5           # Balanced accuracy/creativity
```

---

## Troubleshooting

### Error: "ANTHROPIC_API_KEY not found"
- **Solution**: Make sure you've created `.env` with your API key, or set the environment variable

### Error: "ModuleNotFoundError: anthropic"
- **Solution**: Run `pip install -r requirements.txt`

### Commands not found (Python/pip)
- **Windows**: Make sure Python is installed and added to PATH
- **Linux/macOS**: Try `python3` and `pip3` instead of `python` and `pip`

### Nothing gets compiled
- **Solution**: Make sure files in `raw/` are `.md` or `.txt`
- Check the API key is valid (test with a simple query first)
- Look for error messages in the console

---

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Configure API key in `.env`
3. ✅ Test with example: `python tools/compile.py --new`
4. Add your own documents to `raw/`
5. Compile: `python tools/compile.py --new`
6. Ask questions: `python tools/query.py "What do you know?"`
7. Explore in Obsidian (optional)
8. Build your knowledge base!

---

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete system documentation and advanced usage
- **[README.md](README.md)** - Overview and feature list
- **[config.yaml](config.yaml)** - Configuration options with comments

---

## Getting Help

**For CLI help:**
```bash
python tools/compile.py --help
python tools/query.py --help
python tools/search.py --help
python tools/lint.py --help
```

**For detailed documentation:**
Read [CLAUDE.md](CLAUDE.md) - it covers everything including:
- Article format specification
- Workflow examples
- Obsidian integration
- Advanced scripting
- Troubleshooting

---

## Happy Knowledge Building! 📚

Start with `python tools/compile.py --new` and explore from there.
