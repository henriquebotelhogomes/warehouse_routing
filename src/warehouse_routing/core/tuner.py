import numpy as np
import optuna
from loguru import logger

from warehouse_routing.core.config import BASE_REWARDS_MATRIX, LOCATIONS
from warehouse_routing.core.q_learning import WarehouseRouteOptimizer


class HyperparameterTuner:
    """Busca automática dos melhores parâmetros para convergência da IA."""

    def objective(self, trial: optuna.Trial) -> float:
        alpha = trial.suggest_float("alpha", 0.01, 0.5)
        gamma = trial.suggest_float("gamma", 0.5, 0.99)

        optimizer = WarehouseRouteOptimizer(
            locations=LOCATIONS,
            rewards_matrix=BASE_REWARDS_MATRIX,
            gamma=gamma,
            alpha=alpha,
        )

        # Treina para um ponto fixo e mede a força do aprendizado (Soma de Q)
        q_table = optimizer.train(ending_location="G", epochs=600)
        return float(np.sum(q_table))

    def run(self, n_trials: int = 20) -> dict:
        logger.info(f"Iniciando Optuna Study ({n_trials} trials)...")
        study = optuna.create_study(direction="maximize")
        study.optimize(self.objective, n_trials=n_trials)
        logger.success(f"Melhores Parâmetros: {study.best_params}")
        return study.best_params


if __name__ == "__main__":
    HyperparameterTuner().run()
