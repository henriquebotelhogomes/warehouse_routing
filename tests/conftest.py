from pathlib import Path
from typing import Dict, Generator

import numpy as np
import pytest
from fastapi.testclient import TestClient
from warehouse_routing.api.main import app
from warehouse_routing.core.config import BASE_REWARDS_MATRIX, LOCATIONS, settings
from warehouse_routing.core.q_learning import WarehouseRouteOptimizer


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path: Path) -> Generator[None, None, None]:
    """
    Configura o ambiente de teste de forma isolada.
    O 'autouse=True' garante que todos os testes usem um diretório temporário
    para salvar/carregar modelos, evitando erros de permissão no Windows.
    """
    # Criamos um caminho temporário único para esta execução de teste
    test_model_path = tmp_path / "model_test.joblib"

    # Backup do path original para restaurar depois
    original_path = settings.model_save_path

    # Sobrescrevemos o path nas configurações globais para o contexto do teste
    settings.model_save_path = str(test_model_path)

    yield

    # Restaura o path original após o fim dos testes
    settings.model_save_path = original_path


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Cria o cliente de teste para a API disparando o lifespan."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def optimizer() -> WarehouseRouteOptimizer:
    """Retorna uma instância limpa do otimizador para testes unitários."""
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
