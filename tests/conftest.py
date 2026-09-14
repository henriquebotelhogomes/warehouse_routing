from typing import Generator

import pytest
from fastapi.testclient import TestClient

from warehouse_routing.api.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Cria o cliente de teste para a API disparando o lifespan."""
    with TestClient(app) as c:
        yield c
