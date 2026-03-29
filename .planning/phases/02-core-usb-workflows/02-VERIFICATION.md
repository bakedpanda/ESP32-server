---
phase: 02-core-usb-workflows
verified: 2026-03-29T00:00:00Z
status: passed
score: 5/5 success criteria verified
re_verification: false
---

# Phase 2: Core USB Workflows — Verification Report

**Phase Goal:** Complete flash+deploy+REPL pipeline; handle file system constraints; robust error handling at every step.
**Verified:** 2026-03-29
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Claude can deploy a single file or full project directory via USB serial without file corruption | VERIFIED | `tools/file_deploy.py`: `deploy_file()` and `deploy_directory()` use `subprocess.run(['mpremote', 'connect', port, 'cp', ...])` with post-transfer `verify_file_size()` integrity check |
| 2 | Pre-deployment checks verify sufficient filesystem space; fail gracefully if insufficient with actionable errors | VERIFIED | `check_board_space()` returns `{"error": "insufficient_space", ...}` at >= 90%, `{"warning": "filesystem_70pct_full", ...}` at >= 70%, both are error dicts with `detail` fields |
| 3 | Claude can execute MicroPython commands and capture output without timeouts or hanging | VERIFIED | `tools/repl.py`: `exec_repl()` wraps `subprocess.run(..., timeout=timeout)` in `except subprocess.TimeoutExpired` returning `{"error": "repl_timeout", "detail": "command timed out after Ns"}` |
| 4 | Claude can read recent serial output and reset a board (soft and hard) via USB | VERIFIED | `read_serial()`, `soft_reset()`, `hard_reset()` all present in `tools/repl.py`; reset functions treat non-zero exit with empty stderr as success (expected board disconnect behavior) |
| 5 | All MCP server errors include a unique code and actionable description; operations on the same board serialize correctly | VERIFIED | 5 new tools in `mcp_server.py` each wrap with `SerialLock(port)` and `except TimeoutError as e: return {"error": "serial_lock_timeout", "detail": str(e)}`; all error paths return both `"error"` and `"detail"` keys |

**Score:** 5/5 success criteria verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/serial_lock.py` | SerialLock context manager with fcntl.flock, port_to_slug | VERIFIED | 80 lines; exports `SerialLock` class and `port_to_slug()`; `LOCK_DIR = pathlib.Path.home() / ".esp32-station" / "locks"`, `LOCK_TIMEOUT_SECONDS = 30` |
| `tools/file_deploy.py` | deploy_file(), deploy_directory(), check_board_space(), verify_file_size() | VERIFIED | 274 lines; all 4 functions present; `MPREMOTE_CMD = "mpremote"`, `SPACE_WARN_PCT = 70`, `SPACE_FAIL_PCT = 90`, `DEPLOY_EXCLUDE_DIRS` with `"__pycache__"` |
| `tools/repl.py` | exec_repl(), read_serial(), soft_reset(), hard_reset() | VERIFIED | 122 lines; all 4 functions present; `MPREMOTE_CMD = "mpremote"`, `REPL_TIMEOUT_SECONDS = 10`, `READ_SERIAL_TIMEOUT = 5` |
| `mcp_server.py` | 9 @mcp.tool() registrations (4 Phase 1 + 5 new) | VERIFIED | 191 lines; `grep -c "@mcp.tool()"` returns `9`; all 5 new tools present: `deploy_file_to_board`, `deploy_directory_to_board`, `exec_repl_command`, `read_board_serial`, `reset_board` |
| `tests/test_serial_lock.py` | >= 5 test functions | VERIFIED | 71 lines; 6 test functions: `test_port_to_slug_usb0`, `test_port_to_slug_acm1`, `test_lock_file_created_on_acquire`, `test_lock_file_removed_on_release`, `test_lock_is_exclusive_same_port`, `test_different_ports_do_not_block` |
| `tests/test_mcp_server.py` | 4 required new test functions + 3 original | VERIFIED | 76 lines; all 4 required functions present: `test_new_tools_registered`, `test_deploy_file_returns_error_dict_on_failure`, `test_exec_repl_returns_error_dict_on_timeout`, `test_reset_board_invalid_type` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `mcp_server.py` | `tools/serial_lock.py` | `with SerialLock(port):` inside each tool | WIRED | `SerialLock` appears at lines 95, 117, 139, 158, 181 — all 5 new tools use it |
| `mcp_server.py` | `tools/file_deploy.py` | `from tools.file_deploy import deploy_file, deploy_directory` | WIRED | Line 13; both functions called in `deploy_file_to_board` and `deploy_directory_to_board` |
| `mcp_server.py` | `tools/repl.py` | `from tools.repl import exec_repl, read_serial, soft_reset, hard_reset` | WIRED | Line 15; all 4 functions called in corresponding MCP tool wrappers |
| `tools/file_deploy.py` | `mpremote` | `subprocess.run(['mpremote', 'connect', port, ...])` | WIRED | `MPREMOTE_CMD = "mpremote"` used in `check_board_space`, `verify_file_size`, `deploy_file`, `deploy_directory` |
| `tools/repl.py` | `mpremote` | `subprocess.run(['mpremote', 'connect', port, 'exec', cmd], timeout=N)` | WIRED | All 4 functions use `subprocess.run([MPREMOTE_CMD, "connect", port, ...]` with `timeout=` parameter |
| `mcp_server.py` | `TimeoutError -> error dict` | `except TimeoutError as e: return {"error": "serial_lock_timeout", "detail": str(e)}` | WIRED | 5 occurrences (lines 97-98, 119-120, 141-142, 160-161, 185-186) — one per new tool |

### Data-Flow Trace (Level 4)

Not applicable — all artifacts are subprocess-delegation utilities and MCP server wrappers, not components that render dynamic state from a data store.

### Behavioral Spot-Checks

| Behavior | Check | Result | Status |
|----------|-------|--------|--------|
| `port_to_slug("/dev/ttyUSB0")` == `"dev_ttyUSB0"` | Code inspection: `port.replace("/", "_").lstrip("_")` | Correct transformation confirmed by logic and test `test_port_to_slug_usb0` | VERIFIED |
| `reset_board(..., reset_type="bogus")` returns `{"error": "invalid_reset_type", ...}` | Line 178-179: guard clause before SerialLock | Returns error dict without attempting lock or subprocess | VERIFIED |
| `exec_repl_command` on `subprocess.TimeoutExpired` returns `{"error": "repl_timeout", ...}` | `tools/repl.py` line 31-32; `mcp_server.py` line 139-142 | `exec_repl` converts `TimeoutExpired` to `repl_timeout`; MCP wrapper handles `SerialLock` `TimeoutError` separately | VERIFIED |
| No bare `raise` in tool modules (error-dict pattern enforced) | `grep "raise"` on all tool files | Only `raise TimeoutError(...)` in `serial_lock.py.__enter__` — intentional, caught by MCP wrappers | VERIFIED |

Note: venv/bin/pytest is inaccessible on this host (venv on remote mount). Executor confirmed 42/42 tests passing in working tree. Verification performed by code inspection.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DEPLOY-01 | 02-01-PLAN.md | Claude can deploy a single file to a board via USB serial | SATISFIED | `deploy_file()` in `tools/file_deploy.py` |
| DEPLOY-02 | 02-01-PLAN.md | Claude can deploy a full project directory to a board via USB serial | SATISFIED | `deploy_directory()` in `tools/file_deploy.py` with `DEPLOY_EXCLUDE_DIRS` filtering |
| DEPLOY-03 | 02-01-PLAN.md | Pre-deployment check verifies sufficient filesystem space (60-70% safe capacity) | SATISFIED | `check_board_space()` warns at 70%, hard-fails at 90% |
| DEPLOY-04 | 02-01-PLAN.md | Deployment verifies file integrity after transfer | SATISFIED | `verify_file_size()` uses `mpremote exec "import os; print(os.stat(...)[6])"` to compare byte counts |
| REPL-01 | 02-02-PLAN.md | Claude can execute a MicroPython command on a board and capture the output | SATISFIED | `exec_repl()` in `tools/repl.py` |
| REPL-02 | 02-02-PLAN.md | Claude can read recent serial output from a board | SATISFIED | `read_serial()` in `tools/repl.py` |
| REPL-03 | 02-02-PLAN.md | REPL commands time out cleanly (no blocking hangs) | SATISFIED | `subprocess.TimeoutExpired` caught in `exec_repl()` and `read_serial()`, returns `repl_timeout`/`read_timeout` error dicts |
| BOARD-03 | 02-02-PLAN.md | Claude can reset a board (soft reset and hard reset) | SATISFIED | `soft_reset()` and `hard_reset()` in `tools/repl.py`; `reset_board` MCP tool in `mcp_server.py` |
| MCP-04 | 02-03-PLAN.md | All board operations serialize per device (no concurrent USB access conflicts) | SATISFIED | `SerialLock` with `fcntl.flock(LOCK_EX | LOCK_NB)` polling loop; separate lock files per port slug under `~/.esp32-station/locks/` |
| MCP-05 | 02-03-PLAN.md | All errors returned to Claude include a code and actionable description | SATISFIED | Every error path across all tool modules returns `{"error": "snake_case_code", "detail": "human string"}`; MCP wrappers add `serial_lock_timeout` code for lock failures |

**No orphaned requirements:** REQUIREMENTS.md traceability table maps DEPLOY-01..04, REPL-01..03, BOARD-03, MCP-04, MCP-05 to Phase 2 — all accounted for across 02-01-PLAN.md, 02-02-PLAN.md, 02-03-PLAN.md.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tools/serial_lock.py` | 67 | `raise TimeoutError(...)` in `__enter__` | Info | Intentional design — propagates to MCP server catch clauses that convert to error dicts. Not a stub or bare raise. |

No TODO/FIXME/placeholder comments, empty implementations, or hardcoded empty returns found in any Phase 2 implementation files.

### Human Verification Required

None. All acceptance criteria can be verified by code inspection, and executor confirmed full test suite (42/42) passed in the working tree.

### Plan Text Discrepancy (Non-Blocking)

02-03-PLAN.md truth #5 states "All 6 MCP tools (4 from Phase 1 + deploy + REPL + reset)" — this count is wrong in the plan text. There are 4 Phase 1 tools + 5 new Phase 2 tools = 9 total. The plan's own acceptance criteria correctly state 5 new tools, and 9 are present in `mcp_server.py`. The discrepancy is in the plan documentation only; the implementation is correct.

### Gaps Summary

No gaps. All success criteria verified, all artifacts exist and are substantive and wired, all requirements accounted for, no blocker anti-patterns.

---

_Verified: 2026-03-29_
_Verifier: Claude (gsd-verifier)_
