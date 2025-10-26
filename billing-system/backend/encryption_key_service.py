"""Encryption key management utilities for application services.

This module centralizes how symmetric encryption keys are loaded, rotated,
and validated at startup.  It supports environment-based keyrings for local
development and integrates with AWS KMS for production deployments.  Keys are
versioned so ciphertext can be associated with the correct material, and a
rotation schedule is tracked to satisfy compliance requirements (e.g. SOC 2
CC6.6 and PCI DSS 3.6).
"""

from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from cryptography.fernet import Fernet


logger = logging.getLogger(__name__)


class KeyManagementError(RuntimeError):
    """Raised when encryption key material cannot be loaded securely."""


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string if provided."""

    if not value:
        return None

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise KeyManagementError(f"Invalid datetime value: {value}") from exc

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _utcnow() -> datetime:
    """Return the current UTC time with timezone info."""

    return datetime.now(timezone.utc)


@dataclass
class RotationSchedule:
    """Tracks when encryption keys must be rotated."""

    interval_days: int
    last_rotated_at: datetime = field(default_factory=_utcnow)

    def next_rotation_due(self) -> datetime:
        return self.last_rotated_at + timedelta(days=self.interval_days)

    def is_due(self, reference_time: Optional[datetime] = None) -> bool:
        reference = reference_time or _utcnow()
        return reference >= self.next_rotation_due()

    def mark_rotated(self, rotated_at: Optional[datetime] = None) -> None:
        self.last_rotated_at = rotated_at or _utcnow()


@dataclass
class KeyManagementConfig:
    """Configuration for loading encryption keys."""

    provider: str
    active_key_version: str
    rotation_interval_days: int = 90
    last_rotated_at: Optional[datetime] = None
    keyring: Dict[str, str] = field(default_factory=dict)
    key_metadata: Dict[str, Dict[str, str]] = field(default_factory=dict)
    keyring_path: Optional[Path] = None
    kms_key_ids: Dict[str, str] = field(default_factory=dict)
    kms_encrypted_keys: Dict[str, str] = field(default_factory=dict)
    kms_region: Optional[str] = None
    kms_endpoint: Optional[str] = None

    @classmethod
    def from_environment(
        cls, manual_master_key: Optional[str] = None
    ) -> "KeyManagementConfig":
        provider = os.getenv("ENCRYPTION_KEY_PROVIDER", "env").lower()

        active_version = os.getenv("ENCRYPTION_ACTIVE_KEY_VERSION")
        rotation_interval = int(os.getenv("ENCRYPTION_ROTATION_INTERVAL_DAYS", "90"))
        last_rotated_at = _parse_datetime(os.getenv("ENCRYPTION_LAST_ROTATION_AT"))

        metadata: Dict[str, Dict[str, str]] = {}
        keyring: Dict[str, str] = {}
        keyring_path: Optional[Path] = None

        if manual_master_key:
            provider = "manual"
            active_version = active_version or "manual"
            keyring = {active_version: manual_master_key}
        else:
            keyring_env = os.getenv("ENCRYPTION_KEYRING")
            metadata_env = os.getenv("ENCRYPTION_KEY_METADATA")

            if keyring_env:
                parsed = json.loads(keyring_env)
                if "keys" in parsed:
                    keyring = parsed.get("keys", {})
                    metadata = parsed.get("metadata", {})
                    active_version = active_version or parsed.get("active_version")
                    rotation = parsed.get("rotation", {})
                    if rotation:
                        rotation_interval = int(
                            rotation.get("interval_days", rotation_interval)
                        )
                        last_rotated_at = _parse_datetime(
                            rotation.get("last_rotated_at")
                        )
                else:
                    keyring = parsed
            else:
                keyring_path = Path(
                    os.getenv(
                        "ENCRYPTION_KEYRING_PATH",
                        "config/encryption_keys.dev.json",
                    )
                )
                if keyring_path.exists():
                    with keyring_path.open("r", encoding="utf-8") as fh:
                        parsed = json.load(fh)
                    if isinstance(parsed, dict):
                        if "keys" in parsed:
                            keyring = parsed.get("keys", {})
                            metadata = parsed.get("metadata", {})
                            active_version = active_version or parsed.get(
                                "active_version"
                            )
                            rotation = parsed.get("rotation", {})
                            if rotation:
                                rotation_interval = int(
                                    rotation.get("interval_days", rotation_interval)
                                )
                                last_rotated_at = _parse_datetime(
                                    rotation.get("last_rotated_at")
                                )
                        else:
                            keyring = parsed
                else:
                    logger.warning(
                        "Encryption keyring file %s not found; encryption will fail "
                        "unless keys are provided via environment.",
                        keyring_path,
                    )

            if metadata_env:
                metadata.update(json.loads(metadata_env))

        kms_key_ids: Dict[str, str] = {}
        kms_encrypted_keys: Dict[str, str] = {}
        kms_region = None
        kms_endpoint = None

        if provider == "aws-kms":
            kms_key_ids = json.loads(os.getenv("ENCRYPTION_KMS_KEY_IDS", "{}"))
            kms_encrypted_keys = json.loads(
                os.getenv("ENCRYPTION_KMS_ENCRYPTED_KEYS", "{}")
            )
            default_key_id = os.getenv("ENCRYPTION_KMS_KEY_ID")
            if default_key_id and not kms_key_ids:
                kms_key_ids = {"default": default_key_id}
            kms_region = os.getenv("ENCRYPTION_KMS_REGION")
            kms_endpoint = os.getenv("ENCRYPTION_KMS_ENDPOINT")

        if not active_version:
            raise KeyManagementError(
                "ENCRYPTION_ACTIVE_KEY_VERSION must be specified for key management"
            )

        return cls(
            provider=provider,
            active_key_version=active_version,
            rotation_interval_days=rotation_interval,
            last_rotated_at=last_rotated_at,
            keyring=keyring,
            key_metadata=metadata,
            keyring_path=keyring_path,
            kms_key_ids=kms_key_ids,
            kms_encrypted_keys=kms_encrypted_keys,
            kms_region=kms_region,
            kms_endpoint=kms_endpoint,
        )


class KeyProvider:
    """Abstract base class for key providers."""

    name = "base"

    def load_keyring(self) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
        raise NotImplementedError

    def generate_new_key(self, version: str) -> Tuple[str, Dict[str, str]]:
        raise NotImplementedError

    def persist_keyring(
        self,
        keyring: Dict[str, str],
        metadata: Dict[str, Dict[str, str]],
        active: str,
        rotation_interval_days: int,
    ) -> None:
        """Persist the keyring if supported by the provider."""

    def supported_versions(self) -> Iterable[str]:
        return []


class EnvironmentKeyProvider(KeyProvider):
    """Loads keys from environment variables or configuration files."""

    name = "env"

    def __init__(
        self,
        keyring: Dict[str, str],
        metadata: Dict[str, Dict[str, str]],
        keyring_path: Optional[Path] = None,
    ) -> None:
        self._keyring = keyring
        self._metadata = metadata
        self._keyring_path = keyring_path

    def load_keyring(self) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
        if not self._keyring:
            raise KeyManagementError(
                "No encryption keys available. Set ENCRYPTION_KEYRING or provide "
                "a configuration file via ENCRYPTION_KEYRING_PATH."
            )
        return dict(self._keyring), dict(self._metadata)

    def generate_new_key(self, version: str) -> Tuple[str, Dict[str, str]]:
        new_key = Fernet.generate_key().decode()
        return new_key, {"source": "environment", "version": version}

    def persist_keyring(
        self,
        keyring: Dict[str, str],
        metadata: Dict[str, Dict[str, str]],
        active: str,
        rotation_interval_days: int,
    ) -> None:
        if not self._keyring_path:
            logger.info(
                "No keyring path configured; skipping persistence of rotated keys."
            )
            return

        payload = {
            "active_version": active,
            "keys": keyring,
            "metadata": metadata,
            "rotation": {
                "last_rotated_at": _utcnow().isoformat(),
                "interval_days": rotation_interval_days,
            },
        }
        with self._keyring_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        logger.info("Persisted updated encryption keyring to %s", self._keyring_path)


class AWSKMSKeyProvider(KeyProvider):
    """Loads encryption keys from AWS KMS."""

    name = "aws-kms"

    def __init__(
        self,
        key_ids: Dict[str, str],
        encrypted_keys: Dict[str, str],
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ) -> None:
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - import guard
            raise KeyManagementError(
                "boto3 must be installed to use the AWS KMS key provider"
            ) from exc

        if not encrypted_keys:
            raise KeyManagementError(
                "No encrypted data keys provided for AWS KMS. Populate "
                "ENCRYPTION_KMS_ENCRYPTED_KEYS with ciphertext blobs."
            )

        self._key_ids = key_ids
        self._encrypted_keys = encrypted_keys
        self._client = boto3.client(
            "kms", region_name=region_name, endpoint_url=endpoint_url
        )

    def _decode_ciphertext(self, ciphertext_b64: str) -> bytes:
        try:
            return base64.b64decode(ciphertext_b64)
        except Exception as exc:  # pragma: no cover - defensive
            raise KeyManagementError("Invalid base64 ciphertext for AWS KMS") from exc

    def load_keyring(self) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
        keyring: Dict[str, str] = {}
        metadata: Dict[str, Dict[str, str]] = {}

        for version, ciphertext_b64 in self._encrypted_keys.items():
            ciphertext = self._decode_ciphertext(ciphertext_b64)
            key_id = self._key_ids.get(version) or self._key_ids.get("default")
            decrypt_kwargs = {"CiphertextBlob": ciphertext}
            if key_id:
                decrypt_kwargs["KeyId"] = key_id

            response = self._client.decrypt(**decrypt_kwargs)
            plaintext_key: bytes = response["Plaintext"]
            keyring[version] = base64.urlsafe_b64encode(plaintext_key).decode()
            metadata[version] = {
                "kms_key_id": response.get("KeyId") or key_id or "",
                "source": "aws-kms",
            }

        if not keyring:
            raise KeyManagementError("AWS KMS did not return any decryptable keys")

        return keyring, metadata

    def generate_new_key(self, version: str) -> Tuple[str, Dict[str, str]]:
        key_id = self._key_ids.get(version) or self._key_ids.get("default")
        if not key_id:
            raise KeyManagementError(
                f"No AWS KMS KeyId configured for version '{version}'. Set "
                "ENCRYPTION_KMS_KEY_ID or include the version in "
                "ENCRYPTION_KMS_KEY_IDS."
            )

        response = self._client.generate_data_key(KeyId=key_id, KeySpec="AES_256")
        plaintext_key: bytes = response["Plaintext"]
        encrypted_blob: bytes = response["CiphertextBlob"]

        provider_metadata = {
            "kms_key_id": response.get("KeyId", key_id),
            "ciphertext": base64.b64encode(encrypted_blob).decode(),
            "source": "aws-kms",
        }
        encoded_key = base64.urlsafe_b64encode(plaintext_key).decode()
        return encoded_key, provider_metadata


class EncryptionKeyService:
    """High-level service responsible for encryption key lifecycle."""

    def __init__(self, master_key: Optional[str] = None) -> None:
        self.config = KeyManagementConfig.from_environment(manual_master_key=master_key)
        self.rotation_schedule = RotationSchedule(
            interval_days=self.config.rotation_interval_days,
            last_rotated_at=self.config.last_rotated_at or _utcnow(),
        )

        self._keyring: Dict[str, str] = {}
        self._metadata: Dict[str, Dict[str, str]] = {}
        self._fernet_cache: Dict[str, Fernet] = {}

        self.provider = self._build_provider()
        self._load_keys()

    @property
    def active_key_version(self) -> str:
        return self.config.active_key_version

    def _build_provider(self) -> KeyProvider:
        if self.config.provider in ("env", "manual"):
            return EnvironmentKeyProvider(
                keyring=self.config.keyring,
                metadata=self.config.key_metadata,
                keyring_path=self.config.keyring_path,
            )
        if self.config.provider == "aws-kms":
            return AWSKMSKeyProvider(
                key_ids=self.config.kms_key_ids,
                encrypted_keys=self.config.kms_encrypted_keys,
                region_name=self.config.kms_region,
                endpoint_url=self.config.kms_endpoint,
            )
        raise KeyManagementError(f"Unsupported key provider: {self.config.provider}")

    def _load_keys(self) -> None:
        keyring, metadata = self.provider.load_keyring()

        if self.config.active_key_version not in keyring:
            raise KeyManagementError(
                f"Active encryption key version '{self.config.active_key_version}' "
                "is not present in the configured keyring"
            )

        self._keyring = keyring
        self._metadata = metadata

        for version, key in keyring.items():
            self._fernet_cache[version] = Fernet(
                key.encode() if isinstance(key, str) else key
            )

        logger.info(
            "Loaded %d encryption key version(s); active version=%s",
            len(self._keyring),
            self.config.active_key_version,
        )

    def get_fernet(self, version: Optional[str] = None) -> Fernet:
        ver = version or self.config.active_key_version
        try:
            return self._fernet_cache[ver]
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyManagementError(f"Unknown encryption key version '{ver}'") from exc

    def encrypt(self, plain_text: str, version: Optional[str] = None) -> bytes:
        if plain_text is None:
            return None

        ver = version or self.config.active_key_version
        fernet = self.get_fernet(ver)
        token = fernet.encrypt(plain_text.encode())

        payload = {
            "version": ver,
            "ciphertext": token.decode(),
        }
        return json.dumps(payload).encode()

    def decrypt(self, encrypted_data: bytes) -> str:
        if not encrypted_data:
            return None

        version = None
        ciphertext: Optional[bytes] = None

        try:
            decoded = json.loads(
                encrypted_data.decode() if isinstance(encrypted_data, bytes) else encrypted_data
            )
            if isinstance(decoded, dict) and "version" in decoded:
                version = decoded.get("version")
                ciphertext_value = decoded.get("ciphertext")
                if ciphertext_value is None:
                    raise KeyManagementError("Encrypted payload missing ciphertext")
                ciphertext = ciphertext_value.encode()
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Legacy payload – assume active key was used without version metadata.
            ciphertext = encrypted_data if isinstance(encrypted_data, bytes) else str(encrypted_data).encode()
            version = self.config.active_key_version

        if version not in self._keyring:
            raise KeyManagementError(
                f"Cannot decrypt payload – key version '{version}' is not available"
            )

        fernet = self.get_fernet(version)
        return fernet.decrypt(ciphertext).decode()

    def is_rotation_due(self) -> bool:
        return self.rotation_schedule.is_due()

    def rotation_status(self) -> Dict[str, str]:
        next_due = self.rotation_schedule.next_rotation_due()
        return {
            "interval_days": str(self.rotation_schedule.interval_days),
            "last_rotated_at": self.rotation_schedule.last_rotated_at.isoformat(),
            "next_rotation_due": next_due.isoformat(),
            "is_due": self.rotation_schedule.is_due(),
        }

    def rotate_key(self, new_version: Optional[str] = None) -> Dict[str, str]:
        target_version = new_version or self._generate_next_version()
        encoded_key, provider_metadata = self.provider.generate_new_key(target_version)

        self._keyring[target_version] = encoded_key
        self._metadata[target_version] = {
            **provider_metadata,
            "created_at": _utcnow().isoformat(),
        }
        self._fernet_cache[target_version] = Fernet(encoded_key.encode())
        self.config.active_key_version = target_version
        self.rotation_schedule.mark_rotated()

        self.provider.persist_keyring(
            self._keyring,
            self._metadata,
            target_version,
            rotation_interval_days=self.rotation_schedule.interval_days,
        )

        logger.info("Rotated encryption key; new active version=%s", target_version)

        return {
            "version": target_version,
            "metadata": provider_metadata,
        }

    def _generate_next_version(self) -> str:
        existing_versions = [v for v in self._keyring.keys() if v.startswith("v")]
        if not existing_versions:
            return "v1"

        latest = max(
            (int(v[1:]) for v in existing_versions if v[1:].isdigit()),
            default=0,
        )
        return f"v{latest + 1}"


__all__ = [
    "AWSKMSKeyProvider",
    "EncryptionKeyService",
    "EnvironmentKeyProvider",
    "KeyManagementConfig",
    "KeyManagementError",
    "RotationSchedule",
]

