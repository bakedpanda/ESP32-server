---
phase: 07-setup-onboarding
verified: 2026-03-30T02:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 7: Setup & Onboarding Verification Report

**Phase Goal:** A new user can go from bare Pi to working dev station with one script and clear documentation
**Verified:** 2026-03-30T02:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Running setup.sh on a fresh Pi clones the repo, installs all dependencies, prompts for WiFi credentials, writes the credentials file, and installs+starts the systemd service | VERIFIED | setup.sh exists, executable (-rwxr-xr-x), passes bash -n, contains all 9 steps; all 20 test_setup_script.py tests pass |
| 2 | README contains clear instructions for registering the MCP server URL in Claude Code on the main machine | VERIFIED | README.md contains `claude mcp add --transport http esp32-station`, hostname substitution note, and setup.sh as primary path; all 32 test_readme.py tests pass |
| 3 | setup.sh is idempotent — re-running does not prompt for credentials again if file exists, does not fail if venv already created, does not fail if service already running | VERIFIED | Lines 72-77: credentials overwrite guard; lines 46-52: venv existence check; line 120: `systemctl restart` (idempotent) |
| 4 | WiFi credentials are written to /etc/esp32-station/wifi.json with keys ssid/password/webrepl_password and permissions 600 | VERIFIED | Lines 96-100: Python json.dumps with correct keys piped to sudo tee $CREDS_PATH; line 100: sudo chmod 600 |
| 5 | The service file is patched to use the actual $USER and $HOME before being installed | VERIFIED | Lines 114-116: sed substitution of User=esp32 and /home/esp32 before sudo tee to /etc/systemd/system/esp32-station.service |
| 6 | After service start, the MCP endpoint URL and claude mcp add command are printed to stdout | VERIFIED | Lines 141-145: prints http://${HOSTNAME}.local:8000/mcp and `claude mcp add --transport http esp32-station ...` |
| 7 | README MCP Tools table lists all 15 current tools and Architecture section lists all 12 modules | VERIFIED | README.md lines 95-131: 15-row tools table and 12-module architecture block; parametrized pytest confirms each by name |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `setup.sh` | One-command Pi onboarding script (min 100 lines, contains set -euo pipefail) | VERIFIED | 152 lines, executable, bash -n passes, contains set -euo pipefail and all 9 steps |
| `setup.sh` | Idempotent steps with pre-flight checks (contains `[ -d`) | VERIFIED | Lines 34, 47, 61, 73: directory/file/group checks before every mutating step |
| `tests/test_setup_script.py` | Structural content tests for setup.sh (20 test functions) | VERIFIED | 20 tests, all pass; covers shebang, idempotency, credential prompts, file paths, service patching, output |
| `tests/test_readme.py` | Content tests for README.md (parametrized 15 tools + 12 modules + 5 structural) | VERIFIED | 32 tests total, all pass |
| `README.md` | v1.1 documentation with deploy_boot_config and setup.sh reference | VERIFIED | Contains all 15 tool names, 12 architecture modules, setup.sh quick-start, phases 4-7 status table |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| setup.sh credentials step | /etc/esp32-station/wifi.json | python3 -c json.dumps piped to sudo tee | WIRED | Line 95-99: Python one-liner builds JSON with correct keys, pipes to `sudo tee "$CREDS_PATH"` |
| setup.sh service step | /etc/systemd/system/esp32-station.service | sed substitution then sudo tee | WIRED | Lines 114-116: `sed -e "s\|User=esp32\|User=${USER}\|g" -e "s\|/home/esp32\|${HOME}\|g" "$SERVICE_SRC" \| sudo tee "$SERVICE_DST"` |
| tests/test_setup_script.py | setup.sh | pathlib.Path('setup.sh').read_text() | WIRED | Line 10: `return SETUP_SH.read_text()` where SETUP_SH = pathlib.Path("setup.sh") |
| tests/test_readme.py | README.md | pathlib.Path('README.md').read_text() | WIRED | Line 9: `return README.read_text()` where README = pathlib.Path("README.md") |

### Data-Flow Trace (Level 4)

Not applicable. setup.sh and README.md are static artifacts (a shell script and documentation file), not dynamic data-rendering components. No data-flow trace required.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| bash -n syntax check on setup.sh | `bash -n setup.sh` | "syntax OK" | PASS |
| setup.sh is executable | `ls -la setup.sh` | `-rwxr-xr-x` | PASS |
| All 20 setup.sh structural tests pass | pytest tests/test_setup_script.py -v | 20 passed | PASS |
| All 32 README content tests pass | pytest tests/test_readme.py -v | 32 passed | PASS |
| Combined test run | pytest tests/test_setup_script.py tests/test_readme.py | 52 passed, 0 failed | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SETUP-01 | 07-01-PLAN.md, 07-02-PLAN.md | New user can run setup.sh: clone, deps, WiFi credentials, systemd service install+start | SATISFIED | setup.sh implements all steps; 20 structural tests pass; bash -n exits 0; file is executable |
| SETUP-03 | 07-01-PLAN.md, 07-03-PLAN.md | README includes clear MCP server registration instructions | SATISFIED | README.md contains `claude mcp add --transport http esp32-station`, hostname note, setup.sh primary path; 32 test_readme.py tests pass |

**ROADMAP note:** ROADMAP.md shows "2/3 plans executed" with 07-03-PLAN.md marked `[ ]`. This is a documentation inconsistency — commit `20aa959` (feat(07-03)) and `caf464f` (docs(07-03)) confirm 07-03 executed fully, and all tests and artifacts reflect its completion. The ROADMAP checkbox was not updated after the worktree merge. This does not affect requirement coverage.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

No anti-patterns found. setup.sh has no TODO/FIXME/placeholder markers, no empty implementations, and no stub patterns. README.md is fully populated.

### Human Verification Required

#### 1. End-to-end setup.sh execution on a fresh Raspberry Pi

**Test:** Run `bash setup.sh` on a fresh Pi (or wipe /etc/esp32-station, remove venv, and re-run)
**Expected:** Script completes without error, prompts for WiFi credentials, writes /etc/esp32-station/wifi.json, starts esp32-station.service, prints the `claude mcp add` command with the Pi's actual hostname
**Why human:** Cannot run systemctl, sudo operations, or interactive prompts programmatically in this environment

#### 2. MCP registration round-trip

**Test:** Copy the printed `claude mcp add --transport http esp32-station http://<hostname>.local:8000/mcp` command and run it on the main machine after setup completes
**Expected:** Claude Code recognizes the esp32-station server and can invoke MCP tools
**Why human:** Requires a running Pi with the service active, and a Claude Code installation to test MCP registration against

#### 3. Idempotent re-run behavior

**Test:** Run `bash setup.sh` a second time on an already-configured Pi
**Expected:** Script completes without error; asks "Overwrite existing credentials? [y/N]" and skips credential steps on N; does not fail on existing venv or running service
**Why human:** Interactive prompt behavior cannot be verified without a live terminal session

### Gaps Summary

No gaps found. All phase artifacts exist, are substantive, are wired, and produce correct output as verified by 52 passing tests and direct bash syntax validation.

---

_Verified: 2026-03-30T02:00:00Z_
_Verifier: Claude (gsd-verifier)_
