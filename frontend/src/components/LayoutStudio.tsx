import React, { useState, useEffect, useCallback, useMemo } from "react";
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
  Trash2,
  Info,
} from "lucide-react";
import { useSimulationStore, type WarehouseLayout } from "../store/useSimulationStore";
import { useTranslation } from "../i18n/useTranslation";
import {
  PRESET_MEGA_HUB,
  PRESET_DARK_STORE,
  PRESET_SANDBOX,
} from "../utils/layoutPresets";

type ToolType = "empty" | "pod" | "picking_station" | "charging_dock" | "obstacle";
type PresetKey = "mega" | "dark" | "sandbox" | "custom";

export const LayoutStudio: React.FC = () => {
  const { layout, setLayout, setViewMode } = useSimulationStore();
  const { t } = useTranslation();

  // Ferramenta selecionada
  const [activeTool, setActiveTool] = useState<ToolType>("pod");

  // Dimensões do grid de edição
  const [width, setWidth] = useState<number>(layout?.width || 30);
  const [height, setHeight] = useState<number>(layout?.height || 30);

  // Mapa de células em edição: chave "x,y" -> ToolType
  const [gridData, setGridData] = useState<Map<string, ToolType>>(new Map());
  const [isPainting, setIsPainting] = useState(false);
  const [activePreset, setActivePreset] = useState<PresetKey>("mega");
  const [isLoadingSimulation, setIsLoadingSimulation] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message: string;
    unreachable: { x: number; y: number }[];
  } | null>(null);

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((current) => (current === msg ? null : current));
    }, 3500);
  }, []);

  // Inicializa o editor com o layout ativo ou preset Mega Hub
  useEffect(() => {
    const sourceLayout = layout || PRESET_MEGA_HUB;
    const map = new Map<string, ToolType>();
    sourceLayout.pods.forEach((p) => map.set(`${p.x},${p.y}`, "pod"));
    sourceLayout.picking_stations.forEach((s) => map.set(`${s.x},${s.y}`, "picking_station"));
    sourceLayout.charging_docks.forEach((d) => map.set(`${d.x},${d.y}`, "charging_dock"));
    sourceLayout.obstacles.forEach((o) => map.set(`${o.x},${o.y}`, "obstacle"));
    setGridData(map);
    setWidth(sourceLayout.width);
    setHeight(sourceLayout.height);

    if (sourceLayout.name.includes("Dark Store")) {
      setActivePreset("dark");
    } else if (sourceLayout.name.includes("Sandbox")) {
      setActivePreset("sandbox");
    } else if (sourceLayout.name.includes("Mega") || sourceLayout.name.includes("Amazon")) {
      setActivePreset("mega");
    } else {
      setActivePreset("custom");
    }
  }, [layout]);

  // Listener global de mouseup para evitar que o modo pintura fique preso se soltar fora
  useEffect(() => {
    const handleGlobalMouseUp = () => setIsPainting(false);
    window.addEventListener("mouseup", handleGlobalMouseUp);
    return () => window.removeEventListener("mouseup", handleGlobalMouseUp);
  }, []);

  // Aplicação da ferramenta na célula (sem closure stale)
  const applyToolToCell = useCallback(
    (x: number, y: number) => {
      if (x >= width || y >= height) return;
      const key = `${x},${y}`;
      setGridData((prev) => {
        const next = new Map(prev);
        if (activeTool === "empty") {
          next.delete(key);
        } else {
          next.set(key, activeTool);
        }
        return next;
      });
      setActivePreset("custom");
      setValidationResult(null);
    },
    [activeTool, width, height]
  );

  const handleCellMouseDown = (x: number, y: number) => {
    setIsPainting(true);
    applyToolToCell(x, y);
  };

  const handleCellMouseEnter = (x: number, y: number) => {
    if (isPainting) {
      applyToolToCell(x, y);
    }
  };

  // Carregar Preset de forma síncrona e instantânea (< 1ms)
  const handleLoadPreset = (key: PresetKey) => {
    let preset: WarehouseLayout;
    if (key === "mega") preset = PRESET_MEGA_HUB;
    else if (key === "dark") preset = PRESET_DARK_STORE;
    else if (key === "sandbox") preset = PRESET_SANDBOX;
    else return;

    setWidth(preset.width);
    setHeight(preset.height);
    const map = new Map<string, ToolType>();
    preset.pods.forEach((p) => map.set(`${p.x},${p.y}`, "pod"));
    preset.picking_stations.forEach((s) => map.set(`${s.x},${s.y}`, "picking_station"));
    preset.charging_docks.forEach((d) => map.set(`${d.x},${d.y}`, "charging_dock"));
    preset.obstacles.forEach((o) => map.set(`${o.x},${o.y}`, "obstacle"));
    setGridData(map);
    setActivePreset(key);
    setValidationResult(null);
    showToast(`Preset "${preset.name}" carregado no Studio!`);

    // Tenta sincronizar com o backend em segundo plano (se houver atualizações)
    fetch("/api/v1/layouts/presets")
      .then((r) => (r.ok ? r.json() : []))
      .then((backendPresets: WarehouseLayout[]) => {
        const match = backendPresets.find((p) => {
          if (key === "mega") return p.name.includes("Mega") || p.name.includes("Amazon");
          if (key === "dark") return p.name.includes("Dark Store");
          if (key === "sandbox") return p.name.includes("Sandbox");
          return false;
        });
        if (match && (match.width !== preset.width || match.height !== preset.height)) {
          setWidth(match.width);
          setHeight(match.height);
          const updatedMap = new Map<string, ToolType>();
          match.pods.forEach((p) => updatedMap.set(`${p.x},${p.y}`, "pod"));
          match.picking_stations.forEach((s) => updatedMap.set(`${s.x},${s.y}`, "picking_station"));
          match.charging_docks.forEach((d) => updatedMap.set(`${d.x},${d.y}`, "charging_dock"));
          match.obstacles.forEach((o) => updatedMap.set(`${o.x},${o.y}`, "obstacle"));
          setGridData(updatedMap);
        }
      })
      .catch(() => {
        // Ignora silenciosamente pois o preset embutido já foi aplicado
      });
  };

  // Limpar todo o grid
  const handleClearGrid = () => {
    if (gridData.size === 0) return;
    setGridData(new Map());
    setActivePreset("custom");
    setValidationResult(null);
    showToast("Grid limpo. Comece a desenhar seu novo armazém!");
  };

  // Estatísticas ao vivo dos itens posicionados
  const stats = useMemo(() => {
    let pods = 0;
    let picking = 0;
    let charging = 0;
    let obstacles = 0;

    gridData.forEach((type, key) => {
      const [x, y] = key.split(",").map(Number);
      if (x < width && y < height) {
        if (type === "pod") pods++;
        else if (type === "picking_station") picking++;
        else if (type === "charging_dock") charging++;
        else if (type === "obstacle") obstacles++;
      }
    });

    return { pods, picking, charging, obstacles, totalArea: width * height };
  }, [gridData, width, height]);

  // Set de células inacessíveis para highlight visual
  const unreachableSet = useMemo(() => {
    const s = new Set<string>();
    if (validationResult && !validationResult.valid) {
      validationResult.unreachable.forEach((u) => s.add(`${u.x},${u.y}`));
    }
    return s;
  }, [validationResult]);

  // Monta objeto WarehouseLayout a partir do grid desenhado (filtrando limites)
  const buildLayoutObject = useCallback((): WarehouseLayout => {
    const pods: any[] = [];
    const picking_stations: any[] = [];
    const charging_docks: any[] = [];
    const obstacles: any[] = [];

    let podCount = 1;
    gridData.forEach((type, key) => {
      const [x, y] = key.split(",").map(Number);
      // Ignora células fora das dimensões atuais
      if (x >= width || y >= height) return;

      if (type === "pod") {
        pods.push({
          id: `POD-${String(podCount++).padStart(3, "0")}`,
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

    let layoutName = "Galpão Customizado Studio";
    if (activePreset === "mega") layoutName = "Amazon Mega Fulfillment Center (30x30)";
    else if (activePreset === "dark") layoutName = "Micro-Fulfillment Dark Store (18x18)";
    else if (activePreset === "sandbox") layoutName = "Testing & Conflict Sandbox (12x12)";

    return {
      name: layoutName,
      width,
      height,
      charging_docks,
      picking_stations,
      pods,
      obstacles,
    };
  }, [gridData, width, height, activePreset]);

  // Validação via API
  const handleValidate = async () => {
    const obj = buildLayoutObject();
    if (obj.charging_docks.length === 0) {
      setValidationResult({
        valid: false,
        message: "O galpão precisa de pelo menos 1 Estação de Recarga ⚡.",
        unreachable: [],
      });
      return;
    }
    try {
      const res = await fetch("/api/v1/layouts/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(obj),
      });
      if (res.ok) {
        const data = await res.json();
        setValidationResult({
          valid: data.is_valid,
          message: data.message,
          unreachable: data.unreachable_cells || [],
        });
        showToast(
          data.is_valid
            ? "✅ Layout 100% navegável e pronto para simulação!"
            : `⚠️ Atenção: ${data.unreachable_cells?.length || 0} células isoladas.`
        );
      } else {
        setValidationResult({
          valid: false,
          message: "Erro na resposta da API de validação.",
          unreachable: [],
        });
      }
    } catch (e) {
      console.error("Erro na validação:", e);
      setValidationResult({
        valid: false,
        message: "Servidor offline ou inacessível para validação.",
        unreachable: [],
      });
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
    showToast("Layout exportado em JSON com sucesso!");
  };

  // Importar JSON de arquivo
  const handleImportJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileReader = new FileReader();
    if (e.target.files && e.target.files[0]) {
      fileReader.readAsText(e.target.files[0], "UTF-8");
      fileReader.onload = (event) => {
        try {
          const parsed: WarehouseLayout = JSON.parse(event.target?.result as string);
          if (!parsed.width || !parsed.height) {
            throw new Error("Arquivo não contém width ou height válidos.");
          }
          setWidth(parsed.width);
          setHeight(parsed.height);
          const map = new Map<string, ToolType>();
          parsed.pods.forEach((p) => map.set(`${p.x},${p.y}`, "pod"));
          parsed.picking_stations.forEach((s) => map.set(`${s.x},${s.y}`, "picking_station"));
          parsed.charging_docks.forEach((d) => map.set(`${d.x},${d.y}`, "charging_dock"));
          parsed.obstacles.forEach((o) => map.set(`${o.x},${o.y}`, "obstacle"));
          setGridData(map);
          setActivePreset("custom");
          setValidationResult(null);
          showToast(`Layout "${parsed.name || "Custom"}" importado com sucesso!`);
        } catch (err) {
          alert("Arquivo JSON inválido ou incompatível com o formato NexusFleet.");
        }
      };
    }
  };

  // Carregar Layout no Simulador Ativo
  const handleLoadSimulation = async () => {
    const obj = buildLayoutObject();
    if (obj.charging_docks.length === 0) {
      alert("Adicione ao menos 1 Estação de Recarga ⚡ antes de iniciar a simulação.");
      return;
    }

    setIsLoadingSimulation(true);
    try {
      const res = await fetch("/api/v1/layouts/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(obj),
      });
      if (res.ok) {
        setLayout(obj);
        showToast("Simulador reiniciado com o novo layout!");
        setTimeout(() => {
          setViewMode("simulator");
        }, 300);
      } else {
        const err = await res.json();
        alert(err.detail || "Falha ao carregar layout no simulador.");
      }
    } catch (e) {
      console.error(e);
      alert("Erro ao conectar com o backend para carregar simulação.");
    } finally {
      setIsLoadingSimulation(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto min-h-[calc(100vh-4rem)] flex flex-col gap-5">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 right-8 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-slate-900/95 border border-cyan-500/40 text-cyan-300 text-xs shadow-2xl backdrop-blur animate-in fade-in slide-in-from-top-4 duration-200">
          <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span className="font-semibold">{toastMessage}</span>
        </div>
      )}

      {/* Header do Studio */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Sparkles className="w-6 h-6 text-cyan-400" />
            {t("studio_title")}
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
              v2.0
            </span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">{t("studio_subtitle")}</p>
        </div>

        {/* Presets Rápidos com Destaque Ativo */}
        <div className="flex items-center gap-2 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 px-2 flex items-center gap-1">
            <Info className="w-3.5 h-3.5 text-slate-500" />
            Presets:
          </span>
          <button
            type="button"
            onClick={() => handleLoadPreset("mega")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              activePreset === "mega"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm shadow-cyan-500/20"
                : "bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 border border-transparent"
            }`}
          >
            🏭 Mega Hub (30x30)
          </button>
          <button
            type="button"
            onClick={() => handleLoadPreset("dark")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              activePreset === "dark"
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-sm shadow-amber-500/20"
                : "bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 border border-transparent"
            }`}
          >
            ⚡ Dark Store (18x18)
          </button>
          <button
            type="button"
            onClick={() => handleLoadPreset("sandbox")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              activePreset === "sandbox"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm shadow-emerald-500/20"
                : "bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 border border-transparent"
            }`}
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
            type="button"
            onClick={() => setActiveTool("empty")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTool === "empty"
                ? "bg-slate-700 text-white shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <Square className="w-4 h-4 text-slate-400" />
            {t("tool_empty")}
          </button>

          <button
            type="button"
            onClick={() => setActiveTool("pod")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTool === "pod"
                ? "bg-sky-500/20 text-sky-400 border border-sky-500/40 shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <Package className="w-4 h-4 text-sky-400" />
            {t("tool_pod")}
          </button>

          <button
            type="button"
            onClick={() => setActiveTool("picking_station")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTool === "picking_station"
                ? "bg-amber-500/20 text-amber-400 border border-amber-500/40 shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <Target className="w-4 h-4 text-amber-400" />
            {t("tool_picking")}
          </button>

          <button
            type="button"
            onClick={() => setActiveTool("charging_dock")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTool === "charging_dock"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <Zap className="w-4 h-4 text-emerald-400" />
            {t("tool_charging")}
          </button>

          <button
            type="button"
            onClick={() => setActiveTool("obstacle")}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTool === "obstacle"
                ? "bg-red-500/20 text-red-400 border border-red-500/40 shadow"
                : "bg-slate-800/60 text-slate-400 hover:text-white"
            }`}
          >
            <ShieldAlert className="w-4 h-4 text-red-400" />
            {t("tool_obstacle")}
          </button>

          <div className="h-6 w-px bg-slate-800 mx-1" />

          <button
            type="button"
            onClick={handleClearGrid}
            title="Limpar todos os elementos do grid"
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-slate-800/60 hover:bg-red-950/40 hover:text-red-400 text-slate-400 border border-transparent hover:border-red-500/30 transition-all cursor-pointer"
          >
            <Trash2 className="w-4 h-4" />
            Limpar
          </button>
        </div>

        {/* Dimensões e Ações de Arquivo */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs font-mono">
            <span className="text-slate-400">Dimensões:</span>
            <input
              type="number"
              min={8}
              max={40}
              value={width}
              onChange={(e) => {
                const val = Math.max(8, Math.min(40, parseInt(e.target.value) || 12));
                setWidth(val);
                setActivePreset("custom");
              }}
              className="w-12 bg-slate-900 px-1 py-0.5 rounded text-white text-center focus:outline-none focus:ring-1 focus:ring-cyan-500 border border-slate-800"
            />
            <span className="text-slate-500">x</span>
            <input
              type="number"
              min={8}
              max={40}
              value={height}
              onChange={(e) => {
                const val = Math.max(8, Math.min(40, parseInt(e.target.value) || 12));
                setHeight(val);
                setActivePreset("custom");
              }}
              className="w-12 bg-slate-900 px-1 py-0.5 rounded text-white text-center focus:outline-none focus:ring-1 focus:ring-cyan-500 border border-slate-800"
            />
          </div>

          <button
            type="button"
            onClick={handleValidate}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all cursor-pointer"
          >
            <CheckCircle2 className="w-4 h-4 text-cyan-400" />
            {t("studio_validate")}
          </button>

          <button
            type="button"
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all cursor-pointer"
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
            type="button"
            onClick={handleLoadSimulation}
            disabled={isLoadingSimulation}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/20 transition-all cursor-pointer disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-current" />
            {isLoadingSimulation ? "Carregando..." : t("studio_load_simulation")}
          </button>
        </div>
      </div>

      {/* Barra de Estatísticas do Galpão */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="bg-slate-900/60 border border-slate-800/80 px-3.5 py-2 rounded-xl flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sm">
            📦
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Prateleiras</div>
            <div className="text-sm font-bold text-sky-400 font-mono">{stats.pods}</div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 px-3.5 py-2 rounded-xl flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-sm">
            🎯
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Picking</div>
            <div className="text-sm font-bold text-amber-400 font-mono">{stats.picking}</div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 px-3.5 py-2 rounded-xl flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-sm">
            ⚡
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Doca Recarga</div>
            <div className="text-sm font-bold text-emerald-400 font-mono">{stats.charging}</div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 px-3.5 py-2 rounded-xl flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center text-sm">
            🧱
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Paredes</div>
            <div className="text-sm font-bold text-red-400 font-mono">{stats.obstacles}</div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 px-3.5 py-2 rounded-xl flex items-center gap-2.5 col-span-2 sm:col-span-1">
          <div className="w-7 h-7 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-sm">
            📐
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Área Total</div>
            <div className="text-sm font-bold text-purple-400 font-mono">
              {width}×{height} ({stats.totalArea} m²)
            </div>
          </div>
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
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400" />
          )}
          <span className="font-semibold">{validationResult.message}</span>
        </div>
      )}

      {/* Grid Interativo de Pintura com Régua Numérica dos Eixos X e Y */}
      <div className="flex-1 bg-slate-950 p-6 rounded-2xl border border-slate-800 shadow-2xl overflow-auto flex flex-col items-center justify-center min-h-[520px]">
        <div className="inline-block select-none">
          {/* Régua Superior (Eixo X) */}
          <div
            className="grid gap-[2px] mb-1 pl-7"
            style={{
              gridTemplateColumns: `repeat(${width}, minmax(18px, 24px))`,
            }}
          >
            {Array.from({ length: width }).map((_, x) => (
              <div
                key={`axis-x-${x}`}
                className="text-[9px] font-mono text-slate-500 text-center select-none"
              >
                {x % 5 === 0 || x === width - 1 ? x : "·"}
              </div>
            ))}
          </div>

          {/* Linhas do Grid com Régua Lateral (Eixo Y) */}
          <div className="flex items-start">
            {/* Régua Esquerda (Eixo Y) */}
            <div
              className="grid gap-[2px] pr-2 pt-3"
              style={{
                gridTemplateRows: `repeat(${height}, minmax(18px, 24px))`,
              }}
            >
              {Array.from({ length: height }).map((_, y) => (
                <div
                  key={`axis-y-${y}`}
                  className="w-5 text-[9px] font-mono text-slate-500 flex items-center justify-end select-none"
                >
                  {y % 5 === 0 || y === height - 1 ? y : "·"}
                </div>
              ))}
            </div>

            {/* Grid Principal de Células */}
            <div
              className="grid gap-[2px] bg-slate-900 p-3 rounded-xl border border-slate-800 shadow-inner"
              style={{
                gridTemplateColumns: `repeat(${width}, minmax(18px, 24px))`,
              }}
            >
              {Array.from({ length: height }).map((_, y) =>
                Array.from({ length: width }).map((_, x) => {
                  const key = `${x},${y}`;
                  const cellType = gridData.get(key) || "empty";
                  const isUnreachable = unreachableSet.has(key);

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
                    icon = "🧱";
                  }

                  // Destaque para células inacessíveis
                  if (isUnreachable) {
                    bg = "bg-red-950/90 border-2 border-red-500 text-red-300 animate-pulse";
                    icon = "⚠️";
                  }

                  return (
                    <div
                      key={key}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        handleCellMouseDown(x, y);
                      }}
                      onMouseEnter={() => handleCellMouseEnter(x, y)}
                      className={`w-full aspect-square rounded-sm flex items-center justify-center text-[10px] cursor-pointer transition-all ${bg}`}
                      title={`(${x}, ${y}) - ${cellType}${isUnreachable ? " (INACESSÍVEL / ISOLADO)" : ""}`}
                    >
                      {icon}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
