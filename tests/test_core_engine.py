from warehouse_routing.core.amr_agent import AMRAgent, AMRState
from warehouse_routing.core.chaos_engine import ChaosEngine
from warehouse_routing.core.fleet_orchestrator import FleetOrchestrator
from warehouse_routing.core.grid import WarehouseGrid
from warehouse_routing.core.space_time_mapf import ReservationTable, SpaceTimeAStar


def test_grid_initialization_and_validation():
    grid = WarehouseGrid.create_preset_sandbox()
    assert grid.width == 12
    assert grid.height == 12
    assert len(grid.charging_docks) == 2
    assert len(grid.picking_stations) == 2

    is_valid, unreachable = grid.validate_connectivity()
    assert is_valid is True
    assert len(unreachable) == 0


def test_space_time_astar_collision_avoidance():
    grid = WarehouseGrid.create_preset_sandbox()
    reservations = ReservationTable()
    solver = SpaceTimeAStar(grid, reservations)

    # Robô 1 planeja caminho de (1, 0) até (1, 4) no t=0
    path_1 = solver.find_path("AMR-01", (1, 0), (1, 4), start_time=0)
    assert path_1 is not None
    reservations.reserve_path("AMR-01", path_1, start_time=0)

    # Robô 2 tenta planejar de (1, 4) até (1, 0) no t=0 (sentido oposto, colisão frontal)
    path_2 = solver.find_path("AMR-02", (1, 4), (1, 0), start_time=0)
    assert path_2 is not None

    # Verifica que em nenhum momento t robô 1 e robô 2 estão na mesma célula
    len_min = min(len(path_1), len(path_2))
    for t in range(len_min):
        assert path_1[t] != path_2[t], f"Colisão detectada no instante t={t} na célula {path_1[t]}"


def test_amr_fsm_and_battery():
    agent = AMRAgent("AMR-TEST", initial_x=2, initial_y=2, battery_level=50.0)
    assert agent.state == AMRState.IDLE
    assert agent.is_available_for_orders() is True

    # Atribui caminho de 2 passos
    agent.set_path([(2, 2), (2, 3), (2, 4)])
    agent.state = AMRState.MOVING_TO_POD
    agent.target_pod_id = "POD-01"

    agent.update_tick()  # Anda para (2, 2)
    agent.update_tick()  # Anda para (2, 3)
    agent.update_tick()  # Anda para (2, 4) -> final do path -> LIFTING_POD

    assert agent.grid_x == 2
    assert agent.grid_y == 4
    assert agent.state == AMRState.LIFTING_POD
    assert agent.battery_level < 50.0


def test_fleet_orchestrator_step_and_telemetry():
    grid = WarehouseGrid.create_preset_sandbox()
    orchestrator = FleetOrchestrator(grid, num_amrs=2)

    # Roda 10 passos de simulação
    for _ in range(10):
        orchestrator.step()

    telemetry = orchestrator.get_telemetry_payload()
    assert telemetry["tick"] == 10
    assert len(telemetry["amrs"]) == 2
    assert "metrics" in telemetry
    assert telemetry["metrics"]["fleet_utilization_pct"] >= 0.0


def test_continuous_mission_lifecycle_no_deadlock():
    """Garante que os AMRs executam o ciclo contínuo sem congelar em TRANSITING_TO_PICKING."""
    grid = WarehouseGrid.create_preset_sandbox()
    orchestrator = FleetOrchestrator(grid, num_amrs=2)

    # Roda 120 ticks de simulação (tempo suficiente para completar missões completas)
    for _ in range(120):
        orchestrator.step()

    # Pelo menos 2 ordens de separação devem ter sido concluídas
    assert len(orchestrator.completed_orders) >= 2

    # Verifica que nenhum robô ficou preso indefinidamente em estado de transição sem caminho
    for amr in orchestrator.amrs.values():
        if amr.state in (AMRState.TRANSITING_TO_PICKING, AMRState.MOVING_TO_POD, AMRState.RETURNING_POD):
            # Se está em trânsito, DEVE ter um caminho planejado
            assert len(amr.path) > 0
            assert amr.path_step_idx <= len(amr.path)


def test_dynamic_fleet_scaling():
    """Garante que adicionar e remover N robôs em tempo de execução preserva a integridade do sistema."""
    grid = WarehouseGrid.create_preset_sandbox()
    orchestrator = FleetOrchestrator(grid, num_amrs=3)
    assert len(orchestrator.amrs) == 3

    # Adiciona 2 robôs
    added = orchestrator.add_amrs(2)
    assert len(added) == 2
    assert len(orchestrator.amrs) == 5
    for amr_id in added:
        assert amr_id in orchestrator.amrs

    # Simula alguns passos
    for _ in range(10):
        orchestrator.step()

    # Remove 1 robô
    removed = orchestrator.remove_amrs(1)
    assert len(removed) == 1
    assert len(orchestrator.amrs) == 4
    assert removed[0] not in orchestrator.amrs

    # Ajusta para tamanho exato
    res = orchestrator.set_fleet_size(6)
    assert res["current_count"] == 6
    assert len(orchestrator.amrs) == 6


def test_chaos_injection_and_rca():
    """Garante que a injeção de caos altera o estado dos robôs para CRASHED e produz o laudo RCA."""
    grid = WarehouseGrid.create_preset_sandbox()
    orchestrator = FleetOrchestrator(grid, num_amrs=4)

    # Executa alguns passos para colocar os robôs em missão
    for _ in range(5):
        orchestrator.step()

    report = orchestrator.inject_chaos(failure_type="wheel_slip")
    assert report.incident_id.startswith("INC-")
    assert len(report.involved_amrs) == 2
    assert report.failure_type == "wheel_slip"
    assert len(report.five_whys) == 5
    assert len(report.corrective_actions) > 0
    assert report.is_resolved is False

    # Verifica que os robôs envolvidos estão no estado CRASHED
    for amr_id in report.involved_amrs:
        amr = orchestrator.amrs[amr_id]
        assert amr.state == AMRState.CRASHED
        assert amr.is_crashed is True

    # Verifica se o laudo em Markdown pode ser gerado
    md = ChaosEngine.generate_markdown_report(report)
    assert report.incident_id in md
    assert "ISO 3691-4" in md
    assert "5 Porquês" in md


def test_incident_resolution_and_self_healing():
    """Garante que o protocolo de Auto-Cura isola a área e recupera os robôs."""
    grid = WarehouseGrid.create_preset_sandbox()
    orchestrator = FleetOrchestrator(grid, num_amrs=3)

    report = orchestrator.inject_chaos(failure_type="random")
    incident_id = report.incident_id
    loc = report.location

    # Executa auto-cura
    res = orchestrator.resolve_incident(incident_id=incident_id, self_healing=True)
    assert res["success"] is True
    assert res["is_resolved"] is True
    assert res["self_healing_applied"] is True

    # Verifica que o local do acidente foi adicionado aos blocos dinâmicos de isolamento
    assert (loc["x"], loc["y"]) in orchestrator.grid.dynamic_blocks

    # Verifica que os robôs foram recuperados do estado CRASHED
    for amr_id in report.involved_amrs:
        amr = orchestrator.amrs[amr_id]
        assert amr.state != AMRState.CRASHED
        assert amr.is_crashed is False


