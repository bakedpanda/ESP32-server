"""Boot configuration deployment for ESP32 boards.

Requirements covered: PROV-02 (boot.py with WiFi + WebREPL from Pi-local creds).
"""
import os
import pathlib
import tempfile

from tools.credentials import load_credentials
from tools.file_deploy import deploy_file

TEMPLATE_PATH = pathlib.Path(__file__).parent.parent / "templates" / "boot.py.tpl"


def deploy_boot_config(port: str, hostname: str | None = None) -> dict:
    """Deploy boot.py with WiFi + WebREPL + hostname config to the board.

    Reads credentials from /etc/esp32-station/wifi.json (never from MCP params).
    Fills templates/boot.py.tpl with credential values and hostname.
    Deploys the rendered boot.py to the board via mpremote.

    Per D-11: overwrites existing boot.py silently (provisioning implies fresh board).

    Args:
        port: Serial port path, e.g. "/dev/ttyUSB0"
        hostname: Board hostname for mDNS (default: "esp32"). Used as network.hostname().

    Returns:
        {"port": port, "files_written": ["boot.py"]} on success.
        {"error": error_code, "detail": ...} on failure.
    """
    # Load credentials from Pi-local file (SETUP-02: never from MCP params)
    creds = load_credentials()
    if "error" in creds:
        return creds

    # Validate WebREPL password length (Pitfall 2: must be 4-9 chars)
    webrepl_pass = creds["webrepl_password"]
    if not (4 <= len(webrepl_pass) <= 9):
        return {
            "error": "webrepl_password_invalid",
            "detail": "WebREPL password must be 4-9 characters",
        }

    # Read template
    if not TEMPLATE_PATH.exists():
        return {
            "error": "template_not_found",
            "detail": f"boot.py template not found at {TEMPLATE_PATH}",
        }
    template = TEMPLATE_PATH.read_text()

    # Fill placeholders (D-07: simple .replace())
    hostname = hostname or "esp32"
    boot_code = (
        template
        .replace("{{SSID}}", creds["ssid"])
        .replace("{{PASSWORD}}", creds["password"])
        .replace("{{WEBREPL_PASSWORD}}", webrepl_pass)
        .replace("{{HOSTNAME}}", hostname)
    )

    # Write to temp file and deploy via mpremote (D-10: self-contained)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(boot_code)
        tmp_path = f.name

    try:
        result = deploy_file(port, tmp_path, "boot.py")
    finally:
        os.unlink(tmp_path)

    return result
