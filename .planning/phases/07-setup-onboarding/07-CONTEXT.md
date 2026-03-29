# Phase 7: Setup & Onboarding - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

A new user can go from bare Pi to working dev station with one script and clear documentation. Deliverables:
1. `setup.sh` — single command that clones the repo, installs deps, prompts for WiFi credentials, writes credentials file, and installs+starts the systemd service (SETUP-01)
2. README update — clear instructions for registering the MCP server URL in Claude Code on the main machine, plus updated tools table and architecture diagram to reflect current state (SETUP-03)

Out of scope: REL-01/02/03 (Phase 4 plan 2 — hardware reset, --chip enforcement), fleet management, web UI.

</domain>

<decisions>
## Implementation Decisions

### setup.sh Scope
- **D-01:** Full SETUP-01 scope — single script that: clones repo, creates virtualenv, installs pip deps, adds user to `dialout` group, prompts for WiFi credentials interactively, writes `/etc/esp32-station/wifi.json`, copies+enables+starts the systemd service.
- **D-02:** Idempotent by design — each step checks before acting: skip clone if directory exists, skip pip install if venv up to date, skip dialout if already in group, skip service install if already active. Safe to re-run for updates or debugging.
- **D-03:** Use repo-local virtualenv at `esp32-station/venv/` — consistent with README manual steps; no global pip pollution.
- **D-04:** Sudo only where required — `usermod -aG dialout`, `cp *.service /etc/systemd/system/`, `systemctl` calls. Everything else runs as the current user.
- **D-05:** WiFi credential prompt is required — no skip option. Interactive `read` prompts with `-s` flag for password fields. WebREPL password also prompted (matches credentials format from Phase 6 D-01).
- **D-06:** Credentials file created at `/etc/esp32-station/wifi.json` with `{"ssid": "...", "password": "...", "webrepl_password": "..."}`, permissions 600. Matches Phase 6 D-01 exactly — setup.sh is the canonical creator.
- **D-07:** After service start, script prints the MCP endpoint URL (e.g. `http://raspberrypi.local:8000/mcp`) and the `claude mcp add` command to register it — closing the onboarding loop in one session.

### README Update Scope (SETUP-03)
- **D-08:** MCP registration section — update or verify Step 4 is accurate: `claude mcp add --transport http esp32-station http://<hostname>:8000/mcp`. Include note about finding the Pi's hostname/IP.
- **D-09:** Tools table — update to reflect all 15 current MCP tools (README still shows 11 from v1.0). Add Phase 4-6 tools: board health check, board status, mDNS discovery, deploy_boot_config, and any others added since v1.0.
- **D-10:** Architecture diagram — update `tools/` list to show current modules (credentials.py, boot_deploy.py, board_status.py, mdns_discovery.py added since v1.0 diagram).
- **D-11:** Setup section — README setup steps should stay in sync with what setup.sh does so users can also do it manually if they prefer.

### Claude's Discretion
- Exact wording of prompts and status messages in setup.sh
- Whether to add a `--help` flag or usage header to setup.sh
- Script error handling verbosity (how much context on failure)
- Whether to print a final "success" summary with next steps

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — SETUP-01, SETUP-03 (the two requirements this phase covers)

### Phase 6 Decisions (must match exactly)
- `.planning/phases/06-provisioning/06-CONTEXT.md` — D-01: credentials file path/format/permissions; D-06: error message format when credentials missing

### Existing Files to Update
- `README.md` — current state; update tools table and architecture; verify MCP registration step
- `esp32-station.service` — systemd unit file; setup.sh copies this to `/etc/systemd/system/`

### Project Context
- `.planning/PROJECT.md` — core value, constraints, current tool count (15 tools)
- `.planning/REQUIREMENTS.md` — traceability table shows SETUP-01 and SETUP-03 in Phase 7

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `esp32-station.service` — systemd unit file; setup.sh installs this; no changes needed to the file itself
- `requirements.txt` — pip deps; setup.sh runs `pip install -r requirements.txt` in venv
- `tools/credentials.py` — validates `/etc/esp32-station/wifi.json`; setup.sh creates the file this module reads

### Established Patterns
- README manual steps (clone → venv → pip → dialout → systemd → mcp add) define the expected setup.sh flow
- Error dict pattern irrelevant here (setup.sh is a shell script, not an MCP tool)
- No existing setup automation — this is net-new

### Integration Points
- `setup.sh` sits at repo root; invoked by new user via `curl | bash` or `git clone && ./setup.sh`
- README Setup section is the entry point — should reference setup.sh as the primary path, manual steps as fallback

</code_context>

<specifics>
## Specific Ideas

- setup.sh should print the `claude mcp add` command at the end so the user can copy-paste it immediately — closes the onboarding loop without switching to the README
- Idempotent re-runs are important: user may run setup.sh again after a Pi reinstall or to update an existing installation

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-setup-onboarding*
*Context gathered: 2026-03-30*
