"""Firmware download, caching, and flashing via esptool."""
# Implementation in Plan 03 (01-03-PLAN.md)

def get_firmware_path(chip: str) -> "pathlib.Path":
    """Return local cache path for chip's firmware .bin. Downloads if stale."""
    raise NotImplementedError

def flash_firmware(port: str, chip: str) -> dict:
    """Erase flash and write MicroPython firmware for the given chip variant."""
    raise NotImplementedError
