---
phase: 04-hardening
plan: 02
subsystem: infra
tags: [pyserial, esptool, dtr-rts, hardware-reset, esp32]

# Dependency graph
requires:
  - phase: 04-hardening-01
    provides: "Phase 4 research and validation foundation"
  - phase: 02-core-usb-workflows
    provides: "repl.py hard_reset, firmware_flash.py, mcp_server.py deploy tools"
provides:
  - "Reliable DTR/RTS hardware reset via pyserial (no mpremote dependency)"
  - "Fallback message when hardware reset fails (unplug/replug guidance)"
  - "Explicit --chip flag on all esptool subprocess calls"
  - "Deploy functions use hard_reset instead of soft_reset"
affects: [deployment, flashing, board-management]

# Tech tracking
tech-stack:
  added: [pyserial (serial.Serial for DTR/RTS)]
  patterns: [hardware-signal-reset, explicit-chip-flag]

key-files:
  created: []
  modified:
    - tools/repl.py
    - tools/board_detection.py
    - tools/firmware_flash.py
    - mcp_server.py
    - tests/test_repl.py
    - tests/test_flash.py
    - tests/test_board_detect.py

key-decisions:
  - "DTR/RTS via pyserial replaces mpremote subprocess for hard_reset — works regardless of MicroPython state"
  - "Fallback message provides unplug/replug instructions when serial port cannot be opened"
  - "--chip auto for chip_id, --chip <variant> for erase/write — explicit is always better than silent auto-detect"

patterns-established:
  - "Hardware reset pattern: open serial port, pulse RTS, close port"
  - "Fallback guidance pattern: error dict includes 'fallback' key with user-actionable instructions"

requirements-completed: [REL-01, REL-02, REL-03]

# Metrics
duration: 5min
completed: 2026-03-29
---

# Phase 4 Plan 2: Reliability Hardening Summary

**DTR/RTS hardware reset via pyserial replacing mpremote, with fallback guidance and explicit --chip on all esptool calls**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-29T18:36:40Z
- **Completed:** 2026-03-29T18:41:21Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Replaced unreliable mpremote-based hard_reset with pyserial DTR/RTS hardware signal reset
- Added fallback field with unplug/replug instructions when hardware reset fails
- Enforced explicit --chip argument on all 3 esptool subprocess calls (chip_id, erase_flash, write_flash)
- Updated all 3 deploy MCP tools (deploy_file, deploy_directory, pull_and_deploy_github) to use hard_reset instead of soft_reset
- Added 5 new tests covering DTR/RTS behavior, fallback message, port cleanup, and --chip enforcement

## Task Commits

Each task was committed atomically:

1. **Task 1: Write tests for DTR/RTS reset, fallback, --chip enforcement** - `c973f15` (test) - TDD RED phase
2. **Task 2: Implement DTR/RTS reset, --chip enforcement, deploy updates** - `4f99d89` (feat) - TDD GREEN phase

## Files Created/Modified
- `tools/repl.py` - Replaced mpremote hard_reset with pyserial DTR/RTS signal reset; added fallback message
- `tools/board_detection.py` - Added --chip auto to esptool chip_id call
- `tools/firmware_flash.py` - Added --chip to erase_flash and write_flash esptool calls
- `mcp_server.py` - Changed 3 deploy functions from soft_reset to hard_reset post-deploy
- `tests/test_repl.py` - Added 3 new DTR/RTS tests; updated 2 existing hard_reset tests for pyserial
- `tests/test_flash.py` - Added test_esptool_calls_include_chip_flag
- `tests/test_board_detect.py` - Added test_chip_id_uses_explicit_chip_auto

## Decisions Made
- Used pyserial DTR/RTS signal instead of mpremote subprocess for hard_reset -- works even when MicroPython is unresponsive
- Fallback message provides physical intervention instructions (unplug/replug) when serial port fails
- Used --chip auto for chip_id detection, --chip <variant> for erase/write operations

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing hard_reset tests for new pyserial implementation**
- **Found during:** Task 2 (GREEN phase test run)
- **Issue:** Old test_hard_reset_success and test_hard_reset_failure mocked subprocess.run but hard_reset now uses serial.Serial
- **Fix:** Updated both tests to mock tools.repl.serial.Serial instead of subprocess.run
- **Files modified:** tests/test_repl.py
- **Verification:** All 27 tests in affected files pass
- **Committed in:** 4f99d89 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary fix -- old tests were testing the wrong mock target after implementation change. No scope creep.

## Issues Encountered
- Test environment sandbox has read-only home directory, causing test_mcp_server.py::test_deploy_file_returns_error_dict_on_failure to fail (SerialLock tries to create lock file in ~/.esp32-station/locks/). This is a pre-existing environment issue, not caused by this plan's changes. All tests in the files modified by this plan pass.

## Known Stubs
None -- all functionality is fully wired with no placeholder data.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Hardware reset is reliable and works regardless of MicroPython state
- All esptool calls now have explicit --chip, eliminating silent auto-detect failures
- Deploy pipeline consistently uses hard_reset for post-deploy board restart

---
*Phase: 04-hardening*
*Completed: 2026-03-29*
