# webseed — Guida Completa

## Cos'è webseed

webseed è una pipeline CLI che:
1. Trova business locali italiani **senza sito web** su Google Maps
2. Genera un **sito HTML professionale** per ognuno con Claude AI
3. Testa il sito con **code review automatica** e fix loop
4. Lo deploya su **Vercel** con URL pubblico unico
5. Crea una **email personalizzata** come bozza in Gmail, pronta da inviare
6. Tiene traccia di tutto in un **database locale** (TinyDB)

Ogni step è indipendente e ripetibile. Puoi fermarti a qualsiasi punto e riprendere dopo.

---

## Setup Iniziale

### 1. Installazione

```bash
git clone https://github.com/Mediacom99/webseed.git
cd webseed
python -m venv .venv
source .venv/bin/activate    # su macOS/Linux
pip install -e .
playwright install chromium  # per visual testing e screenshot email
```

### 2. Variabili d'ambiente

```bash
cp .env.example .env
```

Compila `.env` con:

| Variabile | Dove trovarla | Quando serve |
|-----------|--------------|--------------|
| `GOOGLE_MAPS_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/) → API → Places API (legacy) | `search` |
| `CONTACT_EMAIL` | La tua email di contatto | `email` |
| `GMAIL_CREDENTIALS_FILE` | GCP → Gmail API → OAuth credentials (vedi sotto) | `email` |
| `SENDER_NAME` | (opzionale) Nome mittente nelle email | `email` |
| `CLAUDE_CLI_PATH` | (opzionale) Path al binario Claude Code CLI — auto-detect se nel PATH | tutti gli step AI |
| `VERCEL_CLI_PATH` | (opzionale) Path al binario Vercel CLI — auto-detect se nel PATH | `deploy` |

> **Nota:** Claude Code CLI e Vercel CLI gestiscono la propria autenticazione autonomamente. Non serve nessun API key o token nel `.env` per questi tool.

### 3. Prerequisiti CLI

- **Claude Code CLI** — installato e autenticato ([docs](https://docs.anthropic.com/en/docs/claude-code))
- **Vercel CLI** — installato e loggato (`npm i -g vercel`)

### 4. Gmail API (solo per lo step `email`)

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Abilita la **Gmail API**
3. Configura **OAuth consent screen** → External
4. Crea **Credentials** → OAuth client ID → Desktop app
5. Scarica il JSON e salvalo come `credentials.json` nella root del progetto
6. Al primo `webseed email`, si aprirà il browser per il consenso OAuth → verrà salvato `token.json`

---

## Pipeline — I 5 Step

### Step 1: `search` — Trova business su Google Maps

```bash
webseed search --location "Milano, Italy" --query "ristorante" --limit 5
```

**Cosa fa:**
- Cerca business del tipo specificato nella zona indicata
- Filtra quelli che **non hanno un sito web**
- Scarica fino a 3 foto da Google Maps per ogni business
- Salva tutto nel database (`webseed.json`)
- Se la query primaria non trova abbastanza risultati, prova sinonimi automatici (es. "ristorante" → "trattoria", "osteria", "pizzeria")

**Flag:**
| Flag | Descrizione | Default |
|------|-------------|---------|
| `--location` | Città/zona (obbligatorio) | — |
| `--query` | Tipo di business (obbligatorio) | — |
| `--limit` | Numero massimo di business | 10 |

**Deduplicazione:** se un business è già nel database (stesso `place_id`), non viene duplicato — vengono solo aggiornati rating e recensioni. Se è nella blacklist, viene saltato.

**Status risultante:** `searched`

---

### Step 2: `generate` — Genera siti HTML con Claude

```bash
webseed generate PLACE_ID "nome business"
```

**Cosa fa:**
- Prende i business specificati (per place_id o nome parziale)
- Per ognuno, chiama Claude Code CLI con i dati del business
- Genera un file `index.html` completo (HTML + CSS + JS inline)
- Il sito include: hero, chi siamo, servizi, galleria foto, contatti con mappa, footer
- Tutto in italiano, con design professionale e responsive

**Flag:**
| Flag | Descrizione | Default |
|------|-------------|---------|
| `--model` | Modello Claude da usare | default CLI |

**Output per ogni business:**
```
results/{nome_business}/
├── index.html      ← sito generato
├── vercel.json     ← config Vercel
└── img/
    ├── photo1.jpg  ← foto da Google Maps
    ├── photo2.jpg
    └── photo3.jpg
```

**Status risultante:** `generated` (o `error_generate` in caso di errore)

**Costo:** ~$0.07 per sito

---

### Step 3: `test` — Code review e fix automatico

```bash
webseed test PLACE_ID "nome business"
webseed test PLACE_ID --playwright          # anche visual test con Playwright
webseed test PLACE_ID --max-fix-iterations 1  # limita cicli di fix (default: 3)
```

**Cosa fa:**

1. **Code review** (sempre) — Claude Code CLI analizza il sorgente `index.html` contro una QA checklist. Solo testo, nessun browser.
2. **Visual test** (con `--playwright`) — Claude Code CLI + Playwright MCP apre il file locale, fa screenshot, ispeziona il DOM, verifica errori console.
3. **Fix loop** (se il test trova problemi) — Claude Code CLI corregge l'HTML e ritesta, fino a `--max-fix-iterations` cicli.

**Flag:**
| Flag | Descrizione | Default |
|------|-------------|---------|
| `--playwright` | Abilita visual test con Playwright | disabilitato |
| `--test-model` | Modello Claude per il testing | sonnet |
| `--max-fix-iterations` | Numero massimo di cicli fix-retest | 3 |

**Status risultante:** `tested` (o `error_test` in caso di errore)

**Costo:** ~$0.05-0.10 per test, ~$0.03-0.05 per fix

---

### Step 4: `deploy` — Deploy su Vercel

```bash
webseed deploy PLACE_ID "nome business"
```

**Cosa fa per ogni business con status `tested`:**

1. **Deploy** — deploya sotto un singolo progetto `webseed` su Vercel. Ogni business riceve un URL pubblico permanente e unico.
2. **Screenshot email** — cattura un'immagine 1280x600 dell'above-the-fold per l'email via Python Playwright (non bloccante se fallisce).

**Status risultante:** `deployed` (o `error_deploy` in caso di errore)

---

### Step 5: `email` — Crea bozze email in Gmail

```bash
webseed email PLACE_ID "nome business"
webseed email PLACE_ID --model opus    # modello specifico
```

**Cosa fa per ogni business con status `deployed`:**

1. **Genera email con Claude** — email personalizzata in italiano con:
   - Saluto col nome del business
   - Complimento basato su rating/recensioni Google
   - Link al sito già pronto
   - Prezzi: €299 setup + €9/mese
   - Call to action: rispondi o chiama
   - Footer legale minimale
2. **Crea bozza Gmail** — la email viene salvata come bozza nel tuo Gmail con:
   - Label `webseed-queue` per trovarle facilmente
   - Screenshot del sito embeddata come immagine inline
   - Campo `To:` vuoto (da compilare manualmente, perché Maps spesso non ha email)

**Flag:**
| Flag | Descrizione | Default |
|------|-------------|---------|
| `--model` | Modello Claude da usare | default CLI |

**Come inviare:** apri Gmail → cerca la label `webseed-queue` → rivedi ogni bozza → aggiungi destinatario → invia.

**Status risultante:** `email_queued`

**Costo:** ~$0.03 per email

---

## Comando `run` — Pipeline Completa

```bash
webseed run PLACE_ID [PLACE_ID...]       # pipeline completa per business specifici
webseed run "nome business" --no-email   # salta lo step email
webseed run PLACE_ID --model opus        # modello specifico per generazione/email
webseed run PLACE_ID --hard              # qualità massima: opus, 3 fix iterations, verbose
```

Esegue `generate → test → deploy → email` in sequenza per i business specificati.

**Flag:**
| Flag | Descrizione | Default |
|------|-------------|---------|
| `--model` | Modello per generazione e email | default CLI |
| `--test-model` | Modello per testing | sonnet |
| `--max-fix-iterations` | Cicli fix-retest | 3 |
| `--no-email` | Salta lo step email | — |
| `--hard` | Deep run: opus, 3 fix iterations, verbose | — |

---

## Comandi di Gestione

### `status` — Vedi lo stato di tutti i business

```bash
webseed status                         # tutti
webseed status --filter deployed       # solo deployati
webseed status --filter error          # solo errori
```

Mostra una tabella con: nome, status, URL Vercel, data ultimo aggiornamento. Il filtro funziona per prefisso.

### `show` — Dettaglio completo di un business

```bash
webseed show PLACE_ID
webseed show "nome parziale"
```

Mostra tutti i campi del business: nome, indirizzo, telefono, rating, status, URL, screenshot, date, ecc.

### `stats` — Statistiche riassuntive

```bash
webseed stats
```

Conteggio per ogni status + totale business nel database.

### `blacklist-add` / `blacklist-remove` / `blacklist-list`

```bash
webseed blacklist-add PLACE_ID [PLACE_ID...]    # blocca
webseed blacklist-remove PLACE_ID               # sblocca
webseed blacklist-list                          # mostra tutti
```

Il business bloccato viene marcato come `opted_out` nel database e saltato automaticamente.

### `reset` — Resetta lo status

```bash
webseed reset PLACE_ID --to searched    # rigenerare il sito
webseed reset PLACE_ID --to generated   # ritestare
webseed reset PLACE_ID --to tested      # ri-deployare
webseed reset PLACE_ID --to deployed    # ricreare l'email
```

### `db-delete` — Rimuovi dal database

```bash
webseed db-delete PLACE_ID [PLACE_ID...]       # rimuovi specifici (mantiene file e Vercel)
webseed db-delete --all --skip PLACE_ID        # rimuovi tutti tranne quelli specificati
```

### `hard-delete` — Rimuovi tutto

```bash
webseed hard-delete PLACE_ID [PLACE_ID...]     # DB + file locali + deploy Vercel
webseed hard-delete --blacklist PLACE_ID       # come sopra ma mantiene come blacklistato
webseed hard-delete -y PLACE_ID                # senza conferma
```

### `export-csv` — Esporta in CSV

```bash
webseed export-csv --output results.csv
```

---

## Flag Globali

Questi flag si applicano a **tutti** i comandi:

| Flag | Descrizione | Default |
|------|-------------|---------|
| `--db` | File database TinyDB | `webseed.json` |
| `--results-dir` | Directory output | `results/` |
| `-v` / `--verbose` | Logging DEBUG | disabilitato |

---

## Workflow Tipico

```bash
# 1. Cerca ristoranti a Milano
webseed search --location "Milano, Italy" --query "ristorante" --limit 10

# 2. Controlla cosa ha trovato
webseed status
webseed stats

# 3. Pipeline completa per business specifici
webseed run "ristorante da mario" "pizzeria bella napoli"

# oppure step by step:
webseed generate "ristorante da mario"
webseed test "ristorante da mario"
webseed deploy "ristorante da mario"
webseed email "ristorante da mario"

# 4. Controlla i risultati
webseed status --filter deployed

# 5. Vai su Gmail, cerca label "webseed-queue", rivedi e invia

# 6. Esporta tutto in CSV se serve
webseed export-csv
```

---

## Gestione Errori

Se un business fallisce durante uno step, viene marcato con lo status corrispondente (es. `error_generate`, `error_test`). Gli altri business continuano normalmente.

Per ritentare:

```bash
# Vedi quali sono in errore
webseed status --filter error

# Guarda il dettaglio dell'errore
webseed show PLACE_ID

# Resetta e riprova
webseed reset PLACE_ID --to searched
webseed generate PLACE_ID
```

---

## Status di un Business

Un business attraversa questi stati durante la pipeline:

```
searched → generated → tested → deployed → email_queued
```

Stati di errore: `error_generate`, `error_test`, `error_deploy`, `error_email`

Stato speciale: `opted_out` (blacklistato)

Puoi resettare qualsiasi business a uno stato precedente con `reset` per riprocessarlo. La maggior parte dei comandi accetta place_id o nomi parziali (case-insensitive).

---

## File di Stato

| File | Descrizione | In .gitignore |
|------|-------------|---------------|
| `webseed.json` | Database TinyDB con tutti i dati | Sì |
| `blacklist.txt` | Place ID bloccati, uno per riga | Sì |
| `credentials.json` | Credenziali OAuth Gmail | Sì |
| `token.json` | Token OAuth Gmail (auto-generato) | Sì |
| `.env` | Variabili d'ambiente | Sì |
| `results/` | Siti generati, screenshot | Sì |

---

## Costi

| Step | Costo per business |
|------|-------------------|
| Generate | ~$0.07 |
| Test (code review) | ~$0.05-0.10 |
| Fix (per iterazione) | ~$0.03-0.05 |
| Email | ~$0.03 |
| **Caso peggiore (3 cicli fix)** | **~$0.40-0.70** |
| **Caso ottimale (no fix)** | **~$0.15** |

Tutti i costi sono da Claude Code CLI. Google Maps API e Vercel hanno i propri free tier.
