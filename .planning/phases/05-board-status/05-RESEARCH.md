# Phase 5: Board Status - Research

**Researched:** 2026-03-29
**Domain:** MicroPython board status collection (USB + WiFi), health checking, mDNS discovery
**Confidence:** HIGH

## Summary

Phase 5 adds three MCP tools: `get_board_status()`, `check_board_health()`, and `discover_boards()`. The USB path for status and health builds directly on `exec_repl()` -- send a MicroPython snippet that collects data and prints JSON, parse the output. The WiFi path requires executing commands over WebREPL's websocket text protocol -- the vendored `webrepl_cli.py` already implements the websocket handshake and login but only supports interactive REPL and file transfer, not non-interactive command execution. A thin helper module using Python's built-in `socket` module (mirroring the vendored code's approach) will handle WiFi command execution. For mDNS discovery, `python-zeroconf` (v0.148.0) is the standard pure-Python library -- pip-installable, no system dependency on avahi.

The project has strong established patterns: error dicts (never raise), subprocess wrappers, SerialLock for USB, separate `port`/`host` parameters. All three new tools follow these patterns. The main implementation risk is the WebREPL command execution helper -- the protocol is simple (text websocket frames) but needs proper timeout handling and output framing.

**Primary recommendation:** Build `tools/board_status.py` (USB+WiFi status/health logic) and `tools/mdns_discovery.py` (zeroconf-based discovery), then wire three thin `@mcp.tool()` wrappers in `mcp_server.py`. WiFi command execution via a `webrepl_exec()` helper in a new `tools/webrepl_cmd.py` module that reuses the websocket/login pattern from the vendored `webrepl_cli.py`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Single compound REPL script -- one exec_repl() call runs a MicroPython snippet that collects all data points (sys.implementation, network.WLAN, gc.mem_free, uos.statvfs) and prints JSON. One serial round-trip.
- D-02: Dual transport -- status tool accepts either a USB serial port OR a WiFi host+password. USB path uses exec_repl(); WiFi path uses WebREPL websocket to execute the same script.
- D-03: Data points returned: firmware version, WiFi connected (y/n), IP address, free memory, free storage, board name/hostname.
- D-04: REPL ping approach -- send a trivial exec_repl() command (e.g. `print(1)`) with a short timeout. Success = MicroPython running.
- D-05: Dual transport -- health check also accepts port OR host+password.
- D-06: Three failure states: Healthy, Unresponsive, Not found.
- D-07: Use python-zeroconf library on the Pi side. Pure Python, pip-installable, no system dependency on avahi.
- D-08: Browse for `_webrepl._tcp` service type.
- D-09: Configurable browse timeout with default of 3 seconds.
- D-10: Build Pi-side discovery tool fully in Phase 5. Test with manually-configured mDNS on a board.
- D-11: Three separate MCP tools: get_board_status(), check_board_health(), discover_boards().
- D-12: discover_boards() returns IP address, mDNS hostname, and WebREPL port for each board found.
- D-13: Separate port and host parameters (not a single target). Exactly one of port/host required.
- D-14: Error dict pattern: {"error": "snake_case_code", "detail": "human string"} -- never raise.
- D-15: Tool modules in tools/, thin @mcp.tool() wrappers in mcp_server.py.
- D-16: Per-port SerialLock for USB operations.

### Claude's Discretion
- Exact MicroPython snippet for status collection (field extraction, JSON formatting)
- WebREPL execution implementation details (websocket library, command framing)
- Health check ping command and timeout value
- python-zeroconf API usage patterns (ServiceBrowser vs one-shot query)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STAT-01 | MCP tool returns board status: firmware version, WiFi connected (y/n), IP address, free memory/storage | Compound MicroPython snippet via exec_repl (USB) or webrepl_exec (WiFi); JSON output parsed Pi-side |
| STAT-02 | Board health check detects whether MicroPython is running, board is responsive, reports issues | Trivial ping command with short timeout; three-state response (healthy/unresponsive/not_found) |
| STAT-03 | MCP tool discovers MicroPython boards on the local network via mDNS | python-zeroconf ServiceBrowser browsing `_webrepl._tcp.local.` with configurable timeout |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-zeroconf | 0.148.0 | mDNS service discovery | Pure Python, pip-installable, no avahi dependency; maintained actively |
| Python socket (stdlib) | builtin | WebREPL websocket for WiFi command execution | Matches vendored webrepl_cli.py pattern; zero new dependencies for WiFi path |
| mpremote | >=1.23 (already installed) | USB REPL execution via exec_repl() | Already used by project; no change needed |
| pyserial | >=3.5 (already installed) | Serial port detection for health check "not found" state | Already used by project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | builtin | Parse JSON output from MicroPython status snippet | Always -- status collection returns JSON |
| struct (stdlib) | builtin | WebREPL websocket frame encoding | WiFi command execution helper |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw socket WebREPL | `webrepl` pip package (0.2.0) | Last updated 2019; unmaintained; adds dependency for trivial protocol. Raw socket matches vendored code pattern. |
| Raw socket WebREPL | `websockets` pip package | Overkill for WebREPL's simplified websocket; adds async dependency; vendored code already implements the protocol with raw sockets |
| python-zeroconf | avahi-daemon + avahi-browse | System dependency; not always installed; harder to test; python-zeroconf is self-contained |

**Installation:**
```bash
pip install "zeroconf>=0.131,<1.0"
```

**Version note:** python-zeroconf 0.148.0 is the latest as of 2025-10-05. Pin to >=0.131 (stable API) with <1.0 upper bound.

## Architecture Patterns

### Recommended Module Structure
```
tools/
  board_status.py      # get_status() and check_health() -- dual transport
  webrepl_cmd.py       # webrepl_exec(host, password, command, timeout) -- WiFi command execution
  mdns_discovery.py    # discover_boards(timeout) -- zeroconf-based mDNS browse
  repl.py              # existing: exec_repl() -- USB command execution
  serial_lock.py       # existing: SerialLock -- per-port locking
  ota_wifi.py          # existing: deploy_ota_wifi -- WiFi file transfer
mcp_server.py          # add 3 new @mcp.tool() wrappers
```

### Pattern 1: Dual-Transport Status Collection
**What:** Single function `get_status(port=None, host=None, password=None)` that routes to USB or WiFi path based on which parameter is provided.
**When to use:** Both `get_board_status` and `check_board_health` tools.
**Example:**
```python
# tools/board_status.py
import json
from tools.repl import exec_repl
from tools.webrepl_cmd import webrepl_exec

STATUS_SCRIPT = """\
import sys, gc, uos, json
try:
    import network
    w = network.WLAN(network.STA_IF)
    wifi_connected = w.isconnected()
    ip = w.ifconfig()[0] if wifi_connected else None
except:
    wifi_connected = False
    ip = None
gc.collect()
s = uos.statvfs('/')
free_storage = s[0] * s[3]
d = {
    'firmware': '.'.join(str(x) for x in sys.implementation.version),
    'wifi_connected': wifi_connected,
    'ip_address': ip,
    'free_memory': gc.mem_free(),
    'free_storage': free_storage,
    'board': sys.platform,
}
print(json.dumps(d))
"""

def get_status(port=None, host=None, password=None):
    if port and host:
        return {"error": "invalid_params", "detail": "Provide either port or host, not both"}
    if not port and not host:
        return {"error": "invalid_params", "detail": "Provide either port or host"}

    if port:
        result = exec_repl(port, STATUS_SCRIPT, timeout=10)
    else:
        if not password:
            return {"error": "invalid_params", "detail": "password required for WiFi status"}
        result = webrepl_exec(host, password, STATUS_SCRIPT, timeout=15)

    if "error" in result:
        return result

    try:
        data = json.loads(result["output"])
        data["transport"] = "usb" if port else "wifi"
        return data
    except (json.JSONDecodeError, KeyError):
        return {"error": "status_parse_failed", "detail": f"Could not parse board output: {result.get('output', '')}"}
```

### Pattern 2: WebREPL Command Execution Helper
**What:** Low-level helper that connects to WebREPL via websocket, authenticates, sends a command as text frames, reads output, and returns it.
**When to use:** WiFi path for both status and health tools.
**Example:**
```python
# tools/webrepl_cmd.py
import socket
import struct
import time

WEBREPL_PORT = 8266
FRAME_TXT = 0x81
FRAME_BIN = 0x82

def webrepl_exec(host, password, command, timeout=15, port=WEBREPL_PORT):
    """Execute a MicroPython command via WebREPL and return output.

    Returns {"output": "..."} on success.
    Returns {"error": "...", "detail": "..."} on failure.
    Never raises.
    """
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect(socket.getaddrinfo(host, port)[0][4])

        # Websocket handshake (simplified, matching webrepl_cli.py)
        cl = s.makefile("rwb", 0)
        cl.write(b"GET / HTTP/1.1\r\nHost: echo.websocket.org\r\n"
                 b"Connection: Upgrade\r\nUpgrade: websocket\r\n"
                 b"Sec-WebSocket-Key: foo\r\n\r\n")
        while True:
            line = cl.readline()
            if line == b"\r\n":
                break

        # Login -- read until ":" prompt, then send password
        ws = _WebSocket(s)
        _login(ws, password)

        # Send command + newline as text frame, then Ctrl-D to execute
        # Read output until we see ">>> " prompt
        ws.write((command + "\r\n").encode(), FRAME_TXT)

        # Collect output until prompt reappears
        output = _read_until_prompt(ws, timeout)
        s.close()

        return {"output": output.strip()}

    except socket.timeout:
        return {"error": "wifi_timeout", "detail": f"WebREPL connection to {host} timed out after {timeout}s"}
    except OSError as e:
        return {"error": "wifi_unreachable", "detail": f"WebREPL connection to {host} failed: {e}"}
    except Exception as e:
        return {"error": "webrepl_exec_failed", "detail": str(e)}
```

### Pattern 3: mDNS Service Discovery
**What:** Browse for `_webrepl._tcp.local.` services using python-zeroconf ServiceBrowser with a configurable timeout.
**When to use:** `discover_boards()` tool.
**Example:**
```python
# tools/mdns_discovery.py
import time
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ServiceInfo

WEBREPL_SERVICE = "_webrepl._tcp.local."
DEFAULT_TIMEOUT = 3

class _BoardListener(ServiceListener):
    def __init__(self):
        self.boards = []

    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if info:
            addresses = info.parsed_addresses()
            self.boards.append({
                "hostname": name.replace(f".{type_}", ""),
                "ip": addresses[0] if addresses else None,
                "port": info.port or 8266,
            })

    def remove_service(self, zc, type_, name):
        pass

    def update_service(self, zc, type_, name):
        pass


def discover_boards(timeout=DEFAULT_TIMEOUT):
    """Discover MicroPython boards advertising WebREPL via mDNS.

    Returns list of {"hostname": ..., "ip": ..., "port": ...} dicts.
    Returns {"error": ..., "detail": ...} on failure. Never raises.
    """
    try:
        zc = Zeroconf()
        listener = _BoardListener()
        browser = ServiceBrowser(zc, WEBREPL_SERVICE, listener)
        time.sleep(timeout)
        zc.close()
        return listener.boards
    except Exception as e:
        return {"error": "mdns_failed", "detail": str(e)}
```

### Anti-Patterns to Avoid
- **Multiple serial round-trips for status:** Collect all data in a single MicroPython script. Multiple exec_repl() calls waste time and risk the board state changing between calls.
- **Raising exceptions from tool functions:** Always return error dicts. The MCP layer expects structured data, not Python exceptions.
- **Blocking indefinitely on WebREPL:** Always set socket timeouts. WebREPL boards can be powered off mid-connection.
- **Sharing a Zeroconf instance across calls:** Create a fresh Zeroconf instance per discovery call. The instance holds open sockets; long-lived instances leak resources in a tool-call model.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| mDNS multicast | Raw UDP multicast | python-zeroconf | mDNS has edge cases (TTL, cache, multiple interfaces, IPv6); zeroconf handles all of them |
| WebSocket framing | Full websocket library | Vendored webrepl_cli.py's frame encoding pattern | WebREPL uses a simplified websocket (no masking, no extensions); the vendored code already works |
| JSON serialization on-board | Custom string formatting | `json.dumps()` in MicroPython | MicroPython has a built-in json module; hand-built string concatenation breaks on special characters |
| Serial port existence check | Manual /dev enumeration | `serial.tools.list_ports.comports()` | Already used in board_detection.py; handles USB hotplug correctly |

**Key insight:** The WebREPL protocol is intentionally simplified (no websocket masking, no extensions). The vendored `webrepl_cli.py` already implements the exact framing needed -- reuse its pattern rather than importing a full websocket library.

## Common Pitfalls

### Pitfall 1: MicroPython JSON Output Pollution
**What goes wrong:** Board prints boot messages, REPL prompts, or debug output mixed with the JSON status output.
**Why it happens:** MicroPython's REPL echoes the command back and adds prompts (>>>) around the output.
**How to avoid:** Use `exec_repl()` with mpremote -- it already handles prompt stripping. For WebREPL, read until the JSON line (starts with `{`) and ignore prompt/echo noise.
**Warning signs:** `json.loads()` fails on output that looks like `>>> {"firmware": ...}\r\n>>> `.

### Pitfall 2: WebREPL Output Framing
**What goes wrong:** Reading WebREPL output gets stuck or returns partial data.
**Why it happens:** WebREPL sends output character-by-character as text frames. There's no "end of response" marker -- you must detect the REPL prompt reappearing.
**How to avoid:** Accumulate text frame data until you see the `>>> ` prompt pattern. Use a socket timeout as a safety net. Consider sending Ctrl-A (raw REPL mode) + Ctrl-D (execute) for cleaner framing.
**Warning signs:** Output hangs, or JSON is truncated mid-string.

### Pitfall 3: MicroPython Module Import Differences
**What goes wrong:** Status script uses `uos` but board has `os`; or `network` module not available on all boards.
**Why it happens:** MicroPython module names vary by version and port. Newer versions aliased `uos` to `os`.
**How to avoid:** Use try/except in the MicroPython snippet. Try `import os` first, fall back to `import uos`. Wrap network access in try/except since not all boards have WiFi.
**Warning signs:** `ImportError` in REPL output instead of JSON.

### Pitfall 4: Zeroconf Blocking on No Boards
**What goes wrong:** `discover_boards()` blocks for the full timeout even when no boards exist.
**Why it happens:** ServiceBrowser waits for mDNS responses; if no boards advertise, nothing triggers the callback.
**How to avoid:** This is expected behavior. The timeout parameter controls the maximum wait. Document that 3s is the default and empty results are normal when no boards are advertising.
**Warning signs:** User thinks the tool is hanging -- it's just waiting for the timeout.

### Pitfall 5: Health Check False Positives via Serial Port Detection
**What goes wrong:** Health check reports "not found" when board is connected but busy.
**Why it happens:** SerialLock timeout (another operation in progress) looks like "not found" without careful error differentiation.
**How to avoid:** Distinguish three states clearly: (1) port exists and responds = healthy, (2) port exists but REPL times out = unresponsive, (3) port doesn't exist in `list_ports` = not_found. Check port existence first via `serial.tools.list_ports` before attempting REPL ping.
**Warning signs:** Board shows in `list_connected_boards()` but health check says "not found".

## Code Examples

### MicroPython Status Collection Script
```python
# This runs ON the ESP32 board via exec_repl or webrepl_exec
# Must be a single string compatible with exec()
STATUS_SCRIPT = """\
import sys, gc, json
try:
    import os
except ImportError:
    import uos as os
try:
    import network
    w = network.WLAN(network.STA_IF)
    wifi = w.isconnected()
    ip = w.ifconfig()[0] if wifi else None
except:
    wifi = False
    ip = None
gc.collect()
s = os.statvfs('/')
print(json.dumps({
    'firmware': '.'.join(str(x) for x in sys.implementation.version),
    'wifi_connected': wifi,
    'ip_address': ip,
    'free_memory': gc.mem_free(),
    'free_storage': s[0] * s[3],
    'board': sys.platform
}))
"""
```

### Health Check Ping
```python
HEALTH_PING = "print(1)"
HEALTH_TIMEOUT = 5  # short timeout -- we just want to know if it's alive

def check_health(port=None, host=None, password=None):
    # ... parameter validation ...

    if port:
        # Check port exists first
        from serial.tools.list_ports import comports
        port_exists = any(p.device == port for p in comports())
        if not port_exists:
            return {"status": "not_found", "detail": f"No device at {port}"}
        result = exec_repl(port, HEALTH_PING, timeout=HEALTH_TIMEOUT)
    else:
        result = webrepl_exec(host, password, HEALTH_PING, timeout=HEALTH_TIMEOUT)

    if "error" in result:
        if "timeout" in result["error"]:
            return {"status": "unresponsive", "detail": result["detail"]}
        return {"status": "not_found", "detail": result["detail"]}

    return {"status": "healthy"}
```

### mDNS Discovery with python-zeroconf
```python
# Source: python-zeroconf official examples + API docs
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import time

class BoardListener(ServiceListener):
    def __init__(self):
        self.boards = []

    def add_service(self, zc: Zeroconf, type_: str, name: str):
        info = zc.get_service_info(type_, name)
        if info and info.parsed_addresses():
            self.boards.append({
                "hostname": info.server.rstrip("."),
                "ip": info.parsed_addresses()[0],
                "port": info.port or 8266,
            })

    def remove_service(self, zc, type_, name):
        pass

    def update_service(self, zc, type_, name):
        pass

def discover(timeout=3):
    zc = Zeroconf()
    listener = BoardListener()
    ServiceBrowser(zc, "_webrepl._tcp.local.", listener)
    time.sleep(timeout)
    zc.close()
    return listener.boards
```

### MCP Tool Wrappers (mcp_server.py additions)
```python
from tools.board_status import get_status, check_health
from tools.mdns_discovery import discover_boards as _discover_boards

@mcp.tool()
def get_board_status(port: str | None = None, host: str | None = None, password: str | None = None) -> dict:
    """Get firmware version, WiFi status, IP, free memory/storage from an ESP32 board.
    Provide port for USB or host+password for WiFi. Exactly one transport required.
    """
    if port:
        try:
            with SerialLock(port):
                return get_status(port=port)
        except TimeoutError as e:
            return {"error": "serial_lock_timeout", "detail": str(e)}
    return get_status(host=host, password=password)

@mcp.tool()
def check_board_health(port: str | None = None, host: str | None = None, password: str | None = None) -> dict:
    """Check if a board is alive and running MicroPython.
    Returns status: 'healthy', 'unresponsive', or 'not_found'.
    """
    if port:
        try:
            with SerialLock(port):
                return check_health(port=port)
        except TimeoutError as e:
            return {"error": "serial_lock_timeout", "detail": str(e)}
    return check_health(host=host, password=password)

@mcp.tool()
def discover_boards(timeout: int = 3) -> list[dict] | dict:
    """Discover MicroPython boards on the LAN via mDNS (looks for _webrepl._tcp).
    Returns list of {hostname, ip, port} for each board found.
    """
    return _discover_boards(timeout=timeout)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `import uos` | `import os` (aliased in newer MicroPython) | MicroPython 1.20+ | Status script must handle both |
| WebREPL v1 protocol | Same (stable, unchanged) | N/A | Protocol is frozen; vendored code still works |
| avahi-browse CLI | python-zeroconf | Always preferred in Python projects | No system dependency needed |

**Deprecated/outdated:**
- `uos`, `ujson`, `usys` module prefixes: aliased to `os`, `json`, `sys` in MicroPython 1.20+. Use try/except for compatibility.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.0 |
| Config file | none (pytest defaults) |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STAT-01 | get_status returns firmware, wifi, ip, memory, storage via USB | unit | `python -m pytest tests/test_board_status.py::test_get_status_usb_success -x` | Wave 0 |
| STAT-01 | get_status returns data via WiFi (WebREPL) | unit | `python -m pytest tests/test_board_status.py::test_get_status_wifi_success -x` | Wave 0 |
| STAT-01 | get_status returns error dict on parse failure | unit | `python -m pytest tests/test_board_status.py::test_get_status_parse_error -x` | Wave 0 |
| STAT-02 | check_health returns healthy when board responds | unit | `python -m pytest tests/test_board_status.py::test_health_check_healthy -x` | Wave 0 |
| STAT-02 | check_health returns unresponsive on timeout | unit | `python -m pytest tests/test_board_status.py::test_health_check_unresponsive -x` | Wave 0 |
| STAT-02 | check_health returns not_found when port missing | unit | `python -m pytest tests/test_board_status.py::test_health_check_not_found -x` | Wave 0 |
| STAT-03 | discover_boards returns list of board dicts | unit | `python -m pytest tests/test_mdns_discovery.py::test_discover_boards_found -x` | Wave 0 |
| STAT-03 | discover_boards returns empty list when no boards | unit | `python -m pytest tests/test_mdns_discovery.py::test_discover_boards_empty -x` | Wave 0 |
| STAT-01/02 | MCP tools registered (get_board_status, check_board_health, discover_boards) | unit | `python -m pytest tests/test_mcp_server.py::test_new_tools_registered -x` | Wave 0 (update existing) |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_board_status.py` -- covers STAT-01, STAT-02 (new file)
- [ ] `tests/test_mdns_discovery.py` -- covers STAT-03 (new file)
- [ ] `tests/test_webrepl_cmd.py` -- covers WiFi command execution helper (new file)
- [ ] Update `tests/test_mcp_server.py::test_new_tools_registered` -- add 3 new tool names

## Open Questions

1. **WebREPL raw REPL mode vs normal mode**
   - What we know: MicroPython supports Ctrl-A (raw REPL) which gives cleaner output framing (OK/error markers instead of `>>>` prompts). mpremote uses raw REPL internally.
   - What's unclear: Whether WebREPL's text frame channel supports raw REPL mode transitions. The vendored code only uses normal REPL.
   - Recommendation: Start with normal REPL mode (send command + detect `>>>` prompt). If output parsing proves unreliable, try raw REPL (send Ctrl-A, then command, then Ctrl-D). This is a Claude's discretion item.

2. **Board hostname extraction**
   - What we know: D-03 requests hostname in status output. `sys.platform` returns chip name (e.g., "esp32"), not a user-friendly hostname.
   - What's unclear: MicroPython doesn't have a built-in "hostname" concept unless set via `network.WLAN.config(dhcp_hostname=...)`.
   - Recommendation: Try `network.WLAN(network.STA_IF).config('dhcp_hostname')` in the status script with try/except fallback to `sys.platform`. This may not work on all firmware builds.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `tools/repl.py`, `tools/ota_wifi.py`, `tools/vendor/webrepl_cli.py`, `mcp_server.py` -- established patterns
- [python-zeroconf PyPI](https://pypi.org/project/zeroconf/) -- version 0.148.0, Python 3.9+ support
- [python-zeroconf GitHub examples](https://github.com/python-zeroconf/python-zeroconf) -- ServiceBrowser pattern

### Secondary (MEDIUM confidence)
- [webrepl-python](https://github.com/kost/webrepl-python) -- sendcmd() API pattern for WebREPL command execution
- [MicroPython WebREPL](https://github.com/micropython/webrepl) -- official WebREPL protocol and tools
- [webrepl PyPI](https://pypi.org/project/webrepl/) -- v0.2.0, last updated 2019

### Tertiary (LOW confidence)
- WebREPL raw REPL mode support via websocket text frames -- not verified with official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - python-zeroconf is verified, WebREPL protocol is stable and vendored code demonstrates it
- Architecture: HIGH - follows established project patterns (error dicts, subprocess, SerialLock, dual transport)
- Pitfalls: MEDIUM - WebREPL output framing is the main risk area; needs implementation validation

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable domain; WebREPL protocol is frozen, zeroconf API is mature)
