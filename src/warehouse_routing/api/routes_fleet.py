from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/fleet", tags=["Fleet Management"])

_orchestrator_ref: Any = None


def set_orchestrator_instance(orch: Any) -> None:
    global _orchestrator_ref
    _orchestrator_ref = orch


class AddAMRsRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=20, description="Quantidade de robôs a adicionar")


class RemoveAMRsRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=20, description="Quantidade de robôs a remover")
    amr_id: Optional[str] = Field(
        default=None, description="ID opcional de um robô específico a descomissionar"
    )


class ScaleFleetRequest(BaseModel):
    target_count: int = Field(..., ge=1, le=50, description="Tamanho total desejado para a frota")


@router.get("", summary="Listar telemetria de toda a frota")
def get_fleet() -> Dict[str, Any]:
    """Retorna o estado operacional e telemetria de todos os robôs AMRs ativos."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")
    amrs = [a.get_telemetry().model_dump() for a in _orchestrator_ref.amrs.values()]
    return {
        "count": len(amrs),
        "amrs": amrs,
    }


@router.post("/add", summary="Adicionar N robôs à frota")
def add_amrs(payload: AddAMRsRequest) -> Dict[str, Any]:
    """Adiciona dinamicamente N robôs AMRs posicionados em docas ou corredores livres."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")
    added = _orchestrator_ref.add_amrs(payload.count)
    return {
        "success": True,
        "added_count": len(added),
        "added_amrs": added,
        "total_fleet_size": len(_orchestrator_ref.amrs),
    }


@router.post("/remove", summary="Remover N robôs ou robô específico")
def remove_amrs(payload: RemoveAMRsRequest) -> Dict[str, Any]:
    """Descomissiona robôs com segurança (priorizando ociosos e limpando rotas MAPF)."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")
    specific_ids = [payload.amr_id] if payload.amr_id else None
    removed = _orchestrator_ref.remove_amrs(count=payload.count, specific_ids=specific_ids)
    return {
        "success": True,
        "removed_count": len(removed),
        "removed_amrs": removed,
        "total_fleet_size": len(_orchestrator_ref.amrs),
    }


@router.post("/scale", summary="Redimensionar frota para capacidade exata")
def scale_fleet(payload: ScaleFleetRequest) -> Dict[str, Any]:
    """Ajusta o tamanho exato da frota de robôs para atender a picos ou quedas de demanda."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")
    res = _orchestrator_ref.set_fleet_size(payload.target_count)
    return {
        "success": True,
        **res,
    }
