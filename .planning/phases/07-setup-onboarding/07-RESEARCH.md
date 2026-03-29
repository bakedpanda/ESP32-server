# Phase 7: Setup & Onboarding - Research

**Researched:** 2026-03-30
**Domain:** Bash shell scripting, systemd service deployment, README documentation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**setup.sh Scope**
- D-01: Full SETUP-01 scope — single script that: clones repo, creates virtualenv, installs pip deps, adds user to `dialout` group, prompts for WiFi credentials interactively, writes `/etc/esp32-station/wifi.json`, copies+enables+starts the systemd service.
- D-02: Idempotent by design — each step checks before acting: skip clone if directory exists, skip pip install if venv up to date, skip dialout if already in group, skip service install if already active. Safe to re-run for updates or debugging.
- D-03: Use repo-local virtualenv at `esp32-station/venv/` — consistent with README manual steps; no global pip pollution.
- D-04: Sudo only where required — `usermod -aG dialout`, `cp *.service /etc/systemd/system/`, `systemctl` calls. Everything else runs as the current user.
- D-05: WiFi credential prompt is required — no skip option. Interactive `read` prompts with `-s` flag for password fields. WebREPL password also prompted (matches credentials format from Phase 6 D-01).
- D-06: Credentials file created at `/etc/esp32-station/wifi.json` with `{"ssid": "...", "password": "...", "webrepl_password": "..."}`, permissions 600. Matches Phase 6 D-01 exactly — setup.sh is the canonical creator.
- D-07: After service start, script prints the MCP endpoint URL (e.g. `http://raspberrypi.local:8000/mcp`) and the `claude mcp add` command to register it — closing the onboarding loop in one session.

**README Update Scope (SETUP-03)**
- D-08: MCP registration section — update or verify Step 4 is accurate: `claude mcp add --transport http esp32-station http://<hostname>:8000/mcp`. Include note about finding the Pi's hostname/IP.
- D-09: Tools table — update to reflect all 15 current MCP tools (README still shows 11 from v1.0). Add Phase 4-6 tools: board health check, board status, mDNS discovery, deploy_boot_config, and any others added since v1.0.
- D-10: Architecture diagram — update `tools/` list to show current modules (credentials.py, boot_deploy.py, board_status.py, mdns_discovery.py added since v1.0 diagram).
- D-11: Setup section — README setup steps should stay in sync with what setup.sh does so users can also do it manually if they prefer.

### Claude's Discretion
- Exact wording of prompts and status messages in setup.sh
- Whether to add a `--help` flag or usage header to setup.sh
- Script error handling verbosity (how much context on failure)
- Whether to print a final "success" summary with next steps

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SETUP-01 | New user can run a single `setup.sh` script that clones the repo, installs dependencies, prompts for WiFi credentials, writes the credentials file, and installs+starts the systemd service | Shell scripting patterns, idempotency techniques, systemd install sequence |
| SETUP-03 | README includes clear instructions for registering the MCP server URL in Claude Code on the main machine | Current tool inventory (15 tools confirmed), `claude mcp add --transport http` syntax verified from mcp_server.py comments |
</phase_requirements>

---

## Summary

Phase 7 is a pure shell scripting and documentation phase. There are no new Python modules, no new MCP tools, and no new dependencies. The deliverables are one new file (`setup.sh` at repo root) and updates to `README.md`.

The codebase is fully built. The systemd service file (`esp32-station.service`) already exists and is correct. The credentials module (`tools/credentials.py`) defines the exact file format and path (`/etc/esp32-station/wifi.json`, keys: `ssid`, `password`, `webrepl_password`, permissions 600) that setup.sh must produce. The MCP server has exactly 15 tools registered — the README tools table currently shows 11 (v1.0 era) and needs updating.

The primary risks in this phase are (1) the systemd service hardcodes `User=esp32` and `WorkingDirectory=/home/esp32/esp32-station` which may not match the actual user running setup.sh, and (2) idempotency edge cases in the shell script that need careful guards.

**Primary recommendation:** Write setup.sh as a defensive bash script with `set -e` at the top, explicit checks before each mutating step, and a clear final summary that prints both the endpoint URL and the `claude mcp add` command.

---

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| bash | system | Script interpreter | Universal on Raspberry Pi OS; `/bin/bash` always present |
| git | system | Repo clone | Already required; user must have git to clone at all |
| python3 | 3.10+ | Virtualenv creation | Required by project; Pi OS ships 3.11 on Bookworm |
| systemd | system | Service management | Required by project constraints |

### No New Library Dependencies

This phase adds no Python packages. All dependencies (`mcp[cli]`, `esptool`, `pyserial`, `mpremote`, `requests`, `zeroconf`) are already in `requirements.txt`. setup.sh simply runs `pip install -r requirements.txt` inside the virtualenv.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| bash script | Python installer script | Python not guaranteed before venv; bash is simpler and avoids bootstrap problem |
| bash script | Ansible/Makefile | Overkill for single-machine setup; adds dependency on user having Ansible |
| Interactive `read` prompts | .env file pre-created by user | User chose interactive prompts (D-05); no skip option |

---

## Architecture Patterns

### setup.sh Structure

```
setup.sh
├── Shebang: #!/usr/bin/env bash
├── set -euo pipefail  (fail fast on any error)
├── Constants (REPO_URL, INSTALL_DIR, SERVICE_NAME, CREDS_PATH)
├── Helper: log() / warn() / die() functions
├── Step 1: Clone or update repo (idempotent)
├── Step 2: Create virtualenv (idempotent)
├── Step 3: Install pip dependencies
├── Step 4: Add current user to dialout group (idempotent)
├── Step 5: Prompt for WiFi credentials (always; -s for passwords)
├── Step 6: Create credentials file (sudo mkdir + tee + chmod)
├── Step 7: Patch service file for current user + path (critical — see Pitfall 1)
├── Step 8: Install and start systemd service (idempotent)
└── Step 9: Print endpoint URL and claude mcp add command
```

### Pattern 1: Idempotent Clone Step

```bash
INSTALL_DIR="$HOME/esp32-station"
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Repository already cloned — pulling latest..."
    git -C "$INSTALL_DIR" pull
else
    git clone https://github.com/bakedpanda/ESP32-server.git "$INSTALL_DIR"
fi
```

**Confidence:** HIGH (standard git idiom)

### Pattern 2: Idempotent Virtualenv Step

```bash
VENV="$INSTALL_DIR/venv"
if [ ! -f "$VENV/bin/python3" ]; then
    python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"
```

**Confidence:** HIGH

### Pattern 3: Idempotent dialout Group

```bash
if ! groups "$USER" | grep -q '\bdialout\b'; then
    sudo usermod -aG dialout "$USER"
    echo "NOTE: Log out and back in (or reboot) for group membership to take effect."
fi
```

**Confidence:** HIGH

### Pattern 4: Silent Password Prompt

```bash
read -rp "WiFi SSID: " WIFI_SSID
read -rsp "WiFi password: " WIFI_PASSWORD
echo
read -rsp "WebREPL password: " WEBREPL_PASSWORD
echo
```

The `echo` after each `-s` prompt restores the newline that silent mode suppresses. **Confidence:** HIGH

### Pattern 5: Credentials File Creation

```bash
sudo mkdir -p /etc/esp32-station
printf '{"ssid": "%s", "password": "%s", "webrepl_password": "%s"}\n' \
    "$WIFI_SSID" "$WIFI_PASSWORD" "$WEBREPL_PASSWORD" \
    | sudo tee /etc/esp32-station/wifi.json > /dev/null
sudo chmod 600 /etc/esp32-station/wifi.json
```

This matches exactly what `tools/credentials.py` expects: path `/etc/esp32-station/wifi.json`, keys `ssid`/`password`/`webrepl_password`, file permissions 600.

**Confidence:** HIGH (verified against `tools/credentials.py` source)

### Pattern 6: Systemd Service Install (Idempotent)

```bash
SERVICE_SRC="$INSTALL_DIR/esp32-station.service"
SERVICE_DST="/etc/systemd/system/esp32-station.service"

sudo cp "$SERVICE_SRC" "$SERVICE_DST"
sudo systemctl daemon-reload
sudo systemctl enable esp32-station
sudo systemctl restart esp32-station
```

Using `restart` instead of `start` makes this idempotent — works for both first install and re-runs. **Confidence:** HIGH

### Pattern 7: Final Endpoint Print

```bash
HOSTNAME=$(hostname)
echo ""
echo "Setup complete. MCP server running at:"
echo "  http://${HOSTNAME}.local:8000/mcp"
echo ""
echo "On your main machine, register with Claude Code:"
echo "  claude mcp add --transport http esp32-station http://${HOSTNAME}.local:8000/mcp"
echo ""
echo "If hostname resolution fails, replace ${HOSTNAME}.local with the Pi's IP address."
```

**Confidence:** HIGH — matches D-07 exactly.

### Anti-Patterns to Avoid

- **Global pip install:** Never run `pip install` outside the venv. setup.sh must always use `$VENV/bin/pip`.
- **Using `sudo pip`:** This breaks the venv and can pollute system Python.
- **Hardcoding user in service file:** The service file has `User=esp32` and `WorkingDirectory=/home/esp32/esp32-station`. If setup.sh is run by a different user, the service will fail silently. See Pitfall 1.
- **Leaving password in shell history:** `read -s` suppresses echo but the variable is in environment during script execution. Do not `export` the credentials variables. They go directly into the credentials file and are then unset.

---

## Critical Issue: Service File User Mismatch

**This is the most important finding in this research.**

`esp32-station.service` hardcodes:

```
User=esp32
WorkingDirectory=/home/esp32/esp32-station
ExecStart=/home/esp32/esp32-station/venv/bin/python3 /home/esp32/esp32-station/mcp_server.py
```

If the user running setup.sh is not `esp32` (e.g., `pi`, `ubuntu`, `chris`), the service will fail with a "working directory not accessible" or "executable not found" error.

**setup.sh must patch these values before copying the service file.** The patch must use `sed` to substitute `esp32` with `$USER` and `/home/esp32` with `$HOME`:

```bash
sed -e "s|User=esp32|User=${USER}|g" \
    -e "s|/home/esp32|${HOME}|g" \
    "$SERVICE_SRC" | sudo tee "$SERVICE_DST" > /dev/null
```

**Confidence:** HIGH — verified by reading `esp32-station.service` directly.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON credentials file | Custom serializer | `printf '{"ssid": "%s", ...}'` | stdlib printf is sufficient for flat JSON; no arrays or nested objects needed |
| Service management | Custom daemon | systemd (already in project) | Already the chosen approach |
| Dependency install | Version checking | `pip install -r requirements.txt` | pip handles versioning via requirements.txt pins |

---

## Common Pitfalls

### Pitfall 1: Service File User Mismatch (CRITICAL)
**What goes wrong:** `systemctl start esp32-station` fails because `User=esp32` doesn't exist; service shows as failed immediately.
**Why it happens:** Service file was written for a specific username `esp32`. setup.sh runs as a different user (`pi`, `ubuntu`, etc.).
**How to avoid:** sed-patch the service file during install to substitute the actual `$USER` and `$HOME`. Do not copy raw.
**Warning signs:** `systemctl status esp32-station` shows `status=203/EXEC` or `No such file or directory`.

### Pitfall 2: dialout Group Requires Re-login
**What goes wrong:** Even after `usermod -aG dialout`, serial tools fail with permission denied in the same session.
**Why it happens:** Group membership is evaluated at login; `usermod` changes the stored group but not the running session.
**How to avoid:** setup.sh should print a clear notice: "You must log out and back in (or reboot) for dialout group to take effect. The MCP service runs as your user and will have access on next boot."
**Warning signs:** `groups` command does not show `dialout` in current session even after `usermod`.

### Pitfall 3: Special Characters in WiFi Credentials
**What goes wrong:** `printf` interpolation breaks if SSID or password contains `%`, `"`, or `\`.
**Why it happens:** Shell variables in printf format strings are interpreted.
**How to avoid:** Use Python or `jq` to produce the JSON safely, or use `printf '%s'` with explicit argument passing and avoid format string injection. Alternatively, use a Python one-liner:
```bash
"$VENV/bin/python3" -c "
import json, pathlib, sys
data = {'ssid': sys.argv[1], 'password': sys.argv[2], 'webrepl_password': sys.argv[3]}
print(json.dumps(data))
" "$WIFI_SSID" "$WIFI_PASSWORD" "$WEBREPL_PASSWORD" | sudo tee /etc/esp32-station/wifi.json > /dev/null
```
This is safe against all special characters. **Recommended approach.**

### Pitfall 4: set -e Exits on grep/groups Return Code
**What goes wrong:** `set -e` causes the script to exit when `groups $USER | grep -q dialout` returns 1 (not found) on a fresh system.
**Why it happens:** `grep -q` returns exit code 1 when no match found; `set -e` treats any non-zero exit as fatal.
**How to avoid:** Use `if` guards (which suppress exit-on-error for the condition) or temporarily disable `set -e` with `set +e` around the check.

### Pitfall 5: Re-run Prompts Existing Credentials
**What goes wrong:** On re-run, setup.sh overwrites `/etc/esp32-station/wifi.json` with newly entered credentials, which the user may not want.
**Why it happens:** No check for existing credentials file.
**How to avoid:** Check if credentials file already exists and ask user whether to overwrite:
```bash
if [ -f /etc/esp32-station/wifi.json ]; then
    read -rp "Credentials file already exists. Overwrite? [y/N]: " OVERWRITE
    [[ "$OVERWRITE" =~ ^[Yy]$ ]] || { echo "Keeping existing credentials."; SKIP_CREDS=1; }
fi
```

### Pitfall 6: README Tools Table Out of Date
**What goes wrong:** User reads README tools table and believes there are 11 tools; tries to use a tool that exists but isn't documented.
**Why it happens:** README was written at v1.0 (11 tools); 4 more tools added in phases 5 and 6.
**How to avoid:** Update the tools table to show all 15 tools exactly matching `mcp_server.py` registration order. Verified tool count: 15 (confirmed by `test_new_tools_registered` in tests).

---

## README Delta — What Needs Updating

### Current README State (verified by reading file)

| Section | Current State | Required State |
|---------|--------------|----------------|
| Tools table | 11 tools (v1.0) | 15 tools |
| Architecture diagram `tools/` list | 7 modules | 11 modules |
| Setup section | Steps 1-4 (manual only) | Add setup.sh as primary path, manual as fallback |
| Status table | Phases 1-3 only | Add Phases 4-6 (or consolidate) |

### Missing Tools (must add to README table)

From `mcp_server.py` vs README tools table:

| Tool | Phase Added | Missing from README |
|------|-------------|---------------------|
| `get_board_status` | Phase 5 | YES |
| `check_board_health` | Phase 5 | YES |
| `discover_boards` | Phase 5 | YES |
| `deploy_boot_config` | Phase 6 | YES |

### Missing Architecture Modules

Current README architecture lists 7 `tools/` files. Current actual modules:

```
tools/
├── board_detection.py    (in README)
├── firmware_flash.py     (in README)
├── file_deploy.py        (in README)
├── repl.py               (in README)
├── serial_lock.py        (in README)
├── ota_wifi.py           (in README)
├── github_deploy.py      (in README)
├── board_status.py       (MISSING from README)
├── webrepl_cmd.py        (MISSING from README)
├── mdns_discovery.py     (MISSING from README)
├── credentials.py        (MISSING from README)
└── boot_deploy.py        (MISSING from README)
```

### MCP Registration Step (D-08)

The existing README Step 4 already shows the correct command:
```
claude mcp add --transport http esp32-station http://raspberrypi.local:8000/mcp
```
This matches the canonical form in D-08. The only update needed: add a note that `raspberrypi.local` is the default Pi hostname and to substitute the actual hostname or IP address.

---

## Code Examples

### Verified: Credentials File Format Expected by tools/credentials.py

```python
# From tools/credentials.py (source: read directly)
CREDENTIALS_PATH = pathlib.Path("/etc/esp32-station/wifi.json")
REQUIRED_KEYS = {"ssid", "password", "webrepl_password"}
```

setup.sh must write exactly these keys. The file must exist at exactly this path. Permissions 600 are not enforced by code but are documented in Phase 6 D-01.

### Verified: `claude mcp add` Syntax

From comment in `mcp_server.py` line 8:
```
claude mcp add --transport http esp32-station http://raspberrypi.local:8000/mcp
```

This is the authoritative form. The `--transport http` flag is required (SSE is deprecated). The server listens on `0.0.0.0:8000` with path `/mcp`.

### Verified: Service File Paths to Patch

```
# esp32-station.service (read directly)
User=esp32
WorkingDirectory=/home/esp32/esp32-station
ExecStart=/home/esp32/esp32-station/venv/bin/python3 /home/esp32/esp32-station/mcp_server.py
```

All three lines reference `esp32` and `/home/esp32`. All three must be patched by setup.sh.

---

## Runtime State Inventory

Step 2.6: SKIPPED (no rename/refactor involved — this phase creates new files only)

---

## Environment Availability

The script targets Raspberry Pi OS (Bookworm / Debian-based). The following are expected to be present on a fresh Pi:

| Dependency | Required By | Availability | Notes |
|------------|------------|--------------|-------|
| bash | setup.sh shebang | Always present on Pi OS | `/bin/bash` standard |
| git | clone step | Present on Pi OS Bookworm by default; may need `apt install git` on minimal images | setup.sh should check and error clearly |
| python3 | virtualenv creation | Pi OS Bookworm ships 3.11 | Must be >= 3.10 per project constraints |
| python3-venv | `python3 -m venv` | **Not always installed separately on Debian** — may need `apt install python3-venv` | Most common failure point on fresh Pi |
| sudo | privilege escalation | Always present | setup.sh assumes sudo access |
| systemd | service management | Always present on Pi OS | Pi OS uses systemd |
| internet access | git clone, pip install | User's network — not verifiable by script | Script will fail clearly if clone/pip fails |

**Key risk:** `python3-venv` package is not installed by default on all Debian/Raspberry Pi OS images. setup.sh should test for venv capability before attempting creation:

```bash
if ! python3 -c "import venv" 2>/dev/null; then
    echo "python3-venv not available. Install with: sudo apt install python3-venv"
    exit 1
fi
```

---

## Validation Architecture

nyquist_validation is enabled in config.json.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.x |
| Config file | `pytest.ini` (testpaths = tests, asyncio_mode = auto) |
| Quick run command | `source venv/bin/activate && pytest tests/test_mcp_server.py -x -q` |
| Full suite command | `source venv/bin/activate && pytest` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SETUP-01 | setup.sh exists at repo root, is executable, contains required steps | unit/file check | `pytest tests/test_setup_script.py -x` | No — Wave 0 gap |
| SETUP-03 | README contains all 15 tool names and updated architecture | unit/file check | `pytest tests/test_readme.py -x` | No — Wave 0 gap |

**Note:** setup.sh itself cannot be integration-tested in unit tests (it runs as root, requires network, modifies system state). Tests should verify the script's content/structure and the README's content.

### Wave 0 Gaps

- [ ] `tests/test_setup_script.py` — covers SETUP-01: verify setup.sh exists, is executable (`os.access`), contains required patterns (idempotency checks, credential prompt, systemd commands, endpoint print)
- [ ] `tests/test_readme.py` — covers SETUP-03: verify README contains all 15 tool names, updated architecture modules, MCP registration command

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| SSE transport | Streamable HTTP (`--transport http`) | SSE deprecated in Claude Code as of 2025 |
| `esptool.py` command | `esptool` command | v5+ changed binary name |
| Manual README + install | setup.sh + README | This phase creates setup.sh |

---

## Open Questions

1. **Does the user running setup.sh own `$HOME/esp32-station` or should the script install to a different path?**
   - What we know: README shows `git clone ... esp32-station && cd esp32-station` — implies `$HOME/esp32-station`
   - What's unclear: Whether setup.sh should default to `$HOME/esp32-station` or allow a custom path
   - Recommendation: Default to `$HOME/esp32-station`, document this in the script header. No need for a `--dir` flag (Claude's discretion area).

2. **Should setup.sh handle the case where the repo is already cloned in a different path?**
   - What we know: Idempotency requires checking for existing clone (D-02)
   - What's unclear: Whether to search for existing installs or just check the default path
   - Recommendation: Check only the default path. If a different path exists, the script will attempt a new clone and the user can sort it out. Keep it simple.

3. **Should the README status table be updated to include Phases 4-6?**
   - What we know: Current status table only lists Phases 1-3. Phases 4-6 are complete.
   - Recommendation: Yes, add rows for Phases 4-6. This is within SETUP-03 scope (D-09/D-10/D-11).

---

## Project Constraints (from CLAUDE.md)

No project-level CLAUDE.md found at repo root. Global CLAUDE.md has no ESP32-specific directives. Project conventions derived from codebase inspection:

- Error returns: `{"error": "snake_case_code", "detail": "human string"}` — never raise (Python tools only; not applicable to shell script)
- All tool modules in `tools/`; thin `@mcp.tool()` wrappers in `mcp_server.py` (not applicable to this phase — no new tools)
- Virtualenv at `esp32-station/venv/` (D-03 — must match in setup.sh)
- Credentials path: `/etc/esp32-station/wifi.json`, permissions 600 (D-06 — must match exactly)
- No WiFi credentials in conversation (memory directive — confirmed: setup.sh handles credentials locally, never through Claude)

---

## Sources

### Primary (HIGH confidence)
- `tools/credentials.py` — verified credentials path, key names, permission requirements
- `esp32-station.service` — verified hardcoded User/WorkingDirectory/ExecStart values
- `mcp_server.py` — verified 15 tools, `claude mcp add` command, endpoint path
- `README.md` — verified current state (11 tools, 7 architecture modules, 4 setup steps)
- `requirements.txt` — verified no new dependencies needed
- `.planning/phases/07-setup-onboarding/07-CONTEXT.md` — all locked decisions
- `.planning/phases/06-provisioning/06-CONTEXT.md` — D-01 credentials format

### Secondary (MEDIUM confidence)
- Standard bash scripting idioms for idempotency — well-established patterns
- `python3-venv` package availability on Raspberry Pi OS Bookworm — verified from general Debian knowledge; user should test on target machine

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; bash + existing tooling
- Architecture: HIGH — shell script structure is well-understood; service file issue verified by direct file read
- Pitfalls: HIGH — service file user mismatch and python3-venv verified by direct inspection; special characters in credentials is a known bash pitfall

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable domain — bash, systemd, mDNS all stable)
