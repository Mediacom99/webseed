# 🌱 webseed

Pipeline CLI che trova business locali italiani senza sito web su Google Maps, genera automaticamente un sito HTML professionale con Claude AI, lo deploya su Vercel, e salva tutto in un CSV pronto per outreach commerciale.

## Prerequisites

- Python 3.9+
- [Vercel CLI](https://vercel.com/docs/cli) installata globalmente (`npm i -g vercel`)
- API keys:
  - [Google Maps Platform](https://console.cloud.google.com/) — Places API abilitata
  - [Anthropic](https://console.anthropic.com/) — Claude API
  - [Vercel](https://vercel.com/account/tokens) — deploy token

## Setup

```bash
git clone https://github.com/Mediacom99/webseed.git && cd webseed
pip install -r requirements.txt
cp .env.example .env   # poi compila con le tue API keys
```

Per lo smoke test opzionale (flag `--test`):
```bash
playwright install chromium
```

## Usage

```bash
# Cerca 5 ristoranti a Garbagnate Milanese senza sito web
python pipeline.py --location "Garbagnate Milanese, Italy" --query "ristorante" --limit 5

# Cerca 10 parrucchieri a Milano con smoke test
python pipeline.py --location "Milano, Italy" --query "parrucchiere" --limit 10 --test
```

### Opzioni

| Flag | Default | Descrizione |
|------|---------|-------------|
| `--location` | (obbligatorio) | Città/zona da cercare |
| `--query` | (obbligatorio) | Tipo di business |
| `--limit` | 10 | Max business da processare |
| `--output` | `results.csv` | Path del CSV di output |
| `--results-dir` | `results/` | Directory per siti generati |
| `--test` | off | Esegui smoke test Playwright dopo deploy |

## Output

**`results.csv`** — una riga per business con: nome, indirizzo, telefono, rating, recensioni, categoria, URL Vercel, URL Maps, timestamp deploy.

**`results/`** — una cartella per business contenente `index.html`, `vercel.json`, e `img/` con le foto scaricate da Maps.

## Costi

Il generatore usa `claude-opus-4-5` — circa $0.07 per sito generato.
