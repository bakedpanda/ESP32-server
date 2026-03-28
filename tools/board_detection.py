"""Board detection: USB enumeration and chip identification."""
# Implementation in Plan 02 (01-02-PLAN.md)

def list_boards() -> list[dict]:
    """List connected ESP32 boards by USB VID/PID."""
    raise NotImplementedError

def detect_chip(port: str) -> dict:
    """Run esptool chip_id on the given port and return parsed chip info."""
    raise NotImplementedError

def load_board_state() -> dict:
    """Load boards.json from ~/.esp32-station/boards.json."""
    raise NotImplementedError

def save_board_state(state: dict) -> None:
    """Persist boards.json to ~/.esp32-station/boards.json."""
    raise NotImplementedError
