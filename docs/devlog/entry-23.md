← [Back to DEVLOG](../DEVLOG.md)

## Entry 23 — The Daemon, the Bridge, and the Persistence of Memory

**Date:** 2026-04-08 · **Plan:** `integrate-codebase-memory.md`

### The symptom and the UI that wasn't there

The goal for this session was straightforward: add `codebase-memory-mcp` (CBM) to the project stack to give sub-agents cross-session, persistent architectural context. The initial implementation compiled the CBM binary from source and wrapped it in an ephemeral `docker run --rm -i` script invoked by Claude Code via `stdio`.

The symptom was invisible: we assumed CBM was strictly a headless backend tool. It isn't. The official repository documents a 3D interactive graph UI that runs alongside the MCP server. We couldn't see it because our architectural assumptions were blinding us. Because the wrapper script used `--rm`, Docker was spinning up a temporary container, serving the AI's standard input, and instantly annihilating the container (and the UI thread with it) the second the agent finished its task. Furthermore, we had completely omitted port mapping (`-p 9749:9749`).

The UI wasn't missing; we were assassinating it on every cycle.

### The `glibc` ghost and the stubborn loopback

Attempting to fix this by downloading the pre-built UI variant exposed a classic containerization fragility: the `glibc` mismatch. Our Stage 2 runtime was Debian `bookworm-slim` (`glibc 2.36`), but the pre-built binary expected `glibc 2.38`. The fix was a baseline OS upgrade to `ubuntu:24.04`.

With the OS updated and the port mapped, the browser returned `ERR_EMPTY_RESPONSE`. Docker was routing the host's traffic into the container's external interface (`0.0.0.0`), but the CBM binary was stubbornly hardcoded to bind strictly to `127.0.0.1` (the container's internal loopback). It ignored `--host` flags entirely.

The solution was mechanical rather than programmatic: injecting a `socat` bridge into the container's entrypoint. `socat` now listens on `9750` (`0.0.0.0`), catches the Docker-routed traffic, and instantly forwards it to the CBM thread hiding on `127.0.0.1:9749`. The UI appeared immediately.

### The architectural pivot: Daemonizing the cache

Fixing the UI created a new contradiction. If the UI only lives while the container lives, and the container only lives while Claude Code is actively querying `stdio`, the UI is functionally useless to a human developer.

The architecture had to invert. CBM was moved out of the ephemeral wrapper script and into the `docker-compose.ai-tools.yml` stack alongside Serena. Using `stdin_open: true` and `tty: true`, we forced the container to run 24/7 as a background daemon, serving the UI persistently.

To connect Claude Code to this daemon without breaking the required `stdio` transport, the wrapper script (`cbm-mcp.sh`) was rewritten to use `docker exec -i codebase-memory-mcp codebase-memory-mcp`.

This is a massive operational win. Instead of Docker building and booting an entire container from scratch every time an `aiml-engineer` sub-agent wakes up, it now spawns a microscopic, headless worker thread *inside* the existing daemon. It shares the SQLite cache concurrently with the UI. Spin-up latency dropped to zero.

### Consolidating the fragmented registry

As the stack grew, configuration fragmented. Context7 and Serena lived in a root `.mcp.json` file, while CBM was duct-taped into `.claude/settings.json`. When running `claude mcp list`, the CLI exposed another ghost: it was reading a stale, global Homebrew installation of Serena, ignoring the local Docker endpoints entirely.

We learned the hard boundaries of Claude Code's config system:

1. `.claude/settings.json` is strictly for hooks, commands, permissions, and declaring *which* servers to enable. It ignores MCP server routing definitions.
2. `.mcp.json` is the sole canonical source of truth for project-scoped MCP routing.

All servers were moved to `.mcp.json`. The CLI's global registry was purged. The environment is now completely self-contained.

> We will retest serena vs cmp again in next session.
