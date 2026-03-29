# Retrospective — ESP32 MicroPython Dev Station

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-29
**Phases:** 3 | **Plans:** 11

### What Was Built
- MCP server with 11 tools running as systemd daemon on Raspberry Pi
- USB board detection and firmware flashing for 5 ESP32 chip variants
- File/directory deployment with space checks and integrity verification
- REPL command execution and serial output capture
- WiFi OTA deployment via WebREPL with USB fallback
- GitHub clone-and-deploy in a single tool call

### What Worked
- Parallel executor agents completed waves significantly faster than sequential
- Wave-based plan grouping (prerequisites → implementation → integration) kept dependencies clean
- Error-dict-not-exceptions pattern gave Claude consistent structured responses
- Subprocess isolation (esptool, mpremote, git, webrepl_cli) avoided import conflicts and gave clean error boundaries
- Human UAT with real hardware caught soft reset issue that automated checks missed

### What Was Inefficient
- Worktree merges required manual conflict resolution when parallel agents touched STATE.md/ROADMAP.md
- One agent (03-03) failed to find plan files in its worktree on first attempt — retried successfully
- Pi deployment setup (missing deps, PATH issues, service restarts) consumed significant UAT time
- No automated way to deploy code updates to the Pi — manual git pull + restart each time

### Patterns Established
- All tool functions return dicts, never raise exceptions
- MCP wrappers apply SerialLock, implementation modules stay lock-free
- WiFi tools skip SerialLock (no serial port involved)
- Post-deploy auto-reset (soft_reset) for immediate code execution
- Vendored dependencies (webrepl_cli.py) for tools with no pip package

### Key Lessons
- Always include venv PATH in systemd service Environment — subprocess tools need it
- esptool auto-detect is unreliable; enforce explicit --chip flag
- Soft reset via mpremote doesn't always restart user code on ESP32 classic
- Test files on development machine need full filesystem isolation mocks (read-only home issue)
- WiFi credentials should never pass through Claude conversations

## Cross-Milestone Trends

| Metric | v1.0 |
|--------|------|
| Phases | 3 |
| Plans | 11 |
| Requirements | 24 |
| LOC (Python) | 2,446 |
| Timeline (days) | 2 |
| Tech debt items | 5 |
| UAT issues | 0 |
