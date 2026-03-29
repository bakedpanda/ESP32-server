---
phase: 7
slug: setup-onboarding
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash (manual smoke test) + pytest for credential file validation |
| **Config file** | none |
| **Quick run command** | `bash -n setup.sh` |
| **Full suite command** | `bash -n setup.sh && grep -c "esp32_station_url" README.md` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `bash -n setup.sh`
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 7-01-01 | 01 | 1 | SETUP-01 | syntax | `bash -n setup.sh` | ❌ W0 | ⬜ pending |
| 7-01-02 | 01 | 1 | SETUP-01 | file | `test -f setup.sh` | ❌ W0 | ⬜ pending |
| 7-02-01 | 02 | 2 | SETUP-03 | grep | `grep -c "MCP server" README.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `setup.sh` — does not exist yet, must be created in Wave 1

*Existing README infrastructure covers Wave 2 requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| setup.sh runs on fresh Pi, prompts for WiFi, writes credentials, starts service | SETUP-01 | Requires real hardware and interactive input | Run on a fresh Pi OS install; verify `/home/$USER/.esp32_credentials.json` is created and `systemctl status esp32-station` shows active |
| Service starts correctly after setup.sh patches user in service file | SETUP-01 | Requires systemd on real Pi | After `setup.sh` completes, run `systemctl status esp32-station` — expect `Active: active (running)` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
