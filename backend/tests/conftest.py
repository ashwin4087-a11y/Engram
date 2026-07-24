"""
Pytest configuration and test fixtures.
"""
import pytest
from typing import AsyncGenerator
from fastapi.testclient import TestClient

from main import application


@pytest.fixture
def client() -> TestClient:
    return TestClient(application)
