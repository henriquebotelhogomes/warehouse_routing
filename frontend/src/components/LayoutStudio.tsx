import React, { useState, useEffect } from "react";
import {
  Square,
  Package,
  Target,
  Zap,
  ShieldAlert,
  Download,
  Upload,
  Play,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import { useSimulationStore, type WarehouseLayout } from "../store/useSimulationStore";
import { useTranslation } from "../i18n/useTranslation";

type ToolType = "empty" | "pod" | "picking_station" | "charging_dock" | "obstacle";

export const LayoutStudio: React.FC = () => {
  const { layout, setLayout, setViewMode } = useSimulationStore();
  const { t } = useTranslation();

  // Ferramenta selecionada
  const [activeTool, setActiveTool] = useState<ToolType>("pod");

  // Dimensões do grid de edição
  const [width, setWidth] = useState(layout?.width || 25);
  const [height, setHeight] = useState(layout?.height || 25);

  // Mapa de células em edição: chave "x,y" -> ToolType
  const [gridData, setGridData] = useState<Map<string, ToolType>>(new Map());
  const [isPainting, setIsPainting] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message: string;
    unreachable: { x: number; y: number }[];
  } | null>(null);

  // Inicializa o editor com o layout atual
  useEffect(() => {
    if (layout) {
      const map = new Map<string, ToolType>();
      layout.pods.forEach((p) => map.set(`${p.x},${p.y}`, "pod"));
      layout.picking_stations.forEach((s) => map.set(`${s.x},${s.y}`, "picking_station"));
      layout.charging_docks.forEach((d) => map.set(`${d.x},${d.y}`, "charging_dock"));
      layout.obstacles.forEach((o) => map.set(`${o.x},${o.y}`, "obstacle"));
      setGridData(map);
      setWidth(layout.width);
      setHeight(layout.height);
    }
  }, [layout]);

  const handleCellClick = (x: number, y: number) => {
    const key = `${x},${y}`;
    const newMap = new Map(gridData);
    if (activeTool === "empty") {
      newMap.delete(key);
    } else {
      newMap.set(key, activeTool);
    }
    setGridData(newMap);
    setValidationResult(null);
  };

  const handleMouseEnter = (x: number, y: number) => {
    if (isPainting) {
      handleCellClick(x, y);
    }
  };

  // Monta objeto WarehouseLayout a partir do grid desenhado
  const buildLayoutObject = (): WarehouseLayout => {
    const pods: any[] = [];
    const picking_stations: any[] = [];
    const charging_docks: any[] = [];
    const obstacles: any[] = [];

    let podCount = 1;
    gridData.forEach((type, key) => {
      const [x, y] = key.split(",").map(Number);
      if (type === "pod") {
        pods.push({
          id: `POD-${podCount++}`,
          x,
          y,
          sku_category: "Geral",
          item_count: 100,
        });
      } else if (type === "picking_station") {
        picking_stations.push({ x, y });
      } else if (type === "charging_dock") {
        charging_docks.push({ x, y });
      } else if (type === "obstacle") {
        obstacles.push({ x, y });
      }
    });

    return {
      name: "Galpão Customizado Studio",
      width,
      height,
      charging_docks,
      picking_stations,
      pods,
      obstacles,
    };
  };

  // Validação via API
  const handleValidate = async () => {
    const obj = buildLayoutObject();
    try {
      const res = await fetch("/api/v1/layouts/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(obj),
      });
      const data = await res.json();
      setValidationResult({
        valid: data.is_valid,
        message: data.message,
        unreachable: data.unreachable_cells || [],
      });
    } catch (e) {
      console.error("Erro na validação:", e);
    }
  };

  // Exportar JSON para download
  const handleExportJSON = () => {
    const obj = buildLayoutObject();
    const dataStr =
      "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(obj, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `nexusfleet_layout_${width}x${height}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  // Importar JSON de arquivo
  const handleImportJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileReader = new FileReader();
    if (e.target.files && e.target.files[0]) {
      fileReader.readAsText(e.target.files[0], "UTF-8");
      fileReader.onload = (event) => {
        try {
          const parsed: WarehouseLayout = JSON.parse(event.target?.result as string);
          setWidth(parsed.width);
          setHeight(parsed.height);
          const map = new Map<string, ToolType>();
          parsed.pods.forEach((p) => map.set(`${p.x},${p.y}`, "pod"));
          parsed.picking_stations.forEach((s) => map.set(`${s.x},${s.y}`, "picking_station"));
          parsed.charging_docks.forEach((d) => map.set(`${d.x},${d.y}`, "charging_dock"));
          parsed.obstacles.forEach((o) => map.set(`${o.x},${o.y}`, "obstacle"));
          setGridData(map);
          setValidationResult(null);
        } catch (err) {
          alert("Arquivo JSON inválido.");
        }
      };
    }
  };

  // Carregar Layout no Simulador Ativo
  const handleLoadSimulation = async () => {
    const obj = buildLayoutObject();
    try {
      const res = await fetch("/api/v1/layouts/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(obj),
      });
      if (res.ok) {
        setLayout(obj);
        setViewMode("simulator");
      } else {
        const err = await res.json();
        alert(err.detail || "Falha ao carregar layout.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Carregar Preset
  const handleLoadPreset = async (presetName: string) => {
    try {
      const res = await fetch("/api/v1/layouts/presets");
      const presets: WarehouseLayout[] = await res.json();
      const match = presets.find((p) => p.name.includes(presetName));
      if (match) {
        setWidth(match.width);
        setHeight(match.height);
        const map = new Map<string, ToolType>();
        match.pods.forEach((p) => map.set(`${p.x},${p.y}`, "pod"));
        match.picking_stations.forEach((s) => map.set(`${s.x},${s.y}`, "picking_station"));
        match.charging_docks.forEach((d) => map.set(`${d.x},${d.y}`, "charging_dock"));
        match.obstacles.forEach((o) => map.set(`${o.x},${o.y}`, "obstacle"));
        setGridData(map);
        setValidationResult(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div
      className="p-8 max-w-7xl mx-auto min-h-[calc(100vh-4rem)] flex flex-col gap-6"
      onMouseUp={() => setIsPainting(false)}
    >
      {/* Header do Studio */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-cyan-400" />
            {t("studio_title")}
          </h2>
          <p className="text-sm text-slate-400 mt-1">{t("studio_subtitle")}</p>
        </div>

        {/* Presets Rápidos */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Presets:</span>
          <button
            onClick={() => handleLoadPreset("Amazon")}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-all"
          >
            🏭 Mega Hub (30x30)
          </button>
          <button
            onClick={() => handleLoadPreset("Dark Store")}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-all"
          >
            ⚡ Dark Store (18x18)
          </button>
          <button
            onClick={() => handleLoadPreset("Sandbox")}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-all"
          >
            🧪 Sandbox (12x12)
          </button>
        </div>
      </div>

      {/* Toolbar de Ferramentas e Ações */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/90 backdrop-blur p-4 rounded-xl border border-slate-800 shadow-xl">
        {/* Paleta de Pincéis */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTool("empty")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTool === "empty"
                ? "bg-slate-700 text-white shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <Square className="w-4 h-4 text-slate-400" />
            {t("tool_empty")}
          </button>

          <button
            onClick={() => setActiveTool("pod")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTool === "pod"
                ? "bg-sky-500/20 text-sky-400 border border-sky-500/40 shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <Package className="w-4 h-4 text-sky-400" />
            {t("tool_pod")}
          </button>

          <button
            onClick={() => setActiveTool("picking_station")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTool === "picking_station"
                ? "bg-amber-500/20 text-amber-400 border border-amber-500/40 shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <Target className="w-4 h-4 text-amber-400" />
            {t("tool_picking")}
          </button>

          <button
            onClick={() => setActiveTool("charging_dock")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTool === "charging_dock"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <Zap className="w-4 h-4 text-emerald-400" />
            {t("tool_charging")}
          </button>

          <button
            onClick={() => setActiveTool("obstacle")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTool === "obstacle"
                ? "bg-red-500/20 text-red-400 border border-red-500/40 shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <ShieldAlert className="w-4 h-4 text-red-400" />
            {t("tool_obstacle")}
          </button>
        </div>

        {/* Dimensões e Ações de Arquivo */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs font-mono">
            <span className="text-slate-400">Dim:</span>
            <input
              type="number"
              min={10}
              max={40}
              value={width}
              onChange={(e) => setWidth(Math.max(10, Math.min(40, parseInt(e.target.value) || 20)))}
              className="w-12 bg-slate-900 px-1 py-0.5 rounded text-white text-center"
            />
            <span className="text-slate-500">x</span>
            <input
              type="number"
              min={10}
              max={40}
              value={height}
              onChange={(e) => setHeight(Math.max(10, Math.min(40, parseInt(e.target.value) || 20)))}
              className="w-12 bg-slate-900 px-1 py-0.5 rounded text-white text-center"
            />
          </div>

          <button
            onClick={handleValidate}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all"
          >
            <CheckCircle2 className="w-4 h-4 text-cyan-400" />
            {t("studio_validate")}
          </button>

          <button
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all"
          >
            <Download className="w-4 h-4 text-emerald-400" />
            {t("studio_export")}
          </button>

          <label className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 cursor-pointer transition-all">
            <Upload className="w-4 h-4 text-amber-400" />
            {t("studio_import")}
            <input type="file" accept=".json" onChange={handleImportJSON} className="hidden" />
          </label>

          <button
            onClick={handleLoadSimulation}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/20 transition-all"
          >
            <Play className="w-4 h-4 fill-current" />
            {t("studio_load_simulation")}
          </button>
        </div>
      </div>

      {/* Banner de Feedback da Validação */}
      {validationResult && (
        <div
          className={`p-4 rounded-xl border flex items-center gap-3 text-xs ${
            validationResult.valid
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
              : "bg-red-500/10 text-red-400 border-red-500/30"
          }`}
        >
          {validationResult.valid ? (
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
          )}
          <span className="font-semibold">{validationResult.message}</span>
        </div>
      )}

      {/* Grid Interativo de Pintura */}
      <div className="flex-1 bg-slate-950 p-6 rounded-2xl border border-slate-800 shadow-2xl overflow-auto flex items-center justify-center">
        <div
          className="grid gap-[2px] bg-slate-900 p-3 rounded-xl border border-slate-800 shadow-inner select-none"
          style={{
            gridTemplateColumns: `repeat(${width}, minmax(18px, 24px))`,
          }}
          onMouseDown={() => setIsPainting(true)}
        >
          {Array.from({ length: height }).map((_, y) =>
            Array.from({ length: width }).map((_, x) => {
              const key = `${x},${y}`;
              const cellType = gridData.get(key) || "empty";

              let bg = "bg-slate-950 hover:bg-slate-800/80";
              let icon = null;

              if (cellType === "pod") {
                bg = "bg-sky-950/80 border border-sky-500/40 text-sky-400";
                icon = "📦";
              } else if (cellType === "picking_station") {
                bg = "bg-amber-950/80 border border-amber-500/40 text-amber-400";
                icon = "🎯";
              } else if (cellType === "charging_dock") {
                bg = "bg-emerald-950/80 border border-emerald-500/40 text-emerald-400";
                icon = "⚡";
              } else if (cellType === "obstacle") {
                bg = "bg-slate-800 border border-slate-700 text-slate-400";
                icon = "■";
              }

              return (
                <div
                  key={key}
                  onMouseDown={() => handleCellClick(x, y)}
                  onMouseEnter={() => handleMouseEnter(x, y)}
                  className={`w-full aspect-square rounded-sm flex items-center justify-center text-[10px] cursor-pointer transition-all ${bg}`}
                  title={`(${x}, ${y}) - ${cellType}`}
                >
                  {icon}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
