import React, { useState, useMemo } from "react";
import {
  Terminal,
  X,
  Bot,
  Filter,
  Search,
  Copy,
  Check,
  Wrench,
} from "lucide-react";
import { useSimulationStore, type AMRLogEntry } from "../store/useSimulationStore";
import { getAmrColor } from "../utils/robotColors";

export const FleetLogsModal: React.FC = () => {
  const {
    isLogsModalOpen,
    setIsLogsModalOpen,
    logsFilterAmrId,
    setLogsFilterAmrId,
    amrs,
    rescueAmr,
  } = useSimulationStore();

  const [levelFilter, setLevelFilter] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [rescuingId, setRescuingId] = useState<string | null>(null);

  // Consolidação de logs de todos os robôs
  const allLogs = useMemo(() => {
    const list: { amrId: string; log: AMRLogEntry }[] = [];
    amrs.forEach((amr) => {
      (amr.recent_logs || []).forEach((log) => {
        list.push({ amrId: amr.id, log });
      });
    });
    // Ordena decrescente por tick/timestamp
    return list.sort((a, b) => b.log.tick - a.log.tick);
  }, [amrs]);

  // Filtros aplicados
  const filteredLogs = useMemo(() => {
    return allLogs.filter(({ amrId, log }) => {
      if (logsFilterAmrId && amrId !== logsFilterAmrId) return false;
      if (levelFilter !== "ALL" && log.level !== levelFilter) return false;
      if (
        searchTerm &&
        !log.message.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !amrId.toLowerCase().includes(searchTerm.toLowerCase())
      ) {
        return false;
      }
      return true;
    });
  }, [allLogs, logsFilterAmrId, levelFilter, searchTerm]);

  if (!isLogsModalOpen) return null;

  const handleCopyLogs = () => {
    const text = filteredLogs
      .map(
        ({ amrId, log }) =>
          `[${log.timestamp}] [Tick ${log.tick}] [${amrId}] [${log.level}]: ${log.message}`
      )
      .join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRescue = async (amrId: string) => {
    setRescuingId(amrId);
    await rescueAmr(amrId);
    setTimeout(() => setRescuingId(null), 1000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-5xl h-[85vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header do Terminal */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
                Central de Logs & Telemetria da Frota
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono font-normal">
                  Live Stream
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Auditoria e monitoramento de eventos de transição, rotas e FSM de cada AMR
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyLogs}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all cursor-pointer"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Copiado!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copiar Logs</span>
                </>
              )}
            </button>

            <button
              onClick={() => setIsLogsModalOpen(false)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Barra de Filtros e Seleção de Robôs */}
        <div className="px-6 py-3 border-b border-slate-800 bg-slate-900/90 flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Tabs por Robô */}
          <div className="flex items-center gap-1.5 overflow-x-auto max-w-xl py-1">
            <button
              onClick={() => setLogsFilterAmrId(null)}
              className={`px-3 py-1 rounded-lg font-medium transition-all cursor-pointer whitespace-nowrap ${
                logsFilterAmrId === null
                  ? "bg-cyan-500 text-slate-950 font-bold shadow-sm"
                  : "bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700"
              }`}
            >
              Toda a Frota ({allLogs.length})
            </button>

            {amrs.map((a) => {
              const color = getAmrColor(a.id);
              const isSelected = logsFilterAmrId === a.id;
              const isStuck = a.state === "TRANSITING_TO_PICKING" && a.target_x === null;
              return (
                <button
                  key={a.id}
                  onClick={() => setLogsFilterAmrId(a.id)}
                  className={`px-2.5 py-1 rounded-lg font-mono flex items-center gap-1.5 transition-all cursor-pointer whitespace-nowrap ${
                    isSelected
                      ? "bg-slate-800 text-white border shadow-sm"
                      : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800/80"
                  }`}
                  style={{ borderColor: isSelected ? color : undefined }}
                >
                  <span
                    className="w-2 h-2 rounded-full inline-block"
                    style={{ backgroundColor: color }}
                  />
                  <span>{a.id}</span>
                  {isStuck && (
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Filtro por Nível e Busca */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="bg-transparent text-slate-300 focus:outline-none cursor-pointer"
              >
                <option value="ALL">Todos os Níveis</option>
                <option value="INFO">INFO</option>
                <option value="ACTION">ACTION</option>
                <option value="SUCCESS">SUCCESS</option>
                <option value="WARN">WARN</option>
                <option value="ERROR">ERROR</option>
              </select>
            </div>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Filtrar eventos..."
                className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 w-44"
              />
            </div>
          </div>
        </div>

        {/* Conteúdo: Lista de Logs do Terminal + Sidebar de Status */}
        <div className="flex-1 flex overflow-hidden">
          {/* Feed de Logs */}
          <div className="flex-1 bg-slate-950/70 p-4 overflow-y-auto font-mono text-xs space-y-1.5 selection:bg-cyan-500 selection:text-slate-950">
            {filteredLogs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-2">
                <Terminal className="w-8 h-8 opacity-40" />
                <p>Nenhum evento registrado com os filtros selecionados.</p>
              </div>
            ) : (
              filteredLogs.map(({ amrId, log }, idx) => {
                const color = getAmrColor(amrId);

                let badgeColor = "bg-slate-800 text-slate-400 border-slate-700";
                if (log.level === "ACTION") {
                  badgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/30";
                } else if (log.level === "SUCCESS") {
                  badgeColor = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
                } else if (log.level === "WARN") {
                  badgeColor = "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
                } else if (log.level === "ERROR") {
                  badgeColor = "bg-red-500/10 text-red-400 border-red-500/30";
                } else if (log.level === "INFO") {
                  badgeColor = "bg-sky-500/10 text-sky-400 border-sky-500/30";
                }

                return (
                  <div
                    key={`${amrId}-${log.tick}-${idx}`}
                    className="flex items-start gap-2.5 py-1 px-2 rounded hover:bg-slate-900/60 transition-colors border-l-2 border-transparent hover:border-cyan-500/50"
                  >
                    <span className="text-slate-500 text-[10px] select-none whitespace-nowrap pt-0.5">
                      {log.timestamp}
                    </span>

                    <span className="text-slate-600 text-[10px] select-none whitespace-nowrap pt-0.5">
                      T+{log.tick}
                    </span>

                    <span
                      className="px-1.5 py-0.2 rounded font-bold text-[10px] border whitespace-nowrap"
                      style={{
                        backgroundColor: `${color}15`,
                        borderColor: `${color}40`,
                        color: color,
                      }}
                    >
                      {amrId}
                    </span>

                    <span
                      className={`px-1.5 py-0.2 rounded text-[9px] font-bold border uppercase whitespace-nowrap ${badgeColor}`}
                    >
                      {log.level}
                    </span>

                    <span className="text-slate-200 flex-1 leading-relaxed">
                      {log.message}
                    </span>
                  </div>
                );
              })
            )}
          </div>

          {/* Painel Lateral com Status da Frota e Ações Rápidas */}
          <div className="w-72 border-l border-slate-800 bg-slate-900/60 p-4 overflow-y-auto space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5 text-cyan-400" />
              Robôs Monitorados ({amrs.length})
            </h4>

            <div className="space-y-2">
              {amrs.map((a) => {
                const color = getAmrColor(a.id);
                const isStuck =
                  a.state === "TRANSITING_TO_PICKING" && a.target_x === null;
                const isSelected = logsFilterAmrId === a.id;

                return (
                  <div
                    key={a.id}
                    className={`p-3 rounded-xl border transition-all ${
                      isSelected
                        ? "bg-slate-850 border-cyan-500/40 shadow-sm"
                        : "bg-slate-950/60 border-slate-800"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-1.5">
                        <span
                          className="w-2.5 h-2.5 rounded-full inline-block"
                          style={{ backgroundColor: color }}
                        />
                        <span className="font-bold text-white text-xs font-mono">
                          {a.id}
                        </span>
                      </div>

                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                          a.battery_level > 50
                            ? "bg-emerald-500/10 text-emerald-400"
                            : a.battery_level > 20
                            ? "bg-amber-500/10 text-amber-400"
                            : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {a.battery_level}%
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-400 space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span>FSM:</span>
                        <span className="font-mono text-cyan-400 font-medium">
                          {a.state}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Posição:</span>
                        <span className="font-mono text-slate-300">
                          ({a.grid_x}, {a.grid_y})
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Carga:</span>
                        <span className="font-mono text-amber-400">
                          {a.carrying_pod_id || "Livre"}
                        </span>
                      </div>
                    </div>

                    {/* Botão de Destravar (Self-Healing) */}
                    <button
                      onClick={() => handleRescue(a.id)}
                      disabled={rescuingId === a.id}
                      className={`w-full mt-2.5 py-1.5 px-2 rounded-lg text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                        isStuck
                          ? "bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-md animate-pulse"
                          : "bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700"
                      }`}
                    >
                      <Wrench className="w-3 h-3" />
                      {rescuingId === a.id
                        ? "Destravando..."
                        : isStuck
                        ? "Destravar Robô (Self-Healing)"
                        : "Forçar Self-Healing"}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
