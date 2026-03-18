import numpy as np


def test_optimizer_initialization(optimizer):
    """Garante que o otimizador inicia com as dimensões corretas."""
    assert optimizer.num_states == len(optimizer.locations)
    assert len(optimizer._q_table_cache) == 0


def test_training_improves_q_values(optimizer):
    """Verifica se o treinamento preenche a Q-Table com valores positivos."""
    target = "G"
    # Antes do treino, cache vazio
    assert target not in optimizer._q_table_cache

    q_table = optimizer.train(target, epochs=100)

    assert target in optimizer._q_table_cache
    assert np.max(q_table) > 0  # A IA deve ter aprendido alguma recompensa


def test_route_is_physically_possible(optimizer):
    """
    CRITICAL: Valida se a rota sugerida respeita as conexões do armazém.
    Não permite que a IA 'atravesse paredes'.
    """
    start, end = "A", "I"
    route = optimizer.get_route(start, end)

    # Verifica cada salto da rota
    for i in range(len(route) - 1):
        loc_current = route[i]
        loc_next = route[i + 1]

        idx_current = optimizer.location_to_state[loc_current]
        idx_next = optimizer.location_to_state[loc_next]

        # Na matriz de recompensas, 1 significa conexão, 0 significa parede
        assert (
            optimizer.rewards_matrix[idx_current, idx_next] == 1
        ), f"IA sugeriu pulo ilegal de {loc_current} para {loc_next}!"


def test_dynamic_path_blocking(optimizer):
    """Testa se a IA recalcula a rota após um bloqueio de corredor."""
    start, end = "A", "G"

    # Rota original (geralmente passa por B e F)
    original_route = optimizer.get_route(start, end)

    # Bloqueia a conexão B-F
    optimizer.update_path("B", "F", is_open=False)

    # Nova rota após bloqueio
    new_route = optimizer.get_route(start, end)

    assert original_route != new_route
    assert "F" not in new_route or "B" not in new_route  # O par B-F não pode coexistir na rota
