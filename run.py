import os
import sys

import uvicorn
from warehouse_routing.core.config import BASE_REWARDS_MATRIX, LOCATIONS, settings
from warehouse_routing.core.q_learning import WarehouseRouteOptimizer
from warehouse_routing.core.visualizer import WarehouseVisualizer


def main() -> None:
    # Garante que o diretório 'src' está no path
    sys.path.append(os.path.join(os.getcwd(), "src"))

    optimizer = WarehouseRouteOptimizer(
        locations=LOCATIONS,
        rewards_matrix=BASE_REWARDS_MATRIX,
        gamma=settings.gamma,
        alpha=settings.alpha,
    )

    optimizer.load_model(settings.model_save_path)

    print("\n" + "=" * 45)
    print("      WAREHOUSE ROUTING SYSTEM v1.0")
    print("=" * 45)
    print(" 1. [LOCAL] Visualizar Mapa (Janela)")
    print(" 2. [LOCAL] Visualizar Inteligência (Janela)")
    print(" 3. [SERVER] Iniciar API Production")
    print(" 4. [SAIR] Encerrar")
    print("=" * 45)

    choice = input("\nSelecione uma opção: ")

    if choice == "1":
        WarehouseVisualizer.plot_warehouse_graph(BASE_REWARDS_MATRIX, LOCATIONS)
        main()
    elif choice == "2":
        target = input("Destino (Padrão 'G'): ").upper() or "G"
        q_table = optimizer.train(target)
        WarehouseVisualizer.plot_q_table(q_table, LOCATIONS, f"Q-Table para {target}")
        main()
    elif choice == "3":
        uvicorn.run("warehouse_routing.api.main:app", host="127.0.0.1", port=8000, reload=True)
    elif choice == "4":
        sys.exit(0)


if __name__ == "__main__":
    main()
