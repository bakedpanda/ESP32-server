"""Tests for credentials utility: SETUP-02, PROV-02."""
import json
import pathlib

import pytest


def test_load_credentials_returns_dict_when_file_valid(tmp_path, monkeypatch):
    """load_credentials() returns dict with ssid, password, webrepl_password when file is valid."""
    creds = {"ssid": "TestNet", "password": "secret123", "webrepl_password": "webrepl1"}
    cred_file = tmp_path / "wifi.json"
    cred_file.write_text(json.dumps(creds))
    monkeypatch.setattr("tools.credentials.CREDENTIALS_PATH", cred_file)

    from tools.credentials import load_credentials
    result = load_credentials()

    assert result == creds
    assert "error" not in result


def test_load_credentials_returns_error_when_file_missing(tmp_path, monkeypatch):
    """load_credentials() returns credentials_not_found error when file does not exist."""
    monkeypatch.setattr("tools.credentials.CREDENTIALS_PATH", tmp_path / "wifi.json")

    from tools.credentials import load_credentials
    result = load_credentials()

    assert result["error"] == "credentials_not_found"
    assert "/etc/esp32-station/wifi.json" in result["detail"] or "wifi.json" in result["detail"]
    assert "ssid" in result["detail"].lower() or "JSON" in result["detail"]


def test_load_credentials_returns_error_when_json_invalid(tmp_path, monkeypatch):
    """load_credentials() returns credentials_invalid error when file contains bad JSON."""
    cred_file = tmp_path / "wifi.json"
    cred_file.write_text("not valid json {{{")
    monkeypatch.setattr("tools.credentials.CREDENTIALS_PATH", cred_file)

    from tools.credentials import load_credentials
    result = load_credentials()

    assert result["error"] == "credentials_invalid"
    assert "detail" in result


def test_load_credentials_returns_error_when_keys_missing(tmp_path, monkeypatch):
    """load_credentials() returns credentials_incomplete error when required keys are missing."""
    cred_file = tmp_path / "wifi.json"
    cred_file.write_text(json.dumps({"ssid": "TestNet"}))  # missing password, webrepl_password
    monkeypatch.setattr("tools.credentials.CREDENTIALS_PATH", cred_file)

    from tools.credentials import load_credentials
    result = load_credentials()

    assert result["error"] == "credentials_incomplete"
    assert "detail" in result


def test_credentials_path_is_correct():
    """CREDENTIALS_PATH equals pathlib.Path('/etc/esp32-station/wifi.json')."""
    from tools.credentials import CREDENTIALS_PATH
    assert CREDENTIALS_PATH == pathlib.Path("/etc/esp32-station/wifi.json")


def test_required_keys_is_correct():
    """REQUIRED_KEYS equals {'ssid', 'password', 'webrepl_password'}."""
    from tools.credentials import REQUIRED_KEYS
    assert REQUIRED_KEYS == {"ssid", "password", "webrepl_password"}
