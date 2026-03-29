# ESP32 MicroPython Dev Station

## What This Is

A Raspberry Pi-based development server for managing ESP32 boards running MicroPython. It handles full provisioning (flashing firmware + deploying code) via USB and OTA updates over WiFi, with serial/REPL access to connected boards. Claude on the main machine drives the whole thing through an MCP server with 11 tools.

## Core Value

Claude can flash, deploy, and debug any connected ESP32 without the user having to leave their editor or remember tooling commands.

## Current State

Shipped v1.0 MVP with 2,446 LOC Python across 11 MCP tools. All 24 v1 requirements satisfied.
Tech stack: FastMCP, esptool, mpremote, webrepl_cli.py, git subprocess.
Deployed on Raspberry Pi at 192.168.10.123 as systemd service.

## Requirements

### Validated (v1.0)

- Flash MicroPython firmware onto ESP32 boards via USB (5 variants) — v1.0
- Expose all capabilities as MCP server over LAN — v1.0
- Deploy files/directories to ESP32 via USB serial — v1.0
- Read serial output and run REPL commands — v1.0
- Per-port serial locking for concurrent safety — v1.0
- Deploy files to ESP32 via OTA WiFi (WebREPL) — v1.0
- Pull project code from GitHub and deploy — v1.0

### Active

(None — next milestone requirements TBD)

### Out of Scope

- Fleet management / multi-board inventory — single board at a time for now
- Web UI — Claude is the interface, no dashboard needed
- Authentication/security hardening — trusted LAN only
- Non-MicroPython firmware (Arduino, ESP-IDF, Zephyr, etc.)

## Context

- **Hardware**: Raspberry Pi on the same LAN as the main dev machine; ESP32 boards connected via USB serial
- **Firmware source**: MicroPython official releases (esptool for flashing)
- **Code source**: Main machine → GitHub → Pi → ESP32; Pi pulls from GitHub to deploy
- **User**: Tinkering and experimenting with mixed ESP32 variants, sensor/control projects
- **Claude access**: MCP server is the primary interface — Claude should be able to do everything without copy-pasting output
- **Known issues**: Soft reset unreliable on ESP32 classic; esptool auto-detect should enforce explicit --chip

## Constraints

- **Platform**: Raspberry Pi (Linux/ARM) — Pi-compatible tooling only
- **Connectivity**: LAN only — no internet-facing exposure required
- **Boards**: Mixed ESP32 variants — must auto-detect chip type for correct firmware selection
- **Protocol**: MCP server for Claude integration (preferred over REST API for direct tool use)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| MCP server over REST API | Allows Claude to call tools directly without user copying output | ✓ Implemented — streamable-http on port 8000 |
| Pi as deployment hub | Centralizes USB connections and WiFi bridge; main machine stays clean | ✓ Implemented — systemd daemon, auto-start on boot |
| GitHub as code source | User's existing workflow; Pi pulls latest from repo to deploy | ✓ Implemented — pull_and_deploy_github MCP tool |
| host/port on FastMCP() not run() | FastMCP.run() does not accept host/port in mcp>=1.26 | ✓ Applied in Phase 01 |
| Subprocess isolation | esptool, mpremote, git, webrepl_cli as subprocesses not in-process | ✓ Cleaner error handling, no import conflicts |
| Error dicts not exceptions | All tools return {error, detail} dicts; never raise to MCP layer | ✓ Consistent structured errors for Claude |
| Auto soft-reset after deploy | Board runs new code immediately after file/dir/GitHub deploy | ⚠ Unreliable on ESP32 classic; may need hard reset |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-29 after v1.0 milestone*
