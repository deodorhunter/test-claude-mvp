Context
Phase 1 è completata e approvata (Phase Gate 1 — 2026-03-26). Tutte le 7 US della fondazione sono Done. Si parte ora con Phase 2a del workflow definito in .claude/workflow.md, che copre il Plugin System (US-010 + US-011).
Obiettivo: rendere il sistema di plugin hot-pluggable, tenant-aware, e sicuro tramite isolamento in subprocess.

Pre-Flight Check (prima di delegare qualsiasi US)
Un rischio residuo HIGH dalla Phase 1 deve essere verificato manualmente prima di procedere:

Plone REST API compatibility — non ancora verificata con make up. Se Plone non risponde correttamente, US-010 (che usa plone_integration plugin) potrebbe avere problemi.

Azione richiesta: eseguire make up && curl -s <http://localhost:8080> e confermare che Plone risponde. Questo è un prerequisito bloccante solo se tocchiamo il plugin plone_integration nei test (US-011). US-010 può procedere anche senza, perché testa solo il manager in-memory.

Stato Corrente
USTitoloAgenteStatoUS-010Plugin ManagerBackend Dev📋 BacklogUS-011Plugin RuntimeSecurity Engineer📋 Backlog
Dipendenze risolte:

US-010 → US-005 (RBAC Middleware) ✅ Done
US-011 → US-010 (deve completarsi prima)

Sequenza di Esecuzione
US-010 (Backend Dev)
  → Smoke test US-010
  → User approval
  → DocWriter Mode A (US-010)
      ↓
US-011 (Security Engineer)
  → Smoke test US-011
  → User approval
  → DocWriter Mode A (US-011)
      ↓
Mini-Gate 2a (checklist completa)
  → User approval → Phase 2b
US-010 e US-011 devono girare in serie (US-011 dipende da manager.py creato da US-010).

US-010: Plugin Manager
Agente: Backend Dev (modello Haiku — task diretto, non richiede reasoning)
File coinvolti:

backend/app/plugins/manager.py (nuovo)
backend/app/plugins/__init__.py
backend/app/db/models/ (read-only — tenant_plugins già definito)
backend/app/api/v1/plugins.py (stub vuoto — non implementare endpoint)
backend/tests/test_plugin_manager.py (nuovo)
Plugin manifests: plugins/*/manifest.yaml (lettura)
docs/progress/US-010-done.md (output)

Cosa implementa:

PluginManager class con:

load_manifests() — carica tutti i manifest.yaml dalla dir plugins/, valida schema (id, version, capabilities, entrypoint)
get_active_plugins(tenant_id) → lista plugin abilitati per quel tenant (legge tenant_plugins in DB)
enable_plugin(tenant_id, plugin_name) → UPDATE tenant_plugins.enabled = True (immediato, no restart)
disable_plugin(tenant_id, plugin_name) → UPDATE tenant_plugins.enabled = False (immediato)
Manifest validation errors → eccezione esplicita con dettaglio del campo mancante
Isolation: get_active_plugins(tenant_A) non restituisce mai plugin di tenant_B

Smoke test US-010:
bashmake up
curl -s <http://localhost:8000/health>   # → 200
make test backend/tests/test_plugin_manager.py

US-011: Plugin Runtime
Agente: Security Engineer (modello Sonnet — richiede security reasoning)
Dipendenza: US-010 completato e approvato
File coinvolti:

backend/app/plugins/runtime.py (nuovo)
backend/app/plugins/manager.py (integrazione — read + modifica minima)
backend/tests/test_plugin_runtime.py (nuovo)
docs/progress/US-011-done.md (output)

Cosa implementa:

PluginRuntime class con:

execute(tenant_id, plugin_name, input_data: dict) → dict output
Subprocess isolation (non in-process): usa subprocess.Popen con JSON su stdin/stdout
Timeout 10s (SIGKILL se superato)
Resource limits: resource.setrlimit su CPU e memoria (gestisce RLIMIT_CPU non supportato con graceful warning)
Pool di subprocess per (tenant_id, plugin_name) max 2 workers
Network blocking: tutti i plugin eccetto plone_integration vengono avviati senza accesso di rete (usando capabilities Linux se disponibili, o documentato come best-effort su macOS)
JSON-only communication: stdin = json.dumps(input), stdout = json.loads(output)
Cross-tenant isolation: il subprocess non riceve tenant_id di altri tenant

Security notes richieste nel deliverable:

Rischi residui di isolamento (macOS vs Linux behavior)
Network blocking limitations senza cgroups
Piano di hardening per produzione

Smoke test US-011:
bashmake test backend/tests/test_plugin_runtime.py

# Verifica: cross-tenant isolation test passa

# Verifica: timeout test (plugin che dorme 15s viene killato entro 12s)

Mini-Gate 2a — Checklist Completa
Prima di presentare l'approvazione all'utente per procedere a Phase 2b:

 Plugin caricabile da manifest YAML (test dimostrabile)
 enable_plugin / disable_plugin aggiornano DB senza restart
 get_active_plugins(tenant_A) non restituisce plugin di tenant_B
 Subprocess isolation verificata (test cross-tenant passa)
 Timeout 10s enforcement testato (plugin lento viene killato)
 Tutti i test verdi: make test
 curl <http://localhost:8000/health> → 200

Regole di Delegation

Ogni agente riceve solo il suo file US e i suoi file di contesto agente
Mai passare il full spec — solo le sezioni rilevanti
US-010 → Backend Dev agent file + contenuto US-010.md + sezione plugin spec
US-011 → Security Engineer agent file + contenuto US-011.md + ADR-002 (Plugin Isolation)

Verifica End-to-End
Dopo il mini-gate 2a approvato dall'utente:

make test → tutto verde
curl <http://localhost:8000/health> → 200
Nessun errore critico in make logs
DocWriter Mode B non richiesto qui (solo al Phase Gate 2 completo)
Presentare summary mini-gate + aprire discussione Phase 2b
