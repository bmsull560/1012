"""
Secrets Management Module
Handles secure retrieval of secrets from AWS Secrets Manager or environment variables
"""

import os
import json
from typing import Dict, Any, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class SecretsManager:
    """Centralized secrets management"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self._cache = {}
        
        # Only use AWS Secrets Manager in production
        self.use_aws = self.environment == "production"
        
        if self.use_aws:
            try:
                import boto3
                self.client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            except ImportError:
                logger.warning("boto3 not installed. Install with: pip install boto3")
                self.use_aws = False
    
    @lru_cache(maxsize=32)
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager or environment variables
        
        Args:
            secret_name: Name of the secret (e.g., 'valueverse/prod/database')
            
        Returns:
            Dictionary containing secret values
        """
        # Check cache first
        if secret_name in self._cache:
            return self._cache[secret_name]
        
        # Try AWS Secrets Manager in production
        if self.use_aws:
            try:
                response = self.client.get_secret_value(SecretId=secret_name)
                secret_value = json.loads(response['SecretString'])
                self._cache[secret_name] = secret_value
                logger.info(f"Retrieved secret from AWS Secrets Manager: {secret_name}")
                return secret_value
            except Exception as e:
                logger.error(f"Failed to retrieve secret from AWS: {e}")
                # Fall through to environment variables
        
        # Fallback to environment variables
        logger.info(f"Using environment variables for: {secret_name}")
        return self._get_from_env(secret_name)
    
    def _get_from_env(self, secret_name: str) -> Dict[str, Any]:
        """Fallback to environment variables"""
        # Map secret names to environment variable prefixes
        if "database" in secret_name.lower():
            return {
                "username": os.getenv("DB_USERNAME", "postgres"),
                "password": os.getenv("DB_PASSWORD", ""),
                "host": os.getenv("DB_HOST", "localhost"),
                "port": os.getenv("DB_PORT", "5432"),
                "database": os.getenv("DB_NAME", "valueverse"),
            }
        elif "api-keys" in secret_name.lower():
            return {
                "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
                "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "together_api_key": os.getenv("TOGETHER_API_KEY", ""),
                "jwt_secret": os.getenv("JWT_SECRET_KEY", ""),
            }
        elif "jwt" in secret_name.lower():
            return {
                "secret_key": os.getenv("JWT_SECRET_KEY", ""),
                "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
                "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
                "refresh_token_expire_days": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            }
        
        raise ValueError(f"Unknown secret name: {secret_name}")
    
    def get_database_url(self) -> str:
        """Construct database URL from secrets"""
        db_secret = self.get_secret("valueverse/prod/database")
        
        return (
            f"postgresql+asyncpg://{db_secret['username']}:{db_secret['password']}"
            f"@{db_secret['host']}:{db_secret['port']}/{db_secret['database']}"
        )
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """Get JWT configuration"""
        return self.get_secret("valueverse/prod/jwt")
    
    def rotate_secret(self, secret_name: str) -> bool:
        """
        Trigger secret rotation (AWS Secrets Manager)
        
        Args:
            secret_name: Name of the secret to rotate
            
        Returns:
            True if rotation triggered successfully
        """
        if not self.use_aws:
            logger.warning("Secret rotation only available with AWS Secrets Manager")
            return False
        
        try:
            self.client.rotate_secret(SecretId=secret_name)
            # Clear cache
            if secret_name in self._cache:
                del self._cache[secret_name]
            logger.info(f"Secret rotation triggered: {secret_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to rotate secret: {e}")
            return False


# Global secrets manager instance
secrets_manager = SecretsManager()
