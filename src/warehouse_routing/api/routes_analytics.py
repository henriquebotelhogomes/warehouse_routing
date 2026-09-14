from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from warehouse_routing.core.flight_recorder import SimulationSnapshot

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & BI"])

_orchestrator_ref: Any = None


def set_orchestrator_instance(orch: Any) -> None:
    global _orchestrator_ref
    _orchestrator_ref = orch


@router.get("/summary")
def get_analytics_summary() -> Dict[str, Any]:
    """Retorna métricas consolidadas de turno para o dashboard de BI."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")

    orch = _orchestrator_ref
    amrs_telemetry = [amr.get_telemetry() for amr in orch.amrs.values()]

    # Métricas de energia
    battery_levels = [amr.battery_level for amr in amrs_telemetry]
    avg_battery = round(sum(battery_levels) / len(battery_levels), 1) if battery_levels else 100.0

    # Estados
    state_distribution: Dict[str, int] = {}
    for amr in amrs_telemetry:
        state_name = amr.state.value
        state_distribution[state_name] = state_distribution.get(state_name, 0) + 1

    return {
        "tick": orch.current_tick,
        "throughput_per_hour": orch.get_throughput_per_hour(),
        "fleet_utilization_pct": orch.get_fleet_utilization_pct(),
        "total_completed_orders": len(orch.completed_orders),
        "total_pending_orders": len(orch.pending_orders),
        "avg_battery_level": avg_battery,
        "state_distribution": state_distribution,
        "active_incidents_count": len(orch.grid.dynamic_blocks),
        "amrs_count": len(orch.amrs),
    }


@router.get("/timeline", response_model=List[SimulationSnapshot])
def get_flight_recorder_timeline() -> List[SimulationSnapshot]:
    """
    Retorna o histórico dos últimos snapshots gravados pelo Flight Recorder.
    Alimenta o recurso de Timeline Replay (Scrubbing) no frontend.
    """
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")

    return _orchestrator_ref.flight_recorder.get_timeline()


@router.get("/incidents")
def list_incident_records() -> List[Dict[str, Any]]:
    """Retorna o log histórico de incidentes registrados."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")

    return [inc.model_dump() for inc in _orchestrator_ref.incident_history]
