"""Tests for per-port serial locking: SerialLock context manager and port_to_slug helper.

Requirements covered: MCP-04 (concurrent access serialization), MCP-05 (structured errors).
"""
import pathlib
import threading
import time

import pytest


# ── port_to_slug ───────────────────────────────────────────────────────────

def test_port_to_slug_usb0():
    """port_to_slug converts /dev/ttyUSB0 -> dev_ttyUSB0."""
    from tools.serial_lock import port_to_slug
    assert port_to_slug("/dev/ttyUSB0") == "dev_ttyUSB0"


def test_port_to_slug_acm1():
    """port_to_slug converts /dev/ttyACM1 -> dev_ttyACM1."""
    from tools.serial_lock import port_to_slug
    assert port_to_slug("/dev/ttyACM1") == "dev_ttyACM1"


# ── Lock file lifecycle ────────────────────────────────────────────────────

def test_lock_file_created_on_acquire(tmp_path, monkeypatch):
    """Lock file exists at LOCK_DIR/dev_ttyUSB0.lock after __enter__."""
    import tools.serial_lock as sl
    monkeypatch.setattr(sl, "LOCK_DIR", tmp_path)

    with sl.SerialLock("/dev/ttyUSB0") as lock:
        assert lock._lock_path.exists(), "Lock file should exist while held"


def test_lock_file_removed_on_release(tmp_path, monkeypatch):
    """Lock file is deleted after exiting the SerialLock context."""
    import tools.serial_lock as sl
    monkeypatch.setattr(sl, "LOCK_DIR", tmp_path)

    lock_path = None
    with sl.SerialLock("/dev/ttyUSB0") as lock:
        lock_path = lock._lock_path

    assert not lock_path.exists(), "Lock file should be removed after context exit"


# ── Exclusivity ────────────────────────────────────────────────────────────

def test_lock_is_exclusive_same_port(tmp_path, monkeypatch):
    """Second SerialLock on the same port raises TimeoutError while first is held."""
    import tools.serial_lock as sl
    monkeypatch.setattr(sl, "LOCK_DIR", tmp_path)

    with sl.SerialLock("/dev/ttyUSB0", timeout=0.3):
        # Try to acquire a second lock with a very short timeout — must fail
        with pytest.raises(TimeoutError):
            with sl.SerialLock("/dev/ttyUSB0", timeout=0.3):
                pass


def test_different_ports_do_not_block(tmp_path, monkeypatch):
    """SerialLock on /dev/ttyUSB0 does not prevent SerialLock on /dev/ttyUSB1."""
    import tools.serial_lock as sl
    monkeypatch.setattr(sl, "LOCK_DIR", tmp_path)

    with sl.SerialLock("/dev/ttyUSB0"):
        # Should not raise — different port
        with sl.SerialLock("/dev/ttyUSB1"):
            pass  # both locks held simultaneously
