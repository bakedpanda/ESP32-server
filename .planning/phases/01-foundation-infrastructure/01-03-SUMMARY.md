---
phase: 01-foundation-infrastructure
plan: "03"
subsystem: infra
tags: [esptool, requests, firmware, cache, flash]

requires:
  - phase: 01-02
    provides: detect_chip() interface for pre-flight chip detection
provides:
  - Firmware URL map for 5 chip variants (ESP32, S2, S3, C3, C6) — MicroPython v1.27.0
  - 7-day TTL firmware cache at ~/.esp32-station/firmware/
  - esptool erase_flash + write_flash orchestration with correct offsets per chip
  - Pre-flight chip detection integration (chip=None triggers detect_chip)
affects: [01-04]

tech-stack:
  added: [requests]
  patterns: [TTL cache with stale fallback, correct write offsets by chip variant, two-step erase+write]

key-files:
  created: []
  modified: [tools/firmware_flash.py]

key-decisions:
  - "Write offset 0x1000 for classic ESP32, 0x0 for all other variants (S2/S3/C3/C6)"
  - "Stale cache is used on download failure (prefer offline operation)"
  - "FLASH_BAUD=460800 for write, DETECT_BAUD=115200 for erase (matches esptool recommendations)"

requirements-completed: [FLASH-01, FLASH-02, FLASH-03, FLASH-04, FLASH-05]

duration: 6min
completed: 2026-03-28
---

# Phase 01 Plan 03: Firmware Flash Summary

**7-day TTL firmware cache + esptool erase/write orchestration for 5 ESP32 chip variants with pre-flight detection**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-28T22:31:00Z
- **Completed:** 2026-03-28T22:37:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Implemented `get_firmware_path()` with 7-day TTL and stale-cache fallback for offline use
- Implemented `flash_firmware()` with pre-flight chip detection (chip=None), unsupported chip validation, erase+write sequence
- Correct write offsets: `0x1000` for classic ESP32, `0x0` for S2/S3/C3/C6
- All 7 tests in test_flash.py pass

## Task Commits

1. **Task 1: Implement firmware_flash.py** - `5b59b7d` (feat)

## Files Created/Modified
- `tools/firmware_flash.py` — full implementation replacing NotImplementedError stubs

## Decisions Made
- ESP32 classic needs `0x1000` write offset; all newer variants use `0x0` — hardware difference, not a config choice
- Stale cache used on download failure to support offline/air-gapped flashing scenarios
- `FLASH_BAUD=460800` for write speed (higher than detect baud of 115200)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Both `list_boards` and `flash_firmware` are fully implemented; Plan 01-04 can wire them as MCP tools
- `detect_chip` + `flash_firmware` call chain is complete end-to-end

---
*Phase: 01-foundation-infrastructure*
*Completed: 2026-03-28*
