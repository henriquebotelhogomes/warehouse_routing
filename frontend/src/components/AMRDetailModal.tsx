import React from "react";
import { Bot, X, Battery, Package, Navigation, Target, Activity, Trash2 } from "lucide-react";
import { useSimulationStore } from "../store/useSimulationStore";
import { useTranslation } from "../i18n/useTranslation";
import { getAmrColor } from "../utils/robotColors";

export const AMRDetailModal: React.FC = () => {
  const { selectedAmrId, setSelectedAmrId, amrs, removeAmr } = useSimulationStore();
  const { t, language } = useTranslation();

  if (!selectedAmrId) return null;

  const amr = amrs.find((a) => a.id === selectedAmrId);
  if (!amr) return null;

  const amrColor = getAmrColor(amr.id);

  return (
    <div
      className="absolute top-20 right-6 z-30 w-80 bg-slate-900/95 backdrop-blur-xl border rounded-2xl shadow-2xl p-5 animate-in fade-in slide-in-from-right-4 duration-200"
      style={{ borderColor: amrColor }}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-950 font-bold shadow-md"
            style={{ backgroundColor: amrColor }}
          >
            <Bot className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <span>{amr.id}</span>
              <span
                className="w-2 h-2 rounded-full inline-block"
                style={{ backgroundColor: amrColor }}
              />
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              AMR Industrial Autônomo
            </span>
          </div>
        </div>
        <button
          onClick={() => setSelectedAmrId(null)}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Grid de Detalhes da Telemetria */}
      <div className="space-y-3.5 text-xs">
        {/* Nível de Bateria */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between text-[11px] mb-1.5">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Battery className="w-3.5 h-3.5 text-emerald-400" />
              {t("amr_battery")}
            </span>
            <span
              className={`font-mono font-bold ${
                amr.battery_level > 50
                  ? "text-emerald-400"
                  : amr.battery_level > 20
                  ? "text-amber-400"
                  : "text-red-400"
              }`}
            >
              {amr.battery_level}%
            </span>
          </div>
          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                amr.battery_level > 50
                  ? "bg-emerald-400"
                  : amr.battery_level > 20
                  ? "bg-amber-400"
                  : "bg-red-400"
              }`}
              style={{ width: `${Math.max(0, amr.battery_level)}%` }}
            />
          </div>
        </div>

        {/* Estado da FSM */}
        <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            {t("amr_state")}
          </span>
          <span className="font-mono text-cyan-400 font-bold px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-[10px]">
            {amr.state}
          </span>
        </div>

        {/* Carga Transportada (Pod) */}
        <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Package className="w-3.5 h-3.5 text-amber-400" />
            {t("amr_pod")}
          </span>
          <span className="font-mono text-white font-medium">
            {amr.carrying_pod_id || "— (Sem carga)"}
          </span>
        </div>

        {/* Missão Ativa */}
        <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Navigation className="w-3.5 h-3.5 text-blue-400" />
            {t("amr_mission")}
          </span>
          <span className="font-mono text-white font-medium">
            {amr.current_mission_id || "Aguardando despacho"}
          </span>
        </div>

        {/* Posição e Alvo */}
        <div className="flex items-center justify-between py-1">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-red-400" />
            {t("amr_target")}
          </span>
          <span className="font-mono text-white">
            {amr.target_x !== null ? `(${amr.target_x}, ${amr.target_y})` : "—"}
          </span>
        </div>

        {/* Botão de Descomissionar Robô */}
        <button
          onClick={() => {
            removeAmr(amr.id);
            setSelectedAmrId(null);
          }}
          className="w-full mt-2 py-2 px-3 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 flex items-center justify-center gap-2 text-xs font-semibold transition-all shadow-sm"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>{language === "pt" ? "Descomissionar Este Robô" : "Decommission This AMR"}</span>
        </button>
      </div>
    </div>
  );
};
