"""Pytest configuration and fixtures"""

import pytest
import os

# Set test database environment variable before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['TESTING'] = 'true'
