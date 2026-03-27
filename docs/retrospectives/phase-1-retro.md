# PHASE 1 retro

## User prompt

Abbiamo completato l'handoff di phase 1 e stiamo facendo retrospettiva. Implementa aggiornando claude.md, specifiche, log, agenti e backlog. Considera inoltre che l'mvp definition e' stata aggiornata dall'utente.

Questi sono i feedback che sono usciti dalla retrospettiva:

* Utente: richiede esplicitamente una costruzione leggibile e versionabile del backlog, non solo i progress
* Utente: espone come il gate handoff a phase 1 sia stato pieno di errori e servizi che non vengono neanche su e non comunicano, richiede esplicitamente che ci sia più human in the loop e che il workflow di verifica e test sia rafforzato anche a livello di agenti
* Utente: richiede che venga assegnato al team un agente specializzato in scrittura della documentazione con due compiti: scrivere la documentazione per umani e la documentazione per interazione tra agenti al passaggio di consegna di una us
* Utente: richiede esplicitamente che le fasi siano piu' atomiche e controllabili per human in the loop
* Utente: richiede esplicitamente la revisione del mvp spec e aggiornamento del plan e creazione del backlog
* Agenti: richiedono esplicitamente che quando evidenziano del blocker, rischi o implementazioni parziali sul plan queste vengano riportate e verificate da te con piu' impegno e prontezza
* Agenti: richiedono esplicitamente di ricevere nei loro file di configurazione md su quali file devono lavorare per non spendere inutilmente token di ricerca
* Agenti: richiedono esplicitamente di avere un mcp server accessibile come <https://context7.com/> per documentazione e che sia un informazione integrata nelle loro definizioni

Pianifica le azioni necessarie per implementare i feedback della retrospettiva

## Claude Plan

Context
Phase 1 completata ma il gate handoff ha evidenziato problemi critici: servizi che non si avviano, comunicazione inter-servizi fallita, mancanza di verifiche intermedie, blocker degli agenti non gestiti con prontezza. La retrospettiva ha prodotto 8 categorie di feedback da implementare prima di avviare Phase 2.
MVP spec update confermato: provider AI limitati a Ollama (demo mode, dentro container) e Claude API (demo-api mode con API key). GitHub Copilot e altri provider mockati/roadmap.

Azioni da implementare
Azione 1 — Backlog strutturato e versionabile
Problema: I progress file in docs/progress/ sono documenti post-factum, non un backlog navigabile. Non c'è visibilità sulle US future.
Soluzione:

Creare docs/backlog/ con un file per ogni US (US-NNN.md) nel formato standard CLAUDE.md
Creare docs/backlog/BACKLOG.md come indice master con stato, owner, fase, dipendenze per ogni US
Le US completate in Phase 1 vengono archiviate come US-NNN.md con stato ✅ Done e link al progress file
Le US di Phase 2-4 vengono create in anticipo come file individuali

File coinvolti:

docs/backlog/BACKLOG.md (nuovo — indice)
docs/backlog/US-001.md … US-007.md (Phase 1, done)
docs/backlog/US-010.md … US-019.md (Phase 2, backlog)
docs/backlog/US-020.md … US-029.md (Phase 3, backlog)
docs/backlog/US-030.md … US-035.md (Phase 4, backlog)

Azione 2 — Nuovo agente: DocWriter
Problema: Nessun agente è responsabile della documentazione. I passaggi di consegna tra agenti mancano di struttura. I documenti per umani (handoff, test manuale, architettura) non vengono aggiornati sistematicamente.
Soluzione: Creare .claude/agents/doc-writer.md con due modalità:

Modalità Handoff: dopo ogni US completata, produce docs/handoffs/US-NNN-handoff.md — riepilogo tecnico per il prossimo agente che toccherà quei file (what was built, residual risks, file ownership, integration points)
Modalità Human Docs: dopo ogni phase gate, produce documentazione leggibile in docs/architecture/, docs/testing/, docs/runbooks/

Routing rule da aggiungere in CLAUDE.md:
| Documentazione handoff US, runbook, architettura | DocWriter |
Trigger obbligatori (da aggiungere in CLAUDE.md Phase 3 — Integration & Review):

Dopo ogni US completata → spawna DocWriter in modalità Handoff
Dopo ogni phase gate approvato → spawna DocWriter in modalità Human Docs

File coinvolti:

.claude/agents/doc-writer.md (nuovo)
docs/handoffs/ (nuova dir)
docs/architecture/ (nuova dir)
docs/runbooks/ (nuova dir)

Azione 3 — Aggiornare CLAUDE.md: più human-in-the-loop e fasi atomiche
Problema: Phase Gate troppo coarse-grained. Errori scoperti solo a fine fase. Nessun checkpoint intermedio obbligatorio. Protocollo di escalation agenti vago.
Modifiche a CLAUDE.md:
A) Aggiungere checkpoint intra-fase (dopo ogni US, non solo al gate):

### Checkpoint per ogni US completata

1. Leggere output dell'agente contro acceptance criteria
2. Eseguire smoke test esplicito (comandi da eseguire: make up, curl health check)
3. Verificare comunicazione inter-servizio se la US tocca networking
4. Spawna DocWriter per handoff doc
5. Aggiornare status in docs/backlog/US-NNN.md
6. **STOP — mostra risultato smoke test all'utente, attendi conferma prima di procedere**
B) Rafforzare Phase Gate con verifica servizi esplicita:

### Verifica obbligatoria al Phase Gate

1. make down && make up (clean restart)
2. make migrate (verifica migrazione)
3. curl <http://localhost:8000/health> → 200
4. curl <http://localhost:8080> → Plone risponde
5. curl <http://localhost:3000> → Volto risponde
6. curl <http://localhost:6333/health> → Qdrant risponde
7. Test suite completa: make test → tutti green
8. Verifica log per errori di startup: make logs
9. **Solo se tutti i check passano → presentare summary all'utente**
C) Aggiornare Escalation Protocol per agenti:
Quando un agente segnala un blocker o implementazione parziale:
10. Il blocker viene registrato in docs/backlog/US-NNN.md sezione "Blockers"
11. Tech Lead analizza impatto (può bloccare US dipendenti?)
12. Se impatto critico → STOP, presenta al'utente PRIMA di procedere
13. Se impatto contenuto → documenta come residual risk, flagga esplicitamente
14. NON marcare una US come done se ha blockers non risolti critici
15. NON delegare US dipendenti finché i blockers upstream non sono risolti
D) Fasi più atomiche: Dividere Phase 2 in sub-fasi con gate intermedi (vedi Azione 4).
File coinvolti: CLAUDE.md

Azione 4 — Aggiornare .claude/workflow.md: sub-fasi e verifiche
Problema: Phase 2 ha 10 US troppo eterogenee. Non ci sono verification steps per servizi.
Modifiche:
Dividere Phase 2 in 4 sub-fasi, ciascuna con mini-gate:
Phase 2a — Plugin System (US-010, US-011)
  Gate 2a: Plugin caricabile, manifest validato, isolation funzionante

Phase 2b — Model Layer (US-012, US-013)
  Gate 2b: Ollama query funzionante in container, Claude mock funzionante

Phase 2c — MCP + RAG (US-014, US-015, US-016)
  Gate 2c: RAG query ritorna risultati, MCP trust scoring funzionante

Phase 2d — Quota + Planner (US-017, US-018, US-019)
  Gate 2d: Rate limiting funzionante, quota tracking in DB, planner seleziona modello

Phase Gate 2 completo → tutte le sub-fasi done
Ogni sub-gate richiede approvazione esplicita utente prima di procedere alla sub-fase successiva.
File coinvolti: .claude/workflow.md

Azione 5 — Aggiornare tutti i file agenti con file domain espliciti
Problema: Gli agenti spendono token cercando file rilevanti. Nessun file agente specifica i path esatti.
Aggiungere a ogni file agente una sezione "File Domain" con path esatti autorizzati:
AgentePath autorizzatibackend-devbackend/app/api/, backend/app/db/, backend/app/quota/, backend/app/plugins/, backend/app/config.py, backend/app/main.py, backend/alembic/security-engineerbackend/app/auth/, backend/app/rbac/, backend/app/audit/, backend/app/api/v1/auth.pyaiml-engineerai/, backend/app/core/, plugins/frontend-devfrontend/ (da creare in Phase 3)dev-opsinfra/, Makefile, .env.example, .github/qa-engineerbackend/tests/, e2e/ (da creare in Phase 3)doc-writerdocs/ (escluso mvp-spec.md e plan.md, solo lettura)
File coinvolti: tutti i file in .claude/agents/

Azione 6 — Aggiungere context7 MCP ai file agenti (opzionale)
Problema: Gli agenti non hanno accesso a documentazione aggiornata delle librerie (FastAPI, LlamaIndex, SQLAlchemy, Volto, ecc.).
Soluzione: Aggiungere a ogni file agente una sezione "MCP Disponibili" con context7 se configurato dall'utente. Se non disponibile, gli agenti useranno la propria conoscenza interna.
Come configurare context7 (l'utente deve farlo una volta):
Context7 è un MCP server che fornisce documentazione aggiornata di librerie. Per abilitarlo in Claude Code:
Opzione A — Globale (consigliata): esegui nel terminale:
bashclaude mcp add context7 -- npx -y @upstash/context7-mcp@latest
Questo aggiunge context7 a ~/.claude/mcp.json per tutti i progetti.
Opzione B — Solo questo progetto: crea/modifica .claude/mcp.json:
json{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
Richiede Node.js installato. Il package @upstash/context7-mcp viene scaricato automaticamente al primo uso.
Sezione da aggiungere ai file agente (condizionale):
markdown## MCP Disponibili

### context7 (documentazione librerie — se configurato)

Se il MCP context7 è disponibile, usalo per recuperare documentazione aggiornata.
Se non disponibile, procedi con la conoscenza interna.
Librerie rilevanti per questo agente: [specifica per agente]

```

**Se l'utente non vuole configurarlo**: la sezione negli agent file dirà semplicemente di usare la conoscenza interna. context7 è un'ottimizzazione, non un requisito.

**File coinvolti**: tutti i file in `.claude/agents/`, opzionalmente `.claude/mcp.json`

---

### Azione 7 — Aggiornare `docs/mvp-spec.md`

**Modifiche necessarie**:

1. **Sezione 8 — Model Layer**: chiarire che per l'MVP i provider sono:
   - Ollama (demo mode, modello locale nel container, nessuna API key richiesta)
   - Claude via Anthropic API (demo-api mode, richiede `ANTHROPIC_API_KEY`)
   - GitHub Copilot e altri: mockati, non implementati nell'MVP

2. **Sezione 16 — Docker & Kubernetes**: separare MVP (Docker Compose) da roadmap (K8s). L'MVP usa solo Docker Compose. I manifest K8s sono placeholders per il futuro.

3. **Aggiungere Sezione 21 — Configurazione Ambiente**: documentare le due modalità operative:
   - `demo`: Ollama locale, nessuna API key, funziona out-of-the-box
   - `demo-api`: Claude API, richiede `ANTHROPIC_API_KEY` nel `.env`

**File coinvolti**: `docs/mvp-spec.md`

---

### Azione 8 — Aggiornare `docs/plan.md`

**Modifiche**:

1. Aggiornare Phase 1 status con nota sui residual risks non risolti
2. Aggiungere Phase 2 planning dettagliato con le 4 sub-fasi
3. Aggiungere sezione "Residual Risks da Phase 1" con resolution owner
4. Aggiornare dependency graph con sub-fasi

**File coinvolti**: `docs/plan.md`

---

## Ordine di esecuzione

Le azioni sono **indipendenti** e possono essere eseguite in parallelo dove possibile:
```

[Parallel] Azione 1 (backlog) + Azione 2 (doc-writer agent) + Azione 7 (mvp-spec) + Azione 8 (plan.md)
[Parallel] Azione 3 (CLAUDE.md) + Azione 4 (workflow.md)
[Series]   Azione 5 + Azione 6 (agent files — tutte e 6 le file)
Nota: Tutte le azioni producono modifiche a file di configurazione e documentazione, non a codice. Non richiedono agent delegation — sono modifiche dirette ai file di governance del progetto.

Verifica post-implementazione

CLAUDE.md contiene: DocWriter routing, checkpoint intra-fase, phase gate rafforzato, escalation protocol aggiornato
.claude/workflow.md contiene: Phase 2 divisa in 4 sub-fasi con mini-gate
Tutti i file in .claude/agents/ contengono: sezione "File Domain" + sezione "MCP Disponibili"
docs/backlog/BACKLOG.md esiste e lista tutte le US (Phase 1-4) con stato
docs/backlog/US-NNN.md esiste per ogni US
.claude/agents/doc-writer.md esiste e definisce le due modalità operative
docs/mvp-spec.md riflette il provider scope corretto (Ollama + Claude)
docs/plan.md ha Phase 2 sub-fasi e residual risks di Phase 1

Note critiche

Non modificare docs/progress/ — quei file sono l'audit trail della Phase 1 as-is
Non creare codice — tutte le azioni sono su file di governance e documentazione
docs/backlog/US-NNN.md per Phase 2-4 sono placeholder: titolo, agente, dipendenze, priorità. L'acceptance criteria dettagliata verrà scritta durante il Phase 1 planning di ogni sub-fase
Il context7 MCP deve essere verificato come disponibile nell'ambiente prima di essere referenziato negli agent files
