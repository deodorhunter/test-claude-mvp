# 📘 Enterprise AI Workflow Playbook

Benvenuto. Qui usiamo l'AI come un **Compiler Deterministico**, non come un chatbot generico.

## 1. Inizializzazione (Una Tantum)
Dovrebbe esistere un file di reference per l'ai, per ridurre all'osso la token consumption.
Se non esiste, per istruire l'AI sul contesto di questo specifico progetto, esegui:
`claude "Esegui @.claude/commands/init-ai-reference.md"`

## 2. Speed 1: Bug fixing e task veloci

- **Sbagliato:** `claude "fixa il bug del login"` (Costo alto, esplorazione cieca).
- **Corretto:** `claude "Fixa il bug. Lavora solo su @backend/app/auth.py"` (Veloce, chirurgico).

## 3. Comandi Standard (Macro)

Usa le nostre procedure operative:

- `claude "Esegui @.claude/commands/handoff.md"` -> Crea la doc di fine task.
- `claude "Esegui @.claude/commands/compress-state.md"` -> Pulisce la memoria dell'AI se diventa lenta o confusa.
