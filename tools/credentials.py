"""WiFi and WebREPL credential loading from Pi-local file.

Requirements covered: SETUP-02 (credentials on Pi, never via MCP), PROV-02 (boot.py needs creds).
Per D-04: shared utility, error dict pattern (D-20), lazy validation (D-05).
"""
import json
import pathlib

CREDENTIALS_PATH = pathlib.Path("/etc/esp32-station/wifi.json")
REQUIRED_KEYS = {"ssid", "password", "webrepl_password"}


def load_credentials() -> dict:
    """Load WiFi + WebREPL credentials from the Pi-local file.

    Returns credential dict on success, or error dict with setup instructions.
    Per D-06: never raises -- returns error dict with file path + example JSON.
    """
    if not CREDENTIALS_PATH.exists():
        return {
            "error": "credentials_not_found",
            "detail": (
                f"Credentials file not found at {CREDENTIALS_PATH}. "
                "Create it with:\n"
                "  sudo mkdir -p /etc/esp32-station\n"
                f"  sudo tee {CREDENTIALS_PATH} << 'EOF'\n"
                '  {"ssid": "YOUR_SSID", "password": "YOUR_WIFI_PASSWORD", '
                '"webrepl_password": "YOUR_WEBREPL_PASS"}\n'
                "  EOF\n"
                f"  sudo chmod 600 {CREDENTIALS_PATH}"
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
