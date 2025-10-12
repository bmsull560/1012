# backend/tests/test_schemas/user_test.py

import pytest
from pydantic import ValidationError
from backend.app.schemas.user import UserBase, UserCreate, User

def test_user_base_schema():
    user = UserBase(username="test_user", email="test@example.com")
    assert user.username == "test_user"
    assert user.email == "test@example.com"

def test_user_base_schema_invalid_email():
    with pytest.raises(ValidationError):
        UserBase(username="test_user", email="invalid_email")

def test_user_base_schema_strip_whitespace():
    user = UserBase(username="  test_user  ", email="  test@example.com  ")
    assert user.username == "test_user"
    assert user.email == "test@example.com"

def test_user_create_schema():
    user = UserCreate(username="test_user", email="test@example.com", password="TestPassword123!")
    assert user.username == "test_user"
    assert user.email == "test@example.com"
    assert user.password == "TestPassword123!"

def test_user_create_schema_password_must_contain_uppercase():
    with pytest.raises(ValidationError):
        UserCreate(username="test_user", email="test@example.com", password="testpassword123!")

def test_user_create_schema_password_must_contain_lowercase():
    with pytest.raises(ValidationError):
        UserCreate(username="test_user", email="test@example.com", password="TESTPASSWORD123!")

def test_user_create_schema_password_must_contain_number():
    with pytest.raises(ValidationError):
        UserCreate(username="test_user", email="test@example.com", password="TestPassword!")

def test_user_create_schema_password_must_contain_special_char():
    with pytest.raises(ValidationError):
        UserCreate(username="test_user", email="test@example.com", password="TestPassword123")

def test_user_create_schema_password_must_be_at_least_8_chars():
    with pytest.raises(ValidationError):
        UserCreate(username="test_user", email="test@example.com", password="Test123!")

def test_user_schema():
    user = User(id=1, username="test_user", email="test@example.com", is_active=True)
    assert user.id == 1
    assert user.username == "test_user"
    assert user.email == "test@example.com"
    assert user.is_active == True

def test_user_schema_orm_mode():
    user = User(id=1, username="test_user", email="test@example.com", is_active=True)
    assert user.dict() == {"id": 1, "username": "test_user", "email": "test@example.com", "is_active": True}
