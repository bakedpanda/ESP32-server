# Phase 7: Setup & Onboarding - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 07-setup-onboarding
**Mode:** --auto (all choices made by Claude using recommended defaults)
**Areas discussed:** setup.sh scope, virtualenv approach, idempotency, README update scope

---

## setup.sh Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full SETUP-01 scope | Clone, venv, pip, dialout group, WiFi prompt, wifi.json, systemd | ✓ |
| Minimal | Deps + service only, skip credential prompting | |

**Auto-selected:** Full SETUP-01 scope
**Notes:** SETUP-01 explicitly requires credential prompting and wifi.json creation — no ambiguity.

---

## Virtualenv Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Repo-local venv (`esp32-station/venv/`) | Consistent with README manual steps | ✓ |
| System-level pip install | Simpler but pollutes global Python | |
| `/opt/` venv | Separates install from code, more "system" feel | |

**Auto-selected:** Repo-local venv
**Notes:** README already documents `python3 -m venv venv` in manual steps — setup.sh should be consistent.

---

## Idempotency

| Option | Description | Selected |
|--------|-------------|----------|
| Idempotent (check before each step) | Re-run safe: skip clone if dir exists, skip dialout if already in group, etc. | ✓ |
| Fresh-only (fail if already installed) | Simpler script, but forces manual cleanup on re-run | |
| Always overwrite | Simpler but risky (overwrites wifi.json on re-run) | |

**Auto-selected:** Idempotent
**Notes:** User may re-run after Pi reinstall or to update. Especially important not to overwrite wifi.json if it already exists with valid credentials.

---

## README Update Scope

| Option | Description | Selected |
|--------|-------------|----------|
| MCP registration only | Just verify/update step 4 with `claude mcp add` command | |
| Full update | MCP registration + tools table (11→15 tools) + architecture diagram | ✓ |

**Auto-selected:** Full update
**Notes:** README tools table shows 11 tools from v1.0; current server has 15. Architecture `tools/` list is missing 4 modules added in Phases 4-6. README is the primary user-facing doc — keeping it accurate is part of SETUP-03's intent.

---

## Claude's Discretion

- Exact wording of prompts and status messages in setup.sh
- Whether to add a `--help` flag or usage header
- Script error handling verbosity
- Final "success" summary format and content

## Deferred Ideas

None.
