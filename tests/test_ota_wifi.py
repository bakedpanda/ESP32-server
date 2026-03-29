"""Tests for OTA WiFi deployment module: OTA-01, OTA-02.

Tests cover:
  - deploy_ota_wifi success path (mocked subprocess)
  - payload too large returns ota_payload_too_large
  - timeout returns wifi_unreachable with fallback hint
  - connection error returns wifi_unreachable with fallback hint
  - webrepl_cli.py missing returns webrepl_cli_missing
"""
import pathlib
import subprocess
import pytest
from unittest.mock import patch, MagicMock


def _make_run_result(returncode=0, stdout="", stderr=""):
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


def test_deploy_ota_wifi_success(tmp_path):
    """Success path: subprocess exits 0, returns wifi transport dict."""
    from tools.ota_wifi import deploy_ota_wifi
    local_file = tmp_path / "main.py"
    local_file.write_bytes(b"# main" * 100)  # small file, well under 200KB

    run_result = _make_run_result(returncode=0, stdout="", stderr="")
    with patch("subprocess.run", return_value=run_result):
        result = deploy_ota_wifi("192.168.1.42", str(local_file), "/main.py", "testpass")

    assert result == {"port": "192.168.1.42", "files_written": ["/main.py"], "transport": "wifi"}


def test_deploy_ota_wifi_too_large(tmp_path):
    """File exceeding 200KB limit returns ota_payload_too_large without calling subprocess."""
    from tools.ota_wifi import deploy_ota_wifi
    local_file = tmp_path / "big.py"
    local_file.write_bytes(b"x" * (200 * 1024 + 1))  # 1 byte over limit

    result = deploy_ota_wifi("192.168.1.42", str(local_file), "/big.py", "testpass")

    assert result["error"] == "ota_payload_too_large"
    assert "200" in result["detail"] or "limit" in result["detail"].lower()


def test_deploy_ota_wifi_timeout(tmp_path):
    """subprocess.TimeoutExpired returns wifi_unreachable with fallback hint."""
    from tools.ota_wifi import deploy_ota_wifi
    local_file = tmp_path / "main.py"
    local_file.write_bytes(b"# main" * 10)

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="webrepl_cli.py", timeout=30)):
        result = deploy_ota_wifi("192.168.1.42", str(local_file), "/main.py", "testpass")

    assert result["error"] == "wifi_unreachable"
    assert result.get("fallback") == "use deploy_file_to_board"


def test_deploy_ota_wifi_connection_error(tmp_path):
    """returncode=1 with connection-related stderr returns wifi_unreachable with fallback hint."""
    from tools.ota_wifi import deploy_ota_wifi
    local_file = tmp_path / "main.py"
    local_file.write_bytes(b"# main" * 10)

    run_result = _make_run_result(returncode=1, stderr="Connection refused: 192.168.1.42:8266")
    with patch("subprocess.run", return_value=run_result):
        result = deploy_ota_wifi("192.168.1.42", str(local_file), "/main.py", "testpass")

    assert result["error"] == "wifi_unreachable"
    assert result.get("fallback") == "use deploy_file_to_board"


def test_webrepl_cli_missing(tmp_path, monkeypatch):
    """Missing webrepl_cli.py returns webrepl_cli_missing error before subprocess call."""
    from tools import ota_wifi
    monkeypatch.setattr(ota_wifi, "WEBREPL_CLI", tmp_path / "nonexistent_webrepl_cli.py")

    local_file = tmp_path / "main.py"
    local_file.write_bytes(b"# main" * 10)

    result = ota_wifi.deploy_ota_wifi("192.168.1.42", str(local_file), "/main.py", "testpass")

    assert result["error"] == "webrepl_cli_missing"
    assert "tools/vendor/webrepl_cli.py" in result["detail"] or "webrepl_cli" in result["detail"]
