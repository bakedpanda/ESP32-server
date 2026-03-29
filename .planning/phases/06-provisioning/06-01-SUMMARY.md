---
phase: 06-provisioning
plan: 01
subsystem: provisioning
tags: [credentials, wifi, webrepl, boot.py, micropython, template]

# Dependency graph
requires:
  - phase: 03-wifi-advanced
    provides: OTA WiFi deploy and WebREPL integration
provides:
  - load_credentials() shared utility for Pi-local WiFi/WebREPL credential loading
  - boot.py template with WiFi + WebREPL + hostname placeholders
affects: [06-02 deploy_boot_config tool, provisioning flow]

# Tech tracking
tech-stack:
  added: []
  patterns: [error dict pattern for credential failures, template placeholder injection]

key-files:
  created: [tools/credentials.py, templates/boot.py.tpl, tests/test_credentials.py]
  modified: []

key-decisions:
  - "Credentials read from /etc/esp32-station/wifi.json with error dict pattern (never raises)"
  - "boot.py sets hostname BEFORE wlan.active() per MicroPython mDNS requirement"
  - "No _webrepl._tcp service ads -- standard firmware only supports hostname.local discovery"

patterns-established:
  - "Credential loading: return error dict with setup instructions when file missing/invalid"
  - "Template placeholders: {{KEY}} syntax for boot.py generation"

requirements-completed: [SETUP-02, PROV-02]

# Metrics
duration: 6min
completed: 2026-03-29
---

# Phase 6 Plan 1: Credentials Utility and Boot Template Summary

**Pi-local credential loader with error dict pattern and boot.py template with WiFi/WebREPL/hostname placeholders**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-29T22:52:06Z
- **Completed:** 2026-03-29T22:58:20Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- load_credentials() reads WiFi + WebREPL creds from /etc/esp32-station/wifi.json with structured error dicts for all failure modes
- boot.py template with correct hostname-before-active ordering, bounded WiFi loop, and programmatic WebREPL start
- 6 passing tests covering happy path and all error modes (missing file, invalid JSON, incomplete keys, constants)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create credentials utility and tests** - `ece03c5` (test: RED), `b39f3f9` (feat: GREEN)
2. **Task 2: Create boot.py template** - `9a8a932` (feat)

_Note: Task 1 followed TDD with RED/GREEN commits_

## Files Created/Modified
- `tools/credentials.py` - Shared credential loader with CREDENTIALS_PATH, REQUIRED_KEYS, load_credentials()
- `templates/boot.py.tpl` - MicroPython boot.py template with 4 placeholders (SSID, PASSWORD, WEBREPL_PASSWORD, HOSTNAME)
- `tests/test_credentials.py` - 6 tests covering all credential loading paths

## Decisions Made
- Followed plan as specified -- error dict pattern per D-20, credential path per D-01, template per D-07/D-08/D-09

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered
- No venv in worktree -- used pytest from sibling worktree's venv. Pre-existing test failures in test_mcp_server.py (missing mcp module) and test_mdns_discovery.py (attribute error) are unrelated to this plan.

## User Setup Required
None -- no external service configuration required.

## Next Phase Readiness
- tools/credentials.py and templates/boot.py.tpl ready for Plan 02 (deploy_boot_config MCP tool)
- Plan 02 will implement placeholder injection and mpremote deployment

## Self-Check: PASSED

All files exist, all commits verified.

---
*Phase: 06-provisioning*
*Completed: 2026-03-29*
