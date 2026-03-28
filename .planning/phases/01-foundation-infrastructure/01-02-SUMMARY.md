---
phase: 01-foundation-infrastructure
plan: "02"
subsystem: infra
tags: [esptool, pyserial, usb, board-detection, subprocess]

requires:
  - phase: 01-01
    provides: test stubs and project skeleton for board_detection.py
provides:
  - USB port enumeration filtered by 5 known ESP32 VIDs (CH340, CP2102, FTDI, Adafruit, Espressif native)
  - Chip detection via esptool chip_id subprocess with structured error returns
  - Board state persistence to ~/.esp32-station/boards.json
affects: [01-03, 01-04]

tech-stack:
  added: [pyserial, esptool]
  patterns: [error-dict returns instead of exceptions, subprocess with timeout, pathlib state dir]

key-files:
  created: []
  modified: [tools/board_detection.py]

key-decisions:
  - "ESPTOOL_CMD = 'esptool' (not 'esptool.py') — v5 renamed the command"
  - "detect_chip returns error dict rather than raising — callers use 'error' key check"
  - "list_boards reads last-known chip from state without probing hardware (avoid blocking on startup)"

requirements-completed: [BOARD-01, BOARD-02, BOARD-04, FLASH-04, FLASH-05]

duration: 8min
completed: 2026-03-28
---

# Phase 01 Plan 02: Board Detection Summary

**USB enumeration filtered by 5 ESP32 VID/PID sets, esptool chip_id subprocess detection, and boards.json state persistence**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-28T22:23:05Z
- **Completed:** 2026-03-28T22:31:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Implemented `list_boards()` filtering serial ports by ESP32-compatible VIDs (0x1A86, 0x10C4, 0x0403, 0x239A, 0x303A)
- Implemented `detect_chip()` calling esptool subprocess with 30s timeout, parsing "Chip is ESP32-XX" from stdout
- Implemented `load_board_state()` / `save_board_state()` with ~/.esp32-station/boards.json persistence
- All 7 tests in test_board_detect.py pass

## Task Commits

1. **Task 1: Implement board_detection.py** - `2bda3a1` (feat)

## Files Created/Modified
- `tools/board_detection.py` — full implementation replacing NotImplementedError stubs

## Decisions Made
- `ESPTOOL_CMD = "esptool"` not `"esptool.py"` — esptool v5 renamed the entry point
- `detect_chip` returns error dict (not raises) so callers can use `if "error" in result` without try/except at every call site — pre-flight pattern for FLASH-05
- `list_boards` reads last-known chip from state without probing hardware to avoid blocking the MCP tool startup

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- `detect_chip` interface established; Plan 01-03 can import it directly for pre-flight
- `boards.json` schema defined; Plan 01-04 MCP server can load state on startup

---
*Phase: 01-foundation-infrastructure*
*Completed: 2026-03-28*
