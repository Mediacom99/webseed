# webseed — Guida Completa

## Cos'è webseed

webseed è una pipeline CLI che:
1. Trova business locali italiani **senza sito web** su Google Maps
2. Genera un **sito HTML professionale** per ognuno con Claude AI
3. Lo deploya su **Vercel** (preview → test automatico → produzione)
4. Crea una **email personalizzata** come bozza in Gmail, pronta da inviare
5. Tiene traccia di tutto in un **database locale** (TinyDB)

Ogni step è indipendente e ripetibile. Puoi fermarti a qualsiasi punto e riprendere dopo.

---

## Setup Iniziale

### 1. Ambiente Python

```bash
python -m venv .venv
source .venv/bin/activate    # su macOS/Linux
pip install -r requirements.txt
```

### 2. Variabili d'ambiente

```bash
cp .env.example .env
```

Compila `.env` con:

| Variabile | Dove trovarla | Quando serve |
|-----------|--------------|--------------|
| `GOOGLE_MAPS_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/) → API → Places API (legacy) | `search` |
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/) oppure `claude setup-token` per MAX | `generate`, `email` |
| `VERCEL_TOKEN` | [Vercel Dashboard](https://vercel.com/account/tokens) | `deploy` |
| `GMAIL_CREDENTIALS_FILE` | GCP → Gmail API → OAuth credentials (vedi sotto) | `email` |
| `CONTACT_EMAIL` | La tua email di contatto | `email` |

### 3. Vercel CLI

```bash
npm i -g vercel
```

### 4. Playwright (per smoke test e screenshot)

```bash
playwright install chromium
```

### 5. Gmail API (solo per lo step `email`)

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Abilita la **Gmail API**
3. Configura **OAuth consent screen** → External
4. Crea **Credentials** → OAuth client ID → Desktop app
5. Scarica il JSON e salvalo come `credentials.json` nella root del progetto
6. Al primo `python pipeline.py email`, si aprirà il browser per il consenso OAuth → verrà salvato `token.json`

---

## Pipeline — I 4 Step

### Step 1: `search` — Trova business su Google Maps

```bash
python pipeline.py search --location "Milano, Italy" --query "ristorante" --limit 5
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
python pipeline.py generate
```

**Cosa fa:**
- Prende tutti i business con status `searched` dal database
- Per ognuno, chiama Claude AI con i dati del business
- Genera un file `index.html` completo (HTML + CSS + JS inline)
- Il sito include: hero, chi siamo, servizi, galleria foto, contatti con mappa, footer
- Tutto in italiano, con design professionale e responsive

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

### Step 3: `deploy` — Deploy su Vercel (preview → test → prod)

```bash
python pipeline.py deploy
```

**Cosa fa per ogni business con status `generated`:**

1. **Preview deploy** — deploya su un URL di anteprima (no produzione)
2. **Smoke test** — Playwright carica la pagina, verifica che funzioni
3. **Screenshot email** — cattura un'immagine 1280x600 dell'above-the-fold per l'email
4. **Promozione a prod** — se il test passa, promuove a produzione

**Naming Vercel:** ogni progetto si chiama `webseed-{nome-slugificato}`, es:
- "Ristorante Da Mario" → `webseed-ristorante-da-mario.vercel.app`

**Status risultante:** `deployed` (passa per `preview_deployed` → `tested` → `deployed`)

Se il smoke test fallisce, il business resta a `error_test` e non viene promosso.

---

### Step 4: `email` — Crea bozze email in Gmail

```bash
python pipeline.py email
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

**Come inviare:** apri Gmail → cerca la label `webseed-queue` → rivedi ogni bozza → aggiungi destinatario → invia.

**Status risultante:** `email_queued`

**Costo:** ~$0.03 per email

---

## Comandi di Gestione

### `status` — Vedi lo stato di tutti i business

```bash
# Tutti i business
python pipeline.py status

# Solo quelli deployati
python pipeline.py status --filter deployed

# Solo gli errori
python pipeline.py status --filter error
```

Mostra una tabella con: nome, status, URL Vercel, data ultimo aggiornamento.

Il filtro funziona per prefisso: `--filter error` mostra `error_generate`, `error_deploy`, `error_test`, ecc.

---

### `show` — Dettaglio completo di un business

```bash
python pipeline.py show ChIJxxxxxxxxxxxxxxx
```

Mostra tutti i campi del business: nome, indirizzo, telefono, rating, status, URL, screenshot, date, ecc.

Il `place_id` lo trovi nell'output di `status`.

---

### `stats` — Statistiche riassuntive

```bash
python pipeline.py stats
```

Mostra:
- Totale business nel database
- Conteggio per ogni status (quanti searched, generated, deployed, ecc.)
- Data dell'ultimo aggiornamento

---

### `blacklist-add` — Blocca business

```bash
# Uno o più place_id
python pipeline.py blacklist-add ChIJxxxxx ChIJyyyyy
```

Il business viene:
- Aggiunto a `blacklist.txt` (file locale)
- Marcato come `opted_out` nel database
- Saltato automaticamente nelle ricerche future

Utile per business che hanno detto no, che non vuoi contattare, o che nel frattempo hanno un sito.

---

### `blacklist-remove` — Sblocca un business

```bash
python pipeline.py blacklist-remove ChIJxxxxx
```

Rimuove il place_id da `blacklist.txt`. Se vuoi anche resettarne lo status nel DB, usa `reset` dopo.

---

### `blacklist-list` — Mostra la blacklist completa

```bash
python pipeline.py blacklist-list
```

Mostra tutti i place_id bloccati (unione di `blacklist.txt` + status `opted_out` nel database).

---

### `reset` — Resetta lo status di un business

```bash
# Resetta a "searched" per rigenerare il sito
python pipeline.py reset ChIJxxxxx --to searched

# Resetta a "generated" per ri-deployare
python pipeline.py reset ChIJxxxxx --to generated

# Resetta a "deployed" per ricreare l'email
python pipeline.py reset ChIJxxxxx --to deployed
```

Utile quando:
- Un business era in errore e vuoi riprovare
- Vuoi rigenerare il sito con un prompt aggiornato
- Vuoi rifare il deploy

---

### `export-csv` — Esporta in CSV

```bash
python pipeline.py export-csv --output results.csv
```

Esporta l'intero database in formato CSV. Utile per analisi in Excel/Google Sheets o per condividere i dati.

---

## Flag Globali

Questi flag si applicano a **tutti** i comandi:

```bash
# Database diverso (default: webseed.json)
python pipeline.py --db altro.json search --location "Roma" --query "bar"

# Directory output diversa (default: results/)
python pipeline.py --results-dir output/ generate
```

---

## Workflow Tipico

```bash
# 1. Cerca ristoranti a Milano
python pipeline.py search --location "Milano, Italy" --query "ristorante" --limit 10

# 2. Controlla cosa ha trovato
python pipeline.py status
python pipeline.py stats

# 3. Genera i siti
python pipeline.py generate

# 4. Deploya (preview → test → prod)
python pipeline.py deploy

# 5. Controlla i risultati
python pipeline.py status --filter deployed

# 6. Crea le email
python pipeline.py email

# 7. Vai su Gmail, cerca label "webseed-queue", rivedi e invia

# 8. Esporta tutto in CSV se serve
python pipeline.py export-csv
```

---

## Gestione Errori

Se un business fallisce durante uno step, viene marcato con lo status corrispondente (es. `error_generate`, `error_deploy`). Gli altri business continuano normalmente.

Per ritentare:

```bash
# Vedi quali sono in errore
python pipeline.py status --filter error

# Guarda il dettaglio dell'errore
python pipeline.py show ChIJxxxxx

# Resetta e riprova
python pipeline.py reset ChIJxxxxx --to searched
python pipeline.py generate
```

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

## Status di un Business

Un business attraversa questi stati durante la pipeline:

```
searched → generated → preview_deployed → tested → deployed → email_queued → emailed
```

Stati di errore: `error_search`, `error_generate`, `error_deploy`, `error_test`, `error_email`

Stato speciale: `opted_out` (blacklistato)

Puoi resettare qualsiasi business a uno stato precedente con `reset` per riprocessarlo.
