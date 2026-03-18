import io
from typing import List

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import seaborn as sns


class WarehouseVisualizer:
    """
    Utilitário para visualização técnica.
    Suporta modo interativo (janelas) e modo buffer (API).
    """

    @staticmethod
    def _setup_graph(rewards_matrix: np.ndarray, locations: List[str]) -> nx.Graph:
        """Helper interno para construir o objeto do grafo."""
        G = nx.Graph()
        for loc in locations:
            G.add_node(loc)
        num_states = len(locations)
        for i in range(num_states):
            for j in range(num_states):
                if rewards_matrix[i, j] > 0:
                    G.add_edge(locations[i], locations[j])
        return G

    # --- MÉTODOS PARA O TERMINAL / PYCHARM (Abrem Janelas) ---

    @staticmethod
    def plot_warehouse_graph(rewards_matrix: np.ndarray, locations: List[str]) -> None:
        """Abre uma janela com o mapa do armazém."""
        G = WarehouseVisualizer._setup_graph(rewards_matrix, locations)
        plt.figure("Mapa do Armazém", figsize=(10, 7))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(
            G,
            pos,
            with_labels=True,
            node_color="#3498db",
            node_size=2000,
            edge_color="#bdc3c7",
            font_size=12,
            font_weight="bold",
            font_color="white",
        )
        plt.title("Topologia Física do Armazém")
        plt.show()  # Abre a janela no Windows

    @staticmethod
    def plot_q_table(q_table: np.ndarray, locations: List[str], title: str) -> None:
        """Abre uma janela com o Heatmap da Q-Table."""
        plt.figure("Inteligência da IA", figsize=(12, 8))
        sns.heatmap(
            q_table,
            annot=True,
            fmt=".1f",
            xticklabels=locations,
            yticklabels=locations,
            cmap="YlGnBu",
        )
        plt.title(title)
        plt.show()

    # --- MÉTODOS PARA A API (Retornam Buffer de Imagem) ---

    @staticmethod
    def get_graph_image(rewards_matrix: np.ndarray, locations: List[str]) -> io.BytesIO:
        """Retorna buffer PNG do grafo para a API."""
        # Força o backend não-interativo apenas para esta geração
        plt.switch_backend("Agg")
        WarehouseVisualizer.plot_warehouse_graph(rewards_matrix, locations)
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        return buf

    @staticmethod
    def get_q_table_image(q_table: np.ndarray, locations: List[str], title: str) -> io.BytesIO:
        """Retorna buffer PNG do heatmap para a API."""
        plt.switch_backend("Agg")
        WarehouseVisualizer.plot_q_table(q_table, locations, title)
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        return buf
