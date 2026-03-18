from typing import Dict, Generator

import numpy as np
import pytest
from fastapi.testclient import TestClient
from warehouse_routing.api.main import app
from warehouse_routing.core.config import BASE_REWARDS_MATRIX, LOCATIONS
from warehouse_routing.core.q_learning import WarehouseRouteOptimizer


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Cria o cliente de teste para a API (Necessário para o test_api.py)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def optimizer() -> WarehouseRouteOptimizer:
    """Retorna uma instância limpa do otimizador para testes."""
    return WarehouseRouteOptimizer(
        locations=LOCATIONS,
        rewards_matrix=np.copy(BASE_REWARDS_MATRIX),
        gamma=0.8,
        alpha=0.9,
    )


@pytest.fixture
def sample_route_request() -> Dict[str, str]:
    """Dados de exemplo para testes de API."""
    return {"start": "A", "end": "G"}
