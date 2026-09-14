import re
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

    if action_type == "add" or (
        action_type == "scale" and target_count is not None and target_count > prev
    ):
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

    elif action_type == "remove" or (
        action_type == "scale" and target_count is not None and target_count < prev
    ):
        if amr_id:
            removed = orch.remove_amrs(count=1, specific_ids=[amr_id])
        else:
            n = (
                (count or 1)
                if action_type == "remove"
                else (prev - target_count if target_count else 1)
            )
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


# --- Novas Ferramentas Expandidas ---


class GetAMRLogsInput(BaseModel):
    amr_id: Optional[str] = Field(
        default=None,
        description="ID do robô específico (ex: 'AMR-03'). Se omitido, retorna logs de toda a frota.",
    )
    limit: int = Field(default=8, description="Número máximo de eventos a retornar")


class AMRLogItem(BaseModel):
    timestamp: str
    tick: int
    level: str
    message: str
    amr_id: str


class GetAMRLogsOutput(BaseModel):
    success: bool
    amr_id: Optional[str]
    logs: List[AMRLogItem]
    message: str


def tool_get_amr_logs(amr_id: Optional[str] = None, limit: int = 8) -> GetAMRLogsOutput:
    """Consulta os logs recentes e eventos da máquina de estados (FSM) de um robô ou de toda a frota."""
    if _orchestrator_ref is None:
        return GetAMRLogsOutput(
            success=False, amr_id=amr_id, logs=[], message="Orquestrador não inicializado."
        )

    orch = _orchestrator_ref
    logs_list: List[AMRLogItem] = []

    if amr_id:
        # Normaliza ID (ex: "amr-3" -> "AMR-03")
        target_id = amr_id.upper().strip()
        if not target_id.startswith("AMR-"):
            # Se for só número (ex: "3")
            num = re.sub(r"\D", "", target_id)
            if num:
                target_id = f"AMR-{int(num):02d}"

        # Procura amr
        found_amr = None
        for a_id, a_obj in orch.amrs.items():
            if a_id == target_id or a_id.endswith(
                f"-{int(num):02d}" if "num" in locals() and num else "XYZ"
            ):
                found_amr = a_obj
                target_id = a_id
                break

        if not found_amr:
            return GetAMRLogsOutput(
                success=False,
                amr_id=target_id,
                logs=[],
                message=f"Robô '{target_id}' não encontrado na frota ativa ({', '.join(orch.amrs.keys())}).",
            )

        for log_entry in found_amr.logs[-limit:]:
            logs_list.append(
                AMRLogItem(
                    timestamp=log_entry.timestamp,
                    tick=log_entry.tick,
                    level=log_entry.level,
                    message=log_entry.message,
                    amr_id=target_id,
                )
            )
        logs_list.reverse()
        return GetAMRLogsOutput(
            success=True,
            amr_id=target_id,
            logs=logs_list,
            message=f"Recuperados {len(logs_list)} eventos recentes do {target_id}.",
        )

    # Todos os robôs
    for a_id, a_obj in orch.amrs.items():
        for log_entry in a_obj.logs[-5:]:
            logs_list.append(
                AMRLogItem(
                    timestamp=log_entry.timestamp,
                    tick=log_entry.tick,
                    level=log_entry.level,
                    message=log_entry.message,
                    amr_id=a_id,
                )
            )

    logs_list.sort(key=lambda x: x.tick, reverse=True)
    logs_list = logs_list[:limit]
    return GetAMRLogsOutput(
        success=True,
        amr_id=None,
        logs=logs_list,
        message=f"Recuperados {len(logs_list)} eventos recentes da frota.",
    )


class RescueAMRInput(BaseModel):
    amr_id: str = Field(description="ID do robô a destravar/resgatar (ex: 'AMR-03')")


class RescueAMROutput(BaseModel):
    success: bool
    amr_id: str
    action: str
    message: str


def tool_rescue_amr(amr_id: str) -> RescueAMROutput:
    """Aciona o protocolo de Self-Healing para destravar um robô congelado ou com falha de rota."""
    if _orchestrator_ref is None:
        return RescueAMROutput(
            success=False, amr_id=amr_id, action="error", message="Orquestrador não inicializado."
        )

    orch = _orchestrator_ref
    target_id = amr_id.upper().strip()
    num = re.sub(r"\D", "", target_id)
    if num:
        target_id = f"AMR-{int(num):02d}"

    res = orch.rescue_amr(target_id)
    return RescueAMROutput(
        success=res.get("success", False),
        amr_id=target_id,
        action=res.get("action", "unknown"),
        message=res.get("message", "Operação concluída."),
    )


class GetAMRDetailInput(BaseModel):
    amr_id: str = Field(description="ID do robô a consultar (ex: 'AMR-02')")


class GetAMRDetailOutput(BaseModel):
    success: bool
    amr_id: str
    position: Optional[Dict[str, int]]
    state: str
    battery_level: float
    carrying_pod_id: Optional[str]
    current_mission_id: Optional[str]
    target: Optional[Dict[str, int]]
    path_length_remaining: int
    message: str


def tool_get_amr_detail(amr_id: str) -> GetAMRDetailOutput:
    """Consulta detalhes precisos de localização, carga, missão e bateria de um robô específico."""
    if _orchestrator_ref is None:
        return GetAMRDetailOutput(
            success=False,
            amr_id=amr_id,
            position=None,
            state="UNKNOWN",
            battery_level=0.0,
            carrying_pod_id=None,
            current_mission_id=None,
            target=None,
            path_length_remaining=0,
            message="Orquestrador não inicializado.",
        )

    orch = _orchestrator_ref
    target_id = amr_id.upper().strip()
    num = re.sub(r"\D", "", target_id)
    if num:
        target_id = f"AMR-{int(num):02d}"

    if target_id not in orch.amrs:
        return GetAMRDetailOutput(
            success=False,
            amr_id=target_id,
            position=None,
            state="NOT_FOUND",
            battery_level=0.0,
            carrying_pod_id=None,
            current_mission_id=None,
            target=None,
            path_length_remaining=0,
            message=f"Robô '{target_id}' não encontrado na frota ativa.",
        )

    amr = orch.amrs[target_id]
    target_dict = (
        {"x": amr.target_picking_station[0], "y": amr.target_picking_station[1]}
        if amr.target_picking_station
        else (
            {"x": amr.target_charging_station[0], "y": amr.target_charging_station[1]}
            if amr.target_charging_station
            else None
        )
    )

    return GetAMRDetailOutput(
        success=True,
        amr_id=target_id,
        position={"x": amr.grid_x, "y": amr.grid_y},
        state=amr.state.value,
        battery_level=round(amr.battery_level, 1),
        carrying_pod_id=amr.carrying_pod_id,
        current_mission_id=amr.current_mission_id,
        target=target_dict,
        path_length_remaining=len(amr.path) - amr.path_step_idx if amr.path else 0,
        message=f"Robô {target_id} em ({amr.grid_x}, {amr.grid_y}) no estado {amr.state.value}.",
    )


class SimulationControlInput(BaseModel):
    action: str = Field(description="'pause', 'resume', 'toggle' ou 'set_speed'")
    speed: Optional[float] = Field(
        default=None, description="Multiplicador de velocidade (0.5 a 3.0)"
    )


class SimulationControlOutput(BaseModel):
    success: bool
    is_paused: bool
    speed: float
    message: str


def tool_simulation_control(
    action: str = "toggle", speed: Optional[float] = None
) -> SimulationControlOutput:
    """Controla o loop físico da simulação (pausar, retomar ou alterar velocidade)."""
    if _orchestrator_ref is None:
        return SimulationControlOutput(
            success=False, is_paused=False, speed=1.0, message="Orquestrador não inicializado."
        )

    orch = _orchestrator_ref
    act = action.lower().strip()

    if act in ("pause", "pausar", "congelar"):
        orch.is_paused = True
        msg = "Simulação pausada com sucesso. Todos os robôs mantiveram suas posições."
    elif act in ("resume", "play", "iniciar", "retomar", "despausar"):
        orch.is_paused = False
        msg = "Simulação retomada. AMRs continuam navegando normalmente."
    elif act in ("toggle", "alternar"):
        orch.is_paused = not orch.is_paused
        msg = f"Simulação {'pausada' if orch.is_paused else 'retomada'}."
    elif act in ("speed", "set_speed", "velocidade") and speed is not None:
        orch.simulation_speed = max(0.2, min(5.0, speed))
        msg = f"Velocidade da simulação ajustada para {orch.simulation_speed}x."
    else:
        msg = "Ação de simulação não reconhecida."

    if speed is not None and act not in ("speed", "set_speed", "velocidade"):
        orch.simulation_speed = max(0.2, min(5.0, speed))

    return SimulationControlOutput(
        success=True,
        is_paused=orch.is_paused,
        speed=orch.simulation_speed,
        message=msg,
    )


class WarehouseMetricsOutput(BaseModel):
    success: bool
    throughput_per_hour: float
    completed_orders: int
    pending_orders: int
    fleet_utilization_pct: float
    average_battery_pct: float
    active_incidents: int
    grid_size: str
    fleet_size: int
    message: str


def tool_get_warehouse_metrics() -> WarehouseMetricsOutput:
    """Consulta indicadores-chave de desempenho (KPIs) operacionais e de intralogística do galpão."""
    if _orchestrator_ref is None:
        return WarehouseMetricsOutput(
            success=False,
            throughput_per_hour=0.0,
            completed_orders=0,
            pending_orders=0,
            fleet_utilization_pct=0.0,
            average_battery_pct=0.0,
            active_incidents=0,
            grid_size="0x0",
            fleet_size=0,
            message="Orquestrador não inicializado.",
        )

    orch = _orchestrator_ref
    telemetries = [amr.get_telemetry() for amr in orch.amrs.values()]
    avg_bat = sum(t.battery_level for t in telemetries) / len(telemetries) if telemetries else 0.0
    active_in_transit = sum(1 for t in telemetries if t.state.value not in ("IDLE", "CHARGING"))
    utilization = (active_in_transit / len(telemetries) * 100.0) if telemetries else 0.0

    return WarehouseMetricsOutput(
        success=True,
        throughput_per_hour=round(orch.get_throughput_per_hour(), 1),
        completed_orders=len(orch.completed_orders),
        pending_orders=len(orch.pending_orders),
        fleet_utilization_pct=round(utilization, 1),
        average_battery_pct=round(avg_bat, 1),
        active_incidents=len(orch.grid.dynamic_blocks),
        grid_size=f"{orch.grid.width}x{orch.grid.height}",
        fleet_size=len(orch.amrs),
        message="Métricas do armazém calculadas em tempo real.",
    )


class TriggerChaosOutput(BaseModel):
    success: bool
    incident_type: str
    affected_amrs: List[str]
    rca_summary: str
    message: str


def tool_trigger_chaos(incident_type: Optional[str] = None) -> TriggerChaosOutput:
    """Injeta um incidente de teste controlado de Chaos Engineering para testar resiliência."""
    if _orchestrator_ref is None:
        return TriggerChaosOutput(
            success=False,
            incident_type="none",
            affected_amrs=[],
            rca_summary="",
            message="Orquestrador não inicializado.",
        )

    orch = _orchestrator_ref
    chaos = orch.chaos_engine

    t = (incident_type or "random").lower().strip()
    report = None

    if "slip" in t or "derrapagem" in t:
        report = chaos.trigger_wheel_slip()
    elif "wifi" in t or "rede" in t:
        report = chaos.trigger_wifi_packet_drop()
    elif "lidar" in t or "ponto cego" in t:
        report = chaos.trigger_lidar_blind_spot()
    else:
        report = chaos.trigger_random_incident()

    if not report:
        return TriggerChaosOutput(
            success=False,
            incident_type=t,
            affected_amrs=[],
            rca_summary="",
            message="Nenhum robô elegível em movimento no momento para injeção de incidente.",
        )

    return TriggerChaosOutput(
        success=True,
        incident_type=report.fault_type,
        affected_amrs=[report.primary_amr_id]
        + ([report.secondary_amr_id] if report.secondary_amr_id else []),
        rca_summary=report.capa_action,
        message=f"Incidente de teste ({report.fault_type}) injetado com sucesso no {report.primary_amr_id}. Protocolo de isolamento ativado.",
    )
