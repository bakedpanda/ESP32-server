# Phase 5: Board Status - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 05-board-status
**Areas discussed:** Status data collection, Health check design, mDNS discovery, Tool surface

---

## Status Data Collection

### Collection Method

| Option | Description | Selected |
|--------|-------------|----------|
| Single REPL script | One exec_repl() call runs a compound MicroPython snippet that collects everything and prints JSON. Fastest, one serial round-trip. | ✓ |
| Multiple REPL calls | Separate exec_repl() calls for each data point. Simpler per-call but slower (4-5 serial round-trips). | |
| Helper script on board | Deploy a status.py to the board. Import and call it via REPL. Requires script pre-deployed. | |

**User's choice:** Single REPL script (Recommended)
**Notes:** None

### Access Method

| Option | Description | Selected |
|--------|-------------|----------|
| USB port only | Status collected via exec_repl() over USB serial. Consistent with existing tool pattern. | |
| Port or WiFi host | Accept either a serial port or a WiFi IP/hostname. WiFi path uses WebREPL. | ✓ |

**User's choice:** Port or WiFi host
**Notes:** User wants dual-transport status checks -- both USB and WiFi.

### WiFi Execution Method

| Option | Description | Selected |
|--------|-------------|----------|
| WebREPL websocket | Connect to board's WebREPL via websocket, send status script, capture output. Reuses existing WebREPL infrastructure. | ✓ |
| HTTP endpoint on board | Board runs a tiny HTTP server that returns status JSON. More setup, no password needed. | |

**User's choice:** WebREPL websocket (Recommended)
**Notes:** None

### Data Points

| Option | Description | Selected |
|--------|-------------|----------|
| STAT-01 set only | Firmware version, WiFi connected (y/n), IP address, free memory, free storage. | |
| STAT-01 + extras | Add chip type, uptime, board name/hostname, MicroPython build date. | |

**User's choice:** STAT-01 fields + board name/hostname
**Notes:** User specifically wants board name/hostname included but not the full extras set.

---

## Health Check Design

### Probe Approach

| Option | Description | Selected |
|--------|-------------|----------|
| REPL ping | Send trivial exec_repl() command with short timeout. Success = running. Timeout = unresponsive. | ✓ |
| Multi-stage probe | Stage 1: port exists. Stage 2: REPL ping. Stage 3: full status. Granular state at each stage. | |
| Integrated with status | No separate health check -- status tool IS the health check. | |

**User's choice:** REPL ping (Recommended)
**Notes:** None

### WiFi Support

| Option | Description | Selected |
|--------|-------------|----------|
| Both USB and WiFi | Same dual-path as status. Accept port OR host+password. | ✓ |
| USB only | Health check is a quick serial probe only. | |

**User's choice:** Both USB and WiFi (Recommended)
**Notes:** Consistent with status tool decision.

### Failure States

| Option | Description | Selected |
|--------|-------------|----------|
| Three states | Healthy, Unresponsive (port exists but times out), Not found (port missing / WiFi unreachable). | ✓ |
| Binary healthy/unhealthy | Just yes/no with detail string. | |

**User's choice:** Three states (Recommended)
**Notes:** None

---

## mDNS Discovery

### Library Choice

| Option | Description | Selected |
|--------|-------------|----------|
| python-zeroconf | Pure Python, pip-installable, well-maintained. No system dependency. | ✓ |
| avahi-browse subprocess | Shell out to avahi-browse. No pip dependency but requires avahi-daemon. | |
| You decide | Claude picks during planning/research. | |

**User's choice:** python-zeroconf (Recommended)
**Notes:** None

### Service Type

| Option | Description | Selected |
|--------|-------------|----------|
| _webrepl._tcp | Boards advertise WebREPL as mDNS service. Natural fit. | ✓ |
| _micropython._tcp | Custom service type. More descriptive but non-standard. | |
| You decide | Claude picks based on MicroPython mDNS module support. | |

**User's choice:** _webrepl._tcp (Recommended)
**Notes:** None

### Phase 6 Dependency

| Option | Description | Selected |
|--------|-------------|----------|
| Build now, test with manual mDNS | Phase 5 builds Pi-side tool fully. Test with manual board mDNS config. Phase 6 automates via boot.py. | ✓ |
| Stub the discovery tool | Create interface only, Phase 6 fills implementation. | |
| Pull mDNS board-side into Phase 5 | Move board-side mDNS into Phase 5 scope. | |

**User's choice:** Build discovery tool now, test with manual mDNS (Recommended)
**Notes:** None

### Browse Timeout

| Option | Description | Selected |
|--------|-------------|----------|
| 3-second scan | Fixed 3-second browse. Fast for interactive use. | |
| Configurable timeout | Default 3 seconds with timeout parameter. Longer scans for larger networks. | ✓ |
| You decide | Claude picks a reasonable default. | |

**User's choice:** Configurable timeout
**Notes:** None

---

## Tool Surface

### Tool Count

| Option | Description | Selected |
|--------|-------------|----------|
| Three separate tools | get_board_status(), check_board_health(), discover_boards(). Each clear purpose. | ✓ |
| Two tools (combined status+health) | Fewer tools but heavier status call. | |
| One combined tool | Single entry point with mode parameter. Less clear for Claude. | |

**User's choice:** Three separate tools (Recommended)
**Notes:** None

### Discovery Return Data

| Option | Description | Selected |
|--------|-------------|----------|
| IP + hostname + port | IP address, mDNS hostname, and WebREPL port per board. Enough for Claude to call status/health. | ✓ |
| IP only | Just IP addresses. Minimal. | |
| IP + hostname + auto-status | Discover and auto-check each board. Richer but slower. | |

**User's choice:** IP + hostname + port (Recommended)
**Notes:** None

### Parameter Design

| Option | Description | Selected |
|--------|-------------|----------|
| Separate port and host params | port=None, host=None, password=None. Exactly one of port/host required. | ✓ |
| Single target param | target auto-detected as serial port or IP/hostname. Simpler but implicit. | |

**User's choice:** Separate port and host params (Recommended)
**Notes:** Matches existing pattern where USB and WiFi tools have distinct parameters.

---

## Claude's Discretion

- Exact MicroPython snippet for status collection
- WebREPL execution implementation details
- Health check ping command and timeout value
- python-zeroconf API usage patterns

## Deferred Ideas

None -- discussion stayed within phase scope.
