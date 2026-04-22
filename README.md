# LLM Wiki

Sistema di knowledge base personale in Markdown, scritto e mantenuto dall'LLM a partire da fonti grezze fornite dall'utente.

**Principio**: tu depositi le fonti in `raw/`, l'LLM compila il wiki, tu fai le domande.

---

## Setup (una tantum)

```bash
pip install -r requirements.txt
cp .env.example .env
# Apri .env e inserisci la tua ANTHROPIC_API_KEY
```

Configura il tuo wiki in `config.yaml`:
```yaml
wiki:
  name: "Nome del tuo wiki"
  description: "Descrizione del dominio"
  language: "italian"   # oppure "english"
```

---

## Struttura directory

```
raw/              ← Le tue fonti (APPEND-ONLY, non modificare mai)
  papers/         ← PDF di articoli scientifici
  web/            ← .md da Obsidian Web Clipper
  books/          ← Estratti da libri
  notes/          ← Appunti personali
  images/         ← Immagini, figure, schemi
  datasets/       ← Dati strutturati

wiki/             ← Il wiki compilato (dominio esclusivo dell'LLM)
  INDEX.md        ← Punto d'ingresso — aggiornato ad ogni compilazione
  concepts/       ← Articoli generati

outputs/          ← Risposte a query (effimero)
  qa/             ← Risposte in Markdown
  slides/         ← Presentazioni Marp
  charts/         ← Codice matplotlib
```

---

## Comandi

### 1. Compilare le fonti in `raw/`

```bash
# Compila solo i file nuovi o modificati
python tools/compile.py --new

# Ricompila tutto
python tools/compile.py --all

# Limita il numero di file per sessione
python tools/compile.py --new --max-files 10
```

Ogni file processato genera un articolo in `wiki/concepts/` con frontmatter YAML, tags, backlinks e aggiorna `wiki/INDEX.md`.

### 2. Fare domande al wiki

```bash
# Risposta in Markdown
python tools/query.py "Qual è la differenza tra X e Y?"

# Genera presentazione Marp
python tools/query.py "Spiega il concetto Z" --format marp --save

# Genera codice matplotlib
python tools/query.py "Visualizza la relazione tra A e B" --format chart --save

# Usa più documenti come contesto
python tools/query.py "Domanda" --top 10
```

### 3. Cercare nel wiki

```bash
python tools/search.py "parola chiave"

# Output JSON (per scripting)
python tools/search.py "parola chiave" --json
```

### 4. Health check del wiki

```bash
# Tutti i controlli
python tools/lint.py all

# Solo articoli orfani (nessun backlink)
python tools/lint.py orphans

# Controlla summary mancanti
python tools/lint.py summaries

# Cerca contraddizioni tra articoli correlati
python tools/lint.py inconsistencies

# Suggerisce nuovi articoli da scrivere
python tools/lint.py suggest
```

---

## Workflow tipico

```bash
# Deposita fonti in raw/ (PDF, .md da web clipper, appunti)
# poi:

python tools/compile.py --new
# → Crea/aggiorna articoli in wiki/concepts/
# → Aggiorna wiki/INDEX.md

python tools/query.py "Domanda complessa sul dominio" --save
# → Risposta con citazioni agli articoli wiki salvata in outputs/qa/

python tools/lint.py all
# → Trova gap, articoli orfani, suggerisce nuovi topic
```

---

## Aprire in Obsidian

1. File → Open vault → seleziona questa directory
2. Plugin consigliati: **Marp** (per le slide), **Dataview**, **Graph View**
3. `wiki/INDEX.md` è il punto d'ingresso; i `[[WikiLink]]` navigano tra articoli

---

## File critici

| File | Scopo |
|------|-------|
| `AGENTS.md` | Regole operative per l'LLM — leggere prima di ogni sessione |
| `config.yaml` | Configurazione del sistema (modello, lingua, percorsi) |
| `wiki/INDEX.md` | Indice master del wiki, aggiornato automaticamente |
| `.env` | API key Anthropic (non committare mai) |

---

## Monitorare i token

Ogni comando stampa le statistiche token a fine esecuzione:
- `cache_read_input_tokens` — token letti dalla cache (non pagati)
- Alto valore di cache hit = prompt caching funzionante

Per query complesse, usa un modello più potente:
```bash
# In config.yaml
model: "claude-opus-4-7"
# oppure via env
LLM_MODEL=claude-opus-4-7 python tools/query.py "domanda"
```
