from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from warehouse_routing.core.grid import CellCoordinate


class AMRState(str, Enum):
    IDLE = "IDLE"
    MOVING_TO_POD = "MOVING_TO_POD"
    LIFTING_POD = "LIFTING_POD"
    TRANSITING_TO_PICKING = "TRANSITING_TO_PICKING"
    AT_PICKING_STATION = "AT_PICKING_STATION"
    RETURNING_POD = "RETURNING_POD"
    LOWERING_POD = "LOWERING_POD"
    CHARGING = "CHARGING"
    AVOIDING_DEADLOCK = "AVOIDING_DEADLOCK"
    CRASHED = "CRASHED"


class AMRTelemetry(BaseModel):
    id: str
    x: float
    y: float
    grid_x: int
    grid_y: int
    target_x: Optional[int] = None
    target_y: Optional[int] = None
    state: AMRState
    battery_level: float = Field(ge=0.0, le=100.0)
    carrying_pod_id: Optional[str] = None
    current_mission_id: Optional[str] = None
    planned_path: List[CellCoordinate] = Field(default_factory=list)
    is_crashed: bool = False
    crash_reason: Optional[str] = None


class AMRAgent:
    """
    Agente robótico autônomo (AMR) com Máquina de Estados Finita (FSM)
    e modelo dinâmico de consumo de bateria.
    """

    def __init__(
        self,
        agent_id: str,
        initial_x: int,
        initial_y: int,
        battery_level: float = 100.0,
    ):
        self.id = agent_id
        self.x = float(initial_x)
        self.y = float(initial_y)
        self.grid_x = initial_x
        self.grid_y = initial_y

        self.battery_level = battery_level
        self.state = AMRState.IDLE
        self.carrying_pod_id: Optional[str] = None
        self.current_mission_id: Optional[str] = None
        self.is_crashed: bool = False
        self.crash_reason: Optional[str] = None

        # Caminho planejado no tempo: lista de (x, y)
        self.path: List[Tuple[int, int]] = []
        self.path_step_idx: int = 0

        # Contadores de espera para ações mecânicas
        self.action_wait_ticks: int = 0

        # Alvos da missão
        self.target_pod_id: Optional[str] = None
        self.target_pod_pos: Optional[Tuple[int, int]] = None
        self.target_picking_station: Optional[Tuple[int, int]] = None
        self.assigned_dock_pos: Tuple[int, int] = (initial_x, initial_y)

    def is_battery_critical(self) -> bool:
        """Indica se o nível de bateria requer recarga urgente (< 20%)."""
        return self.battery_level < 20.0

    def is_available_for_orders(self) -> bool:
        """Verifica se o robô está livre e com energia suficiente para novas tarefas."""
        return (
            self.state == AMRState.IDLE and not self.is_battery_critical() and not self.is_crashed
        )

    def set_path(self, path: List[Tuple[int, int]]) -> None:
        """Atribui uma nova rota calculada pelo SpaceTimeAStar."""
        self.path = path
        self.path_step_idx = 0

    def force_crash(self, reason: str = "Colisão física detectada") -> None:
        """Força o robô ao estado de avaria/colisão física (Chaos Engineering)."""
        self.state = AMRState.CRASHED
        self.is_crashed = True
        self.crash_reason = reason
        self.path = []
        self.path_step_idx = 0

    def recover_from_crash(self) -> None:
        """Recupera o robô acidentado, restaurando-o ao estado seguro IDLE."""
        self.is_crashed = False
        self.crash_reason = None
        self.state = AMRState.IDLE
        self.path = []
        self.path_step_idx = 0

    def update_tick(self) -> None:
        """
        Executa 1 tick de simulação na Máquina de Estados do robô.
        """
        # 0. Robô acidentado (CRASHED) permanece imobilizado por segurança
        if self.state == AMRState.CRASHED:
            return

        # 1. Comportamento no estado CHARGING
        if self.state == AMRState.CHARGING:
            self.battery_level = min(100.0, self.battery_level + 2.5)
            if self.battery_level >= 95.0:
                self.state = AMRState.IDLE
            return

        # 2. Ações mecânicas com tempo de espera (Lifting / Lowering / At Station)
        if self.action_wait_ticks > 0:
            self.action_wait_ticks -= 1
            if self.action_wait_ticks == 0:
                self._handle_action_completion()
            return

        # 3. Movimentação ao longo do caminho planejado
        if self.path and self.path_step_idx < len(self.path):
            next_pos = self.path[self.path_step_idx]
            self.grid_x, self.grid_y = next_pos
            self.x, self.y = float(self.grid_x), float(self.grid_y)
            self.path_step_idx += 1

            # Consumo de bateria por deslocamento
            discharge_rate = 0.25 if self.carrying_pod_id else 0.15
            self.battery_level = max(0.0, self.battery_level - discharge_rate)

            # Verifica se chegou ao final do caminho atual
            if self.path_step_idx >= len(self.path):
                self._handle_path_arrival()

    @property
    def has_completed_path(self) -> bool:
        """Verifica se o robô não possui caminho ativo ou se já percorreu todos os passos."""
        return not self.path or self.path_step_idx >= len(self.path)

    def _handle_path_arrival(self) -> None:
        """Processa a chegada ao destino de uma perna da missão."""
        self.path = []
        self.path_step_idx = 0

        if self.state == AMRState.MOVING_TO_POD:
            # Chegou embaixo da prateleira -> Inicia acoplamento (LIFTING)
            self.state = AMRState.LIFTING_POD
            self.action_wait_ticks = 2  # 2 ticks para suspender o pod

        elif self.state == AMRState.TRANSITING_TO_PICKING:
            # Chegou na bancada de conferência -> Inicia separação de itens
            self.state = AMRState.AT_PICKING_STATION
            self.action_wait_ticks = 3  # 3 ticks para o operador separar o item

        elif self.state == AMRState.RETURNING_POD:
            # Chegou de volta na vaga da prateleira -> Inicia desacoplamento (LOWERING)
            self.state = AMRState.LOWERING_POD
            self.action_wait_ticks = 2  # 2 ticks para descer o pod

        elif self.state == AMRState.IDLE and self.is_battery_critical():
            # Chegou na doca de recarga
            self.state = AMRState.CHARGING

    def _handle_action_completion(self) -> None:
        """Processa o término de uma ação mecânica."""
        self.path = []
        self.path_step_idx = 0

        if self.state == AMRState.LIFTING_POD:
            self.carrying_pod_id = self.target_pod_id
            self.state = AMRState.TRANSITING_TO_PICKING

        elif self.state == AMRState.LOWERING_POD:
            self.carrying_pod_id = None
            self.target_pod_id = None
            self.current_mission_id = None

            # Avalia se deve ir para recarga ou ficar ocioso
            if self.is_battery_critical():
                self.state = AMRState.IDLE  # O orquestrador planejará a rota até a doca
            else:
                self.state = AMRState.IDLE

    def get_telemetry(self) -> AMRTelemetry:
        """Gera payload serializável de telemetria do robô."""
        target_x: Optional[int] = None
        target_y: Optional[int] = None
        if self.path and self.path_step_idx < len(self.path):
            target_x, target_y = self.path[-1]

        planned = [CellCoordinate(x=p[0], y=p[1]) for p in self.path[self.path_step_idx :]]

        return AMRTelemetry(
            id=self.id,
            x=self.x,
            y=self.y,
            grid_x=self.grid_x,
            grid_y=self.grid_y,
            target_x=target_x,
            target_y=target_y,
            state=self.state,
            battery_level=round(self.battery_level, 1),
            carrying_pod_id=self.carrying_pod_id,
            current_mission_id=self.current_mission_id,
            planned_path=planned,
            is_crashed=self.is_crashed,
            crash_reason=self.crash_reason,
        )
