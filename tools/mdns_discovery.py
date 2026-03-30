"""Discovery of MicroPython boards via hostname.local resolution.

Requirements covered: STAT-03.

MicroPython's WebREPL does not advertise a _webrepl._tcp mDNS service record,
so service browsing doesn't work. Instead we resolve known hostnames saved to
boards.json by deploy_boot_config using the system resolver (avahi/nss-mdns on
Raspberry Pi OS resolves .local hostnames automatically).
"""
import socket

from tools.board_detection import load_board_state

WEBREPL_PORT = 8266
RESOLVE_TIMEOUT = 3.0


def discover_boards(timeout: int = RESOLVE_TIMEOUT) -> list[dict] | dict:
    """Discover MicroPython boards by resolving known hostnames on the LAN.

    Reads hostnames saved by deploy_boot_config from boards.json and attempts
    to resolve each as hostname.local. Returns boards that resolve successfully.

    Args:
        timeout: Seconds to wait per hostname resolution attempt. Default 3.

    Returns:
        list[dict]: Each dict has keys ``hostname``, ``ip``, ``port``.
                    Empty list if no boards found.
        dict: Error dict ``{"error": "discovery_failed", "detail": ...}`` on failure.
    """
    try:
        state = load_board_state()
        hostnames = [
            v["hostname"]
            for v in state.values()
            if isinstance(v, dict) and v.get("hostname")
        ]

        if not hostnames:
            return []

        found = []
        prev_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            for hostname in hostnames:
                try:
                    results = socket.getaddrinfo(
                        hostname + ".local", WEBREPL_PORT, socket.AF_INET
                    )
                    ip = results[0][4][0]
                    found.append({"hostname": hostname + ".local", "ip": ip, "port": WEBREPL_PORT})
                except OSError:
                    pass
        finally:
            socket.setdefaulttimeout(prev_timeout)

        return found
    except Exception as e:
        return {"error": "discovery_failed", "detail": str(e)}
