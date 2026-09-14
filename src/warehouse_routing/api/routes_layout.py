from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from warehouse_routing.core.grid import WarehouseGrid, WarehouseLayout

router = APIRouter(prefix="/api/v1/layouts", tags=["Layouts & Studio"])


class LayoutValidationResponse(BaseModel):
    is_valid: bool
    unreachable_cells: List[Dict[str, int]]
    message: str


# Referência para o orquestrador global (injetado via main.py)
_orchestrator_ref: Any = None


def set_orchestrator_instance(orch: Any) -> None:
    global _orchestrator_ref
    _orchestrator_ref = orch


@router.get("/presets", response_model=List[WarehouseLayout])
def list_preset_layouts() -> List[WarehouseLayout]:
    """Retorna os layouts de demonstração de fábrica."""
    mega = WarehouseGrid.create_preset_mega_hub().layout
    dark = WarehouseGrid.create_preset_dark_store().layout
    sand = WarehouseGrid.create_preset_sandbox().layout
    return [mega, dark, sand]


@router.get("/current", response_model=WarehouseLayout)
def get_current_layout() -> WarehouseLayout:
    """Retorna o layout que está sendo simulado no momento."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")
    return _orchestrator_ref.grid.layout


@router.post("/validate", response_model=LayoutValidationResponse)
def validate_layout(layout: WarehouseLayout) -> LayoutValidationResponse:
    """
    Valida a navegabilidade de um layout desenhado no frontend (BFS / Flood Fill).
    Garante que todas as prateleiras e bancadas têm rota de acesso transitável.
    """
    temp_grid = WarehouseGrid(layout)
    is_valid, unreachable = temp_grid.validate_connectivity()

    unreachable_dicts = [{"x": u[0], "y": u[1]} for u in unreachable]
    msg = (
        "Layout válido e 100% navegável"
        if is_valid
        else f"Atenção: {len(unreachable)} elementos estão isolados por paredes/obstáculos"
    )

    return LayoutValidationResponse(
        is_valid=is_valid,
        unreachable_cells=unreachable_dicts,
        message=msg,
    )


@router.post("/load")
def load_layout(layout: WarehouseLayout) -> Dict[str, Any]:
    """
    Carrega um novo layout customizado no orquestrador ativo.
    Reinicia a simulação com a nova topologia.
    """
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")

    new_grid = WarehouseGrid(layout)
    is_valid, unreachable = new_grid.validate_connectivity()
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Layout inválido: {len(unreachable)} elementos não são alcançáveis.",
        )

    # Reconfigura o orquestrador
    _orchestrator_ref.grid = new_grid
    _orchestrator_ref.reservations.vertex_reservations.clear()
    _orchestrator_ref.reservations.edge_reservations.clear()
    _orchestrator_ref.reservations.agent_reservations.clear()
    _orchestrator_ref.path_finder.grid = new_grid
    _orchestrator_ref.current_tick = 0
    _orchestrator_ref.completed_orders.clear()
    _orchestrator_ref.pending_orders.clear()
    _orchestrator_ref.amrs.clear()
    _orchestrator_ref._initialize_amrs(count=min(12, max(2, len(new_grid.charging_docks))))
    _orchestrator_ref._generate_initial_orders(count=20)
    _orchestrator_ref.flight_recorder.clear()

    return {
        "success": True,
        "message": f"Layout '{layout.name}' carregado com sucesso.",
        "dimensions": f"{layout.width}x{layout.height}",
        "amrs_count": len(_orchestrator_ref.amrs),
    }
