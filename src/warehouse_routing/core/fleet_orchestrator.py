import random
import time
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel

from warehouse_routing.core.amr_agent import AMRAgent, AMRState
from warehouse_routing.core.chaos_engine import ChaosEngine, ChaosFailureType, IncidentReport
from warehouse_routing.core.flight_recorder import FlightRecorder
from warehouse_routing.core.grid import CellCoordinate, WarehouseGrid
from warehouse_routing.core.space_time_mapf import ReservationTable, SpaceTimeAStar


class OrderMission(BaseModel):
    order_id: str
    target_pod_id: str
    target_pod_pos: Tuple[int, int]
    target_picking_station: Tuple[int, int]
    created_at_tick: int
    completed_at_tick: Optional[int] = None


class IncidentRecord(BaseModel):
    id: str
    tick: int
    timestamp: str
    type: str  # "BLOCKAGE", "DEADLOCK_RESOLVED", "LOW_BATTERY", "EMERGENCY_STOP"
    severity: str  # "INFO", "WARNING", "CRITICAL"
    description: str
    affected_amrs: List[str]
    resolved_in_seconds: float = 0.0


class FleetOrchestrator:
    """
    Orquestrador mestre da frota de robôs AMRs.
    Responsável pelo despacho de pedidos, resolução de conflitos MAPF,
    gerenciamento de incidentes e telemetria do armazém.
    """

    def __init__(self, grid: WarehouseGrid, num_amrs: int = 8):
        self.grid = grid
        self.reservations = ReservationTable()
        self.path_finder = SpaceTimeAStar(self.grid, self.reservations)
        self.flight_recorder = FlightRecorder(max_snapshots=600)

        self.current_tick: int = 0
        self.simulation_speed: float = 1.0  # Multiplicador
        self.is_paused: bool = False
        self.emergency_stop_active: bool = False

        # Frota de robôs
        self.amrs: Dict[str, AMRAgent] = {}
        self._initialize_amrs(num_amrs)

        # Fila de pedidos
        self.pending_orders: List[OrderMission] = []
        self.completed_orders: List[OrderMission] = []
        self.order_counter: int = 1

        # Auditoria de Incidentes & Relatórios Forenses (Chaos Engineering)
        self.incident_history: List[IncidentRecord] = []
        self.incident_reports: List[IncidentReport] = []
        self.active_incident: Optional[IncidentReport] = None
        self.incident_counter: int = 1

        # Métricas agregadas
        self.start_wall_time = time.time()
        self._generate_initial_orders(count=20)

    def _initialize_amrs(self, count: int) -> None:
        """Distribui os robôs pelas docas de recarga disponíveis."""
        docks = list(self.grid.charging_docks)
        if not docks:
            docks = [(0, 0)]

        for i in range(count):
            dock_pos = docks[i % len(docks)]
            amr_id = f"AMR-{i + 1:02d}"
            agent = AMRAgent(
                agent_id=amr_id,
                initial_x=dock_pos[0],
                initial_y=dock_pos[1],
                battery_level=random.uniform(75.0, 100.0),
            )
            agent.assigned_dock_pos = dock_pos
            self.amrs[amr_id] = agent

    def add_amrs(self, count: int = 1) -> List[str]:
        """
        Adiciona dinamicamente N robôs AMRs à frota em tempo de execução.
        Posiciona inicialmente em docas desocupadas ou em corredores livres.
        """
        if count <= 0:
            return []

        # Determina posições ocupadas no grid atualmente por outros robôs
        occupied_positions = {(amr.grid_x, amr.grid_y) for amr in self.amrs.values()}

        # Encontra vagas válidas: docas livres primeiro, depois corredores livres
        free_docks = [
            dock for dock in self.grid.charging_docks if dock not in occupied_positions
        ]

        # Corredores livres candidatos (sem obstáculos, sem pods, sem dynamic blocks, sem robôs)
        free_corridors = []
        if len(free_docks) < count:
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    pos = (x, y)
                    if (
                        pos not in self.grid.obstacles
                        and pos not in self.grid.pod_positions
                        and pos not in self.grid.dynamic_blocks
                        and pos not in occupied_positions
                        and pos not in free_docks
                    ):
                        free_corridors.append(pos)

        candidate_positions = free_docks + free_corridors
        if not candidate_positions:
            candidate_positions = list(self.grid.charging_docks) or [(0, 0)]

        # Determina o próximo índice numérico para o ID do robô (ex: AMR-09)
        existing_indices: List[int] = []
        for amr_id in self.amrs.keys():
            if amr_id.startswith("AMR-"):
                try:
                    existing_indices.append(int(amr_id.split("-")[1]))
                except ValueError:
                    pass
        next_idx = max(existing_indices, default=0) + 1

        added_ids: List[str] = []
        for i in range(count):
            spawn_pos = candidate_positions[i % len(candidate_positions)]
            new_id = f"AMR-{next_idx:02d}"
            next_idx += 1

            agent = AMRAgent(
                agent_id=new_id,
                initial_x=spawn_pos[0],
                initial_y=spawn_pos[1],
                battery_level=random.uniform(85.0, 100.0),
            )
            if spawn_pos in self.grid.charging_docks:
                agent.assigned_dock_pos = spawn_pos
            elif self.grid.charging_docks:
                agent.assigned_dock_pos = random.choice(list(self.grid.charging_docks))
            else:
                agent.assigned_dock_pos = spawn_pos

            self.amrs[new_id] = agent
            added_ids.append(new_id)
            occupied_positions.add(spawn_pos)

        # Registra auditoria do redimensionamento da frota
        self.incident_history.insert(
            0,
            IncidentRecord(
                id=f"INC-{self.incident_counter:03d}",
                tick=self.current_tick,
                timestamp=time.strftime("%H:%M:%S"),
                type="FLEET_SCALE",
                severity="INFO",
                description=f"Expansão de frota: +{len(added_ids)} robôs ({', '.join(added_ids)}). Total: {len(self.amrs)} AMRs.",
                affected_amrs=added_ids,
                resolved_in_seconds=0.0,
            ),
        )
        self.incident_counter += 1

        logger.info(
            f"Frota expandida em +{len(added_ids)} AMRs ({', '.join(added_ids)}). Total ativo: {len(self.amrs)}"
        )
        return added_ids

    def remove_amrs(self, count: int = 1, specific_ids: Optional[List[str]] = None) -> List[str]:
        """
        Remove dinamicamente robôs AMRs da frota em tempo de execução com descomissionamento seguro:
        1. Prioriza robôs ociosos (IDLE / CHARGING)
        2. Se em trânsito, devolve o pedido à fila de pendências
        3. Limpa todas as reservas na ReservationTable
        """
        if not self.amrs:
            return []

        targets_to_remove: List[AMRAgent] = []

        if specific_ids:
            for s_id in specific_ids:
                if s_id in self.amrs:
                    targets_to_remove.append(self.amrs[s_id])
        else:
            count = min(count, len(self.amrs))
            # Ordenação por menor criticidade operacional:
            # 1. IDLE ou CHARGING (sem carga ativa)
            # 2. MOVING_TO_POD (ainda não levantou pod)
            # 3. Demais estados
            sorted_amrs = sorted(
                self.amrs.values(),
                key=lambda a: (
                    0
                    if a.state in (AMRState.IDLE, AMRState.CHARGING)
                    else 1
                    if a.state == AMRState.MOVING_TO_POD
                    else 2
                ),
            )
            targets_to_remove = sorted_amrs[:count]

        removed_ids: List[str] = []
        for amr in targets_to_remove:
            # Se estava com uma missão ou pod
            if amr.current_mission_id:
                order_to_requeue = OrderMission(
                    order_id=amr.current_mission_id,
                    target_pod_id=amr.target_pod_id or "POD-001",
                    target_pod_pos=amr.target_pod_pos or (amr.grid_x, amr.grid_y),
                    target_picking_station=amr.target_picking_station or (0, 0),
                    created_at_tick=self.current_tick,
                )
                self.pending_orders.insert(0, order_to_requeue)

            # Limpa todas as reservas de espaço-tempo deste robô
            self.reservations.clear_agent(amr.id)

            # Remove da frota
            self.amrs.pop(amr.id, None)
            removed_ids.append(amr.id)

        if removed_ids:
            self.incident_history.insert(
                0,
                IncidentRecord(
                    id=f"INC-{self.incident_counter:03d}",
                    tick=self.current_tick,
                    timestamp=time.strftime("%H:%M:%S"),
                    type="FLEET_SCALE",
                    severity="WARNING" if any(a.carrying_pod_id for a in targets_to_remove) else "INFO",
                    description=f"Descomissionamento de frota: -{len(removed_ids)} robôs ({', '.join(removed_ids)}). Total restante: {len(self.amrs)} AMRs.",
                    affected_amrs=removed_ids,
                    resolved_in_seconds=0.0,
                ),
            )
            self.incident_counter += 1

            logger.warning(
                f"Frota reduzida em -{len(removed_ids)} AMRs ({', '.join(removed_ids)}). Total restante: {len(self.amrs)}"
            )

        return removed_ids

    def set_fleet_size(self, target_count: int) -> Dict[str, Any]:
        """Ajusta a frota exatamente para o tamanho desejado (scale up ou scale down)."""
        target_count = max(0, min(50, target_count))
        current_count = len(self.amrs)

        added: List[str] = []
        removed: List[str] = []

        if target_count > current_count:
            added = self.add_amrs(target_count - current_count)
        elif target_count < current_count:
            removed = self.remove_amrs(current_count - target_count)

        return {
            "previous_count": current_count,
            "current_count": len(self.amrs),
            "added_amrs": added,
            "removed_amrs": removed,
        }

    def _generate_initial_orders(self, count: int) -> None:
        """Gera uma fila inicial de ordens de separação."""
        pod_ids = list(self.grid.pods_by_id.keys())
        stations = list(self.grid.picking_stations)
        if not pod_ids or not stations:
            return

        for _ in range(count):
            pod_id = random.choice(pod_ids)
            pod = self.grid.pods_by_id[pod_id]
            station = random.choice(stations)

            mission = OrderMission(
                order_id=f"ORD-{self.order_counter:04d}",
                target_pod_id=pod_id,
                target_pod_pos=(pod.x, pod.y),
                target_picking_station=station,
                created_at_tick=self.current_tick,
            )
            self.pending_orders.append(mission)
            self.order_counter += 1

    def dispatch_pending_orders(self) -> None:
        """Atribui ordens aos robôs ociosos disponíveis."""
        available_amrs = [a for a in self.amrs.values() if a.is_available_for_orders()]

        for amr in available_amrs:
            if not self.pending_orders:
                # Se acabaram os pedidos, gera mais para manter a simulação viva
                self._generate_initial_orders(count=10)

            if not self.pending_orders:
                break

            mission = self.pending_orders.pop(0)
            amr.current_mission_id = mission.order_id
            amr.target_pod_id = mission.target_pod_id
            amr.target_pod_pos = mission.target_pod_pos
            amr.target_picking_station = mission.target_picking_station

            # Planeja perna 1: Ir da posição atual até embaixo da prateleira (POD)
            start_pos = (amr.grid_x, amr.grid_y)
            path = self.path_finder.find_path(
                agent_id=amr.id,
                start=start_pos,
                target=mission.target_pod_pos,
                start_time=self.current_tick,
            )

            if path:
                amr.set_path(path)
                amr.state = AMRState.MOVING_TO_POD
                self.reservations.reserve_path(amr.id, path, start_time=self.current_tick)
                logger.info(
                    f"{amr.id} despachado para {mission.target_pod_id} ({len(path)} passos)"
                )
            else:
                # Devolve o pedido para a fila se não encontrou rota
                self.pending_orders.insert(0, mission)

    def handle_mission_transitions(self) -> None:
        """
        Gerencia o planejamento de rotas nas transições de estado dos robôs
        (Ex: Pod levantado -> Rota até estação de picking -> Devolver pod).
        """
        for amr in self.amrs.values():
            # 1. Acabou de levantar o pod -> Rota para Estação de Picking
            if (
                amr.state == AMRState.TRANSITING_TO_PICKING
                and amr.target_picking_station
                and amr.has_completed_path
            ):
                start_pos = (amr.grid_x, amr.grid_y)
                path = self.path_finder.find_path(
                    agent_id=amr.id,
                    start=start_pos,
                    target=amr.target_picking_station,
                    start_time=self.current_tick,
                )
                if path:
                    amr.set_path(path)
                    self.reservations.reserve_path(amr.id, path, start_time=self.current_tick)

            # 2. Concluiu separação na bancada -> Rota para devolver pod na posição original
            elif (
                amr.state == AMRState.AT_PICKING_STATION
                and amr.action_wait_ticks == 0
                and amr.target_pod_pos
            ):
                start_pos = (amr.grid_x, amr.grid_y)
                path = self.path_finder.find_path(
                    agent_id=amr.id,
                    start=start_pos,
                    target=amr.target_pod_pos,
                    start_time=self.current_tick,
                )
                if path:
                    amr.state = AMRState.RETURNING_POD
                    amr.set_path(path)
                    self.reservations.reserve_path(amr.id, path, start_time=self.current_tick)

                    # Registra ordem como concluída
                    self.completed_orders.append(
                        OrderMission(
                            order_id=amr.current_mission_id or "UNKNOWN",
                            target_pod_id=amr.target_pod_id or "UNKNOWN",
                            target_pod_pos=amr.target_pod_pos or (0, 0),
                            target_picking_station=amr.target_picking_station or (0, 0),
                            created_at_tick=self.current_tick - 20,
                            completed_at_tick=self.current_tick,
                        )
                    )

            # 2b. Fallback caso esteja em RETURNING_POD sem caminho ativo
            elif (
                amr.state == AMRState.RETURNING_POD
                and amr.target_pod_pos
                and amr.has_completed_path
            ):
                start_pos = (amr.grid_x, amr.grid_y)
                path = self.path_finder.find_path(
                    agent_id=amr.id,
                    start=start_pos,
                    target=amr.target_pod_pos,
                    start_time=self.current_tick,
                )
                if path:
                    amr.set_path(path)
                    self.reservations.reserve_path(amr.id, path, start_time=self.current_tick)

            # 3. Ficou ocioso com bateria baixa -> Rota para doca de recarga
            elif amr.state == AMRState.IDLE and amr.is_battery_critical() and amr.has_completed_path:
                start_pos = (amr.grid_x, amr.grid_y)
                if start_pos == amr.assigned_dock_pos:
                    amr.state = AMRState.CHARGING
                else:
                    path = self.path_finder.find_path(
                        agent_id=amr.id,
                        start=start_pos,
                        target=amr.assigned_dock_pos,
                        start_time=self.current_tick,
                    )
                    if path:
                        amr.set_path(path)
                        self.reservations.reserve_path(amr.id, path, start_time=self.current_tick)

    def block_area(
        self, x: int, y: int, reason: str = "Incidente manual"
    ) -> Tuple[bool, List[str], float]:
        """
        Interdita uma célula no armazém e re-planeja imediatamente as rotas dos AMRs afetados.
        Retorna (sucesso, lista_robos_afetados, impacto_medio_segundos).
        """
        if not self.grid.add_dynamic_block(x, y):
            return False, [], 0.0

        affected_amrs: List[str] = []
        extra_steps_total = 0

        for amr in self.amrs.values():
            if not amr.path:
                continue

            # Verifica se o caminho futuro do robô cruza a célula bloqueada
            remaining_path = amr.path[amr.path_step_idx :]
            if (x, y) in remaining_path:
                affected_amrs.append(amr.id)
                old_len = len(remaining_path)
                target = amr.path[-1]

                # Remove reservas antigas do robô e calcula nova rota
                self.reservations.clear_agent(amr.id)
                new_path = self.path_finder.find_path(
                    agent_id=amr.id,
                    start=(amr.grid_x, amr.grid_y),
                    target=target,
                    start_time=self.current_tick,
                )

                if new_path:
                    amr.set_path(new_path)
                    self.reservations.reserve_path(amr.id, new_path, start_time=self.current_tick)
                    extra_steps = max(0, len(new_path) - old_len)
                    extra_steps_total += extra_steps
                    logger.warning(
                        f"Desvio de rota aplicado a {amr.id}: {old_len} -> {len(new_path)} passos"
                    )

        avg_impact = (
            round((extra_steps_total / len(affected_amrs)) * 1.5, 2) if affected_amrs else 0.0
        )

        # Registra incidente na auditoria
        self.incident_history.insert(
            0,
            IncidentRecord(
                id=f"INC-{self.incident_counter:03d}",
                tick=self.current_tick,
                timestamp=time.strftime("%H:%M:%S"),
                type="BLOCKAGE",
                severity="WARNING" if len(affected_amrs) > 0 else "INFO",
                description=f"Bloqueio em ({x}, {y}): {reason}",
                affected_amrs=affected_amrs,
                resolved_in_seconds=avg_impact,
            ),
        )
        self.incident_counter += 1

        return True, affected_amrs, avg_impact

    def unblock_area(self, x: int, y: int) -> bool:
        """Libera uma célula previamente bloqueada."""
        return self.grid.remove_dynamic_block(x, y)

    def emergency_stop(self, activate: bool) -> None:
        """Ativa ou desativa a parada de emergência da frota (ISO 3691-4)."""
        self.emergency_stop_active = activate
        self.incident_history.insert(
            0,
            IncidentRecord(
                id=f"INC-{self.incident_counter:03d}",
                tick=self.current_tick,
                timestamp=time.strftime("%H:%M:%S"),
                type="EMERGENCY_STOP",
                severity="CRITICAL" if activate else "INFO",
                description="Parada de Emergência Geral da Frota "
                + ("ATIVADA" if activate else "DESATIVADA"),
                affected_amrs=list(self.amrs.keys()) if activate else [],
            ),
        )
        self.incident_counter += 1

    def step(self) -> None:
        """Avança 1 tick da simulação do armazém."""
        if self.is_paused or self.emergency_stop_active:
            return

        self.current_tick += 1

        # 1. Atribui novos pedidos para robôs ociosos
        self.dispatch_pending_orders()

        # 2. Executa o tick mecânico de cada robô
        for amr in self.amrs.values():
            amr.update_tick()

        # 3. Gerencia transições entre etapas das missões
        self.handle_mission_transitions()

        # 4. Registra snapshot no Flight Recorder a cada 2 ticks para economizar memória
        if self.current_tick % 2 == 0:
            telemetries = [amr.get_telemetry() for amr in self.amrs.values()]
            dynamic_blocks = [CellCoordinate(x=c[0], y=c[1]) for c in self.grid.dynamic_blocks]
            self.flight_recorder.record_snapshot(
                tick=self.current_tick,
                amrs=telemetries,
                dynamic_blocks=dynamic_blocks,
                throughput_per_hour=self.get_throughput_per_hour(),
                fleet_utilization_pct=self.get_fleet_utilization_pct(),
                completed_orders_total=len(self.completed_orders),
            )

    def get_throughput_per_hour(self) -> float:
        """Calcula a vazão estimada de pedidos por hora."""
        if self.current_tick == 0:
            return 0.0
        # Supondo 1 tick = 0.5 segundo -> 7200 ticks por hora
        return round((len(self.completed_orders) / max(1, self.current_tick)) * 7200, 1)

    def get_fleet_utilization_pct(self) -> float:
        """Calcula a % de robôs realizando atividades produtivas."""
        if not self.amrs:
            return 0.0
        active = sum(
            1 for a in self.amrs.values() if a.state not in (AMRState.IDLE, AMRState.CHARGING)
        )
        return round((active / len(self.amrs)) * 100, 1)

    def get_telemetry_payload(self) -> dict:
        """Gera payload completo para o canal de WebSocket do frontend."""
        telemetries = [amr.get_telemetry().model_dump() for amr in self.amrs.values()]
        blocks = [{"x": c[0], "y": c[1]} for c in self.grid.dynamic_blocks]

        return {
            "tick": self.current_tick,
            "is_paused": self.is_paused,
            "emergency_stop": self.emergency_stop_active,
            "speed": self.simulation_speed,
            "amrs": telemetries,
            "dynamic_blocks": blocks,
            "active_incident": self.active_incident.model_dump() if self.active_incident else None,
            "incidents_count": len(self.incident_reports),
            "metrics": {
                "throughput_per_hour": self.get_throughput_per_hour(),
                "fleet_utilization_pct": self.get_fleet_utilization_pct(),
                "completed_orders": len(self.completed_orders),
                "pending_orders": len(self.pending_orders),
                "active_incidents": len(self.grid.dynamic_blocks),
            },
        }

    def inject_chaos(self, failure_type: str = "random", count: int = 1) -> IncidentReport:
        """Injeta colisão controlada e anomalia física na frota (Chaos Engineering)."""
        try:
            parsed_type = ChaosFailureType(failure_type.lower())
        except ValueError:
            parsed_type = ChaosFailureType.RANDOM

        report = ChaosEngine.inject_collision(self, failure_type=parsed_type, target_count=count)
        self.active_incident = report
        self.incident_reports.insert(0, report)

        # Adiciona no log de auditoria
        self.incident_history.insert(
            0,
            IncidentRecord(
                id=report.incident_id,
                tick=self.current_tick,
                timestamp=report.timestamp,
                type="COLLISION",
                severity=report.impact_metrics.damage_severity,
                description=report.summary,
                affected_amrs=report.involved_amrs,
            ),
        )
        logger.warning(f"💥 CAOS INJETADO: {report.summary}")
        return report

    def resolve_incident(self, incident_id: str, self_healing: bool = True) -> Dict[str, Any]:
        """Resolve o incidente, aplicando opcionalmente auto-cura (Self-Healing)."""
        report = next((r for r in self.incident_reports if r.incident_id == incident_id), None)
        if not report:
            return {"success": False, "message": f"Incidente {incident_id} não encontrado."}

        report.is_resolved = True
        report.resolved_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Aplica Self-Healing: adiciona barreira de isolamento temporária no ponto da colisão
        if self_healing:
            cx, cy = report.location["x"], report.location["y"]
            self.block_area(cx, cy, reason=f"Isolamento perimetral do acidente {incident_id}")
            report.isolation_block_cells.append({"x": cx, "y": cy})

        # 2. Recupera os robôs acidentados
        for amr_id in report.involved_amrs:
            if amr_id in self.amrs:
                amr = self.amrs[amr_id]
                amr.recover_from_crash()
                self.reservations.clear_agent(amr_id)
                amr.carrying_pod_id = None
                amr.current_mission_id = None
                amr.path = []
                amr.path_step_idx = 0

        if self.active_incident and self.active_incident.incident_id == incident_id:
            self.active_incident = None

        return {
            "success": True,
            "incident_id": incident_id,
            "is_resolved": True,
            "self_healing_applied": self_healing,
            "message": f"Incidente {incident_id} resolvido com sucesso.",
        }
