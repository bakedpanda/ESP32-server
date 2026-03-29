# Milestones

## v1.0 MVP (Shipped: 2026-03-29)

**Phases completed:** 3 phases, 11 plans, 16 tasks

**Key accomplishments:**

- pytest collecting 17 failing stubs covering all 11 Phase 1 requirements; FastMCP stub, esptool wrappers, and systemd unit present on disk
- USB enumeration filtered by 5 ESP32 VID/PID sets, esptool chip_id subprocess detection, and boards.json state persistence
- 7-day TTL firmware cache + esptool erase/write orchestration for 5 ESP32 chip variants with pre-flight detection
- FastMCP server with 4 ESP32 tools on streamable-http://0.0.0.0:8000, registered with Claude Code, running as systemd daemon
- mpremote-backed file deploy with 70%/90% space thresholds and post-transfer os.stat integrity verification
- exec_repl, read_serial, soft_reset, hard_reset via mpremote subprocess — all returning error dicts, never raising
- fcntl file-based per-port mutex wrapping 5 new MCP tools; all errors as structured {error, detail} dicts
- Vendored webrepl_cli.py and created 8 RED test stubs (5 OTA WiFi + 3 GitHub deploy) gating Phase 3 implementation plans
- deploy_ota_wifi() function with WebREPL subprocess, 200KB size gate, and wifi_unreachable fallback hint to USB
- pull_and_deploy_github() clones repos via git subprocess into temp dirs and deploys to boards via existing deploy_directory() pipeline with token sanitization
- Two new @mcp.tool() registrations (deploy_ota_wifi, pull_and_deploy_github) wired into mcp_server.py completing Phase 3 with 11 total tools

---
