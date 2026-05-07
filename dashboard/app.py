#!/usr/bin/env python3
"""LLM Wiki Dashboard — FastAPI backend"""

import asyncio
import json
import os
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="LLM Wiki Dashboard")

WIKIS_FILE = Path(__file__).parent / "wikis.json"
STATIC_DIR = Path(__file__).parent / "static"


# ── Wiki registry ──────────────────────────────────────────────────────────────

def load_registry() -> dict:
    if WIKIS_FILE.exists():
        return json.loads(WIKIS_FILE.read_text(encoding="utf-8"))
    return {"wikis": [], "active": None}


def save_registry(data: dict):
    WIKIS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_active_path() -> Path:
    reg = load_registry()
    if not reg["active"]:
        raise HTTPException(400, "Nessun wiki selezionato")
    p = Path(reg["active"])
    if not p.exists():
        raise HTTPException(400, f"Cartella non trovata: {p}")
    return p


def is_valid_wiki(p: Path) -> bool:
    return (p / "config.yaml").exists() and (p / "tools" / "compile.py").exists()


def wiki_env(wiki: Path) -> dict:
    """Environment with .env loaded from the wiki directory."""
    env = os.environ.copy()
    dotenv_path = wiki / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=True)
        env.update({k: v for k, v in os.environ.items()})
    return env


def wiki_model(wiki: Path) -> str:
    cfg = yaml.safe_load((wiki / "config.yaml").read_text(encoding="utf-8"))
    return cfg.get("llm", {}).get("model", "claude-haiku-4-5-20251001")


def wiki_client(wiki: Path):
    import anthropic
    env = wiki_env(wiki)
    key = env.get("ANTHROPIC_API_KEY")
    if not key:
        raise HTTPException(400, "ANTHROPIC_API_KEY non trovata nel wiki")
    return anthropic.Anthropic(api_key=key)


async def search_slugs(wiki: Path, query: str, top: int = 5) -> list[str]:
    """Run BM25 search and return top slugs."""
    cmd = [sys.executable, str(wiki / "tools" / "search.py"), query, "--top", str(top), "--json"]
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=str(wiki),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        env=wiki_env(wiki),
    )
    stdout, _ = await proc.communicate()
    try:
        return [r["slug"] for r in json.loads(stdout.decode("utf-8", errors="replace"))]
    except Exception:
        return []


def load_articles_text(wiki: Path, slugs: list[str]) -> list[str]:
    """Load article body text for given slugs (strips frontmatter)."""
    docs = []
    for slug in slugs:
        path = wiki / "wiki" / "concepts" / f"{slug}.md"
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            content = parts[2].strip() if len(parts) >= 3 else content
        docs.append(f"## {slug}\n{content[:2000]}")
    return docs


def make_slug(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return re.sub(r"-+", "-", s).strip("-")


# ── API: Wiki management ───────────────────────────────────────────────────────

@app.get("/api/wikis")
def list_wikis():
    return load_registry()


class WikiPath(BaseModel):
    path: str


@app.post("/api/wikis")
def add_wiki(body: WikiPath):
    p = Path(body.path).expanduser().resolve()
    if not p.exists():
        raise HTTPException(404, "Percorso non trovato")
    if not is_valid_wiki(p):
        raise HTTPException(400, "Non è una cartella wiki valida (manca config.yaml o tools/)")
    reg = load_registry()
    s = str(p)
    if s not in reg["wikis"]:
        reg["wikis"].append(s)
    if not reg["active"]:
        reg["active"] = s
    save_registry(reg)
    return reg


@app.delete("/api/wikis")
def remove_wiki(body: WikiPath):
    reg = load_registry()
    s = str(Path(body.path).expanduser().resolve())
    reg["wikis"] = [w for w in reg["wikis"] if w != s]
    if reg["active"] == s:
        reg["active"] = reg["wikis"][0] if reg["wikis"] else None
    save_registry(reg)
    return reg


@app.post("/api/wikis/active")
def set_active(body: WikiPath):
    s = str(Path(body.path).expanduser().resolve())
    reg = load_registry()
    if s not in reg["wikis"]:
        raise HTTPException(404, "Wiki non registrato")
    reg["active"] = s
    save_registry(reg)
    return reg


@app.get("/api/wiki/info")
def wiki_info():
    wiki = get_active_path()
    cfg = yaml.safe_load((wiki / "config.yaml").read_text(encoding="utf-8"))
    concepts = wiki / "wiki" / "concepts"
    raw_dir = wiki / "raw"
    article_count = len(list(concepts.glob("*.md"))) if concepts.exists() else 0
    raw_count = len([f for f in raw_dir.rglob("*") if f.is_file() and not f.name.startswith("_")]) if raw_dir.exists() else 0
    return {
        "path": str(wiki),
        "name": cfg.get("wiki", {}).get("name", wiki.name),
        "description": cfg.get("wiki", {}).get("description", ""),
        "article_count": article_count,
        "raw_count": raw_count,
    }


# ── API: File upload ───────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...), folder: str = ""):
    wiki = get_active_path()
    dest_dir = wiki / "raw" / folder if folder else wiki / "raw"
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files:
        dest = dest_dir / f.filename
        dest.write_bytes(await f.read())
        saved.append(f.filename)
    return {"saved": saved}


@app.get("/api/raw")
def list_raw():
    wiki = get_active_path()
    raw_dir = wiki / "raw"
    if not raw_dir.exists():
        return {"files": []}
    files = [
        {"name": f.name, "size": f.stat().st_size}
        for f in sorted(raw_dir.rglob("*"))
        if f.is_file() and not f.name.startswith("_")
    ]
    return {"files": files}


# ── SSE streaming ──────────────────────────────────────────────────────────────

async def stream_tool(cmd: list[str], wiki: Path):
    env = wiki_env(wiki)
    kwargs = {}
    if sys.platform == "win32":
        import subprocess
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(wiki),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env,
        **kwargs,
    )

    async for line in process.stdout:
        text = line.decode("utf-8", errors="replace").rstrip()
        if text:
            yield f"data: {json.dumps(text)}\n\n"

    await process.wait()
    yield f"data: {json.dumps({'__done__': True, 'returncode': process.returncode})}\n\n"


# ── API: Compile ───────────────────────────────────────────────────────────────

@app.get("/api/stream/compile")
async def stream_compile(mode: str = "new"):
    wiki = get_active_path()
    flag = "--all" if mode == "all" else "--new"
    cmd = [sys.executable, str(wiki / "tools" / "compile.py"), flag]
    return StreamingResponse(stream_tool(cmd, wiki), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── API: Lint ──────────────────────────────────────────────────────────────────

@app.get("/api/stream/lint")
async def stream_lint(check: str = "all"):
    wiki = get_active_path()
    if check not in {"all", "orphans", "summaries", "inconsistencies", "suggest"}:
        raise HTTPException(400, f"Check non valido: {check}")
    cmd = [sys.executable, str(wiki / "tools" / "lint.py"), check]
    return StreamingResponse(stream_tool(cmd, wiki), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── API: Query ─────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    format: str = "md"
    top: int = 5


@app.post("/api/query")
async def run_query(body: QueryRequest):
    wiki = get_active_path()
    cmd = [
        sys.executable, str(wiki / "tools" / "query.py"),
        body.question,
        "--format", body.format,
        "--top", str(body.top),
        "--raw",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=str(wiki),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=wiki_env(wiki),
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        detail = stderr.decode("utf-8", errors="replace") or "Errore sconosciuto"
        raise HTTPException(500, detail)
    return {"answer": stdout.decode("utf-8", errors="replace")}


# ── API: Search ────────────────────────────────────────────────────────────────

@app.get("/api/search")
async def run_search(q: str, top: int = 10):
    wiki = get_active_path()
    cmd = [sys.executable, str(wiki / "tools" / "search.py"), q, "--top", str(top), "--json"]
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=str(wiki),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=wiki_env(wiki),
    )
    stdout, _ = await proc.communicate()
    try:
        results = json.loads(stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        results = []
    return {"results": results}


# ── API: Articles ──────────────────────────────────────────────────────────────

@app.get("/api/articles")
def list_articles():
    wiki = get_active_path()
    summaries_path = wiki / "wiki" / "_meta" / "summaries.json"
    if summaries_path.exists():
        summaries = json.loads(summaries_path.read_text(encoding="utf-8"))
        return {"articles": [{"slug": k, "summary": v} for k, v in summaries.items()]}
    concepts = wiki / "wiki" / "concepts"
    if not concepts.exists():
        return {"articles": []}
    return {"articles": [{"slug": f.stem, "summary": ""} for f in sorted(concepts.glob("*.md"))]}


@app.get("/api/articles/{slug}")
def read_article(slug: str):
    wiki = get_active_path()
    path = wiki / "wiki" / "concepts" / f"{slug}.md"
    if not path.exists():
        raise HTTPException(404, "Articolo non trovato")
    return {"content": path.read_text(encoding="utf-8")}


@app.get("/api/index")
def read_index():
    wiki = get_active_path()
    path = wiki / "wiki" / "INDEX.md"
    content = path.read_text(encoding="utf-8") if path.exists() else "*Nessun articolo ancora.*"
    return {"content": content}


# ── API: Config ────────────────────────────────────────────────────────────────

@app.get("/api/config")
def read_config():
    wiki = get_active_path()
    return {"content": (wiki / "config.yaml").read_text(encoding="utf-8")}


class ConfigBody(BaseModel):
    content: str


@app.put("/api/config")
def write_config(body: ConfigBody):
    wiki = get_active_path()
    try:
        yaml.safe_load(body.content)
    except yaml.YAMLError as e:
        raise HTTPException(400, f"YAML non valido: {e}")
    (wiki / "config.yaml").write_text(body.content, encoding="utf-8")
    return {"ok": True}


# ── API: Log ───────────────────────────────────────────────────────────────────

@app.get("/api/log")
def read_log():
    wiki = get_active_path()
    path = wiki / "log.md"
    content = path.read_text(encoding="utf-8") if path.exists() else "*Nessun log ancora.*"
    return {"content": content}


# ── API: Chat ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    messages: list[dict]   # [{role: "user"|"assistant", content: "..."}]
    top: int = 4


@app.post("/api/chat")
async def chat(body: ChatRequest):
    wiki = get_active_path()
    if not body.messages:
        raise HTTPException(400, "Nessun messaggio")

    last_user = next((m["content"] for m in reversed(body.messages) if m["role"] == "user"), "")

    # Retrieve wiki context via BM25
    slugs = await search_slugs(wiki, last_user, top=body.top)
    docs = load_articles_text(wiki, slugs)

    system = "Sei un assistente che risponde basandosi sulla knowledge base wiki fornita.\n" \
             "Rispondi in modo chiaro e conversazionale. " \
             "Quando citi un articolo usa la sintassi [[slug]].\n\n"
    if docs:
        system += "Articoli rilevanti dal wiki:\n\n" + "\n\n---\n\n".join(docs)
    else:
        system += "Il wiki è vuoto o non contiene articoli rilevanti. Rispondi con le tue conoscenze generali."

    client = wiki_client(wiki)
    response = client.messages.create(
        model=wiki_model(wiki),
        max_tokens=4096,
        system=system,
        messages=body.messages,
    )
    return {"answer": response.content[0].text, "context_slugs": slugs}


# ── API: Save to wiki ──────────────────────────────────────────────────────────

class SaveRequest(BaseModel):
    title: str
    content: str


@app.post("/api/save-to-wiki")
def save_to_wiki(body: SaveRequest):
    wiki = get_active_path()
    slug = make_slug(body.title)
    if not slug:
        raise HTTPException(400, "Titolo non valido")

    path = wiki / "wiki" / "concepts" / f"{slug}.md"
    now = datetime.now().isoformat(timespec="seconds")
    summary = body.content.split("\n")[0][:150]

    article = (
        f"---\ntitle: {body.title}\ntype: concept\n"
        f"created: {now}\nupdated: {now}\n"
        f"tags: []\nsummary: {summary}\nsources: [outputs/qa]\nrelated: []\n---\n\n"
        f"{body.content}\n"
    )
    path.write_text(article, encoding="utf-8")

    # Update summaries index
    sp = wiki / "wiki" / "_meta" / "summaries.json"
    summaries = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
    summaries[slug] = summary
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")

    return {"ok": True, "slug": slug}


# ── API: Obsidian ──────────────────────────────────────────────────────────────

@app.post("/api/obsidian")
def open_obsidian():
    wiki = get_active_path()
    from urllib.parse import quote
    webbrowser.open(f"obsidian://open?path={quote(str(wiki), safe='')}")
    return {"ok": True}


# ── Static files ───────────────────────────────────────────────────────────────

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
