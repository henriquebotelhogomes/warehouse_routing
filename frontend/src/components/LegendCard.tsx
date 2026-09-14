import React, { useState } from "react";
import { HelpCircle, ChevronDown, ChevronUp } from "lucide-react";
import { useTranslation } from "../i18n/useTranslation";
import { useSimulationStore } from "../store/useSimulationStore";

export const LegendCard: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(true);
  const { language } = useTranslation();
  const { showHeatmap } = useSimulationStore();

  return (
    <div className="absolute bottom-20 left-6 z-20 bg-slate-900/95 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl p-3.5 max-w-xs transition-all">
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-2 text-xs font-bold text-white">
          <HelpCircle className="w-4 h-4 text-cyan-400" />
          <span>{language === "pt" ? "Legenda do Galpão" : "Warehouse Legend"}</span>
        </div>
        <button className="text-slate-400 hover:text-white">
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2.5 text-[11px]">
          <div className="flex items-center gap-2">
            <div className="flex -space-x-1">
              <span className="w-3 h-3 rounded-full bg-cyan-400 ring-1 ring-slate-900" />
              <span className="w-3 h-3 rounded-full bg-purple-400 ring-1 ring-slate-900" />
              <span className="w-3 h-3 rounded-full bg-amber-400 ring-1 ring-slate-900" />
            </div>
            <span className="text-slate-300">{language === "pt" ? "Cor por Robô & Rota" : "AMR & Path Colors"}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className="w-3.5 h-3.5 rounded-full bg-slate-700 border-2 border-amber-400 shadow-sm flex items-center justify-center text-[8px]">
              📦
            </div>
            <span className="text-slate-300">{language === "pt" ? "Com Prateleira" : "Carrying Pod"}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className="w-3.5 h-3.5 rounded-full bg-emerald-500 border border-white shadow-sm" />
            <span className="text-slate-300">{language === "pt" ? "Recarregando" : "Charging"}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className="w-3.5 h-3.5 rounded bg-slate-800 border border-sky-400 text-center leading-none text-[9px] flex items-center justify-center">
              📦
            </div>
            <span className="text-slate-300">{language === "pt" ? "Prateleira" : "Storage Pod"}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className="w-3.5 h-3.5 rounded bg-amber-500/20 border border-amber-400 text-center leading-none text-[8px] font-mono text-amber-400 flex items-center justify-center">
              🎯
            </div>
            <span className="text-slate-300">{language === "pt" ? "Bancada Coleta" : "Picking Bay"}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className="w-3.5 h-3.5 rounded bg-emerald-500/20 border border-emerald-400 text-center leading-none text-[8px] font-mono text-emerald-400 flex items-center justify-center">
              ⚡
            </div>
            <span className="text-slate-300">{language === "pt" ? "Doca Recarga" : "Charging Dock"}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className="w-3.5 h-3.5 rounded bg-red-500/40 border-2 border-red-500 text-center leading-none text-[8px] flex items-center justify-center shadow-sm">
              ⚠️
            </div>
            <span className="text-slate-300 font-medium text-red-300">
              {language === "pt" ? "Bloqueio / Incidente" : "Hazard Block"}
            </span>
          </div>

          {showHeatmap && (
            <div className="col-span-2 pt-2 border-t border-slate-800/80 animate-in fade-in">
              <div className="text-[10.5px] text-slate-300 font-semibold mb-1.5 flex items-center justify-between">
                <span className="flex items-center gap-1">
                  <span>🔥</span>
                  <span>{language === "pt" ? "Gradiente Térmico" : "Thermal Gradient"}</span>
                </span>
                <span className="text-[9px] text-slate-400 font-normal">
                  {language === "pt" ? "Dissipa em ~12s" : "Cools down in ~12s"}
                </span>
              </div>
              <div className="h-2.5 rounded-full w-full bg-gradient-to-r from-sky-400 via-emerald-400 via-amber-400 to-red-500 shadow-inner" />
              <div className="flex justify-between text-[9px] text-slate-400 mt-1 font-mono">
                <span className="text-sky-300">{language === "pt" ? "Leve" : "Light"}</span>
                <span className="text-emerald-300">{language === "pt" ? "Moderado" : "Moderate"}</span>
                <span className="text-amber-300">{language === "pt" ? "Denso" : "Dense"}</span>
                <span className="text-red-400 font-bold">{language === "pt" ? "Gargalo" : "Bottleneck"}</span>
              </div>
            </div>
          )}

          <div className="col-span-2 mt-1 pt-2 border-t border-slate-800/80 text-[10.5px] text-slate-400 leading-snug">
            💡 {language === "pt"
              ? "Clique em uma célula livre para interditar passagem ou clique sobre o ⚠️ vermelho para liberar."
              : "Click a free cell to block passage or click the red ⚠️ to remove the block."}
          </div>
        </div>
      )}
    </div>
  );
};
