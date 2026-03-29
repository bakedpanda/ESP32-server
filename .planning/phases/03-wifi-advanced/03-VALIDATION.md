---
phase: 3
slug: wifi-advanced
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (configured in `pytest.ini`) |
| **Config file** | `pytest.ini` (testpaths = tests, asyncio_mode = auto) |
| **Quick run command** | `venv/bin/pytest tests/test_ota_wifi.py tests/test_github_deploy.py -x` |
| **Full suite command** | `venv/bin/pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `venv/bin/pytest tests/test_ota_wifi.py tests/test_github_deploy.py -x`
- **After every plan wave:** Run `venv/bin/pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | OTA-01 | unit | `venv/bin/pytest tests/test_ota_wifi.py -x` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 0 | OTA-02 | unit | `venv/bin/pytest tests/test_ota_wifi.py -x` | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 0 | DEPLOY-05 | unit | `venv/bin/pytest tests/test_github_deploy.py -x` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | OTA-01 | unit | `venv/bin/pytest tests/test_ota_wifi.py::test_deploy_ota_wifi_success -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | OTA-01 | unit | `venv/bin/pytest tests/test_ota_wifi.py::test_deploy_ota_wifi_too_large -x` | ❌ W0 | ⬜ pending |
| 3-02-03 | 02 | 1 | OTA-02 | unit | `venv/bin/pytest tests/test_ota_wifi.py::test_deploy_ota_wifi_timeout -x` | ❌ W0 | ⬜ pending |
| 3-02-04 | 02 | 1 | OTA-02 | unit | `venv/bin/pytest tests/test_ota_wifi.py::test_deploy_ota_wifi_connection_error -x` | ❌ W0 | ⬜ pending |
| 3-02-05 | 02 | 1 | OTA-01 | unit | `venv/bin/pytest tests/test_ota_wifi.py::test_webrepl_cli_missing -x` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 2 | DEPLOY-05 | unit | `venv/bin/pytest tests/test_github_deploy.py::test_pull_and_deploy_success -x` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 2 | DEPLOY-05 | unit | `venv/bin/pytest tests/test_github_deploy.py::test_git_clone_timeout -x` | ❌ W0 | ⬜ pending |
| 3-03-03 | 03 | 2 | DEPLOY-05 | unit | `venv/bin/pytest tests/test_github_deploy.py::test_token_not_leaked -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_ota_wifi.py` — stubs for OTA-01, OTA-02
- [ ] `tests/test_github_deploy.py` — stubs for DEPLOY-05
- [ ] Install dependencies: `python3 -m venv venv && venv/bin/pip install -r requirements.txt`
- [ ] Vendor webrepl_cli.py: `mkdir -p tools/vendor && curl -o tools/vendor/webrepl_cli.py https://raw.githubusercontent.com/micropython/webrepl/master/webrepl_cli.py`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WebREPL file transfer reaches a real ESP32 | OTA-01 | Requires physical hardware + WiFi network | Connect ESP32 to WiFi, enable WebREPL, call `deploy_ota_wifi` with board IP |
| USB fallback triggers when WiFi unavailable | OTA-02 | Requires real timeout condition | Unplug ESP32 from network, call `deploy_ota_wifi`, verify USB fallback hint in response |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
