# Phase 2: Core USB Workflows - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Deploy files to ESP32 boards via USB serial, execute REPL commands and capture output, reset boards (soft + hard), and add USB access serialization + structured error handling to all operations.

No WiFi, no OTA, no GitHub integration — those are Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Tooling
- **D-01:** Use `mpremote` for file deployment and REPL interaction — already a dependency (v1.23+), handles MicroPython filesystem correctly
- **D-02:** Follow Phase 1 error-dict pattern: return `{"error": "code", "detail": "..."}` — never raise exceptions to callers

### Deployment
- **D-03:** Deploy excludes: `__pycache__/`, `*.pyc`, `.git/`, `tests/`, `.planning/` — deploy only `.py` files and non-Python resources (`.json`, `.txt`, etc.) from project root
- **D-04:** Silent overwrite — files on the board are replaced without prompting; return a list of files written in the success dict
- **D-05:** Space check threshold: warn at 70% full, hard-fail at 90% full (DEPLOY-03: "60-70% safe capacity")
- **D-06:** Verify file integrity after transfer via size comparison (DEPLOY-04)

### REPL
- **D-07:** Single-command execution model — one Python expression or statement per call; no interactive session management
- **D-08:** REPL timeout: configurable, default 10 seconds (REPL-03)

### Serialization & Errors
- **D-09:** Per-port file lock (`~/.esp32-station/locks/<port_slug>.lock`) — serializes concurrent access per device, not globally (MCP-04)
- **D-10:** All errors include `code` (snake_case string) and `detail` (human-readable) fields (MCP-05)

### Claude's Discretion
- Lock timeout value, exact mpremote command flags, reset implementation (mpremote vs raw serial)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 Artifacts
- `.planning/phases/01-foundation-infrastructure/01-02-SUMMARY.md` — board detection patterns, error dict shape
- `.planning/phases/01-foundation-infrastructure/01-03-SUMMARY.md` — firmware flash patterns, subprocess usage
- `.planning/phases/01-foundation-infrastructure/01-04-SUMMARY.md` — MCP tool registration pattern

### Requirements
- `.planning/REQUIREMENTS.md` — DEPLOY-01 through DEPLOY-04, REPL-01 through REPL-03, BOARD-03, MCP-04, MCP-05

### Project Context
- `.planning/PROJECT.md` — core value, constraints, out-of-scope items

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/board_detection.py` — `detect_chip()`, `load_board_state()`, `save_board_state()`: state persistence pattern to reuse
- `tools/firmware_flash.py` — subprocess + timeout pattern, error dict returns, pre-flight integration pattern
- `mcp_server.py` — `@mcp.tool()` registration pattern; new tools follow same thin-wrapper structure

### Established Patterns
- Error returns: `{"error": "snake_case_code", "detail": "human string"}` — never raise
- State dir: `~/.esp32-station/` — new subdirs go here (e.g., `locks/`)
- subprocess: `subprocess.run([...], capture_output=True, text=True, timeout=N)`
- Tool modules in `tools/`, thin wrappers in `mcp_server.py`

### Integration Points
- `mcp_server.py` — add new `@mcp.tool()` decorators for deploy, REPL, reset tools
- `tools/board_detection.py` — `detect_chip()` available as pre-flight for deploy/REPL ops

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard mpremote-based approaches.

</specifics>

<deferred>
## Deferred Ideas

None — user skipped discussion; no scope creep raised.

</deferred>

---

*Phase: 02-core-usb-workflows*
*Context gathered: 2026-03-29*
