"""Authentication and authorization module for ValueVerse Billing System."""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Set
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db
from .models import Organization

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-this-in-production":
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: JWT_SECRET_KEY environment variable must be set to a secure, "
        "non-default value. This is required for production security. "
        "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Reduced from 30 for better security
REFRESH_TOKEN_EXPIRE_DAYS = 7

# OIDC configuration
ENABLE_OIDC = os.getenv("ENABLE_OIDC_AUTH", "true").lower() not in {"0", "false", "no"}
OIDC_ISSUER = os.getenv("OIDC_ISSUER_URL")
OIDC_METADATA_URL = os.getenv("OIDC_METADATA_URL")
OIDC_JWKS_URL = os.getenv("OIDC_JWKS_URL")
OIDC_AUDIENCE = [aud.strip() for aud in os.getenv("OIDC_AUDIENCE", "").split(",") if aud.strip()]
OIDC_ALLOWED_ALGORITHMS = [alg.strip() for alg in os.getenv("OIDC_ALLOWED_ALGORITHMS", "RS256").split(",") if alg.strip()]
OIDC_ROLE_CLAIM = os.getenv("OIDC_ROLE_CLAIM", "roles")
OIDC_PERMISSION_CLAIM = os.getenv("OIDC_PERMISSION_CLAIM", "permissions")
OIDC_SCOPE_CLAIM = os.getenv("OIDC_SCOPE_CLAIM", "scope")
OIDC_ORGANIZATION_CLAIM = os.getenv("OIDC_ORGANIZATION_CLAIM", "organization_id")
OIDC_USER_ID_CLAIM = os.getenv("OIDC_USER_ID_CLAIM", "sub")
OIDC_EMAIL_CLAIM = os.getenv("OIDC_EMAIL_CLAIM", "email")
OIDC_ACTIVE_CLAIM = os.getenv("OIDC_ACTIVE_CLAIM", "is_active")
OIDC_ADMIN_CLAIM = os.getenv("OIDC_ADMIN_CLAIM", "is_admin")
OIDC_SESSION_CLAIM = os.getenv("OIDC_SESSION_CLAIM", "sid")
OIDC_TOKEN_TYPE_CLAIM = os.getenv("OIDC_TOKEN_TYPE_CLAIM", "typ")
OIDC_ACCESS_TOKEN_VALUES = {
    value.strip()
    for value in os.getenv("OIDC_ACCESS_TOKEN_VALUES", "access,at+jwt").split(",")
    if value.strip()
}
OIDC_REFRESH_TOKEN_VALUES = {
    value.strip()
    for value in os.getenv("OIDC_REFRESH_TOKEN_VALUES", "refresh,rt+jwt").split(",")
    if value.strip()
}
OIDC_ADMIN_ROLES = {
    value.strip()
    for value in os.getenv("OIDC_ADMIN_ROLES", "admin,billing_admin").split(",")
    if value.strip()
}
OIDC_CLOCK_SKEW_SECONDS = int(os.getenv("OIDC_CLOCK_SKEW_SECONDS", "120"))
OIDC_JWKS_CACHE_SECONDS = int(os.getenv("OIDC_JWKS_CACHE_SECONDS", "3600"))

if ENABLE_OIDC:
    if not OIDC_ISSUER:
        raise RuntimeError(
            "OIDC_ISSUER_URL environment variable must be set when ENABLE_OIDC_AUTH is enabled"
        )
    if not (OIDC_JWKS_URL or OIDC_METADATA_URL):
        OIDC_METADATA_URL = f"{OIDC_ISSUER.rstrip('/')}/.well-known/openid-configuration"


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class JWKSFetchError(Exception):
    """Raised when JWKS keys cannot be retrieved from the IdP."""


class JWKSCache:
    """Async cache for JWKS keys with automatic refresh and cache control support."""

    def __init__(
        self,
        metadata_url: Optional[str],
        jwks_url: Optional[str],
        cache_seconds: int,
    ) -> None:
        self._metadata_url = metadata_url
        self._jwks_url = jwks_url
        self._cache_seconds = cache_seconds
        self._keys: Dict[str, Dict[str, Any]] = {}
        self._expires_at: datetime = datetime.min
        self._lock = asyncio.Lock()

    async def get_signing_key(self, kid: str) -> Dict[str, Any]:
        """Return the signing key for the provided key identifier."""

        async with self._lock:
            await self._refresh_if_needed()
            key = self._keys.get(kid)
            if key:
                return key

            # Kid not cached (rotated key?) refresh immediately once more
            await self._refresh(force=True)
            key = self._keys.get(kid)
            if not key:
                raise JWKSFetchError(
                    f"Signing key with kid '{kid}' was not found in JWKS response"
                )
            return key

    async def _refresh_if_needed(self) -> None:
        if datetime.utcnow() >= self._expires_at:
            await self._refresh()

    async def _refresh(self, force: bool = False) -> None:
        """Refresh JWKS keys from the IdP."""

        if not force and datetime.utcnow() < self._expires_at:
            return

        jwks_url = await self._resolve_jwks_url()
        if not jwks_url:
            raise JWKSFetchError(
                "Unable to resolve JWKS URL from OpenID configuration"
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise JWKSFetchError(f"Failed to download JWKS keys: {exc}") from exc

        data = response.json()
        keys = data.get("keys", [])
        if not keys:
            raise JWKSFetchError("JWKS response did not contain any signing keys")

        self._keys = {key["kid"]: key for key in keys if "kid" in key}
        if not self._keys:
            raise JWKSFetchError("JWKS response is missing required 'kid' attributes")

        cache_seconds = self._extract_cache_seconds(response.headers)
        if cache_seconds is None:
            cache_seconds = self._cache_seconds

        self._expires_at = datetime.utcnow() + timedelta(seconds=cache_seconds)

    async def _resolve_jwks_url(self) -> Optional[str]:
        if self._jwks_url:
            return self._jwks_url

        if not self._metadata_url:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self._metadata_url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise JWKSFetchError(
                f"Failed to download OIDC metadata from {self._metadata_url}: {exc}"
            ) from exc

        metadata = response.json()
        jwks_uri = metadata.get("jwks_uri")
        if not jwks_uri:
            raise JWKSFetchError("OIDC metadata does not define 'jwks_uri'")

        self._jwks_url = jwks_uri
        return jwks_uri

    def _extract_cache_seconds(self, headers: Dict[str, str]) -> Optional[int]:
        cache_control = headers.get("Cache-Control")
        if not cache_control:
            return None

        directives = [directive.strip() for directive in cache_control.split(",")]
        for directive in directives:
            if "=" not in directive:
                continue
            key, value = directive.split("=", 1)
            if key.lower() == "max-age":
                try:
                    return int(value)
                except ValueError:
                    return None
        return None


jwks_cache = JWKSCache(OIDC_METADATA_URL, OIDC_JWKS_URL, OIDC_JWKS_CACHE_SECONDS)


class TokenData(BaseModel):
    organization_id: str
    user_id: str
    email: str
    scopes: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_admin: bool = False
    session_id: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    raw_claims: Dict[str, Any] = Field(default_factory=dict)


class AuthUser(BaseModel):
    id: UUID
    email: str
    organization_id: UUID
    is_active: bool = True
    is_admin: bool = False
    roles: Set[str] = Field(default_factory=set)
    permissions: Set[str] = Field(default_factory=set)
    scopes: Set[str] = Field(default_factory=set)
    claims: Dict[str, Any] = Field(default_factory=dict)


def _to_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        if not value:
            return []
        return [item for item in value.replace(",", " ").split() if item]
    if isinstance(value, (set, tuple, list)):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    value_str = str(value).strip().lower()
    if value_str in {"true", "1", "yes", "y"}:
        return True
    if value_str in {"false", "0", "no", "n"}:
        return False
    return default


def _get_first_present(payload: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verify and decode a JWT or OIDC token and normalise its claims."""

    if token_type not in {"access", "refresh"}:
        raise ValueError("token_type must be either 'access' or 'refresh'")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise credentials_exception from exc

    algorithm = unverified_header.get("alg")
    if not algorithm:
        raise credentials_exception

    decode_kwargs: Dict[str, Any] = {
        "algorithms": [algorithm],
        "options": {
            "verify_aud": bool(OIDC_AUDIENCE),
            "verify_iss": False,
            "leeway": OIDC_CLOCK_SKEW_SECONDS,
        },
    }

    key: Any
    is_oidc_token = not algorithm.startswith("HS")

    if is_oidc_token:
        if not ENABLE_OIDC:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC validation is disabled but required for asymmetric tokens",
            )
        if algorithm not in OIDC_ALLOWED_ALGORITHMS:
            raise credentials_exception
        kid = unverified_header.get("kid")
        if not kid:
            raise credentials_exception
        try:
            key = await jwks_cache.get_signing_key(kid)
        except JWKSFetchError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to retrieve signing keys for token verification: {exc}",
            ) from exc
        if OIDC_AUDIENCE:
            decode_kwargs["audience"] = OIDC_AUDIENCE if len(OIDC_AUDIENCE) > 1 else OIDC_AUDIENCE[0]
        decode_kwargs["issuer"] = OIDC_ISSUER
        decode_kwargs["options"]["verify_iss"] = True
    else:
        key = SECRET_KEY
        decode_kwargs["algorithms"] = [ALGORITHM]
        decode_kwargs["options"]["verify_aud"] = False
        decode_kwargs["options"]["verify_iss"] = False

    try:
        payload = jwt.decode(token, key, **decode_kwargs)
    except JWTError as exc:
        raise credentials_exception from exc

    token_type_claim = _get_first_present(
        payload,
        [
            OIDC_TOKEN_TYPE_CLAIM,
            "token_use",
            "type",
            "token_type",
            "typ",
        ],
    )

    expected_values = (
        OIDC_ACCESS_TOKEN_VALUES if token_type == "access" else OIDC_REFRESH_TOKEN_VALUES
    )
    if token_type_claim and str(token_type_claim).lower() not in {
        value.lower() for value in expected_values
    }:
        raise credentials_exception

    organization_id = _get_first_present(
        payload,
        [
            OIDC_ORGANIZATION_CLAIM,
            "org_id",
            "tenant_id",
            "tenant",
            "organization",
        ],
    )
    user_id = _get_first_present(payload, [OIDC_USER_ID_CLAIM, "user_id", "uid"])
    email = _get_first_present(
        payload,
        [
            OIDC_EMAIL_CLAIM,
            "email",
            "preferred_username",
            "upn",
        ],
    )

    if not organization_id or not user_id:
        raise credentials_exception

    if token_type == "access" and not email:
        raise credentials_exception

    scopes = set(_to_string_list(payload.get(OIDC_SCOPE_CLAIM)))
    if not scopes:
        scopes = set(_to_string_list(payload.get("scp")))

    roles = set(_to_string_list(payload.get(OIDC_ROLE_CLAIM)))
    permissions = set(_to_string_list(payload.get(OIDC_PERMISSION_CLAIM)))
    is_active = _to_bool(payload.get(OIDC_ACTIVE_CLAIM), default=True)
    is_admin = _to_bool(payload.get(OIDC_ADMIN_CLAIM)) or bool(
        roles.intersection(OIDC_ADMIN_ROLES)
    )

    session_id = _get_first_present(
        payload,
        [OIDC_SESSION_CLAIM, "sid", "session_id"],
    )

    issued_at = None
    if "iat" in payload:
        try:
            issued_at = datetime.fromtimestamp(float(payload["iat"]), tz=timezone.utc)
        except (TypeError, ValueError):
            issued_at = None

    expires_at = None
    if "exp" in payload:
        try:
            expires_at = datetime.fromtimestamp(float(payload["exp"]), tz=timezone.utc)
        except (TypeError, ValueError):
            expires_at = None

    token_data = TokenData(
        organization_id=str(organization_id),
        user_id=str(user_id),
        email=str(email) if email is not None else "",
        scopes=sorted(scopes),
        roles=sorted(roles),
        permissions=sorted(permissions),
        is_active=is_active,
        is_admin=is_admin,
        session_id=str(session_id) if session_id else None,
        issued_at=issued_at,
        expires_at=expires_at,
        raw_claims=payload,
    )
    return token_data

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> AuthUser:
    """Get the current authenticated user from token"""
    token_data = await verify_token(token, token_type="access")

    if not token_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    try:
        user_id = UUID(str(token_data.user_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject is not a valid UUID",
        ) from exc

    try:
        organization_id = UUID(str(token_data.organization_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token organization identifier is invalid",
        ) from exc

    user = AuthUser(
        id=user_id,
        email=token_data.email,
        organization_id=organization_id,
        is_active=token_data.is_active,
        is_admin=token_data.is_admin,
        roles=set(token_data.roles),
        permissions=set(token_data.permissions),
        scopes=set(token_data.scopes),
        claims=token_data.raw_claims,
    )

    return user

async def get_current_organization(
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Get the current user's organization"""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    if organization.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is not active"
        )
    
    return organization

def require_scopes(*required_scopes: str):
    """Dependency to require specific scopes"""
    async def scope_checker(
        current_user: AuthUser = Depends(get_current_user)
    ):
        missing: Set[str] = set()
        for scope in required_scopes:
            if not scope:
                continue
            normalized = scope.strip()
            if normalized.startswith("role:"):
                role_name = normalized.split(":", 1)[1]
                if role_name not in current_user.roles:
                    missing.add(normalized)
                continue
            if normalized.startswith("permission:"):
                permission_name = normalized.split(":", 1)[1]
                if permission_name not in current_user.permissions:
                    missing.add(normalized)
                continue

            if normalized == "admin":
                if not current_user.is_admin:
                    missing.add(normalized)
                continue

            if (
                normalized not in current_user.scopes
                and normalized not in current_user.permissions
            ):
                missing.add(normalized)

        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Not enough permissions",
                    "missing": sorted(missing),
                },
            )
        return current_user
    return scope_checker

# Rate limiting decorator
from functools import wraps
from collections import defaultdict
from datetime import datetime
import asyncio

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, key: str) -> bool:
        """Check if rate limit is exceeded"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > minute_ago
        ]
        
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

async def check_rate_limit(
    current_user: AuthUser = Depends(get_current_user)
) -> None:
    """Check rate limit for current user"""
    key = f"user:{current_user.id}"
    
    if not await rate_limiter.check_rate_limit(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
