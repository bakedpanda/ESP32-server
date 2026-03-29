"""Tests for boot configuration deployment: PROV-02 (boot.py with WiFi + WebREPL from Pi-local creds)."""
import pathlib
import pytest
from unittest.mock import patch, MagicMock


# ── Fixtures ──────────────────────────────────────────────────────────────

FAKE_CREDS = {
    "ssid": "TestNetwork",
    "password": "testpass123",
    "webrepl_password": "webrepl",
}

TEMPLATE_CONTENT = (pathlib.Path(__file__).parent.parent / "templates" / "boot.py.tpl").read_text()


@pytest.fixture
def mock_creds():
    """Monkeypatch load_credentials to return test creds."""
    with patch("tools.boot_deploy.load_credentials", return_value=dict(FAKE_CREDS)) as m:
        yield m


@pytest.fixture
def mock_deploy():
    """Monkeypatch deploy_file to capture args (including temp file content) and return success.

    The side_effect reads the temp file before deploy_boot_config deletes it,
    storing the content in mock_deploy.captured_content for test assertions.
    """
    captured = {}

    def _capture_deploy(port, local_path, remote_path=None):
        captured["content"] = pathlib.Path(local_path).read_text()
        captured["local_path"] = local_path
        return {"port": port, "files_written": [remote_path or pathlib.Path(local_path).name]}

    m = MagicMock(side_effect=_capture_deploy)
    m.captured = captured
    with patch("tools.boot_deploy.deploy_file", m):
        yield m


@pytest.fixture
def mock_template(tmp_path):
    """Monkeypatch TEMPLATE_PATH to a tmp file with real template content."""
    tpl = tmp_path / "boot.py.tpl"
    tpl.write_text(TEMPLATE_CONTENT)
    with patch("tools.boot_deploy.TEMPLATE_PATH", tpl):
        yield tpl


# ── Tests ─────────────────────────────────────────────────────────────────

def test_deploy_boot_config_calls_load_and_deploy(mock_creds, mock_deploy, mock_template):
    """Test 1: deploy_boot_config calls load_credentials, fills template, deploys via deploy_file."""
    from tools.boot_deploy import deploy_boot_config
    result = deploy_boot_config("/dev/ttyUSB0")

    mock_creds.assert_called_once()
    mock_deploy.assert_called_once()
    call_args = mock_deploy.call_args
    assert call_args[0][0] == "/dev/ttyUSB0"  # port
    assert call_args[0][2] == "boot.py"  # remote_path
    assert result == {"port": "/dev/ttyUSB0", "files_written": ["boot.py"]}


def test_deploy_boot_config_returns_cred_error(mock_template):
    """Test 2: deploy_boot_config returns credential error dict unchanged."""
    cred_error = {"error": "credentials_not_found", "detail": "File not found"}
    with patch("tools.boot_deploy.load_credentials", return_value=cred_error):
        from tools.boot_deploy import deploy_boot_config
        result = deploy_boot_config("/dev/ttyUSB0")
    assert result == cred_error


def test_deploy_boot_config_uses_custom_hostname(mock_creds, mock_deploy, mock_template):
    """Test 3: deploy_boot_config uses hostname parameter when provided."""
    from tools.boot_deploy import deploy_boot_config
    deploy_boot_config("/dev/ttyUSB0", hostname="esp32-kitchen")

    content = mock_deploy.captured["content"]
    assert "esp32-kitchen" in content
    assert "{{HOSTNAME}}" not in content


def test_deploy_boot_config_defaults_hostname(mock_creds, mock_deploy, mock_template):
    """Test 4: deploy_boot_config defaults hostname to 'esp32' when None."""
    from tools.boot_deploy import deploy_boot_config
    deploy_boot_config("/dev/ttyUSB0")

    content = mock_deploy.captured["content"]
    assert 'hostname("esp32")' in content


def test_deploy_boot_config_webrepl_password_too_short(mock_template):
    """Test 5a: deploy_boot_config returns error when WebREPL password is too short."""
    short_creds = dict(FAKE_CREDS, webrepl_password="abc")
    with patch("tools.boot_deploy.load_credentials", return_value=short_creds):
        from tools.boot_deploy import deploy_boot_config
        result = deploy_boot_config("/dev/ttyUSB0")
    assert result["error"] == "webrepl_password_invalid"
    assert "4-9" in result["detail"]


def test_deploy_boot_config_webrepl_password_too_long(mock_template):
    """Test 5b: deploy_boot_config returns error when WebREPL password is too long."""
    long_creds = dict(FAKE_CREDS, webrepl_password="1234567890")
    with patch("tools.boot_deploy.load_credentials", return_value=long_creds):
        from tools.boot_deploy import deploy_boot_config
        result = deploy_boot_config("/dev/ttyUSB0")
    assert result["error"] == "webrepl_password_invalid"
    assert "4-9" in result["detail"]


def test_deploy_boot_config_template_not_found(mock_creds):
    """Test 6: deploy_boot_config returns error when template is missing."""
    with patch("tools.boot_deploy.TEMPLATE_PATH", pathlib.Path("/nonexistent/boot.py.tpl")):
        from tools.boot_deploy import deploy_boot_config
        result = deploy_boot_config("/dev/ttyUSB0")
    assert result["error"] == "template_not_found"


def test_deploy_boot_config_fills_placeholders(mock_creds, mock_deploy, mock_template):
    """Test 7: Temp file contains actual creds, not placeholders."""
    from tools.boot_deploy import deploy_boot_config
    deploy_boot_config("/dev/ttyUSB0")

    content = mock_deploy.captured["content"]
    assert "TestNetwork" in content
    assert "testpass123" in content
    assert "webrepl" in content
    assert "{{SSID}}" not in content
    assert "{{PASSWORD}}" not in content
    assert "{{WEBREPL_PASSWORD}}" not in content
    assert "{{HOSTNAME}}" not in content
