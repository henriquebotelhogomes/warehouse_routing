import heapq
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger

from warehouse_routing.core.grid import WarehouseGrid


class ReservationTable:
    """
    Tabela de Reserva Espaço-Temporal para prevenção formal de colisões em MAPF.
    Mapeia ocupações de células e arestas no tempo (x, y, t).
    """

    def __init__(self) -> None:
        # Vértice: (x, y, t) -> agent_id
        self.vertex_reservations: Dict[Tuple[int, int, int], str] = {}
        # Aresta: ((from_x, from_y), (to_x, to_y), t) -> agent_id
        self.edge_reservations: Dict[Tuple[Tuple[int, int], Tuple[int, int], int], str] = {}
        # Mapeamento reverso para limpeza rápida por agente
        self.agent_reservations: Dict[str, List[Tuple[int, int, int]]] = {}

    def is_vertex_reserved(self, x: int, y: int, t: int, requesting_agent: str) -> bool:
        """Verifica se a célula (x, y) está reservada no instante t por outro agente."""
        occupant = self.vertex_reservations.get((x, y, t))
        return occupant is not None and occupant != requesting_agent

    def is_edge_reserved(
        self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], t: int, requesting_agent: str
    ) -> bool:
        """
        Verifica conflito de aresta: se outro agente estiver se movendo
        na direção oposta exatamente no mesmo instante de tempo (colisão frontal).
        """
        reverse_edge = (to_pos, from_pos, t)
        occupant = self.edge_reservations.get(reverse_edge)
        return occupant is not None and occupant != requesting_agent

    def reserve_path(self, agent_id: str, path: List[Tuple[int, int]], start_time: int = 0) -> None:
        """Reserva a trajetória completa de um robô na malha espaço-temporal."""
        self.clear_agent(agent_id)

        reserved_cells: List[Tuple[int, int, int]] = []
        for i, (x, y) in enumerate(path):
            t = start_time + i
            self.vertex_reservations[(x, y, t)] = agent_id
            reserved_cells.append((x, y, t))

            if i > 0:
                prev_pos = path[i - 1]
                edge = (prev_pos, (x, y), t - 1)
                self.edge_reservations[edge] = agent_id

        self.agent_reservations[agent_id] = reserved_cells

    def clear_agent(self, agent_id: str) -> None:
        """Remove todas as reservas de um agente (usado ao recalcular rota ou concluir missão)."""
        if agent_id in self.agent_reservations:
            for x, y, t in self.agent_reservations[agent_id]:
                self.vertex_reservations.pop((x, y, t), None)
            del self.agent_reservations[agent_id]

        # Limpa arestas do agente
        edges_to_remove = [
            edge for edge, occupant in self.edge_reservations.items() if occupant == agent_id
        ]
        for edge in edges_to_remove:
            del self.edge_reservations[edge]


class SpaceTimeAStar:
    """
    Solucionador de caminho ótimo individual dentro de uma reserva espaço-temporal compartilhada.
    Navega em dimensão tridimensional (X, Y, Tempo).
    """

    def __init__(self, grid: WarehouseGrid, reservation_table: ReservationTable):
        self.grid = grid
        self.reservations = reservation_table

    @staticmethod
    def heuristic(pos: Tuple[int, int], target: Tuple[int, int]) -> int:
        """Distância Manhattan como heurística admissível."""
        return abs(pos[0] - target[0]) + abs(pos[1] - target[1])

    def find_path(
        self,
        agent_id: str,
        start: Tuple[int, int],
        target: Tuple[int, int],
        start_time: int = 0,
        max_time_horizon: int = 250,
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Encontra uma trajetória livre de colisões do ponto `start` até `target`
        respeitando as reservas de outros agentes na ReservationTable.
        """
        if start == target:
            return [start]

        # Fila de prioridade: (f_score, g_score, (x, y, t), path)
        open_set: List[Tuple[int, int, Tuple[int, int, int], List[Tuple[int, int]]]] = []
        initial_h = self.heuristic(start, target)
        heapq.heappush(open_set, (initial_h, 0, (start[0], start[1], start_time), [start]))

        # Conjunto de estados visitados no espaço-tempo: (x, y, t)
        closed_set: Set[Tuple[int, int, int]] = set()

        while open_set:
            _, g, (curr_x, curr_y, curr_t), path = heapq.heappop(open_set)

            if (curr_x, curr_y) == target:
                return path

            state_key = (curr_x, curr_y, curr_t)
            if state_key in closed_set:
                continue
            closed_set.add(state_key)

            if curr_t - start_time >= max_time_horizon:
                continue

            # Gera vizinhos incluindo a ação de esperar na mesma célula
            next_t = curr_t + 1
            neighbors = self.grid.get_neighbors(curr_x, curr_y, allow_wait=True)

            for nx, ny in neighbors:
                # 1. Regra de Corredor Industrial: prateleiras intermediárias são obstáculos físicos
                # (o robô só pode ingressar na célula da prateleira se for a origem ou o destino final)
                if (nx, ny) in self.grid.pod_positions and (nx, ny) != target and (nx, ny) != start:
                    continue

                # 2. Verifica se a célula está livre no espaço-tempo t+1
                if self.reservations.is_vertex_reserved(nx, ny, next_t, requesting_agent=agent_id):
                    continue

                # 3. Verifica se não há colisão de aresta (robôs trocando de posição)
                if self.reservations.is_edge_reserved(
                    (curr_x, curr_y), (nx, ny), curr_t, requesting_agent=agent_id
                ):
                    continue

                neighbor_state = (nx, ny, next_t)
                if neighbor_state in closed_set:
                    continue

                next_g = g + 1
                next_h = self.heuristic((nx, ny), target)
                next_f = next_g + next_h

                heapq.heappush(open_set, (next_f, next_g, neighbor_state, path + [(nx, ny)]))

        logger.warning(
            f"SpaceTimeAStar: Nenhum caminho livre de colisão encontrado para {agent_id} "
            f"de {start} até {target} dentro do horizonte {max_time_horizon}."
        )
        return None
