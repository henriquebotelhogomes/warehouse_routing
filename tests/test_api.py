from fastapi.testclient import TestClient
from warehouse_routing.api.main import app

client = TestClient(app)


def test_api_calculate_route_success() -> None:
    """Testa o endpoint de cálculo de rota."""
    response = client.post("/api/v1/routes", json={"start": "A", "end": "G"})
    assert response.status_code == 200
    data = response.json()
    assert "route" in data
    assert data["route"][0] == "A"
    assert data["route"][-1] == "G"


def test_api_invalid_location() -> None:
    """Testa erro 400 ao enviar local inexistente."""
    response = client.post("/api/v1/routes", json={"start": "Z", "end": "G"})
    assert response.status_code == 400
    assert "detail" in response.json()


def test_api_visualize_graph() -> None:
    """Testa se o endpoint de imagem retorna um PNG válido."""
    response = client.get("/api/v1/visualize/graph")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_api_performance_header(client: TestClient) -> None:
    """
    Testa se o middleware de performance está injetando o header de tempo de processamento.
    """
    response = client.get("/api/v1/visualize/graph")
    assert "X-Process-Time-Ms" in response.headers
