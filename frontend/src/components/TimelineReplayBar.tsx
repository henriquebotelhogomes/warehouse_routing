import { History } from "lucide-react";
import { useSimulationStore } from "../store/useSimulationStore";
import { useTranslation } from "../i18n/useTranslation";

export const TimelineReplayBar: React.FC = () => {
  const {
    timelineBuffer,
    isReplayActive,
    setIsReplayActive,
    replayIndex,
    setReplayIndex,
    tick,
  } = useSimulationStore();
  const { t } = useTranslation();

  const bufferLength = timelineBuffer.length;
  if (bufferLength === 0) return null;

  const currentSnapshot = timelineBuffer[replayIndex] || timelineBuffer[bufferLength - 1];

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const idx = parseInt(e.target.value, 10);
    setReplayIndex(idx);
    setIsReplayActive(idx < bufferLength - 1);
  };

  const handleLiveClick = () => {
    setIsReplayActive(false);
    setReplayIndex(bufferLength - 1);
  };

  const handleRewind10s = () => {
    setIsReplayActive(true);
    // Supondo 2 ticks por segundo -> 20 ticks = 10s
    setReplayIndex(Math.max(0, replayIndex - 20));
  };

  return (
    <div className="h-16 border-t border-slate-800 bg-slate-900/95 backdrop-blur-md px-6 flex items-center justify-between z-20 sticky bottom-0">
      {/* Indicador de Modo Replay */}
      <div className="flex items-center gap-3 w-64">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-cyan-400">
          <History className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-white tracking-wide">
              {t("replay_title")}
            </span>
            {isReplayActive ? (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 font-bold animate-pulse">
                REPLAY (Tick {currentSnapshot?.tick})
              </span>
            ) : (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold">
                {t("replay_live")}
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 truncate">
            {t("replay_scrub_hint")}
          </p>
        </div>
      </div>

      {/* Scrubbing Slider Interativo */}
      <div className="flex-1 max-w-2xl mx-8 flex items-center gap-4">
        <button
          onClick={handleRewind10s}
          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700 transition-all whitespace-nowrap"
          title="Recuar 10 segundos no tempo"
        >
          {t("replay_rewind")}
        </button>

        <div className="flex-1 flex flex-col gap-1">
          <input
            type="range"
            min={0}
            max={bufferLength - 1}
            value={isReplayActive ? replayIndex : bufferLength - 1}
            onChange={handleSliderChange}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 hover:accent-cyan-300"
          />
          <div className="flex justify-between text-[10px] font-mono text-slate-500">
            <span>- {Math.round(bufferLength / 2)}s atrás</span>
            <span>Tick atual: {tick}</span>
            <span>Agora (0s)</span>
          </div>
        </div>

        {isReplayActive && (
          <button
            onClick={handleLiveClick}
            className="px-3 py-1 rounded bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold shadow-md shadow-cyan-500/20 transition-all whitespace-nowrap"
          >
            {t("replay_live")} ➔
          </button>
        )}
      </div>

      {/* Métricas Rápidas no Rodapé */}
      <div className="hidden lg:flex items-center gap-4 text-xs font-mono">
        <div className="text-right">
          <div className="text-slate-400 text-[10px]">Vazão no Snapshot</div>
          <div className="text-cyan-400 font-bold">
            {currentSnapshot?.throughput_per_hour || 0} ped/h
          </div>
        </div>
        <div className="h-6 w-px bg-slate-800" />
        <div className="text-right">
          <div className="text-slate-400 text-[10px]">Ocupação Frota</div>
          <div className="text-emerald-400 font-bold">
            {currentSnapshot?.fleet_utilization_pct || 0}%
          </div>
        </div>
      </div>
    </div>
  );
};
