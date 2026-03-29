"""mDNS discovery of MicroPython boards advertising WebREPL.

Requirements covered: STAT-03.
"""
import time

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

WEBREPL_SERVICE = "_webrepl._tcp.local."
DEFAULT_TIMEOUT = 3


class _BoardListener(ServiceListener):
    """Listener that collects boards discovered via mDNS."""

    def __init__(self):
        self.boards: list[dict] = []
        self._zc: Zeroconf | None = None

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info and info.parsed_addresses():
            self.boards.append({
                "hostname": info.server.rstrip("."),
                "ip": info.parsed_addresses()[0],
                "port": info.port or 8266,
            })

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass


def discover_boards(timeout: int = DEFAULT_TIMEOUT) -> list[dict] | dict:
    """Discover MicroPython boards advertising WebREPL via mDNS.

    Browses for _webrepl._tcp services on the local network for ``timeout``
    seconds and returns a list of discovered boards.

    Args:
        timeout: Seconds to browse before returning. Default 3.

    Returns:
        list[dict]: Each dict has keys ``hostname``, ``ip``, ``port``.
                    Empty list if no boards found.
        dict: Error dict ``{"error": "mdns_failed", "detail": ...}`` on failure.
    """
    try:
        zc = Zeroconf()
        listener = _BoardListener()
        ServiceBrowser(zc, WEBREPL_SERVICE, listener)
        time.sleep(timeout)
        zc.close()
        return listener.boards
    except Exception as e:
        return {"error": "mdns_failed", "detail": str(e)}
