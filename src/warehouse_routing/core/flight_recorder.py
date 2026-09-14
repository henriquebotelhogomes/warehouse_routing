import time
from collections import deque
from typing import List, Optional

from pydantic import BaseModel

from warehouse_routing.core.amr_agent import AMRTelemetry
from warehouse_routing.core.grid import CellCoordinate


class SimulationSnapshot(BaseModel):
    tick: int
    timestamp_ms: int
    amrs: List[AMRTelemetry]
    dynamic_blocks: List[CellCoordinate]
    throughput_per_hour: float
    fleet_utilization_pct: float
    completed_orders_total: int


class FlightRecorder:
    """
    Gravador de 'Caixa Preta' (Flight Recorder / Timeline Replay).
    Mantém um buffer circular com os últimos N segundos de simulação
    para reprodução e auditoria de incidentes no frontend.
    """

    def __init__(self, max_snapshots: int = 600) -> None:
        self.max_snapshots = max_snapshots
        self.buffer: deque[SimulationSnapshot] = deque(maxlen=max_snapshots)

    def record_snapshot(
        self,
        tick: int,
        amrs: List[AMRTelemetry],
        dynamic_blocks: List[CellCoordinate],
        throughput_per_hour: float,
        fleet_utilization_pct: float,
        completed_orders_total: int,
    ) -> None:
        """Registra o estado do galpão no tick atual."""
        snapshot = SimulationSnapshot(
            tick=tick,
            timestamp_ms=int(time.time() * 1000),
            amrs=amrs,
            dynamic_blocks=dynamic_blocks,
            throughput_per_hour=round(throughput_per_hour, 1),
            fleet_utilization_pct=round(fleet_utilization_pct, 1),
            completed_orders_total=completed_orders_total,
        )
        self.buffer.append(snapshot)

    def get_timeline(self) -> List[SimulationSnapshot]:
        """Retorna todo o histórico disponível no buffer."""
        return list(self.buffer)

    def get_history(self, limit: int = 15) -> List[SimulationSnapshot]:
        """Retorna os últimos N snapshots arquivados no buffer."""
        items = list(self.buffer)
        return items[-limit:] if limit > 0 else items

    def get_snapshot_by_tick(self, tick: int) -> Optional[SimulationSnapshot]:
        """Recupera o estado exato de um tick específico."""
        for s in reversed(self.buffer):
            if s.tick == tick:
                return s
        return None

    def clear(self) -> None:
        """Limpa o buffer histórico."""
        self.buffer.clear()
