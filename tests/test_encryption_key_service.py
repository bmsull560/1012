import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "billing-system"
BACKEND_PATH = PACKAGE_ROOT / "backend"

billing_system_pkg = types.ModuleType("billing_system")
billing_system_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules.setdefault("billing_system", billing_system_pkg)

backend_pkg = types.ModuleType("billing_system.backend")
backend_pkg.__path__ = [str(BACKEND_PATH)]
sys.modules.setdefault("billing_system.backend", backend_pkg)

MODULE_PATH = BACKEND_PATH / "database_security.py"

spec = importlib.util.spec_from_file_location(
    "billing_system.backend.database_security", MODULE_PATH
)
if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
    raise RuntimeError("Unable to load database_security module for tests")
database_security = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = database_security
spec.loader.exec_module(database_security)

EncryptionManager = database_security.EncryptionManager


def _configure_env(monkeypatch) -> str:
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY_PROVIDER", "env")
    monkeypatch.setenv("ENCRYPTION_ACTIVE_KEY_VERSION", "v1")
    monkeypatch.setenv("ENCRYPTION_KEYRING", json.dumps({"v1": key}))
    monkeypatch.delenv("ENCRYPTION_KEYRING_PATH", raising=False)
    return key


def test_encrypt_decrypt_with_versioned_payload(monkeypatch):
    _configure_env(monkeypatch)

    manager = EncryptionManager()

    ciphertext = manager.encrypt("super-secret")
    payload = json.loads(ciphertext.decode())

    assert payload["version"] == "v1"
    assert manager.decrypt(ciphertext) == "super-secret"


def test_decrypt_legacy_payload(monkeypatch):
    key = _configure_env(monkeypatch)

    manager = EncryptionManager()

    legacy_token = Fernet(key.encode()).encrypt(b"legacy-data")
    assert manager.decrypt(legacy_token) == "legacy-data"


def test_missing_key_configuration_fails(monkeypatch):
    monkeypatch.delenv("ENCRYPTION_KEY_PROVIDER", raising=False)
    monkeypatch.delenv("ENCRYPTION_KEYRING", raising=False)
    monkeypatch.setenv("ENCRYPTION_KEY_PROVIDER", "env")
    monkeypatch.setenv("ENCRYPTION_ACTIVE_KEY_VERSION", "v1")
    monkeypatch.setenv("ENCRYPTION_KEYRING_PATH", "config/missing_keys.json")

    with pytest.raises(RuntimeError):
        EncryptionManager()
