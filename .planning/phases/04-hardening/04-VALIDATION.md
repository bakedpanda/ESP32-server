---
phase: 4
slug: hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=7.0 (in venv on Pi) |
| **Config file** | `pytest.ini` (testpaths=tests) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 0 | REL-01 | unit | `pytest tests/test_repl.py::test_hard_reset_uses_dtr_rts -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 0 | REL-02 | unit | `pytest tests/test_repl.py::test_hard_reset_fallback_message -x` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 0 | REL-03 | unit | `pytest tests/test_flash.py::test_esptool_calls_include_chip_flag -x` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 0 | DEBT-02 | unit | `pytest tests/test_mcp_server.py::test_systemd_no_stale_comments -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | REL-01 | unit | `pytest tests/test_repl.py::test_hard_reset_uses_dtr_rts -x` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | REL-02 | unit | `pytest tests/test_repl.py::test_hard_reset_fallback_message -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 1 | REL-03 | unit | `pytest tests/test_flash.py::test_esptool_calls_include_chip_flag -x` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 2 | DEBT-01 | unit | `pytest tests/test_board_detect.py::test_detect_chip_success -x` | ✅ exists | ⬜ pending |
| 04-04-02 | 04 | 2 | DEBT-03 | unit | `pytest tests/test_mcp_server.py::test_new_tools_registered -x` | ✅ exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_repl.py::test_hard_reset_uses_dtr_rts` — mock pyserial, verify setRTS calls (REL-01)
- [ ] `tests/test_repl.py::test_hard_reset_fallback_message` — mock serial.Serial to raise, verify fallback key (REL-02)
- [ ] `tests/test_flash.py::test_esptool_calls_include_chip_flag` — verify --chip in subprocess args (REL-03)
- [ ] `tests/test_mcp_server.py::test_systemd_no_stale_comments` — verify line 1 is not a comment (DEBT-02)

*Existing infrastructure covers DEBT-01 and DEBT-03 (tests exist, need fix/update).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Board actually restarts after DTR/RTS reset | REL-01 | Requires physical ESP32 board connected via USB | 1. Deploy a file, 2. Observe board LED sequence showing reboot, 3. Verify MicroPython REPL responds after reset |
| Native USB boards get fallback prompt | REL-02 | Requires ESP32-S2/S3 with native USB (no UART bridge) | 1. Connect native USB board, 2. Deploy, 3. Verify fallback message appears when RTS has no effect |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
