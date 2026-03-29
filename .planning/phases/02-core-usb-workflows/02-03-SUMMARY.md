---
phase: 02-core-usb-workflows
plan: "03"
subsystem: mcp-server-wiring
tags: [serial-lock, fcntl, mcp-tools, error-dict, concurrency]

requires:
  - phase: 02-core-usb-workflows
    plan: "01"
    provides: deploy_file, deploy_directory from tools/file_deploy.py
  - phase: 02-core-usb-workflows
    plan: "02"
    provides: exec_repl, read_serial, soft_reset, hard_reset from tools/repl.py

provides:
  - SerialLock context manager — per-port fcntl file-based mutex at ~/.esp32-station/locks/
  - port_to_slug() — /dev/ttyUSB0 -> dev_ttyUSB0 converter
  - 5 new MCP tools: deploy_file_to_board, deploy_directory_to_board, exec_repl_command, read_board_serial, reset_board
  - All tools wrapped in SerialLock for concurrent-call safety
  - All tools return structured {error, detail} dicts on failure

affects: [mcp-server, phase-03-ota-deployment]

tech-stack:
  added: [fcntl (stdlib), pathlib mutex pattern]
  patterns:
    - "File-based mutex: fcntl.LOCK_EX | LOCK_NB with polling loop and deadline"
    - "TimeoutError catch in MCP wrappers -> {error: serial_lock_timeout, detail: str(e)}"
    - "Lock files at ~/.esp32-station/locks/<port_slug>.lock, cleaned up on __exit__"

key-files:
  created:
    - tools/serial_lock.py
    - tests/test_serial_lock.py
  modified:
    - mcp_server.py
    - tests/test_mcp_server.py

key-decisions:
  - "Use fcntl.flock (file-level kernel lock) rather than threading.Lock — safe across subprocesses and restarts"
  - "Polling loop with 0.1s sleep intervals up to LOCK_TIMEOUT_SECONDS=30 — avoids busy-wait while remaining responsive"
  - "TimeoutError from SerialLock.__enter__ caught at MCP wrapper layer, not propagated — Claude receives actionable error dict"
  - "reset_board validates reset_type before acquiring lock — avoids holding lock for invalid input"

requirements-completed: [MCP-04, MCP-05]

duration: 5min
completed: 2026-03-29
---

# Phase 02 Plan 03: Serial Lock and MCP Tool Wiring Summary

**fcntl file-based per-port mutex wrapping 5 new MCP tools; all errors as structured {error, detail} dicts**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-29T10:53:05Z
- **Completed:** 2026-03-29T10:57:34Z
- **Tasks:** 2 (Task 1 TDD: RED + GREEN; Task 2: implementation)
- **Files modified:** 4

## Accomplishments

- Implemented `tools/serial_lock.py` with `SerialLock` context manager and `port_to_slug()`
- File-based mutex uses `fcntl.flock(LOCK_EX | LOCK_NB)` with polling; lock files at `~/.esp32-station/locks/<slug>.lock`
- Concurrent calls to same port serialize (second waits up to 30s, then TimeoutError); different ports do not block each other
- All 6 lock tests pass (TDD: RED commit + GREEN commit)
- Added 5 new MCP tools to `mcp_server.py` (total: 9 tools = 4 original + 5 new)
- All tools wrapped with `SerialLock`; `TimeoutError` caught and returned as `{"error": "serial_lock_timeout", "detail": ...}`
- `reset_board` validates `reset_type` before acquiring lock (early return with `invalid_reset_type`)
- Added 4 new tests to `test_mcp_server.py`; full suite: 42/42 passing, zero regressions

## Task Commits

Each task committed atomically:

1. **Task 1 RED — Failing SerialLock tests** - `128fedb` (test)
2. **Task 1 GREEN — SerialLock implementation** - `00706f0` (feat)
3. **Task 2 — MCP tool wiring + test updates** - `ccdee9e` (feat)

## Files Created/Modified

- `tools/serial_lock.py` — LOCK_DIR, LOCK_TIMEOUT_SECONDS, port_to_slug(), SerialLock context manager
- `tests/test_serial_lock.py` — 6 tests: port_to_slug, lock file created/removed, exclusivity, different-port independence
- `mcp_server.py` — 3 new imports + 5 new MCP tool wrappers; 9 total @mcp.tool() registrations
- `tests/test_mcp_server.py` — 4 new tests: tool registration, deploy error shape, repl timeout shape, reset invalid type

## Decisions Made

- `fcntl.flock` over `threading.Lock`: file-based locking is process-safe; MCP server may fork or restart, and file locks survive parent process issues in ways in-memory locks cannot.
- Polling at 0.1s intervals: responsive enough for user-facing operations while not burning CPU; 30s timeout matches the longest expected board operation (firmware flash is handled separately without SerialLock).
- TimeoutError caught at MCP wrapper layer: the lock module raises Python's built-in `TimeoutError`; wrappers convert to error dict so Claude always gets `{error, detail}` regardless of failure mode.
- `reset_board` validates `reset_type` before `SerialLock` acquisition: invalid input is rejected instantly without holding the port lock.

## Deviations from Plan

None — plan executed exactly as written. The `_tool_manager.list_tools()` API was confirmed to be synchronous (not async) before writing the test, which matched the plan's test code exactly.

## Known Stubs

None — all 5 MCP tool wrappers call real functions from `tools/file_deploy.py` and `tools/repl.py`.

## Self-Check: PASSED

- tools/serial_lock.py: FOUND
- tests/test_serial_lock.py: FOUND
- mcp_server.py: FOUND (9 @mcp.tool() registrations confirmed)
- tests/test_mcp_server.py: FOUND (7 tests total)
- commit 128fedb: FOUND (RED tests)
- commit 00706f0: FOUND (GREEN serial_lock.py)
- commit ccdee9e: FOUND (task 2 MCP wiring)
- Full test suite: 42/42 passed

---
*Phase: 02-core-usb-workflows*
*Completed: 2026-03-29*
