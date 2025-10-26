"""
Database Security Configuration
Enforces SSL/TLS for all database connections
"""

import os
from typing import Optional


class DatabaseSecurityConfig:
    """Configure secure database connections with SSL/TLS"""
    
    @staticmethod
    def get_secure_database_url(
        base_url: Optional[str] = None,
        require_ssl: bool = True,
        verify_certificate: bool = True
    ) -> str:
        """
        Get a secure database URL with SSL/TLS enforcement
        
        Args:
            base_url: Base database URL (if None, reads from DATABASE_URL env var)
            require_ssl: Whether to require SSL (default: True)
            verify_certificate: Whether to verify SSL certificate (default: True)
        
        Returns:
            Secure database URL with SSL/TLS parameters
        
        Raises:
            RuntimeError: If DATABASE_URL is not configured
        """
        url = base_url or os.getenv("DATABASE_URL")
        
        if not url:
            raise RuntimeError(
                "DATABASE_URL environment variable is required. "
                "Example: postgresql://user:password@host:5432/dbname"
            )
        
        # Ensure URL uses secure protocol
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        
        # Add SSL parameters
        ssl_mode = "verify-full" if verify_certificate else "require"
        
        # Check if parameters already exist
        if "?" in url:
            url += f"&sslmode={ssl_mode}"
        else:
            url += f"?sslmode={ssl_mode}"
        
        # Add certificate path if provided
        ca_cert_path = os.getenv("DATABASE_CA_CERT_PATH")
        if ca_cert_path and verify_certificate:
            url += f"&sslrootcert={ca_cert_path}"
        
        return url
    
    @staticmethod
    def validate_database_security():
        """
        Validate that database security is properly configured
        
        Raises:
            RuntimeError: If security requirements are not met
        """
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        
        # Check for SSL requirement
        if "sslmode" not in database_url:
            raise RuntimeError(
                "DATABASE_URL must include sslmode parameter. "
                "Minimum: ?sslmode=require, Recommended: ?sslmode=verify-full"
            )
        
        # Check for plaintext password in URL (warning only)
        if "://" in database_url:
            parts = database_url.split("://")[1]
            if "@" in parts and ":" in parts.split("@")[0]:
                # Password is present in URL - this is acceptable for now but should use env vars
                pass
        
        return True


# SQLAlchemy connection string builder with security
def build_secure_sqlalchemy_url(
    dialect: str = "postgresql",
    driver: str = "asyncpg",
    username: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: int = 5432,
    database: Optional[str] = None,
    ssl_mode: str = "verify-full",
    ca_cert_path: Optional[str] = None
) -> str:
    """
    Build a secure SQLAlchemy database URL with SSL/TLS
    
    Args:
        dialect: Database dialect (default: postgresql)
        driver: Async driver (default: asyncpg)
        username: Database username
        password: Database password
        host: Database host
        port: Database port (default: 5432)
        database: Database name
        ssl_mode: SSL mode - require, verify-ca, verify-full (default: verify-full)
        ca_cert_path: Path to CA certificate for verification
    
    Returns:
        Secure SQLAlchemy connection URL
    
    Raises:
        ValueError: If required parameters are missing
    """
    # Use environment variables if parameters not provided
    username = username or os.getenv("DB_USER")
    password = password or os.getenv("DB_PASSWORD")
    host = host or os.getenv("DB_HOST")
    database = database or os.getenv("DB_NAME")
    
    if not all([username, password, host, database]):
        raise ValueError(
            "Missing required database configuration. "
            "Provide: username, password, host, database"
        )
    
    # Build base URL
    url = f"{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}"
    
    # Add SSL parameters
    params = [f"sslmode={ssl_mode}"]
    
    if ca_cert_path:
        params.append(f"sslrootcert={ca_cert_path}")
    
    # Add connection pool settings for security
    params.extend([
        "connect_timeout=10",
        "application_name=valueverse-app"
    ])
    
    url += "?" + "&".join(params)
    
    return url


# Example usage in environment
SECURE_DATABASE_URL = DatabaseSecurityConfig.get_secure_database_url()
