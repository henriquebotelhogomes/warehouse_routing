from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Referência global para o orquestrador
_orchestrator_ref: Any = None


def set_orchestrator_instance(orch: Any) -> None:
    global _orchestrator_ref
    _orchestrator_ref = orch


# Schemas Pydantic v2 para entrada e saída das ferramentas


class BlockZoneInput(BaseModel):
    x: int = Field(description="Coordenada X (coluna) da célula a bloquear")
    y: int = Field(description="Coordenada Y (linha) da célula a bloquear")
    reason: str = Field(
        default="Incidente reportado",
        description="Justificativa do bloqueio (ex: 'Derramamento de óleo', 'Pallet caído')",
    )


class BlockZoneOutput(BaseModel):
    success: bool
    blocked_cell: Dict[str, int]
    affected_amrs: List[str]
    rerouted_count: int
    sla_impact_seconds_avg: float
    message: str


class UnblockZoneInput(BaseModel):
    x: int = Field(description="Coordenada X da célula a liberar")
    y: int = Field(description="Coordenada Y da célula a liberar")


class UnblockZoneOutput(BaseModel):
    success: bool
    freed_cell: Dict[str, int]
    message: str


class GetFleetTelemetryInput(BaseModel):
    amr_id: Optional[str] = Field(
        default=None,
        description="ID opcional do robô (ex: 'AMR-02'). Se omitido, resume toda a frota.",
    )


class FleetSummaryOutput(BaseModel):
    total_amrs: int
    active_in_transit: int
    charging_count: int
    idle_count: int
    critical_battery_amrs: List[str]
    current_throughput_per_hour: float
    selected_amr_detail: Optional[Dict[str, Any]] = None


class EmergencyStopInput(BaseModel):
    activate: bool = Field(
        default=True,
        description="True para paralisar todos os robôs; False para retomar",
    )
    reason: str = Field(description="Motivo da parada de emergência (ISO 3691-4)")


class EmergencyStopOutput(BaseModel):
    requires_hitl_approval: bool = True
    action_token: str
    target_sector: str
    impact_warning: str


# Implementações das Funções Executáveis


def tool_block_zone(x: int, y: int, reason: str = "Incidente operacional") -> BlockZoneOutput:
    """Interdita uma célula no armazém e re-planeja as rotas dos robôs que cruzavam o ponto."""
    if _orchestrator_ref is None:
        return BlockZoneOutput(
            success=False,
            blocked_cell={"x": x, "y": y},
            affected_amrs=[],
            rerouted_count=0,
            sla_impact_seconds_avg=0.0,
            message="Orquestrador não inicializado.",
        )

    success, affected, impact = _orchestrator_ref.block_area(x, y, reason)
    msg = (
        f"Zona ({x}, {y}) bloqueada com sucesso por '{reason}'. "
        f"{len(affected)} robôs tiveram suas rotas recalculadas sem colisões."
        if success
        else f"Não foi possível bloquear ({x}, {y}) (coordenadas fora dos limites)."
    )

    return BlockZoneOutput(
        success=success,
        blocked_cell={"x": x, "y": y},
        affected_amrs=affected,
        rerouted_count=len(affected),
        sla_impact_seconds_avg=impact,
        message=msg,
    )


def tool_unblock_zone(x: int, y: int) -> UnblockZoneOutput:
    """Libera uma célula bloqueada para o tráfego de robôs."""
    if _orchestrator_ref is None:
        return UnblockZoneOutput(
            success=False, freed_cell={"x": x, "y": y}, message="Erro de init."
        )

    success = _orchestrator_ref.unblock_area(x, y)
    msg = (
        f"Célula ({x}, {y}) liberada para tráfego normal."
        if success
        else f"A célula ({x}, {y}) não estava bloqueada."
    )
    return UnblockZoneOutput(success=success, freed_cell={"x": x, "y": y}, message=msg)


def tool_get_fleet_telemetry(amr_id: Optional[str] = None) -> FleetSummaryOutput:
    """Retorna um resumo agregado da telemetria da frota de robôs."""
    if _orchestrator_ref is None:
        return FleetSummaryOutput(
            total_amrs=0,
            active_in_transit=0,
            charging_count=0,
            idle_count=0,
            critical_battery_amrs=[],
            current_throughput_per_hour=0.0,
        )

    orch = _orchestrator_ref
    telemetries = [amr.get_telemetry() for amr in orch.amrs.values()]

    active = sum(1 for a in telemetries if a.state.value not in ("IDLE", "CHARGING"))
    charging = sum(1 for a in telemetries if a.state.value == "CHARGING")
    idle = sum(1 for a in telemetries if a.state.value == "IDLE")
    critical = [a.id for a in telemetries if a.battery_level < 20.0]

    detail: Optional[Dict[str, Any]] = None
    if amr_id and amr_id in orch.amrs:
        detail = orch.amrs[amr_id].get_telemetry().model_dump()

    return FleetSummaryOutput(
        total_amrs=len(telemetries),
        active_in_transit=active,
        charging_count=charging,
        idle_count=idle,
        critical_battery_amrs=critical,
        current_throughput_per_hour=orch.get_throughput_per_hour(),
        selected_amr_detail=detail,
    )


class ScaleFleetInput(BaseModel):
    action_type: str = Field(
        default="scale",
        description="Tipo de ação: 'add' (adicionar), 'remove' (remover) ou 'scale' (definir tamanho total)",
    )
    count: Optional[int] = Field(
        default=1,
        description="Quantidade de robôs a adicionar ou remover",
    )
    target_count: Optional[int] = Field(
        default=None,
        description="Tamanho final desejado para a frota (quando action_type='scale')",
    )
    amr_id: Optional[str] = Field(
        default=None,
        description="ID específico do robô a remover (ex: 'AMR-03')",
    )
    reason: str = Field(
        default="Ajuste operacional de demanda",
        description="Justificativa do redimensionamento",
    )


class ScaleFleetOutput(BaseModel):
    success: bool
    action: str
    previous_count: int
    current_count: int
    affected_amrs: List[str]
    message: str


def tool_scale_fleet(
    action_type: str = "scale",
    count: Optional[int] = 1,
    target_count: Optional[int] = None,
    amr_id: Optional[str] = None,
    reason: str = "Ajuste de demanda",
) -> ScaleFleetOutput:
    """Ajusta dinamicamente a capacidade da frota adicionando ou removendo robôs."""
    if _orchestrator_ref is None:
        return ScaleFleetOutput(
            success=False,
            action=action_type,
            previous_count=0,
            current_count=0,
            affected_amrs=[],
            message="Orquestrador não inicializado.",
        )

    orch = _orchestrator_ref
    prev = len(orch.amrs)

    if action_type == "add" or (action_type == "scale" and target_count is not None and target_count > prev):
        n = (count or 1) if action_type == "add" else (target_count - prev if target_count else 1)
        added = orch.add_amrs(max(1, n))
        return ScaleFleetOutput(
            success=True,
            action="add",
            previous_count=prev,
            current_count=len(orch.amrs),
            affected_amrs=added,
            message=f"Frota expandida: +{len(added)} robôs adicionados ({', '.join(added)}). Total atual: {len(orch.amrs)} robôs.",
        )

    elif action_type == "remove" or (action_type == "scale" and target_count is not None and target_count < prev):
        if amr_id:
            removed = orch.remove_amrs(count=1, specific_ids=[amr_id])
        else:
            n = (count or 1) if action_type == "remove" else (prev - target_count if target_count else 1)
            removed = orch.remove_amrs(count=max(1, n))

        return ScaleFleetOutput(
            success=True,
            action="remove",
            previous_count=prev,
            current_count=len(orch.amrs),
            affected_amrs=removed,
            message=f"Frota reduzida: -{len(removed)} robôs removidos ({', '.join(removed)}). Total restante: {len(orch.amrs)} robôs.",
        )

    elif target_count is not None and target_count == prev:
        return ScaleFleetOutput(
            success=True,
            action="noop",
            previous_count=prev,
            current_count=prev,
            affected_amrs=[],
            message=f"A frota já possui exatamente {prev} robôs operacionais.",
        )

    # Fallback
    res = orch.set_fleet_size(target_count or count or 8)
    return ScaleFleetOutput(
        success=True,
        action="scale",
        previous_count=res["previous_count"],
        current_count=res["current_count"],
        affected_amrs=res["added_amrs"] or res["removed_amrs"],
        message=f"Capacidade da frota ajustada para {res['current_count']} robôs.",
    )

