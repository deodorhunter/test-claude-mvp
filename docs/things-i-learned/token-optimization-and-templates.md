# 🚀 Enterprise AI Workflow: Da Copilot a Claude Code

## 1. Il Problema: "Agentic Bloat"

Passare da un assistente passivo (come Copilot) a un agente autonomo (come Claude Code) richiede un cambio di paradigma. Se usiamo Claude Code come un semplice chatbot chiedendogli di "sistemare un bug" senza fornirgli contesto, l'agente avvierà un loop di **esplorazione autonoma**.
Userà comandi bash (`ls`, `find`, `cat`) per esplorare il progetto, consumando decine di migliaia di token a ogni interazione *prima* ancora di scrivere una riga di codice. Questo fa esplodere i costi (fino a $2-3 per un task banale) e causa allucinazioni.

## 2. La Soluzione: Il Compilatore Deterministico

Per scalare l'uso dell'AI su decine di progetti aziendali rispettando i costi e le normative (EU AI Act), passiamo da un approccio "Pull" (l'AI cerca i dati) a un approccio "Push" (noi iniettiamo i dati). Abbiamo definito **6 Pilastri Architetturali**:

1. **Push Context:** Gli agenti hanno il divieto di esplorare il file system. I file da modificare vanno passati esplicitamente (o tramite interfaccia o via terminale).
2. **Tool Muzzling:** Tutti i comandi eseguiti dall'AI (`pytest`, `pip`, `npm`) devono essere silenziati (`-q`, `> /dev/null`) per non inquinare la context window con log inutili.
3. **Circuit Breakers:** Massimo 2 tentativi di debug autonomo per i test falliti. Se fallisce due volte, l'AI si ferma e chiede l'intervento umano. Evitiamo i loop infiniti.
4. **Targeted Editing:** Nessuna riscrittura completa di file lunghi. L'AI deve usare tool di edit mirato o `sed`/`awk`.
5. **Git Diff Reviews:** Chi fa Code Review o Documentazione (QA, DocWriter) non legge il codice sorgente, ma solo l'output di `git diff`.
6. **Dual-Speed Workflow & Dynamic Routing:** - **Speed 1 (Copilot Mode):** Per bugfix veloci. Usa modelli economici (`Haiku`), non usa agenti complessi.
   - **Speed 2 (Orchestration Mode):** Per feature intere. Usa l'agente "Tech Lead" (`Sonnet`) che delega a sub-agenti specializzati.

## 3. Il "Context Repository Pattern" e i Commands

Invece di programmare tool custom o mantenere prompt giganti, usiamo file Markdown come **Macro (Commands)** e una singola fonte di verità per il progetto (**AI Reference**).

- `docs/AI_REFERENCE.md`: Viene generato *una sola volta* all'inizio del progetto. Contiene lo stack, la struttura delle cartelle e i comandi di test. Gli agenti leggeranno sempre e solo questo file per orientarsi.
- `.claude/commands/*.md`: Procedure operative standard scritte in inglese. Invece di inventare prompt, i dev scrivono: `claude "Esegui @.claude/commands/handoff.md"`.

---

## 📁 I TEMPLATE AZIENDALI (Da copiare nella root di ogni progetto)

### A. Il Guardrail Universale (`CLAUDE.md`)

*Da posizionare nella root del repository.*

```markdown
# 🤖 AI Development Framework - Universal Guardrails

## 🛑 PART 1: GLOBAL TOKEN OPTIMIZATION RULES (MANDATORY)
1. **NO AUTONOMOUS EXPLORATION:** Do not use `ls`, `find`, or `tree`. Rely STRICTLY on files injected via `<file>` tags or attached by the user. 
2. **SILENCE VERBOSE OUTPUTS:** Suppress bash noise (`pip install -q > /dev/null`, `pytest -q --tb=short`). NEVER pipe full logs into your context.
3. **TARGETED EDITING:** Do not rewrite entire files. Use native Edit tools or `sed`/`awk`.
4. **CIRCUIT BREAKER:** Max 2 debug attempts per failing test/command. If it fails twice, STOP and ask the human.

## 🧠 PART 2: PROJECT KNOWLEDGE
NEVER guess the project stack. Always refer to `docs/AI_REFERENCE.md` for architecture, directory map, and test commands. If missing, tell the user to run the `init-ai-reference` command.

## ⚙️ PART 3: OPERATING MODES (Dual-Speed)
**Speed 1: Copilot Mode (Maintenance & Quick Fixes)**
*Trigger: User attaches a specific file and asks for a bugfix.*
- Act as a Senior Dev. Answer directly, apply the fix. Respect Global Token Rules. Model: `claude-3-5-haiku` (or `claude-3-7-sonnet` if complex).

**Speed 2: Orchestration Mode (Tech Lead)**
*Trigger: User asks to "execute a Phase" or "break down requirements".*
- Act as Orchestrator. Do NOT write code directly. Break work into User Stories (US) and delegate to `.claude/agents/`.
- **Context Injection:** `cat` required files and inject as `<file>[content]</file>` before spawning agents.
- **Git Diff:** Inject `<git_diff>` for DocWriter/QA instead of raw files.
- **State Compression:** Inject `<metrics>` XML. DocWriter appends summaries to `docs/ARCHITECTURE_STATE.md`.
