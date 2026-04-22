# AGENTS.md — Regole operative per l'LLM agent

Questo file è il **sistema operativo del wiki**. L'LLM agent deve leggerlo prima di ogni operazione e rispettarne le regole senza eccezioni. Se una regola va cambiata, aggiornare questo file prima di applicare la modifica.

---

## 1. Missione

Costruire e mantenere una **knowledge base personale in Markdown** a partire da fonti grezze fornite dall'utente. Il wiki è scritto e mantenuto dall'LLM; l'utente cura le fonti e pone le domande.

Il dominio del wiki è definito in `config.yaml` (campo `wiki.name` e `wiki.description`). Aggiornare quella sezione quando si inizia un nuovo progetto wiki.

---

## 2. Ownership dei file

| Directory | Owner | Regola |
|-----------|-------|--------|
| `raw/` | Utente | **APPEND-ONLY**. L'LLM non modifica mai file in `raw/`. Mai. |
| `wiki/` | LLM | Completamente rigenerabile. L'LLM scrive, aggiorna, elimina articoli liberamente. |
| `outputs/` | LLM (effimero) | Risposte a query. Non indicizzato, non linkato nel wiki. |
| `tools/` | Sviluppatore | L'LLM può modificare solo su esplicita richiesta dell'utente. |

---

## 3. Convenzioni di naming file

- **Formato**: `kebab-case.md` (tutto minuscolo, parole separate da trattini)
- **Lingua nomi file**: italiano, salvo nomi propri/termini tecnici (es. `overjet.md`, `twin-block.md`)
- **Nessun accento nei nomi file** (es. `analisi-cefalometrica.md`, non `análisi-cefalométrica.md`)
- **Esempi corretti**: `classe-ii-angle.md`, `espansore-palatale-rapido.md`, `analisi-steiner.md`
- **Esempi errati**: `ClasseII.md`, `classe_II_div.1.md`, `Classe-II Angle.md`

---

## 4. Frontmatter YAML obbligatorio

Ogni articolo in `wiki/` deve avere questo frontmatter:

```yaml
---
title: Titolo dell'articolo
type: concept
created: 2026-04-22
updated: 2026-04-22
tags: [tag1, tag2]
summary: Descrizione in una riga (max 150 caratteri)
sources: [raw/papers/autore-anno.pdf, raw/web/articolo.md]
related: [[articolo-collegato-1]], [[articolo-collegato-2]]
---
```

**Campo `type`** — valori ammessi:
- `concept` — concetti fondamentali e definizioni
- `topic` — argomenti ampi e panoramiche
- `condition` — quadri clinici e patologie
- `treatment` — trattamenti e procedure
- `person` — ricercatori, clinici di rilievo
- `paper` — schede sintetiche di singoli articoli scientifici
- `guideline` — linee guida e consensus

---

## 5. Linking

- **Link interni**: wikilink Obsidian `[[nome-file-senza-estensione]]`
- **Link esterni**: Markdown standard `[testo](https://url)`
- I link sono **bidirezionali**: quando si crea un link A→B, verificare se B dovrebbe anche linkare A
- Non usare mai path relativi per link interni (es. `[testo](../concepts/file.md)` è sbagliato)

---

## 6. Quando creare un nuovo articolo vs espandere uno esistente

**Creare nuovo articolo** se:
- Il concetto ha ≥ ~300 parole di contenuto potenziale
- Almeno 2 fonti in `raw/` lo citano in modo non accessorio
- È già referenziato con `[[wikilink]]` da altri articoli

**Espandere articolo esistente** se:
- Il concetto è una sfumatura o sottocaso di un articolo già esistente
- Le informazioni aggiuntive sono < ~200 parole

---

## 7. Aggiornamento indici (obbligatorio)

Dopo ogni operazione che crea, rinomina o elimina articoli:

1. Aggiornare `wiki/INDEX.md` — eseguire `wiki_ops.write_index()` o ricostruire manualmente
2. Aggiornare `wiki/_meta/backlinks.json` — eseguire `wiki_ops.rebuild_backlinks()`
3. Aggiornare `wiki/_meta/summaries.json` — eseguire `wiki_ops.rebuild_summaries()`

**Non lasciare mai INDEX.md desincronizzato rispetto agli articoli in `wiki/concepts/`.**

---

## 8. Stile di scrittura

- **Lingua**: italiano tecnico preciso
- **Terminologia**: clinica/scientifica esatta; termini tecnici inglesi consolidati sono ammessi (es. *overjet*, *crossbite*, *workflow*)
- **Niente padding divulgativo**: no frasi del tipo "È importante sapere che...", "Come tutti sappiamo..."
- **Citazioni puntuali**: ogni affermazione non banale cita almeno una fonte da `raw/` nel frontmatter o inline con `(fonte: [[paper-slug]])`
- **Sezione "Controversie"**: se due fonti divergono su un punto, aggiungere sezione dedicata — non scegliere arbitrariamente

---

## 9. Gestione delle contraddizioni tra fonti

Se fonte A e fonte B affermano cose diverse sullo stesso punto:

```markdown
## Controversie

**Posizione A** (fonte: [[paper-a]]): ...descrizione...

**Posizione B** (fonte: [[paper-b]]): ...descrizione...

*Allo stato attuale non esiste consenso su questo punto.*
```

L'LLM non prende posizione senza evidenza esplicita da fonti in `raw/`.

---

## 10. Limiti di scope

- Il wiki **non dà consigli clinici** al paziente
- È strumento di ricerca, studio e apprendimento
- Non inventare riferimenti bibliografici: se una fonte non è in `raw/`, non citarla come se lo fosse
- Non riscrivere `wiki/` da zero senza avvertire l'utente e attendere conferma per modifiche > 10 file

---

## 11. Commit git

- **Un commit per fase operativa** (ingestion, compilazione, linting, ecc.)
- **Messaggio in inglese imperativo**, es:
  - `compile: add 3 articles from raw/papers/`
  - `lint: fix 2 broken wikilinks`
  - `update: expand classe-ii-angle with treatment section`
- Committare sempre dopo una compilazione andata a buon fine

---

## 12. Procedura per modifiche massive

Prima di modificare > 10 file:
1. Descrivere il piano all'utente
2. Attendere conferma esplicita
3. Eseguire in batch con commit intermedi
4. Comunicare il risultato

---

*Fine AGENTS.md. Questo file va letto a ogni sessione di lavoro sul wiki.*
