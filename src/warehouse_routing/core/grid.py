from enum import Enum
from typing import Dict, List, Set, Tuple

from pydantic import BaseModel, Field


class CellType(str, Enum):
    EMPTY = "empty"
    POD = "pod"
    PICKING_STATION = "picking_station"
    CHARGING_DOCK = "charging_dock"
    OBSTACLE = "obstacle"


class CellCoordinate(BaseModel):
    x: int = Field(ge=0, description="Coordenada X (coluna)")
    y: int = Field(ge=0, description="Coordenada Y (linha)")

    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def manhattan_distance(self, other: "CellCoordinate") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CellCoordinate):
            return self.x == other.x and self.y == other.y
        if isinstance(other, tuple) and len(other) == 2:
            return (self.x, self.y) == other
        return False


class StoragePod(BaseModel):
    id: str = Field(description="Identificador único da prateleira (ex: 'POD-01')")
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    sku_category: str = Field(default="Geral", description="Categoria de produtos estocados")
    item_count: int = Field(default=100, ge=0)


class WarehouseLayout(BaseModel):
    """
    Estrutura que representa a topologia completa de um galpão.
    Exportável e importável em formato JSON.
    """

    name: str = Field(default="Layout Customizado")
    width: int = Field(default=25, ge=10, le=50, description="Largura do grid")
    height: int = Field(default=25, ge=10, le=50, description="Altura do grid")
    charging_docks: List[CellCoordinate] = Field(default_factory=list)
    picking_stations: List[CellCoordinate] = Field(default_factory=list)
    pods: List[StoragePod] = Field(default_factory=list)
    obstacles: List[CellCoordinate] = Field(default_factory=list)


class WarehouseGrid:
    """
    Representação espacial 2D do armazém para roteamento e simulação física.
    """

    def __init__(self, layout: WarehouseLayout):
        self.layout = layout
        self.width = layout.width
        self.height = layout.height

        # Conjuntos de posições estáticas
        self.charging_docks: Set[Tuple[int, int]] = {(d.x, d.y) for d in layout.charging_docks}
        self.picking_stations: Set[Tuple[int, int]] = {(s.x, s.y) for s in layout.picking_stations}
        self.obstacles: Set[Tuple[int, int]] = {(o.x, o.y) for o in layout.obstacles}
        self.pods_by_id: Dict[str, StoragePod] = {p.id: p for p in layout.pods}
        self.pod_positions: Dict[Tuple[int, int], str] = {(p.x, p.y): p.id for p in layout.pods}

        # Conjunto de bloqueios dinâmicos temporários (incidentes, derramamentos)
        self.dynamic_blocks: Set[Tuple[int, int]] = set()

    def is_within_bounds(self, x: int, y: int) -> bool:
        """Verifica se as coordenadas estão dentro dos limites do grid."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_traversable(self, x: int, y: int, ignore_dynamic_blocks: bool = False) -> bool:
        """
        Verifica se uma célula pode ser percorrida por um robô AMR.
        Robôs podem navegar sobre corredores vazios, estações de carga e estações de picking.
        Paredes/obstáculos e bloqueios dinâmicos impedem o trânsito.
        """
        if not self.is_within_bounds(x, y):
            return False

        coord = (x, y)
        if coord in self.obstacles:
            return False

        if not ignore_dynamic_blocks and coord in self.dynamic_blocks:
            return False

        return True

    def get_neighbors(self, x: int, y: int, allow_wait: bool = True) -> List[Tuple[int, int]]:
        """
        Retorna as células adjacentes válidas (4 direções ortogonais + espera ativa opcional).
        """
        neighbors: List[Tuple[int, int]] = []
        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in moves:
            nx, ny = x + dx, y + dy
            if self.is_traversable(nx, ny):
                neighbors.append((nx, ny))

        if allow_wait and self.is_traversable(x, y):
            # Ação de aguardar na mesma célula
            neighbors.append((x, y))

        return neighbors

    def add_dynamic_block(self, x: int, y: int) -> bool:
        """Adiciona um bloqueio dinâmico (ex: derramamento ou manutenção)."""
        if self.is_within_bounds(x, y):
            self.dynamic_blocks.add((x, y))
            return True
        return False

    def remove_dynamic_block(self, x: int, y: int) -> bool:
        """Remove um bloqueio dinâmico previamente registrado."""
        coord = (x, y)
        if coord in self.dynamic_blocks:
            self.dynamic_blocks.remove(coord)
            return True
        return False

    def validate_connectivity(self) -> Tuple[bool, List[Tuple[int, int]]]:
        """
        Utiliza BFS / Flood Fill para garantir que todas as estações e prateleiras
        são alcançáveis a partir de pelo menos uma estação de recarga.
        Retorna (is_valid, lista_de_celulas_inacessiveis).
        """
        if not self.charging_docks:
            return False, []

        start_dock = next(iter(self.charging_docks))
        visited: Set[Tuple[int, int]] = set()
        queue = [start_dock]
        visited.add(start_dock)

        while queue:
            cx, cy = queue.pop(0)
            for nx, ny in self.get_neighbors(cx, cy, allow_wait=False):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        unreachable: List[Tuple[int, int]] = []

        for dock in self.charging_docks:
            if dock not in visited:
                unreachable.append(dock)

        for station in self.picking_stations:
            if station not in visited:
                unreachable.append(station)

        for pod_pos in self.pod_positions.keys():
            if pod_pos not in visited:
                unreachable.append(pod_pos)

        is_valid = len(unreachable) == 0
        return is_valid, unreachable

    @classmethod
    def create_preset_mega_hub(cls) -> "WarehouseGrid":
        """Preset 1: Amazon Mega Fulfillment Center (30x30)."""
        width, height = 30, 30
        charging_docks = [CellCoordinate(x=i, y=0) for i in range(1, 9)]
        picking_stations = [CellCoordinate(x=i, y=height - 1) for i in range(5, 25, 4)]
        pods: List[StoragePod] = []
        pod_id = 1
        categories = ["Eletrônicos", "Moda", "Alimentos", "Livros", "Brinquedos"]

        # Fileiras de pods organizadas em blocos com corredores duplos
        for y in range(4, 24, 4):
            for x in range(3, 27):
                if x % 6 != 0:  # Cria corredores verticais a cada 6 células
                    pods.append(
                        StoragePod(
                            id=f"POD-{pod_id:03d}",
                            x=x,
                            y=y,
                            sku_category=categories[pod_id % len(categories)],
                            item_count=50 + (pod_id * 7) % 150,
                        )
                    )
                    pods.append(
                        StoragePod(
                            id=f"POD-{pod_id + 1:03d}",
                            x=x,
                            y=y + 1,
                            sku_category=categories[(pod_id + 1) % len(categories)],
                            item_count=40 + (pod_id * 11) % 120,
                        )
                    )
                    pod_id += 2

        obstacles = [CellCoordinate(x=0, y=y) for y in range(height)] + [
            CellCoordinate(x=width - 1, y=y) for y in range(height)
        ]

        layout = WarehouseLayout(
            name="Amazon Mega Fulfillment Center (30x30)",
            width=width,
            height=height,
            charging_docks=charging_docks,
            picking_stations=picking_stations,
            pods=pods,
            obstacles=obstacles,
        )
        return cls(layout)

    @classmethod
    def create_preset_dark_store(cls) -> "WarehouseGrid":
        """Preset 2: Micro-Dark Store Ultra-Rápida (18x18)."""
        width, height = 18, 18
        charging_docks = [
            CellCoordinate(x=1, y=1),
            CellCoordinate(x=2, y=1),
            CellCoordinate(x=3, y=1),
        ]
        picking_stations = [
            CellCoordinate(x=8, y=16),
            CellCoordinate(x=9, y=16),
        ]
        pods: List[StoragePod] = []
        pod_id = 1
        for y in range(4, 14, 3):
            for x in range(2, 16, 2):
                pods.append(
                    StoragePod(
                        id=f"DS-POD-{pod_id:02d}",
                        x=x,
                        y=y,
                        sku_category="Bebidas & Snacks" if pod_id % 2 == 0 else "Higiene",
                        item_count=80,
                    )
                )
                pod_id += 1

        layout = WarehouseLayout(
            name="Micro-Fulfillment Dark Store (18x18)",
            width=width,
            height=height,
            charging_docks=charging_docks,
            picking_stations=picking_stations,
            pods=pods,
            obstacles=[],
        )
        return cls(layout)

    @classmethod
    def create_preset_sandbox(cls) -> "WarehouseGrid":
        """Preset 3: Sandbox Compacto de Testes (12x12)."""
        width, height = 12, 12
        charging_docks = [CellCoordinate(x=1, y=0), CellCoordinate(x=2, y=0)]
        picking_stations = [CellCoordinate(x=5, y=11), CellCoordinate(x=6, y=11)]
        pods = [
            StoragePod(id="SANDBOX-01", x=3, y=4, sku_category="Amostras", item_count=30),
            StoragePod(id="SANDBOX-02", x=4, y=4, sku_category="Amostras", item_count=30),
            StoragePod(id="SANDBOX-03", x=7, y=7, sku_category="Amostras", item_count=30),
            StoragePod(id="SANDBOX-04", x=8, y=7, sku_category="Amostras", item_count=30),
        ]
        obstacles = [
            CellCoordinate(x=5, y=5),
            CellCoordinate(x=6, y=5),
        ]
        layout = WarehouseLayout(
            name="Testing & Conflict Sandbox (12x12)",
            width=width,
            height=height,
            charging_docks=charging_docks,
            picking_stations=picking_stations,
            pods=pods,
            obstacles=obstacles,
        )
        return cls(layout)
