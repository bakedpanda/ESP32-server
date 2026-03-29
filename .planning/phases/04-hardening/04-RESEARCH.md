# Phase 4: Hardening - Research

**Researched:** 2026-03-29
**Domain:** ESP32 serial reset reliability, esptool subprocess hardening, test fixes
**Confidence:** HIGH

## Summary

Phase 4 addresses three categories of work: (1) replacing the unreliable soft reset with DTR/RTS hardware reset for post-deploy board restart, (2) enforcing explicit `--chip` flags on all esptool subprocess calls, and (3) fixing existing test gaps and cleaning up stale artifacts. All changes are within the existing Python codebase on the Pi -- no new dependencies, no new tools, no architectural changes.

The codebase already has `pyserial` as a dependency (used for `serial.tools.list_ports` in board detection). The same library provides `serial.Serial` with `.setRTS()` / `.setDTR()` methods needed for hardware reset. The esptool source code confirms that a hard reset is simply: set RTS high (EN pin low) for 100ms, then set RTS low (EN pin high). This is a 10-line function.

**Primary recommendation:** Replace `machine.reset()` via mpremote with direct DTR/RTS pulse via pyserial. Add `--chip` to all 3 esptool subprocess calls. Fix the 3 test/service issues. Ship it.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REL-01 | Post-deploy reset uses DTR/RTS hardware reset by default | pyserial `setRTS()` method -- confirmed working pattern from esptool source |
| REL-02 | If hardware reset fails, user is prompted to unplug/replug | Error dict pattern already established -- add fallback message to error return |
| REL-03 | All esptool calls use explicit `--chip` flag, never auto-detect | 3 calls identified in codebase -- chip is always known at call site |
| DEBT-01 | Fix `test_detect_chip_success` for read-only filesystem | Test already patches `BOARDS_JSON` and `STATE_DIR` to `tmp_path` -- the fix exists, needs verification |
| DEBT-02 | Remove stale planning comment from `esp32-station.service` line 1 | Line 1 is `# Full implementation in Plan 04 (01-04-PLAN.md)` -- just delete it |
| DEBT-03 | Add Phase 3 tool assertions to `test_new_tools_registered` | Phase 3 tools: `deploy_ota_wifi`, `pull_and_deploy_github` -- add to expected list |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyserial | >=3.5,<4.0 | DTR/RTS hardware reset via `serial.Serial` | Already a project dependency for board detection |
| esptool | >=5.0.0,<6.0.0 | Firmware flash (with `--chip` flag) | Already a project dependency |
| pytest | >=7.0,<8.0 | Test runner | Already a project dependency |

### No New Dependencies

This phase adds zero new packages. All work uses existing pyserial for the reset function.

## Architecture Patterns

### Current Reset Flow (broken)
```
mcp_server.py deploy_file_to_board() -> soft_reset(port)
  -> mpremote connect <port> exec "import machine; machine.soft_reset()"
  -> UNRELIABLE on ESP32 classic (known issue from v1.0)

mcp_server.py deploy_directory_to_board() -> soft_reset(port)
  -> same problem

tools/repl.py hard_reset(port)
  -> mpremote connect <port> exec "import machine; machine.reset()"
  -> Also unreliable -- requires MicroPython to be running and responsive
```

### New Reset Flow (REL-01, REL-02)
```
tools/repl.py hard_reset(port)
  -> Open serial port with pyserial
  -> setRTS(True)   # pull EN pin LOW (chip held in reset)
  -> sleep(0.1)     # 100ms hold
  -> setRTS(False)  # release EN pin (chip starts booting)
  -> Close port
  -> Return {"port": port, "reset": "hard"}
  -> On ANY exception: return error dict with "unplug/replug" fallback message

mcp_server.py deploy_file_to_board() -> hard_reset(port)  # change from soft_reset
mcp_server.py deploy_directory_to_board() -> hard_reset(port)
mcp_server.py pull_and_deploy_github() -> hard_reset(port)
```

### Esptool `--chip` Enforcement (REL-03)

Three subprocess calls need `--chip`:

1. **`board_detection.py:87`** -- `detect_chip()` runs `chip_id`
   - Problem: `chip_id` is called to DISCOVER the chip, so chip is unknown
   - Solution: `chip_id` does not benefit from `--chip` (it's a detection command), but the requirement says "every esptool subprocess call passes an explicit --chip flag"
   - Resolution: Use `--chip auto` explicitly (makes intent clear, satisfies requirement)
   - Alternative: Skip `--chip` for `chip_id` only since its purpose IS detection. But requirement is absolute ("no auto-detect anywhere"), so pass `--chip auto` to be explicit about intent

2. **`firmware_flash.py:115`** -- `erase_flash` -- chip IS known at this point (from detect_chip or parameter)
   - Add `"--chip", chip` before `"--port"`

3. **`firmware_flash.py:126`** -- `write_flash` -- chip IS known
   - Add `"--chip", chip` before `"--port"`

### Pattern: Error Dict with Fallback Guidance

The project uses error dicts (not exceptions). REL-02 requires a user-facing fallback message:

```python
# Pattern for REL-02 fallback
return {
    "error": "hard_reset_failed",
    "detail": str(exc),
    "fallback": "Unplug the board from USB, wait 3 seconds, then plug it back in"
}
```

This follows the existing pattern in `ota_wifi.py` which includes `"fallback": "use deploy_file_to_board"`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DTR/RTS reset | Raw file descriptor manipulation | pyserial `serial.Serial.setRTS()` | Cross-platform, handles OS quirks |
| Chip detection skip | "Smart" logic to skip `--chip` when unnecessary | Always pass `--chip` | Simpler, satisfies requirement absolutely |

## Common Pitfalls

### Pitfall 1: Serial Port Already Open
**What goes wrong:** pyserial cannot open a port that mpremote still has locked
**Why it happens:** deploy_file uses mpremote (which opens the port), then hard_reset tries to open same port via pyserial
**How to avoid:** The `hard_reset()` function runs inside the `SerialLock` context in `mcp_server.py`, after mpremote finishes. The mpremote subprocess has already exited. No conflict.
**Warning signs:** "Permission denied" or "port already in use" errors

### Pitfall 2: RTS Pin Not Connected to EN
**What goes wrong:** DTR/RTS reset does nothing on boards with native USB (ESP32-S2/S3/C6 without external UART bridge)
**Why it happens:** Native USB-CDC boards (Espressif VID 0x303A) may not route RTS to the EN pin
**How to avoid:** This is exactly why REL-02 exists -- if hardware reset fails (no response detected), prompt the user to power-cycle
**Warning signs:** `setRTS()` succeeds but board doesn't restart

### Pitfall 3: test_detect_chip_success Already Patched Correctly
**What goes wrong:** Wasting time "fixing" a test that may already work
**Why it happens:** DEBT-01 description says "patch BOARDS_JSON in test" -- but looking at the code, the test at line 31-38 ALREADY patches both `BOARDS_JSON` and `STATE_DIR` to `tmp_path`
**How to avoid:** Run the test first to confirm whether it actually fails. The issue may be that `STATE_DIR.mkdir()` in the production code runs before the patch takes effect (module-level vs function-level). Verify before changing.
**Warning signs:** Test passes on first run -- if so, DEBT-01 may already be resolved

### Pitfall 4: chip_id and --chip Flag
**What goes wrong:** Passing `--chip esp32` to `chip_id` when you don't know the chip yet
**Why it happens:** REL-03 says "every esptool call" but chip_id is the detection command
**How to avoid:** For the `chip_id` command specifically, pass `--chip auto` to make the auto-detection explicit rather than implicit. This satisfies the letter of REL-03 (every call has `--chip`) while preserving correct behavior.

## Code Examples

### DTR/RTS Hardware Reset (from esptool source)
```python
# Source: https://github.com/espressif/esptool/blob/master/esptool/reset.py
# HardReset class -- simplified for our use case
import serial
import time

def dtr_rts_reset(port: str) -> dict:
    """Hardware reset via DTR/RTS signal (equivalent to pressing RST button)."""
    try:
        ser = serial.Serial(port, baudrate=115200)
        ser.setRTS(True)    # EN -> LOW (hold chip in reset)
        time.sleep(0.1)     # 100ms hold
        ser.setRTS(False)   # EN -> HIGH (chip starts booting)
        time.sleep(0.05)    # 50ms settle
        ser.close()
        return {"port": port, "reset": "hard"}
    except Exception as exc:
        return {
            "error": "hard_reset_failed",
            "detail": str(exc),
            "fallback": "Unplug the board from USB, wait 3 seconds, then plug it back in"
        }
```

### Esptool with Explicit --chip
```python
# Current (REL-03 violation):
[ESPTOOL_CMD, "--port", port, "--baud", str(DETECT_BAUD), "erase_flash"]

# Fixed:
[ESPTOOL_CMD, "--chip", chip, "--port", port, "--baud", str(DETECT_BAUD), "erase_flash"]

# For chip_id (detection command -- chip unknown):
[ESPTOOL_CMD, "--chip", "auto", "--port", port, "--baud", str(BAUD), "chip_id"]
```

### Phase 3 Tool Assertions (DEBT-03)
```python
# Current expected list in test_new_tools_registered:
expected = [
    "deploy_file_to_board",
    "deploy_directory_to_board",
    "exec_repl_command",
    "read_board_serial",
    "reset_board",
]

# Add Phase 3 tools:
expected = [
    "deploy_file_to_board",
    "deploy_directory_to_board",
    "exec_repl_command",
    "read_board_serial",
    "reset_board",
    "deploy_ota_wifi",
    "pull_and_deploy_github",
]
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.0 (in venv on Pi) |
| Config file | `pytest.ini` (exists, testpaths=tests) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REL-01 | hard_reset uses DTR/RTS via pyserial | unit | `pytest tests/test_repl.py::test_hard_reset_uses_dtr_rts -x` | Wave 0 |
| REL-02 | hard_reset returns fallback message on failure | unit | `pytest tests/test_repl.py::test_hard_reset_fallback_message -x` | Wave 0 |
| REL-03 | All esptool calls include --chip flag | unit | `pytest tests/test_flash.py::test_esptool_calls_include_chip_flag -x` | Wave 0 |
| DEBT-01 | test_detect_chip_success passes | unit | `pytest tests/test_board_detect.py::test_detect_chip_success -x` | Exists (may need fix) |
| DEBT-02 | Service file has no stale comments | unit | `pytest tests/test_mcp_server.py::test_systemd_no_stale_comments -x` | Wave 0 |
| DEBT-03 | Phase 3 tools in registered tool list | unit | `pytest tests/test_mcp_server.py::test_new_tools_registered -x` | Exists (needs update) |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before verify-work

### Wave 0 Gaps
- [ ] `tests/test_repl.py::test_hard_reset_uses_dtr_rts` -- covers REL-01 (mock pyserial, verify setRTS calls)
- [ ] `tests/test_repl.py::test_hard_reset_fallback_message` -- covers REL-02 (mock serial.Serial to raise, verify fallback key)
- [ ] `tests/test_flash.py::test_esptool_calls_include_chip_flag` -- covers REL-03 (verify --chip in subprocess args)
- [ ] `tests/test_mcp_server.py::test_systemd_no_stale_comments` -- covers DEBT-02 (verify line 1 is not a comment)

## Inventory of Changes

All files that need modification (exhaustive):

| File | Change | Requirement |
|------|--------|-------------|
| `tools/repl.py` | Rewrite `hard_reset()` to use pyserial DTR/RTS instead of mpremote | REL-01, REL-02 |
| `tools/board_detection.py:87` | Add `"--chip", "auto"` to chip_id subprocess call | REL-03 |
| `tools/firmware_flash.py:115` | Add `"--chip", chip` to erase_flash subprocess call | REL-03 |
| `tools/firmware_flash.py:126` | Add `"--chip", chip` to write_flash subprocess call | REL-03 |
| `mcp_server.py:100` | Change `soft_reset(port)` to `hard_reset(port)` in deploy_file_to_board | REL-01 |
| `mcp_server.py:128` | Change `soft_reset(port)` to `hard_reset(port)` in deploy_directory_to_board | REL-01 |
| `mcp_server.py:249` | Change `soft_reset(port)` to `hard_reset(port)` in pull_and_deploy_github | REL-01 |
| `esp32-station.service:1` | Delete stale comment line | DEBT-02 |
| `tests/test_mcp_server.py` | Add Phase 3 tools to expected list in test_new_tools_registered | DEBT-03 |
| `tests/test_board_detect.py` | Verify/fix test_detect_chip_success | DEBT-01 |
| `tests/test_repl.py` | Add tests for DTR/RTS reset and fallback | REL-01, REL-02 |
| `tests/test_flash.py` | Add test for --chip flag presence | REL-03 |

## Sources

### Primary (HIGH confidence)
- [esptool reset.py source](https://github.com/espressif/esptool/blob/master/esptool/reset.py) - HardReset class confirms DTR/RTS sequence
- [pySerial 3.5 API docs](https://pyserial.readthedocs.io/en/latest/pyserial_api.html) - setRTS/setDTR methods
- [esptool Advanced Options](https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/advanced-options.html) - --chip, --before, --after flags
- Direct codebase inspection - all 3 esptool subprocess calls identified and verified

### Secondary (MEDIUM confidence)
- [ESP32 Forum: pyserial reset behavior](https://esp32.com/viewtopic.php?t=35211) - confirms DTR/RTS toggle causes reset
- [esptool troubleshooting](https://docs.espressif.com/projects/esptool/en/latest/esp32/troubleshooting.html) - RTS/EN pin wiring on various boards

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in requirements.txt, no new deps
- Architecture: HIGH - direct codebase inspection, clear 12-file change list
- Pitfalls: HIGH - known issues from v1.0 experience, esptool source confirms reset sequence

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable domain, no moving targets)
