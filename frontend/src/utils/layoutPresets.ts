import type { WarehouseLayout, StoragePod } from "../store/useSimulationStore";

export const PRESET_MEGA_HUB: WarehouseLayout = (() => {
  const width = 30;
  const height = 30;
  const charging_docks = Array.from({ length: 8 }, (_, i) => ({ x: i + 1, y: 0 }));
  const picking_stations = [5, 9, 13, 17, 21].map((x) => ({ x, y: height - 1 }));
  const pods: StoragePod[] = [];
  let podId = 1;
  const categories = ["Eletrônicos", "Moda", "Alimentos", "Livros", "Brinquedos"];

  for (let y = 4; y <= 20; y += 4) {
    for (let x = 3; x <= 26; x++) {
      if (x % 6 !== 0) {
        pods.push({
          id: `POD-${String(podId).padStart(3, "0")}`,
          x,
          y,
          sku_category: categories[podId % categories.length],
          item_count: 50 + ((podId * 7) % 150),
        });
        pods.push({
          id: `POD-${String(podId + 1).padStart(3, "0")}`,
          x,
          y: y + 1,
          sku_category: categories[(podId + 1) % categories.length],
          item_count: 40 + ((podId * 11) % 120),
        });
        podId += 2;
      }
    }
  }

  const obstacles = [
    ...Array.from({ length: height }, (_, y) => ({ x: 0, y })),
    ...Array.from({ length: height }, (_, y) => ({ x: width - 1, y })),
  ];

  return {
    name: "Amazon Mega Fulfillment Center (30x30)",
    width,
    height,
    charging_docks,
    picking_stations,
    pods,
    obstacles,
  };
})();

export const PRESET_DARK_STORE: WarehouseLayout = (() => {
  const width = 18;
  const height = 18;
  const charging_docks = [
    { x: 1, y: 1 },
    { x: 2, y: 1 },
    { x: 3, y: 1 },
  ];
  const picking_stations = [
    { x: 8, y: 16 },
    { x: 9, y: 16 },
  ];
  const pods: StoragePod[] = [];
  let podId = 1;

  for (let y = 4; y <= 13; y += 3) {
    for (let x = 2; x <= 14; x += 2) {
      pods.push({
        id: `DS-POD-${String(podId).padStart(2, "0")}`,
        x,
        y,
        sku_category: podId % 2 === 0 ? "Bebidas & Snacks" : "Higiene",
        item_count: 80,
      });
      podId++;
    }
  }

  return {
    name: "Micro-Fulfillment Dark Store (18x18)",
    width,
    height,
    charging_docks,
    picking_stations,
    pods,
    obstacles: [],
  };
})();

export const PRESET_SANDBOX: WarehouseLayout = {
  name: "Testing & Conflict Sandbox (12x12)",
  width: 12,
  height: 12,
  charging_docks: [
    { x: 1, y: 0 },
    { x: 2, y: 0 },
  ],
  picking_stations: [
    { x: 5, y: 11 },
    { x: 6, y: 11 },
  ],
  pods: [
    { id: "SANDBOX-01", x: 3, y: 4, sku_category: "Amostras", item_count: 30 },
    { id: "SANDBOX-02", x: 4, y: 4, sku_category: "Amostras", item_count: 30 },
    { id: "SANDBOX-03", x: 7, y: 7, sku_category: "Amostras", item_count: 30 },
    { id: "SANDBOX-04", x: 8, y: 7, sku_category: "Amostras", item_count: 30 },
  ],
  obstacles: [
    { x: 5, y: 5 },
    { x: 6, y: 5 },
  ],
};

export const BUILTIN_PRESETS = [PRESET_MEGA_HUB, PRESET_DARK_STORE, PRESET_SANDBOX];
