import pytest
import numpy as np
from warehouse_routing.core.q_learning import WarehouseRouteOptimizer
from warehouse_routing.core.config import LOCATIONS, BASE_REWARDS_MATRIX
from typing import Dict


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
