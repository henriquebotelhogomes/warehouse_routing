from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Verifica se o endpoint de health check responde 200 e com status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "NexusFleet AMR Engine"


def test_scalar_docs(client: TestClient) -> None:
    """Verifica se o endpoint de documentação Scalar responde com HTML válido."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "scalar" in response.text.lower()


def test_list_presets(client: TestClient) -> None:
    """Verifica se os 3 presets de layout são retornados corretamente."""
    response = client.get("/api/v1/layouts/presets")
    assert response.status_code == 200
    presets = response.json()
    assert len(presets) == 3
    names = [p["name"] for p in presets]
    assert any("Amazon" in n for n in names)
    assert any("Dark Store" in n for n in names)
    assert any("Sandbox" in n for n in names)


def test_get_current_layout(client: TestClient) -> None:
    """Verifica se o layout atual do simulador é retornado."""
    response = client.get("/api/v1/layouts/current")
    assert response.status_code == 200
    layout = response.json()
    assert "width" in layout
    assert "height" in layout


def test_analytics_summary(client: TestClient) -> None:
    """Verifica se o resumo de analytics traz métricas consistentes."""
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "throughput_per_hour" in data
    assert "fleet_utilization_pct" in data
    assert "amrs_count" in data
    assert data["amrs_count"] >= 1


def test_copilot_chat_status(client: TestClient) -> None:
    """Testa consulta conversacional de status ao Copiloto."""
    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Qual o status atual da frota?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "Total de AMRs" in data["reply"]


def test_copilot_chat_emergency_stop_hitl(client: TestClient) -> None:
    """Testa o acionamento de parada de emergência via chat protegida por HITL."""
    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Ativar parada de emergência geral da frota agora"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["hitl_action_required"] is True
    assert "hitl_card" in data
    token = data["hitl_card"]["token"]

    # Confirma a ação via endpoint HITL
    confirm_resp = client.post(
        "/api/v1/copilot/actions/confirm",
        json={"action_token": token},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["success"] is True


def test_frontend_static_serving(client: TestClient) -> None:
    """Verifica se o build de produção do frontend é servido na rota raiz /."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "NexusFleet AMR" in response.text or "root" in response.text


def test_fleet_routes(client: TestClient) -> None:
    """Testa endpoints REST de consulta e escalonamento da frota."""
    # Listar frota
    resp = client.get("/api/v1/fleet")
    assert resp.status_code == 200
    initial_count = resp.json()["count"]
    assert initial_count > 0

    # Adicionar 2 robôs
    add_resp = client.post("/api/v1/fleet/add", json={"count": 2})
    assert add_resp.status_code == 200
    assert add_resp.json()["total_fleet_size"] == initial_count + 2

    # Remover 1 robô
    rem_resp = client.post("/api/v1/fleet/remove", json={"count": 1})
    assert rem_resp.status_code == 200
    assert rem_resp.json()["total_fleet_size"] == initial_count + 1

    # Escalonar para tamanho exato
    scale_resp = client.post("/api/v1/fleet/scale", json={"target_count": 6})
    assert scale_resp.status_code == 200
    assert scale_resp.json()["current_count"] == 6


def test_copilot_scale_fleet_intent(client: TestClient) -> None:
    """Testa se o Copiloto processa comandos de adicionar robôs via linguagem natural."""
    resp = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Adicionar 2 robôs à frota"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Frota Expandida" in data["reply"]
    assert any(t["tool"] == "scale_fleet" for t in data["executed_tools"])


def test_chaos_api_endpoints(client: TestClient) -> None:
    """Testa endpoints REST de injeção de caos, consulta de RCA, exportação e resolução."""
    # Injetar colisão
    inject_resp = client.post(
        "/api/v1/chaos/inject",
        json={"failure_type": "sensor_blindspot", "count": 1},
    )
    assert inject_resp.status_code == 200
    data = inject_resp.json()
    assert data["success"] is True
    incident = data["incident"]
    incident_id = incident["incident_id"]
    assert incident_id.startswith("INC-")

    # Listar incidentes
    list_resp = client.get("/api/v1/chaos/incidents")
    assert list_resp.status_code == 200
    assert list_resp.json()["count"] >= 1

    # Obter detalhes do incidente
    detail_resp = client.get(f"/api/v1/chaos/incidents/{incident_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["incident_id"] == incident_id

    # Exportar laudo pericial em Markdown
    export_resp = client.get(f"/api/v1/chaos/incidents/{incident_id}/export")
    assert export_resp.status_code == 200
    assert "text/markdown" in export_resp.headers["content-type"]
    assert incident_id in export_resp.text

    # Resolver incidente com Self-Healing
    resolve_resp = client.post(
        f"/api/v1/chaos/incidents/{incident_id}/resolve",
        json={"self_healing": True},
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["success"] is True
