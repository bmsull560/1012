"""
Unit tests for password policy module
"""

import pytest
from backend.password_policy import PasswordValidator, PasswordStrengthConfig


class TestPasswordValidator:
    """Test password validation functionality"""
    
    def test_calculate_entropy_simple_lowercase(self):
        """Test entropy calculation for simple lowercase password"""
        validator = PasswordValidator()
        
        # Password with only lowercase letters (26 possible characters)
        # Entropy = length * log2(charset_size) = 8 * log2(26) ≈ 37.60
        password = "abcdefgh"
        entropy = validator._calculate_entropy(password)
        
        assert entropy > 0
        assert 37.0 < entropy < 38.0  # Expected ~37.60
    
    def test_calculate_entropy_mixed_case(self):
        """Test entropy calculation for mixed case password"""
        validator = PasswordValidator()
        
        # Password with uppercase and lowercase (52 possible characters)
        # Entropy = length * log2(charset_size) = 8 * log2(52) ≈ 45.60
        password = "AbCdEfGh"
        entropy = validator._calculate_entropy(password)
        
        assert entropy > 0
        assert 45.0 < entropy < 46.0  # Expected ~45.60
    
    def test_calculate_entropy_with_numbers(self):
        """Test entropy calculation for password with numbers"""
        validator = PasswordValidator()
        
        # Password with lowercase and numbers (36 possible characters)
        # Entropy = length * log2(charset_size) = 8 * log2(36) ≈ 41.36
        password = "abc12345"
        entropy = validator._calculate_entropy(password)
        
        assert entropy > 0
        assert 41.0 < entropy < 42.0  # Expected ~41.36
    
    def test_calculate_entropy_complex_password(self):
        """Test entropy calculation for complex password with all character types"""
        validator = PasswordValidator()
        
        # Password with uppercase, lowercase, numbers, and special chars
        # Charset size = 26 + 26 + 10 + special chars (~30) = ~92
        # Entropy = length * log2(charset_size) = 12 * log2(92) ≈ 78.48
        password = "P@ssw0rd!123"
        entropy = validator._calculate_entropy(password)
        
        assert entropy > 0
        assert entropy > 70  # Should be high entropy
    
    def test_calculate_entropy_empty_password(self):
        """Test entropy calculation for empty password"""
        validator = PasswordValidator()
        
        password = ""
        entropy = validator._calculate_entropy(password)
        
        assert entropy == 0
    
    def test_calculate_entropy_longer_password_higher_entropy(self):
        """Test that longer passwords have higher entropy"""
        validator = PasswordValidator()
        
        short_password = "Pass123!"
        long_password = "Pass123!Pass123!"
        
        short_entropy = validator._calculate_entropy(short_password)
        long_entropy = validator._calculate_entropy(long_password)
        
        assert long_entropy > short_entropy
        # Long password should have roughly double the entropy
        assert long_entropy > short_entropy * 1.8
