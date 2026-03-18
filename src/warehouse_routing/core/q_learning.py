import os
import time
from typing import Dict, List

import joblib
import numpy as np
from loguru import logger


class WarehouseRouteOptimizer:
    """
    Motor de IA baseado em Q-Learning para otimização de rotas.
    Inclui persistência de modelo e monitoramento de performance.
    """

    def __init__(
        self,
        locations: List[str],
        rewards_matrix: np.ndarray,
        gamma: float,
        alpha: float,
    ):
        self.locations = locations
        self.num_states = len(locations)
        self.rewards_matrix = rewards_matrix
        self.gamma = gamma
        self.alpha = alpha

        # Mapeamentos para tradução Estado <-> Local
        self.location_to_state: Dict[str, int] = {loc: i for i, loc in enumerate(locations)}
        self.state_to_location: Dict[int, str] = {i: loc for i, loc in enumerate(locations)}

        # Cache de Q-Tables (Inteligência por destino)
        self._q_table_cache: Dict[str, np.ndarray] = {}

    def save_model(self, filepath: str) -> None:
        """Persiste o conhecimento da IA no disco."""
        try:
            logger.info(f"Salvando inteligência em: {filepath}")
            joblib.dump(self._q_table_cache, filepath)
        except Exception as e:
            logger.error(f"Falha ao salvar modelo: {e}")

    def load_model(self, filepath: str) -> None:
        """Carrega o conhecimento prévio da IA."""
        if os.path.exists(filepath):
            try:
                logger.info(f"Carregando inteligência prévia de: {filepath}")
                self._q_table_cache = joblib.load(filepath)
            except Exception as e:
                logger.error(f"Erro ao carregar modelo: {e}. Iniciando do zero.")
        else:
            logger.warning("Nenhum modelo prévio encontrado. O agente iniciará sem memória.")

    def _validate_location(self, location: str) -> None:
        if location not in self.location_to_state:
            raise ValueError(f"Local '{location}' não existe no mapa do armazém.")

    def train(
        self, ending_location: str, epochs: int = 1000, force_retrain: bool = False
    ) -> np.ndarray:
        """Treina o agente para chegar a um destino específico."""
        self._validate_location(ending_location)

        if not force_retrain and ending_location in self._q_table_cache:
            logger.debug(f"Cache HIT: Usando inteligência existente para {ending_location}")
            return self._q_table_cache[ending_location]

        # --- MEDIÇÃO DE PERFORMANCE DA IA ---
        start_time = time.perf_counter()

        logger.info(f"IA treinando nova rota para: {ending_location}...")

        r_new = np.copy(self.rewards_matrix)
        ending_state = self.location_to_state[ending_location]
        r_new[ending_state, ending_state] = 1000

        q_table = np.zeros((self.num_states, self.num_states))

        for _ in range(epochs):
            current_state = np.random.randint(0, self.num_states)
            playable_actions = np.where(r_new[current_state, :] > 0)[0]

            if len(playable_actions) == 0:
                continue

            next_state = np.random.choice(playable_actions)
            td = (
                r_new[current_state, next_state]
                + self.gamma * np.max(q_table[next_state, :])
                - q_table[current_state, next_state]
            )
            q_table[current_state, next_state] += self.alpha * td

        self._q_table_cache[ending_location] = q_table

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.success(f"Treino concluído para {ending_location} em {duration_ms:.2f}ms")

        return q_table

    def update_path(self, location_a: str, location_b: str, is_open: bool) -> None:
        """Altera a topologia do armazém dinamicamente."""
        self._validate_location(location_a)
        self._validate_location(location_b)

        state_a = self.location_to_state[location_a]
        state_b = self.location_to_state[location_b]
        reward = 1 if is_open else 0

        self.rewards_matrix[state_a, state_b] = reward
        self.rewards_matrix[state_b, state_a] = reward

        logger.warning(
            f"Grafo alterado: {location_a}-{location_b} -> {'Aberto' if is_open else 'Bloqueado'}"
        )
        self._q_table_cache.clear()  # Invalida cache pois o ambiente mudou

    def get_route(self, starting_location: str, ending_location: str) -> List[str]:
        """Extrai a melhor rota baseada na Q-Table treinada."""
        self._validate_location(starting_location)
        self._validate_location(ending_location)

        q_table = self.train(ending_location)
        route = [starting_location]
        next_location = starting_location

        while next_location != ending_location:
            current_state = self.location_to_state[next_location]
            next_state = int(np.argmax(q_table[current_state, :]))
            next_location = self.state_to_location[next_state]
            route.append(next_location)

        return route

    def get_route_with_intermediary(self, start: str, intermediary: str, end: str) -> List[str]:
        """Calcula rota composta passando por um ponto de coleta."""
        route_1 = self.get_route(start, intermediary)
        route_2 = self.get_route(intermediary, end)
        return route_1 + route_2[1:]
