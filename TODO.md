# TODO

## Blockers / Bug fix

- [ ] Fix Playwright visual test timeout — il comando `claude --print` va in timeout dopo 180s durante il visual test con Playwright MCP
- [ ] Fix Unsplash fallback — `source.unsplash.com` is deprecated/dead. Either switch to Unsplash API, use a different stock photo source, or remove fallback entirely
- [x] Gestione CTRL-C (KeyboardInterrupt) — intercettare il segnale per fermarsi in modo pulito, salvare lo stato corrente del business nel DB (evitare stati transitori/inconsistenti), e uscire con messaggio chiaro

## Qualità pipeline

- [ ] Review completa logging e dati salvati a DB — cosa logghiamo, cosa salviamo per business, campi ridondanti o mancanti
- [ ] Review completa configurazione — check CLI tools (claude, vercel, playwright), env vars, working directory setup, error messages chiari se manca qualcosa
- [ ] Gestione avanzata Claude Code CLI — esporre flag configurabili (modello, timeout, max tokens, system prompt override, allowedTools, etc.) tramite CLI args o config. Verificare tutte le opzioni disponibili di `claude --print` e decidere quali esporre
- [ ] Validate location in `search` — Google Maps treats nonsense locations as keyword searches (e.g. "Punto Nemo, Pacific Ocean" returns Italian restaurants). Consider geocoding the location first and warning if it doesn't resolve
- [ ] Add `--max-places` flag to `search` — limit how many Maps results are checked before stopping (currently pages through all ~60 results even if `--limit` is already met early)

## Qualità output

- [ ] Migliorare prompt generazione sito — più specifico su qualità output, gestione edge case (no foto, no telefono), stile per categoria, struttura HTML semantica
- [ ] Migliorare prompt testing (code review + visual test) — checklist più completa, criteri più precisi, ridurre falsi positivi/negativi
- [ ] Riscrivere prompt generazione frontend — passare da HTML statico a Vue.js SPA con DaisyUI components. Requisiti: responsive e fluido su ogni device, PageSpeed Insights score minimo 95 su tutte le metriche (performance, accessibility, best practices, SEO) sia desktop che mobile
- [ ] Integrare PageSpeed Insights API nel pipeline — dopo il deploy, analizzare automaticamente performance/accessibility/best practices/SEO del sito. Usare i risultati per feedback al ciclo di fix o come gate di qualità prima di procedere all'email

## Business / Growth

- [ ] Recupero email business — Google Maps API non fornisce email. Esplorare alternative: scraping pagina Maps per link social/email, integrazione con API di business data (Hunter.io, Apollo, ecc.), o step manuale con comando `webseed set-email PLACE_ID email@example.com` per pre-popolare il campo "To" nei draft Gmail
- [ ] Email: personalizzare il tono come Edoardo Bertoli — freelance software engineer & digital nomad, non un bot. Includere link al sito personale, profilo LinkedIn, ecc. Far percepire che c'è una persona reale dietro, non un servizio automatizzato
- [ ] Email: aggiungere clausola di scadenza — dopo X giorni senza risposta il sito viene rimosso automaticamente. Aggiungere opt-out facile ("rispondi a questa email per rimuovere il sito"). Verificare aspetto legale: chiarire che i dati usati sono pubblicamente accessibili da Google Maps
- [ ] Sconto lancio primi 10 clienti — sito a €199 invece di €299, aggiornare prompt email con offerta limitata e urgency ("solo per i primi 10 clienti")
- [x] Comando `close` — blacklista un cliente, rimuove il deploy da Vercel (`vercel rm`), ma mantiene il sito in locale
- [ ] Gestione dominio personalizzato — definire offerta per passaggio a dominio proprio del cliente (costo dominio, configurazione DNS, hosting). Oppure lasciare su Vercel come opzione base. Chiarire pricing e flow nel prompt email
- [ ] Migliorare ranking risultati ricerca — ordinare business per "probabilità di conversione": più foto disponibili, rating alto, molte recensioni, categoria commerciale (ristoranti > associazioni). Prioritizzare business con più dati per generare siti migliori
- [ ] Tracking limiti Vercel — monitorare e avvisare sui limiti del piano free (numero progetti, bandwidth, build minutes, ecc.) prima di ogni deploy per evitare addebiti inattesi. Considerare comando `webseed limits` o check automatico pre-deploy
- [ ] Use Google Places API Place photos and Place Details to get as many info as possible