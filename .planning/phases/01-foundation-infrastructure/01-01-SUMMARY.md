---
phase: 01-foundation-infrastructure
plan: "01"
subsystem: testing
tags: [pytest, python, mcp, fastmcp, esptool, pyserial, stub, tdd]

# Dependency graph
requires: []
provides:
  - Project directory skeleton with all stub modules (tools/, state/, service file)
  - requirements.txt with 5 runtime + 2 test deps (pinned version ranges)
  - pytest infrastructure: pytest.ini, conftest.py with shared fixtures
  - 17 failing test stubs covering BOARD-01/02/04, FLASH-01-05, MCP-01/02/03
affects:
  - 01-02-PLAN.md (board detection implementation — finds test stubs ready)
  - 01-03-PLAN.md (firmware flash implementation — finds test stubs ready)
  - 01-04-PLAN.md (MCP server implementation — finds test stubs ready)

# Tech tracking
tech-stack:
  added: [pytest>=7.0, pytest-asyncio>=0.23, mcp[cli]>=1.26.0, esptool>=5.0, pyserial>=3.5, requests>=2.31, mpremote>=1.23]
  patterns: [stub-first TDD scaffold, NotImplementedError stubs for deferred implementation, conftest.py shared fixtures]

key-files:
  created:
    - requirements.txt
    - mcp_server.py
    - tools/__init__.py
    - tools/board_detection.py
    - tools/firmware_flash.py
    - state/.gitkeep
    - esp32-station.service
    - pytest.ini
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_board_detect.py
    - tests/test_flash.py
    - tests/test_mcp_server.py
    - .gitignore
  modified: []

key-decisions:
  - "Venv must be created in /tmp (not project root) — project is on CIFS/SMB mount that blocks symlinks required by venv creation"
  - "mcp_server.py stub imports FastMCP at module level so test_mcp_server_imports passes before Plan 04 implementation"
  - "tests/test_mcp_server.py uses pathlib.Path('esp32-station.service') relative path — pytest must run from project root"

patterns-established:
  - "Stub pattern: raise NotImplementedError in every function body until Plan N implements it"
  - "Module-level constants (BOARDS_JSON, STATE_DIR, FIRMWARE_DIR) patched in tests to isolate I/O"
  - "conftest.py fixtures named mock_esptool_success/failure mirror the two code paths under test"

requirements-completed:
  - BOARD-01
  - BOARD-02
  - BOARD-04
  - FLASH-01
  - FLASH-02
  - FLASH-03
  - FLASH-04
  - FLASH-05
  - MCP-01
  - MCP-02
  - MCP-03

# Metrics
duration: 3min
completed: 2026-03-28
---

# Phase 1 Plan 01: Project Skeleton and Test Scaffold Summary

**pytest collecting 17 failing stubs covering all 11 Phase 1 requirements; FastMCP stub, esptool wrappers, and systemd unit present on disk**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-28T21:57:31Z
- **Completed:** 2026-03-28T21:59:40Z
- **Tasks:** 2 of 2
- **Files modified:** 14

## Accomplishments
- Created full project skeleton: tools/ package, state/ directory, systemd service stub, and mcp_server.py entry point
- Wrote requirements.txt with all 5 runtime dependencies and 2 test dependencies with pinned version ranges
- Created pytest infrastructure (pytest.ini, conftest.py) with 5 shared fixtures for mock serial ports and esptool subprocess results
- Wrote 17 test stubs across 3 test files; all collected by pytest with zero import/syntax errors; all fail with NotImplementedError as expected

## Task Commits

Each task was committed atomically:

1. **Task 1: Create project skeleton and requirements.txt** - `583bdef` (feat)
2. **Task 2: Create pytest configuration and all test stubs** - `47a26df` (test)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `requirements.txt` - 7 dependencies with pinned version ranges
- `mcp_server.py` - FastMCP stub (imports cleanly; full impl in Plan 04)
- `tools/__init__.py` - Package marker
- `tools/board_detection.py` - Stubs: list_boards, detect_chip, load/save_board_state
- `tools/firmware_flash.py` - Stubs: get_firmware_path, flash_firmware
- `state/.gitkeep` - Runtime boards.json directory placeholder
- `esp32-station.service` - systemd unit stub (full impl in Plan 04)
- `pytest.ini` - testpaths=tests, asyncio_mode=auto
- `tests/__init__.py` - Package marker
- `tests/conftest.py` - Shared fixtures: mock_serial_ports, non_esp32_port, mock_esptool_success/failure/no_chip_line
- `tests/test_board_detect.py` - 7 stubs (BOARD-01, BOARD-02, BOARD-04)
- `tests/test_flash.py` - 7 stubs (FLASH-01 through FLASH-05)
- `tests/test_mcp_server.py` - 3 stubs (MCP-01, MCP-02, MCP-03)
- `.gitignore` - Python cache, venv, runtime state

## Decisions Made
- Venv must be created in `/tmp` not project root — the project lives on a CIFS/SMB mount that does not support the `lib64` symlink required by `python -m venv`. Command: `python3 -m venv /tmp/esp32-station-venv && /tmp/esp32-station-venv/bin/pip install -r requirements.txt`
- `mcp_server.py` stub imports FastMCP at module level so `test_mcp_server_imports` can pass without waiting for Plan 04; stub needs no further implementation for test collection to succeed
- `tests/test_mcp_server.py::test_systemd_service_file_content` uses a relative path — pytest must always be run from the project root (`/mnt/anton/Claude/ESP32-server/`)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created venv in /tmp instead of project root**
- **Found during:** Task 2 (pytest test collection verification)
- **Issue:** `python3 -m venv venv` failed with `[Errno 95] Operation not supported: 'lib' -> 'venv/lib64'` — CIFS mount blocks symlink creation required by venv
- **Fix:** Created venv at `/tmp/esp32-station-venv` and installed dependencies there; ran `pytest` via `/tmp/esp32-station-venv/bin/pytest`
- **Files modified:** .gitignore (added venv/ to exclusions)
- **Verification:** `pytest tests/ --collect-only -q` exits 0, 17 tests collected
- **Committed in:** `47a26df` (Task 2 commit)

**2. [Rule 2 - Missing Critical] Added .gitignore**
- **Found during:** Task 2 (git status check after writing test files)
- **Issue:** No .gitignore; `__pycache__/` and `.pytest_cache/` would pollute commits
- **Fix:** Created `.gitignore` covering Python cache, venv, runtime state, editor files
- **Files modified:** `.gitignore`
- **Verification:** `git status` no longer shows cache directories
- **Committed in:** `47a26df` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both auto-fixes essential for functional test environment and clean git history. No scope creep.

## Known Stubs
- `tools/board_detection.py`: `list_boards`, `detect_chip`, `load_board_state`, `save_board_state` — all `raise NotImplementedError`; resolved in Plan 02
- `tools/firmware_flash.py`: `get_firmware_path`, `flash_firmware` — both `raise NotImplementedError`; resolved in Plan 03
- `mcp_server.py`: FastMCP instance created but no tools registered; tools added in Plan 04
- `esp32-station.service`: Uses `User=pi` and hardcoded Pi paths; generalized in Plan 04

These stubs are intentional — this plan's goal is scaffolding only. All stubs will be resolved by Plans 02-04.

## Issues Encountered
- CIFS/SMB mount (`//anton.local/Claude`) does not support symlinks, blocking `python -m venv`. Resolved by using `/tmp` for the virtualenv. This affects all plans that need to run pytest — use `/tmp/esp32-station-venv/bin/pytest` or create venv in `/tmp` before running tests on this host.

## Next Phase Readiness
- All test stubs present on disk; Plans 02/03/04 can immediately run their target test files and drive TDD cycles
- `pytest tests/ --collect-only -q` passes with 17 items; no import errors
- Virtual environment command for next agents: `python3 -m venv /tmp/esp32-station-venv && /tmp/esp32-station-venv/bin/pip install -r requirements.txt`

## Self-Check: PASSED

- FOUND: requirements.txt
- FOUND: mcp_server.py
- FOUND: tests/conftest.py
- FOUND: tests/test_board_detect.py
- FOUND: tests/test_flash.py
- FOUND: tests/test_mcp_server.py
- FOUND: 01-01-SUMMARY.md
- FOUND commit 583bdef: feat(01-01): create project skeleton and requirements.txt
- FOUND commit 47a26df: test(01-01): create pytest config and all test stubs (17 tests collected)

---
*Phase: 01-foundation-infrastructure*
*Completed: 2026-03-28*
