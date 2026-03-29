# Phase 6: Provisioning - Research

**Researched:** 2026-03-29
**Domain:** ESP32 provisioning automation (flash, WiFi config, boot.py deployment)
**Confidence:** HIGH

## Summary

Phase 6 adds three new components to the project: a credentials utility (`tools/credentials.py`), a boot.py template system (`templates/boot.py.tpl`), and a new MCP tool (`deploy_boot_config`). The existing `flash_firmware()` already satisfies PROV-01 (always-erase) -- only its tool description needs updating and a test confirming the erase call. The credentials module is straightforward JSON file reading with permission checks. The boot.py template is where the most technical nuance lives.

**Critical finding on mDNS service advertisement:** Standard MicroPython ESP32 firmware (v1.27.0, used by this project) includes a built-in mDNS responder that handles hostname.local resolution via `network.hostname()`. However, it does NOT support mDNS **service advertisement** (e.g., `_webrepl._tcp`). The only library that adds service advertisement (`micropython-mdns` by cbrand) requires **custom firmware** with the built-in mDNS disabled -- it cannot coexist with the standard firmware's mDNS implementation due to port 5353 conflicts. This means the boot.py template should use `network.hostname()` for hostname-based discovery, and mDNS service advertisement should be deferred or implemented via a lightweight board-side workaround. See the mDNS section below for the recommended approach.

**Primary recommendation:** Build `tools/credentials.py` as a shared utility, create `templates/boot.py.tpl` with WiFi + WebREPL + hostname (no service advertisement in standard firmware), wire `deploy_boot_config` as MCP tool #15, and update the Pi-side `discover_boards()` to also support hostname-based discovery as a fallback.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** JSON format -- `/etc/esp32-station/wifi.json` with `{"ssid": "...", "password": "...", "webrepl_password": "..."}`. File permissions 600, created by setup.sh (Phase 7) or manually by user.
- **D-02:** Single network vs multiple -- Claude's discretion. Start simple, can extend later.
- **D-03:** WebREPL password stored in the same credentials file alongside WiFi credentials. Single source of truth.
- **D-04:** Shared utility `tools/credentials.py` with `load_credentials()` -- returns dict or error dict. Follows existing `tools/` module pattern.
- **D-05:** Lazy validation -- credentials file checked only when a tool needs it, not at server startup. Non-provisioning tools work without it.
- **D-06:** When credentials file is missing, tool returns error dict with clear instructions: file path, expected JSON format, example content. No MCP tool writes credentials -- user handles it manually or via setup.sh. Credentials never pass through MCP tool calls (SETUP-02).
- **D-07:** Template with placeholder injection -- `templates/boot.py.tpl` in the repo with `{{SSID}}`, `{{PASSWORD}}`, `{{WEBREPL_PASSWORD}}`, `{{HOSTNAME}}` placeholders. Deploy tool reads credentials from wifi.json, fills placeholders, writes to temp file, deploys via mpremote.
- **D-08:** boot.py configures four things: WiFi auto-connect, WebREPL start, mDNS advertisement (`_webrepl._tcp`), and hostname setting.
- **D-09:** Hostname -- Claude prompts the user for a hostname if one isn't specified in the MicroPython code being deployed. Enables meaningful mDNS identification (e.g. `esp32-kitchen`).
- **D-10:** Dedicated MCP tool `deploy_boot_config(port, hostname=None)` -- reads credentials, fills template, deploys as boot.py. Self-contained, one step in provisioning chain.
- **D-11:** Overwrite silently -- provisioning implies starting fresh (board was just erased and flashed). No confirmation needed for replacing boot.py.
- **D-12:** Physical action instructions delivered via `user_action` key in tool return dict.
- **D-13:** Proactive guidance -- tool returns `user_action` BEFORE the step that needs physical intervention.
- **D-14:** First-timer friendly detail level.
- **D-15:** Five readiness levels, Claude orchestrates by chaining separate tools.
- **D-16:** Claude asks whether WiFi should be disabled to save battery for projects that don't need it.
- **D-17:** No readiness-level tool -- Claude knows the levels from tool descriptions and chains accordingly.
- **D-18:** Auto-verify after provisioning -- Claude always calls `check_board_health()` and/or `get_board_status()`.
- **D-19:** PROV-01 already satisfied by existing `flash_firmware()`. Update tool description + add test.
- **D-20:** Error dict pattern: `{"error": "snake_case_code", "detail": "human string"}` -- never raise.
- **D-21:** Tool modules in `tools/`, thin `@mcp.tool()` wrappers in `mcp_server.py`.
- **D-22:** Separate `port`/`host` parameters for USB/WiFi tools.

### Claude's Discretion
- Single vs multiple network support in credentials file (start simple)
- boot.py template exact MicroPython code (WiFi connect, WebREPL init, mDNS setup)
- Exact `user_action` message wording for each physical step
- How to condense guidance for experienced users in follow-up interactions
- mDNS service name and TXT record content in boot.py

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROV-01 | Every firmware flash starts with a full erase | Already implemented in `flash_firmware()` step 4. Needs description update + test assertion. |
| PROV-02 | User can deploy WiFi + WebREPL config (boot.py) to a board, with credentials read from Pi-local file | New `tools/credentials.py` + `templates/boot.py.tpl` + `deploy_boot_config` MCP tool. Template injection pattern. |
| PROV-03 | Every step requiring user action includes clear explanation of what to do and why | `user_action` key in tool return dicts. `flash_micropython` updated to include BOOT button guidance. |
| PROV-04 | Tools remain separate so Claude can chain them | No new orchestration tool. `deploy_boot_config` is standalone. Claude chains based on readiness level descriptions in tool docstrings. |
| SETUP-02 | WiFi credentials stored on Pi, never transmitted through MCP tool calls | `load_credentials()` reads from `/etc/esp32-station/wifi.json`. Credentials injected into boot.py template server-side before deployment. Never in MCP call params. |

</phase_requirements>

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastMCP (mcp[cli]) | 1.26+ | MCP server framework | Already in use, 14 tools registered |
| mpremote | 1.23+ | File deployment to ESP32 | Already used by `deploy_file()` |
| esptool | 5+ | Firmware flashing | Already used by `flash_firmware()` |

### New Dependencies
None. This phase uses only Python stdlib (`json`, `pathlib`, `os`, `tempfile`, `string.Template` or simple `.replace()`). No new pip packages needed.

### MicroPython Board-Side Dependencies
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `network` | built-in | WiFi STA_IF connection | Standard in all ESP32 MicroPython |
| `webrepl` | built-in | WebREPL daemon | Standard since MicroPython 1.8+ |
| `network.hostname()` | since v1.20 | Set mDNS hostname | Must call BEFORE `wlan.active(True)` |

**No additional MicroPython libraries required.** Service advertisement is not feasible with standard firmware (see mDNS section below).

## Architecture Patterns

### New Files
```
tools/credentials.py     # load_credentials() -- shared utility
templates/boot.py.tpl    # boot.py template with placeholders
tests/test_credentials.py  # credential loading tests
tests/test_boot_deploy.py  # boot config deployment tests
```

### Modified Files
```
mcp_server.py            # Add deploy_boot_config tool (#15)
                          # Update flash_micropython docstring (PROV-01 clarity)
                          # Add user_action to flash_micropython return (PROV-03)
tests/test_mcp_server.py  # Add deploy_boot_config to expected tools list
tests/test_flash.py       # Add test verifying erase_flash subprocess call
```

### Pattern 1: Credential Loading (`tools/credentials.py`)
**What:** Single function that reads `/etc/esp32-station/wifi.json`, validates keys, returns dict or error dict.
**When to use:** Called by `deploy_boot_config` before template injection.

```python
import json
import os
import pathlib

CREDENTIALS_PATH = pathlib.Path("/etc/esp32-station/wifi.json")
REQUIRED_KEYS = {"ssid", "password", "webrepl_password"}

def load_credentials() -> dict:
    """Load WiFi + WebREPL credentials from the Pi-local file.

    Returns credential dict on success, or error dict with setup instructions.
    """
    if not CREDENTIALS_PATH.exists():
        return {
            "error": "credentials_not_found",
            "detail": (
                f"Credentials file not found at {CREDENTIALS_PATH}. "
                "Create it with: sudo mkdir -p /etc/esp32-station && "
                f"sudo tee {CREDENTIALS_PATH} << 'EOF'\n"
                '{"ssid": "YOUR_SSID", "password": "YOUR_WIFI_PASSWORD", '
                '"webrepl_password": "YOUR_WEBREPL_PASS"}\nEOF\n'
                f"sudo chmod 600 {CREDENTIALS_PATH}"
            ),
        }

    try:
        data = json.loads(CREDENTIALS_PATH.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return {"error": "credentials_invalid", "detail": str(exc)}

    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        return {
            "error": "credentials_incomplete",
            "detail": f"Missing keys in {CREDENTIALS_PATH}: {missing}",
        }

    return data
```

### Pattern 2: Template Injection
**What:** Read `templates/boot.py.tpl`, replace `{{PLACEHOLDER}}` with credential values, write to temp file, deploy via `deploy_file()`.
**When to use:** Inside the `deploy_boot_config` tool function.

```python
import tempfile

TEMPLATE_PATH = pathlib.Path(__file__).parent.parent / "templates" / "boot.py.tpl"

def deploy_boot_config(port: str, hostname: str | None = None) -> dict:
    creds = load_credentials()
    if "error" in creds:
        return creds

    template = TEMPLATE_PATH.read_text()
    hostname = hostname or "esp32"

    # WebREPL password must be 4-9 chars
    webrepl_pass = creds["webrepl_password"]
    if not (4 <= len(webrepl_pass) <= 9):
        return {
            "error": "webrepl_password_invalid",
            "detail": "WebREPL password must be 4-9 characters",
        }

    boot_code = (
        template
        .replace("{{SSID}}", creds["ssid"])
        .replace("{{PASSWORD}}", creds["password"])
        .replace("{{WEBREPL_PASSWORD}}", webrepl_pass)
        .replace("{{HOSTNAME}}", hostname)
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(boot_code)
        tmp_path = f.name

    result = deploy_file(port, tmp_path, "boot.py")
    os.unlink(tmp_path)
    return result
```

### Pattern 3: boot.py Template (MicroPython code)
**What:** The template that runs on the ESP32 at boot.

```python
# boot.py -- auto-generated by ESP32 MicroPython Dev Station
# WiFi + WebREPL + hostname configuration

import network
import time

# Set hostname BEFORE activating interface (required for mDNS)
network.hostname("{{HOSTNAME}}")

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    wlan.connect("{{SSID}}", "{{PASSWORD}}")
    for _ in range(20):  # 10 second timeout (20 * 0.5s)
        if wlan.isconnected():
            break
        time.sleep(0.5)

if wlan.isconnected():
    print("WiFi connected:", wlan.ifconfig()[0])
else:
    print("WiFi connection failed")

# Start WebREPL (password set programmatically, no webrepl_cfg.py needed)
try:
    import webrepl
    webrepl.start(password="{{WEBREPL_PASSWORD}}")
except Exception as e:
    print("WebREPL start failed:", e)
```

### Pattern 4: user_action Return Key (PROV-03)
**What:** Tools that need physical user intervention return a `user_action` dict before the action.

```python
# In flash_micropython MCP wrapper, BEFORE calling flash_firmware():
return {
    "user_action": "Hold the BOOT button on the ESP32 board, then briefly press the EN (reset) button while still holding BOOT. Release BOOT when you see 'Connecting...' in the output. The BOOT button is usually the smaller of two buttons on the board.",
    "reason": "ESP32 must be in bootloader mode for firmware flashing. The BOOT button forces the chip into download mode.",
    "next_step": "flash_micropython"
}
```

### Anti-Patterns to Avoid
- **Credentials in MCP tool parameters:** Never accept WiFi credentials as tool call arguments. Always read from server-side file.
- **Hardcoded credentials in boot.py template:** Placeholders are filled at deploy time, not stored in the repo.
- **Interactive webrepl_setup:** Don't use `import webrepl_setup` on the board. Use `webrepl.start(password=...)` which works programmatically.
- **network.hostname() after wlan.active():** The hostname must be set BEFORE activating the interface, or mDNS will use the default "espressif" hostname.

## mDNS Architecture Decision

### The Problem
CONTEXT.md D-08 specifies boot.py should advertise `_webrepl._tcp` mDNS service. The Pi-side `mdns_discovery.py` browses for `_webrepl._tcp.local.` services using zeroconf.

**Standard MicroPython ESP32 firmware (v1.27.0) does NOT support mDNS service advertisement.** It only supports:
- Hostname resolution via `network.hostname()` (e.g., `esp32-kitchen.local` resolves to the board's IP)
- A record responding (other devices can find the board by hostname)

The `micropython-mdns` third-party library by cbrand supports service advertisement BUT **requires custom firmware** with the built-in mDNS disabled (port 5353 conflict). This is incompatible with the project's use of standard MicroPython firmware from micropython.org.

### Recommended Approach

**Use hostname-based discovery as the primary mechanism:**

1. **boot.py sets `network.hostname("esp32-{hostname}")`** -- this enables `esp32-kitchen.local` resolution via built-in mDNS
2. **Update `discover_boards()` on the Pi** to support two discovery methods:
   - Primary: `_webrepl._tcp` service browse (works if user has custom firmware or future MicroPython adds service ads)
   - Fallback: hostname-pattern scanning (ping known hostnames, or use the board state registry)
3. **For this phase:** boot.py does WiFi + WebREPL + hostname. Service advertisement is a known gap documented in the tool description. Discovery via `hostname.local:8266` is the practical path.

This is the pragmatic choice. The built-in mDNS hostname resolution works reliably on v1.23+ and the project already uses v1.27.0. Service advertisement can be added later when MicroPython adds native support or when the project decides to use custom firmware.

**Confidence:** HIGH -- verified via official MicroPython docs, GitHub issues (#11450, #15296), and micropython-mdns library documentation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File deployment to board | Custom serial write | `deploy_file()` from `tools/file_deploy.py` | Already handles space check, integrity verify, error dicts |
| JSON config parsing | Custom parser | Python stdlib `json` | One function, zero dependencies |
| Temp file management | Manual file creation | `tempfile.NamedTemporaryFile` | OS handles cleanup on crash |
| WebREPL password setup | `webrepl_setup` interactive script | `webrepl.start(password="...")` | Programmatic, no user interaction needed on board |
| WiFi connect with timeout | Bare `wlan.connect()` | Loop with `time.sleep(0.5)` and counter | Must handle slow DHCP, avoid infinite hang |

## Common Pitfalls

### Pitfall 1: network.hostname() Timing
**What goes wrong:** Hostname set after `wlan.active(True)` -- mDNS registers with default "espressif" hostname.
**Why it happens:** The mDNS implementation initializes hostname once during connection.
**How to avoid:** Always call `network.hostname("name")` BEFORE `wlan.active(True)`.
**Warning signs:** Board is reachable at `espressif.local` instead of the configured hostname.

### Pitfall 2: WebREPL Password Length
**What goes wrong:** WebREPL silently fails or crashes with passwords outside 4-9 character range.
**Why it happens:** MicroPython WebREPL has a hard-coded password length restriction.
**How to avoid:** Validate password length in `deploy_boot_config` before template injection.
**Warning signs:** WebREPL doesn't start, `webrepl.start()` throws exception.

### Pitfall 3: Credentials File Permissions
**What goes wrong:** MCP server can't read `/etc/esp32-station/wifi.json` due to permissions.
**Why it happens:** File created as root (600), MCP server runs as `esp32` user.
**How to avoid:** File should be owned by the service user (`esp32:esp32`) with mode 600. Or owned by root with group readable by the service group.
**Warning signs:** `load_credentials()` returns `OSError: Permission denied`.

### Pitfall 4: Template Injection with Special Characters
**What goes wrong:** WiFi password containing `{{` or `}}` or backslashes breaks template injection.
**Why it happens:** Simple string replacement doesn't escape special characters.
**How to avoid:** Since boot.py uses Python string literals, passwords with quotes or backslashes need escaping. Use `repr()` for the password values in the template, or use `json.dumps()` to produce safely-quoted strings.
**Warning signs:** SyntaxError when boot.py runs on the board.

### Pitfall 5: Board Not in Flash Mode
**What goes wrong:** `esptool erase_flash` fails with "Failed to connect."
**Why it happens:** User didn't hold BOOT button.
**How to avoid:** Return `user_action` BEFORE the flash step. Wait for user confirmation. Include first-timer-friendly instructions about which button and when to release.
**Warning signs:** `erase_failed` error from `flash_firmware()`.

### Pitfall 6: WiFi Connection Timeout in boot.py
**What goes wrong:** Board hangs at boot waiting for WiFi.
**Why it happens:** No timeout on WiFi connection loop.
**How to avoid:** Use a bounded loop (e.g., 20 iterations * 500ms = 10 seconds max). Board continues to boot even without WiFi.
**Warning signs:** Board unresponsive via USB because boot.py blocks forever.

## Code Examples

### Verified: webrepl.start(password=...) API
```python
# Source: https://github.com/micropython/micropython-lib/blob/master/micropython/net/webrepl/webrepl_setup.py
# and https://docs.micropython.org/en/latest/esp32/quickref.html

# Programmatic WebREPL start (no webrepl_cfg.py needed):
import webrepl
webrepl.start(password="mypass")  # 4-9 chars required

# This is equivalent to running webrepl_setup interactively
# but can be done entirely in boot.py without user interaction.
```

### Verified: network.hostname() before connection
```python
# Source: https://docs.micropython.org/en/latest/library/network.html
# "you must set the hostname before activating/connecting your network interfaces"

import network
network.hostname("esp32-kitchen")  # MUST be before wlan.active(True)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("ssid", "password")
# After connection, board is reachable at esp32-kitchen.local
```

### Verified: WiFi connection pattern with timeout
```python
# Source: https://docs.micropython.org/en/latest/esp32/quickref.html

import network, machine
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("ssid", "key")
# Bounded wait -- don't use machine.idle() in a bare while loop
for _ in range(20):
    if wlan.isconnected():
        break
    import time
    time.sleep(0.5)
print("connected" if wlan.isconnected() else "failed")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `wlan.config(dhcp_hostname="name")` | `network.hostname("name")` | MicroPython v1.20 | Global hostname, works across all interfaces |
| `import webrepl_setup` (interactive) | `webrepl.start(password="...")` | Available since early versions | Programmatic, no board-side interaction |
| mDNS service ads (ESP-IDF C API) | Not exposed in MicroPython Python API | Ongoing | Service advertisement not available in standard firmware |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (version from project venv) |
| Config file | `pytest.ini` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROV-01 | flash_firmware always calls erase_flash | unit | `pytest tests/test_flash.py::test_erase_always_called -x` | Wave 0 |
| PROV-02 | deploy_boot_config reads creds, fills template, deploys | unit | `pytest tests/test_boot_deploy.py -x` | Wave 0 |
| PROV-03 | flash tool returns user_action before physical step | unit | `pytest tests/test_flash.py::test_user_action_guidance -x` | Wave 0 |
| PROV-04 | Tools separate, no orchestration tool | unit | `pytest tests/test_mcp_server.py::test_new_tools_registered -x` | Exists (update expected list) |
| SETUP-02 | Credentials loaded from file, never in MCP params | unit | `pytest tests/test_credentials.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] `tests/test_credentials.py` -- covers SETUP-02 (credential loading, missing file, invalid JSON, missing keys)
- [ ] `tests/test_boot_deploy.py` -- covers PROV-02 (template injection, deployment, hostname handling)
- [ ] Update `tests/test_mcp_server.py::test_new_tools_registered` expected list to include `deploy_boot_config`
- [ ] Update `tests/test_flash.py` with erase assertion (PROV-01) and user_action test (PROV-03)

## Open Questions

1. **mDNS service advertisement gap**
   - What we know: Standard MicroPython v1.27 cannot advertise `_webrepl._tcp` services. Only hostname.local works.
   - What's unclear: Whether the Pi-side `discover_boards()` should be updated now or deferred.
   - Recommendation: Boot.py sets hostname only (reliable). Document the gap in tool description. Update `discover_boards()` to also accept hostname-based discovery as a follow-up or within this phase. The existing `_webrepl._tcp` browse still works if users have custom firmware.

2. **user_action flow for flash_micropython**
   - What we know: D-13 says proactive guidance before the step. D-12 says via return dict.
   - What's unclear: Whether the MCP tool should return the user_action and then be called again, or whether it should be a two-call flow.
   - Recommendation: The `flash_micropython` tool description should mention BOOT button requirement. Claude (the LLM) reads the description, tells the user, waits for confirmation, then calls the tool. The tool itself can also return user_action guidance on connection failure as a fallback.

3. **Credentials file ownership**
   - What we know: File at `/etc/esp32-station/wifi.json`, mode 600.
   - What's unclear: Whether it should be owned by root or the service user.
   - Recommendation: Owned by the service user (`esp32:esp32`) with mode 600. This avoids permission issues. Document in the error message instructions.

## Sources

### Primary (HIGH confidence)
- [MicroPython network.hostname() docs](https://docs.micropython.org/en/latest/library/network.html) -- hostname API, timing requirements
- [MicroPython ESP32 Quick Reference](https://docs.micropython.org/en/latest/esp32/quickref.html) -- WiFi and WebREPL setup
- [MicroPython webrepl_setup.py source](https://github.com/micropython/micropython-lib/blob/master/micropython/net/webrepl/webrepl_setup.py) -- password format, `webrepl.start(password=...)` API
- [micropython/micropython#15296](https://github.com/micropython/micropython/issues/15296) -- mDNS fixed in v1.23.0
- [micropython/micropython#11450](https://github.com/micropython/micropython/issues/11450) -- network.hostname() and mDNS scope

### Secondary (MEDIUM confidence)
- [micropython-mdns library](https://github.com/cbrand/micropython-mdns) -- confirmed service advertisement requires custom firmware
- [micropython-mdns REFERENCE.md](https://github.com/cbrand/micropython-mdns/blob/main/REFERENCE.md) -- service advertisement API

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing patterns
- Architecture: HIGH -- follows established project patterns exactly (tools/, error dicts, mcp_server.py wrappers)
- Boot.py template: HIGH -- WiFi + WebREPL verified against official docs; hostname timing confirmed
- mDNS service advertisement: HIGH -- confirmed NOT possible with standard firmware (verified against library docs and GitHub issues)
- Pitfalls: HIGH -- all based on documented MicroPython behavior

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable domain, standard MicroPython APIs)
