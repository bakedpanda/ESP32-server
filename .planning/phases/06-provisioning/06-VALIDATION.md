---
phase: 6
slug: provisioning
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini (exists) |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | SETUP-02 | unit | `python -m pytest tests/test_credentials.py -v` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | PROV-01 | unit | `python -m pytest tests/test_firmware_flash.py -v -k erase` | ✅ | ⬜ pending |
| 06-02-01 | 02 | 1 | PROV-02 | unit | `python -m pytest tests/test_boot_config.py -v` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 1 | PROV-03 | unit | `python -m pytest tests/test_boot_config.py -v -k guidance` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 2 | PROV-04 | integration | `python -m pytest tests/test_mcp_server.py -v -k deploy_boot` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_credentials.py` — stubs for SETUP-02 (load_credentials, missing file error)
- [ ] `tests/test_boot_config.py` — stubs for PROV-02, PROV-03 (template fill, deploy, guidance)

*Existing test infrastructure (pytest, conftest) already in place from prior phases.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| BOOT button hold during flash | PROV-03 | Physical hardware interaction | Flash a board, verify user_action text appears before erase step |
| Power cycle after flash | PROV-03 | Physical hardware interaction | Complete flash, verify power cycle guidance appears |
| WiFi connection after boot.py deploy | PROV-02 | Requires physical board + WiFi network | Deploy boot.py, power cycle board, verify it connects to WiFi |
| mDNS hostname discovery | PROV-02 | Requires board on network | Deploy boot.py with hostname, run discover_boards(), verify hostname appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
