from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from warehouse_routing.core.chaos_engine import (
    ChaosEngine,
)

router = APIRouter(prefix="/api/v1/chaos", tags=["Chaos Engineering & RCA"])

_orchestrator_ref: Any = None


def set_orchestrator_instance(orch: Any) -> None:
    global _orchestrator_ref
    _orchestrator_ref = orch


class InjectChaosRequest(BaseModel):
    failure_type: str = Field(
        default="random",
        description="Tipo de anomalia física: 'random', 'wheel_slip', 'network_latency', 'sensor_blindspot'",
    )
    count: int = Field(default=1, ge=1, le=5, description="Quantidade de acidentes a forçar")


class ResolveIncidentRequest(BaseModel):
    self_healing: bool = Field(
        default=True,
        description="Se True, aplica isolamento automático com cones virtuais e desvio de rotas",
    )


@router.post("/inject", summary="Injetar colisão física (Chaos Engineering)")
def inject_chaos(payload: InjectChaosRequest) -> Dict[str, Any]:
    """
    Injeta uma anomalia física controlada (derrapagem, latência Wi-Fi ou falha de sensor),
    força colisão entre AMRs em cruzamento e gera o laudo forense RCA com 5-Porquês.
    """
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")

    try:
        report = _orchestrator_ref.inject_chaos(
            failure_type=payload.failure_type, count=payload.count
        )
        return {
            "success": True,
            "incident": report.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao injetar anomalia de caos: {str(e)}"
        ) from e


@router.get("/incidents", summary="Listar histórico de incidentes")
def list_incidents() -> Dict[str, Any]:
    """Retorna todos os relatórios de incidentes e acidentes gerados na sessão."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")

    reports = [r.model_dump() for r in _orchestrator_ref.incident_reports]
    return {
        "count": len(reports),
        "incidents": reports,
    }


@router.get("/incidents/{incident_id}", summary="Obter detalhes de um incidente (RCA)")
def get_incident(incident_id: str) -> Dict[str, Any]:
    """Retorna os detalhes forenses completos, 5-Porquês e telemetria da caixa preta."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")

    report = next(
        (r for r in _orchestrator_ref.incident_reports if r.incident_id == incident_id), None
    )
    if not report:
        raise HTTPException(status_code=404, detail="Incidente não encontrado")

    return report.model_dump()


@router.get("/incidents/{incident_id}/export", summary="Exportar laudo pericial (Markdown)")
def export_incident_report(incident_id: str) -> Response:
    """Gera e retorna o laudo pericial formal em formato Markdown para download."""
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")

    report = next(
        (r for r in _orchestrator_ref.incident_reports if r.incident_id == incident_id), None
    )
    if not report:
        raise HTTPException(status_code=404, detail="Incidente não encontrado")

    md_content = ChaosEngine.generate_markdown_report(report)
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="laudo-{incident_id}.md"'},
    )


@router.post("/incidents/{incident_id}/resolve", summary="Resolver incidente e aplicar Auto-Cura")
def resolve_incident(incident_id: str, payload: ResolveIncidentRequest) -> Dict[str, Any]:
    """
    Executa o protocolo de resolução e auto-recuperação (Self-Healing):
    - Cones de isolamento na célula do acidente
    - Robôs acidentados são recuperados e encaminhados para doca
    - Frota ativa recalcula rotas de desvio instantaneamente
    """
    if _orchestrator_ref is None:
        raise HTTPException(status_code=503, detail="Simulador não inicializado")

    result = _orchestrator_ref.resolve_incident(
        incident_id=incident_id, self_healing=payload.self_healing
    )
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))

    return result
