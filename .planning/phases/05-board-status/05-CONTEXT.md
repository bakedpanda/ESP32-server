# Phase 5: Board Status - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Claude can check whether a board is alive, what firmware it runs, and its resource state -- without the user running REPL commands manually. Includes USB-connected boards (via serial REPL) and WiFi-connected boards (via WebREPL). Also includes mDNS discovery of MicroPython boards on the LAN.

Out of scope: board-side mDNS advertisement setup (Phase 6 deploys boot.py with mDNS config), fleet management, board provisioning.

</domain>

<decisions>
## Implementation Decisions

### Status Data Collection
- **D-01:** Single compound REPL script -- one exec_repl() call runs a MicroPython snippet that collects all data points (sys.implementation, network.WLAN, gc.mem_free, uos.statvfs) and prints JSON. One serial round-trip.
- **D-02:** Dual transport -- status tool accepts either a USB serial port OR a WiFi host+password. USB path uses exec_repl(); WiFi path uses WebREPL websocket to execute the same script.
- **D-03:** Data points returned: firmware version, WiFi connected (y/n), IP address, free memory, free storage, board name/hostname. (STAT-01 plus hostname.)

### Health Check
- **D-04:** REPL ping approach -- send a trivial exec_repl() command (e.g. `print(1)`) with a short timeout. Success = MicroPython running. Timeout = unresponsive. No response = not found.
- **D-05:** Dual transport -- health check also accepts port OR host+password, same as status tool.
- **D-06:** Three failure states: 1) Healthy (MicroPython responds), 2) Unresponsive (port exists but REPL times out -- board hung or not running MicroPython), 3) Not found (port doesn't exist / WiFi unreachable).

### mDNS Discovery
- **D-07:** Use python-zeroconf library on the Pi side. Pure Python, pip-installable, no system dependency on avahi.
- **D-08:** Browse for `_webrepl._tcp` service type. Boards advertise WebREPL as their mDNS service.
- **D-09:** Configurable browse timeout with default of 3 seconds. Most boards respond within 1-2 seconds; longer timeout available for larger networks.
- **D-10:** Build the Pi-side discovery tool fully in Phase 5. Test with manually-configured mDNS on a board. Phase 6 automates board-side mDNS via boot.py deployment.

### Tool Surface
- **D-11:** Three separate MCP tools: `get_board_status()` (STAT-01), `check_board_health()` (STAT-02), `discover_boards()` (STAT-03). Claude chains them as needed.
- **D-12:** `discover_boards()` returns IP address, mDNS hostname, and WebREPL port for each board found.
- **D-13:** Separate `port` and `host` parameters (not a single `target`). `get_board_status(port=None, host=None, password=None)` -- exactly one of port/host required. Matches existing pattern where USB and WiFi tools have distinct parameters.

### Patterns (carried from Phase 2/3)
- **D-14:** Error dict pattern: `{"error": "snake_case_code", "detail": "human string"}` -- never raise exceptions to callers.
- **D-15:** Tool modules in `tools/`, thin `@mcp.tool()` wrappers in `mcp_server.py`.
- **D-16:** Per-port `SerialLock` for USB operations.

### Claude's Discretion
- Exact MicroPython snippet for status collection (field extraction, JSON formatting)
- WebREPL execution implementation details (websocket library, command framing)
- Health check ping command and timeout value
- python-zeroconf API usage patterns (ServiceBrowser vs one-shot query)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` -- STAT-01, STAT-02, STAT-03

### Existing Implementation (patterns to follow)
- `tools/repl.py` -- exec_repl() is the USB-side execution mechanism; health check and status collection build on this
- `tools/ota_wifi.py` -- WebREPL subprocess pattern for WiFi operations; status/health WiFi path will use similar approach
- `tools/board_detection.py` -- detect_chip(), list_boards(), load_board_state() for board enumeration patterns
- `tools/serial_lock.py` -- SerialLock context manager for USB operations
- `mcp_server.py` -- @mcp.tool() registration pattern, existing 11 tools

### Prior Phase Context
- `.planning/phases/02-core-usb-workflows/02-CONTEXT.md` -- error dict pattern, deployment patterns, SerialLock design
- `.planning/phases/03-wifi-advanced/03-CONTEXT.md` -- WebREPL transport decisions, WiFi addressing (host parameter per-call)

### Project Context
- `.planning/PROJECT.md` -- core value, constraints, out-of-scope items

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/repl.py:exec_repl()` -- single-command REPL execution with timeout; direct foundation for status collection and health ping
- `tools/repl.py:hard_reset()` -- pyserial-based serial port interaction pattern; relevant for low-level serial detection
- `tools/ota_wifi.py` -- WebREPL subprocess wrapper; pattern for WiFi-based command execution
- `tools/serial_lock.py:SerialLock` -- per-port locking; wrap USB status/health calls the same way

### Established Patterns
- Error returns: `{"error": "snake_case_code", "detail": "human string"}` -- never raise
- subprocess: `subprocess.run([...], capture_output=True, text=True, timeout=N)`
- Tool modules in `tools/`, thin wrappers in `mcp_server.py`
- WiFi tools take `host` parameter; USB tools take `port` parameter

### Integration Points
- `mcp_server.py` -- add 3 new `@mcp.tool()` decorators: get_board_status, check_board_health, discover_boards
- `requirements.txt` / `setup.py` -- add `zeroconf` as a new dependency

</code_context>

<specifics>
## Specific Ideas

- Status tool returns board name/hostname in addition to STAT-01 fields -- user specifically requested this
- WiFi status path reuses WebREPL infrastructure from Phase 3 (same password-per-call pattern)
- Discovery tool returns structured data (IP + hostname + port), not just IPs -- gives Claude enough context to call status/health tools immediately

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 05-board-status*
*Context gathered: 2026-03-29*
