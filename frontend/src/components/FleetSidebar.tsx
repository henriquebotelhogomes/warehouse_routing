import React from "react";
import { Bot, Battery, Eye, Navigation, ChevronLeft, ChevronRight, Plus, Minus, Trash2 } from "lucide-react";
import { useSimulationStore, type AMRTelemetry } from "../store/useSimulationStore";
import { useTranslation } from "../i18n/useTranslation";
import { getAmrColor, hexToRgba } from "../utils/robotColors";

interface FleetSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onFocusAmr: (amr: AMRTelemetry) => void;
  followedAmrId?: string | null;
  onStopFollow?: () => void;
}

const STATE_TRANSLATIONS: Record<string, { label: string; color: string }> = {
  IDLE: { label: "Aguardando Missão", color: "text-slate-400 bg-slate-800" },
  MOVING_TO_POD: { label: "Buscando Prateleira", color: "text-cyan-400 bg-cyan-950 border border-cyan-800" },
  LIFTING_POD: { label: "Acoplando Prateleira", color: "text-amber-400 bg-amber-950 border border-amber-800" },
  TRANSITING_TO_PICKING: { label: "Levando para Bancada", color: "text-blue-400 bg-blue-950 border border-blue-800" },
  AT_PICKING_STATION: { label: "Em Separação", color: "text-emerald-400 bg-emerald-950 border border-emerald-800" },
  RETURNING_POD: { label: "Devolvendo ao Estoque", color: "text-purple-400 bg-purple-950 border border-purple-800" },
  LOWERING_POD: { label: "Desacoplando Pod", color: "text-indigo-400 bg-indigo-950 border border-indigo-800" },
  CHARGING: { label: "Recarregando Bateria", color: "text-green-400 bg-green-950 border border-green-800" },
  AVOIDING_DEADLOCK: { label: "Desviando de Bloqueio", color: "text-red-400 bg-red-950 border border-red-800" },
};

export const FleetSidebar: React.FC<FleetSidebarProps> = ({
  isOpen,
  onToggle,
  onFocusAmr,
  followedAmrId,
  onStopFollow,
}) => {
  const { amrs, selectedAmrId, setSelectedAmrId, addAmrs, removeAmrs, removeAmr } = useSimulationStore();
  const { language } = useTranslation();

  return (
    <>
      {/* Botão de Abrir / Recolher Barra Lateral */}
      <button
        onClick={onToggle}
        className={`absolute top-20 z-30 flex items-center justify-center w-8 h-12 bg-slate-900/95 border border-slate-700 text-cyan-400 rounded-r-xl shadow-xl hover:bg-slate-800 transition-all ${
          isOpen ? "left-80" : "left-0"
        }`}
        title={isOpen ? "Recolher Lista de Robôs" : "Expandir Lista de Robôs"}
      >
        {isOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
      </button>

      {/* Painel Lateral da Frota */}
      {isOpen && (
        <aside className="absolute top-16 left-0 bottom-16 w-80 bg-slate-900/95 backdrop-blur-xl border-r border-slate-800 shadow-2xl z-20 flex flex-col">
          {/* Header do Painel */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-cyan-400" />
              <h3 className="text-sm font-bold text-white tracking-wide">
                {language === "pt" ? "Frota de Robôs" : "Robot Fleet"} ({amrs.length})
              </h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Live FSM
            </span>
          </div>

          {/* Barra de Gestão e Escalonamento da Frota */}
          <div className="px-3.5 py-2.5 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-semibold text-slate-300">
                {language === "pt" ? "Frota:" : "Fleet:"}
              </span>
              <div className="flex items-center bg-slate-900 rounded-lg border border-slate-700/80 p-0.5">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeAmrs(1);
                  }}
                  disabled={amrs.length <= 1}
                  className="w-5 h-5 rounded flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  title={language === "pt" ? "Remover 1 robô" : "Remove 1 robot"}
                >
                  <Minus className="w-3 h-3" />
                </button>
                <span className="px-2 font-mono text-xs font-bold text-cyan-400">
                  {amrs.length}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    addAmrs(1);
                  }}
                  disabled={amrs.length >= 30}
                  className="w-5 h-5 rounded flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  title={language === "pt" ? "Adicionar 1 robô" : "Add 1 robot"}
                >
                  <Plus className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Ações Rápidas de Adição (+1, +3) */}
            <div className="flex items-center gap-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  addAmrs(1);
                }}
                className="px-2 py-0.5 rounded text-[10.5px] font-semibold bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 transition-all flex items-center gap-0.5"
                title={language === "pt" ? "Adicionar 1 robô" : "Add 1 robot"}
              >
                <Plus className="w-3 h-3" />
                <span>1</span>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  addAmrs(3);
                }}
                className="px-2 py-0.5 rounded text-[10.5px] font-semibold bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 transition-all flex items-center gap-0.5"
                title={language === "pt" ? "Adicionar 3 robôs" : "Add 3 robots"}
              >
                <Plus className="w-3 h-3" />
                <span>3</span>
              </button>
            </div>
          </div>

          {/* Dica rápida de uso */}
          <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800 text-[11px] text-slate-400 leading-snug">
            💡 {language === "pt"
              ? "Clique em 'Seguir' para a câmera focar e acompanhar o robô no mapa."
              : "Click 'Follow' to focus and follow the robot on the map."}
          </div>

          {/* Lista de Robôs */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
            {amrs.map((amr) => {
              const isSelected = selectedAmrId === amr.id;
              const stateInfo =
                STATE_TRANSLATIONS[amr.state] || {
                  label: amr.state,
                  color: "text-slate-400 bg-slate-800",
                };
              const amrColor = getAmrColor(amr.id);

              return (
                <div
                  key={amr.id}
                  onClick={() => setSelectedAmrId(amr.id)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer relative overflow-hidden ${
                    isSelected
                      ? "bg-slate-800/95 shadow-lg"
                      : "bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900"
                  }`}
                  style={{
                    borderColor: isSelected ? amrColor : undefined,
                    boxShadow: isSelected ? `0 8px 20px -4px ${hexToRgba(amrColor, 0.35)}` : undefined,
                  }}
                >
                  {/* Faixa lateral indicadora da cor do robô */}
                  <div
                    className="absolute left-0 top-0 bottom-0 w-1"
                    style={{ backgroundColor: amrColor }}
                  />

                  <div className="flex items-center justify-between mb-2 pl-1">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-6 h-6 rounded-lg font-bold font-mono text-xs flex items-center justify-center text-slate-950 shadow-sm"
                        style={{ backgroundColor: amrColor }}
                      >
                        {amr.id.replace("AMR-", "")}
                      </div>
                      <span className="text-xs font-bold text-white">{amr.id}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1 text-[11px] font-mono font-medium">
                        <Battery
                          className={`w-3.5 h-3.5 ${
                            amr.battery_level > 50
                              ? "text-emerald-400"
                              : amr.battery_level > 20
                              ? "text-amber-400"
                              : "text-red-400"
                          }`}
                        />
                        <span
                          className={
                            amr.battery_level > 50
                              ? "text-emerald-400"
                              : amr.battery_level > 20
                              ? "text-amber-400"
                              : "text-red-400"
                          }
                        >
                          {Math.round(amr.battery_level)}%
                        </span>
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (followedAmrId === amr.id) {
                            onStopFollow?.();
                          } else {
                            setSelectedAmrId(amr.id);
                            onFocusAmr(amr);
                          }
                        }}
                        className={`px-2 py-1 rounded text-[10px] font-semibold flex items-center gap-1 transition-all ${
                          followedAmrId === amr.id
                            ? "text-slate-950 font-bold shadow-md ring-2 ring-white/40"
                            : "bg-slate-800 hover:text-slate-950 text-slate-300"
                        }`}
                        style={{
                          backgroundColor: followedAmrId === amr.id ? amrColor : undefined,
                        }}
                        title={
                          followedAmrId === amr.id
                            ? "Câmera acompanhando este robô. Clique para soltar."
                            : "Acompanhar movimento deste robô com a câmera"
                        }
                      >
                        <Eye className="w-3 h-3" />
                        <span>
                          {followedAmrId === amr.id
                            ? language === "pt"
                              ? "Seguindo"
                              : "Following"
                            : language === "pt"
                            ? "Seguir"
                            : "Follow"}
                        </span>
                      </button>

                      {/* Botão de Descomissionar Robô Individual */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeAmr(amr.id);
                        }}
                        className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
                        title={
                          language === "pt"
                            ? `Descomissionar e remover ${amr.id}`
                            : `Decommission and remove ${amr.id}`
                        }
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Estado da FSM em Português */}
                  <div className="flex items-center justify-between">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${stateInfo.color}`}>
                      {stateInfo.label}
                    </span>

                    <span className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
                      <Navigation className="w-2.5 h-2.5" />
                      ({Math.round(amr.x)}, {Math.round(amr.y)})
                    </span>
                  </div>

                  {/* Carga se houver */}
                  {amr.carrying_pod_id && (
                    <div className="mt-2 text-[10px] font-mono text-amber-300/90 bg-amber-950/30 px-2 py-0.5 rounded border border-amber-800/40">
                      📦 Transportando: {amr.carrying_pod_id}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </aside>
      )}
    </>
  );
};
