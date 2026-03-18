import numpy as np
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Configurações globais da aplicação utilizando Pydantic Settings.
    Os valores podem ser sobrescritos por variáveis de ambiente ou um arquivo .env.
    """

    # Metadados da API
    app_name: str = "Warehouse AI Route Optimizer"
    environment: str = "development"

    # Hiperparâmetros do Q-Learning (Valores padrão otimizados)
    # Gamma: Fator de desconto (importância de recompensas futuras)
    # Alpha: Taxa de aprendizado
    gamma: float = 0.75
    alpha: float = 0.9
    training_epochs: int = 1000

    # Persistência
    model_save_path: str = "warehouse_q_model.joblib"

    # Configuração para carregar arquivo .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Instância global para ser importada nos outros módulos
settings = Settings()

# =============================================================================
# DEFINIÇÃO DA TOPOLOGIA DO ARMAZÉM
# =============================================================================

# Lista de locais (Nós do Grafo)
LOCATIONS: List[str] = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]


def generate_base_rewards_matrix() -> np.ndarray:
    """
    Gera a matriz de recompensas (R) baseada nas conexões físicas do armazém.
    Valor 1 indica que existe um corredor entre os dois locais.
    Valor 0 indica que não há conexão direta.
    """
    num_locations = len(LOCATIONS)
    # Inicializa matriz com zeros
    r = np.zeros((num_locations, num_locations))

    # Mapeamento manual de adjacência (Conexões do Grafo)
    # Exemplo: A conecta com B (índice 0 com índice 1)
    connections = [
        ("A", "B"),
        ("B", "C"),
        ("B", "F"),
        ("C", "D"),
        ("D", "E"),
        ("E", "I"),
        ("F", "G"),
        ("G", "H"),
        ("H", "I"),
        ("I", "J"),
        ("J", "K"),
        ("K", "L"),
    ]

    # Preenche a matriz (Grafo não direcionado: se A vai para B, B vai para A)
    location_to_idx = {loc: i for i, loc in enumerate(LOCATIONS)}

    for loc_a, loc_b in connections:
        idx_a = location_to_idx[loc_a]
        idx_b = location_to_idx[loc_b]
        r[idx_a, idx_b] = 1
        r[idx_b, idx_a] = 1

    return r


# Matriz base que será utilizada pelo motor de Q-Learning
BASE_REWARDS_MATRIX = generate_base_rewards_matrix()
