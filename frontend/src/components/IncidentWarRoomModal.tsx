import React, { useState } from "react";
import {
  AlertTriangle,
  X,
  Rewind,
  Download,
  ShieldCheck,
  Gauge,
  ChevronDown,
  ChevronUp,
  FileText,
  Sparkles,
} from "lucide-react";
import { useSimulationStore, type IncidentReport } from "../store/useSimulationStore";
import { useTranslation } from "../i18n/useTranslation";

interface IncidentWarRoomModalProps {
  incident: IncidentReport;
  onClose: () => void;
}

export const IncidentWarRoomModal: React.FC<IncidentWarRoomModalProps> = ({
  incident,
  onClose,
}) => {
  const { language } = useTranslation();
  const {
    timelineBuffer,
    setReplayIndex,
    setIsReplayActive,
    resolveIncident,
  } = useSimulationStore();

  const [isFiveWhysExpanded, setIsFiveWhysExpanded] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [isHealing, setIsHealing] = useState(false);

  // Rebobina a simulação na Caixa Preta 5 segundos antes do acidente
  const handleRewindReplay = () => {
    if (timelineBuffer.length === 0) return;

    // Procura o snapshot que corresponde ao tick do acidente ou mais próximo
    const targetTick = Math.max(0, incident.tick - 10);
    let targetIndex = timelineBuffer.findIndex((s) => s.tick >= targetTick);
    if (targetIndex === -1) {
      targetIndex = Math.max(0, timelineBuffer.length - 15);
    }

    setReplayIndex(targetIndex);
    setIsReplayActive(true);
    onClose();
  };

  // Faz download direto do laudo pericial formal em Markdown
  const handleExportReport = async () => {
    setIsExporting(true);
    try {
      const response = await fetch(`/api/v1/chaos/incidents/${incident.incident_id}/export`);
      if (!response.ok) throw new Error("Erro ao baixar laudo");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Laudo-RCA-${incident.incident_id}.md`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error(err);
    } finally {
      setIsExporting(false);
    }
  };

  // Executa o protocolo de auto-cura (Self-Healing)
  const handleSelfHealing = () => {
    setIsHealing(true);
    resolveIncident(incident.incident_id, true);
    setTimeout(() => {
      setIsHealing(false);
      onClose();
    }, 400);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-red-500/40 rounded-2xl shadow-2xl shadow-red-950/40 p-6 text-slate-100 flex flex-col gap-5 border-t-red-500">
        {/* Cabeçalho do Incidente com Sinalizador de Emergência */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/50 flex items-center justify-center text-red-400 animate-pulse">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30">
                  {incident.impact_metrics.damage_severity} SEVERITY
                </span>
                <span className="text-xs font-mono text-slate-400">
                  ID: <strong className="text-white">{incident.incident_id}</strong>
                </span>
                {incident.is_resolved && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    {language === "pt" ? "RESOLVIDO" : "RESOLVED"}
                  </span>
                )}
              </div>
              <h2 className="text-lg font-bold text-white mt-1">
                {language === "pt"
                  ? "War Room: Investigação Forense de Colisão (RCA)"
                  : "War Room: Incident Root Cause Analysis (RCA)"}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Resumo Rápido da Causa e Localização */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-xl flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-500/10 text-red-400 font-mono text-xs">
              📍 (X, Y)
            </div>
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                {language === "pt" ? "Local do Impacto" : "Impact Location"}
              </div>
              <div className="text-sm font-mono font-bold text-cyan-300">
                X: {incident.location.x} | Y: {incident.location.y}
              </div>
            </div>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-xl flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 font-mono text-xs">
              🤖 AMRs
            </div>
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                {language === "pt" ? "Agentes Envolvidos" : "Involved AMRs"}
              </div>
              <div className="text-xs font-bold text-slate-200">
                <span className="text-red-400 font-bold">{incident.primary_fault_amr}</span> (Infrator) vs{" "}
                {incident.involved_amrs.find((a) => a !== incident.primary_fault_amr) || "Obstáculo"}
              </div>
            </div>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-xl flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 font-mono text-xs">
              💥 MODO
            </div>
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                {language === "pt" ? "Modo de Falha" : "Failure Mode"}
              </div>
              <div className="text-xs font-bold text-amber-300 truncate max-w-[150px]" title={incident.failure_type_label}>
                {incident.failure_type_label}
              </div>
            </div>
          </div>
        </div>

        {/* Métricas Operacionais de Impacto */}
        <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-3.5">
          <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Gauge className="w-3.5 h-3.5 text-cyan-400" />
            <span>{language === "pt" ? "Impacto na Linha de Produção" : "Operational Line Impact"}</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
              <span className="text-slate-400 block text-[10px]">{language === "pt" ? "Velocidade Impacto" : "Impact Speed"}</span>
              <span className="font-mono font-bold text-white text-sm">
                {incident.impact_metrics.speed_at_impact_ms} m/s
              </span>
            </div>
            <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
              <span className="text-slate-400 block text-[10px]">{language === "pt" ? "Ordens Afetadas" : "Orders Dropped"}</span>
              <span className="font-mono font-bold text-amber-300 text-sm">
                {incident.impact_metrics.interrupted_orders.length}
              </span>
            </div>
            <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
              <span className="text-slate-400 block text-[10px]">{language === "pt" ? "Atraso no SLA" : "Estimated SLA Delay"}</span>
              <span className="font-mono font-bold text-red-400 text-sm">
                +{incident.impact_metrics.estimated_sla_delay_seconds}s
              </span>
            </div>
            <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
              <span className="text-slate-400 block text-[10px]">{language === "pt" ? "Pods Danificados" : "Damaged Pods"}</span>
              <span className="font-mono font-bold text-slate-200 text-sm">
                {incident.impact_metrics.affected_pods.length > 0
                  ? incident.impact_metrics.affected_pods.join(", ")
                  : "0"}
              </span>
            </div>
          </div>
        </div>

        {/* Parecer Técnico da Causa Raiz */}
        <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-3.5 text-xs">
          <div className="font-bold text-slate-200 mb-1 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-cyan-400" />
            <span>{language === "pt" ? "Diagnóstico Técnico Forense" : "Technical Forensic Diagnostic"}</span>
          </div>
          <p className="text-slate-300 leading-relaxed font-sans">
            {incident.root_cause_analysis}
          </p>
        </div>

        {/* Metodologia dos 5 Porquês (5-Whys Industrial) */}
        <div className="bg-slate-950/50 border border-slate-800 rounded-xl overflow-hidden text-xs">
          <button
            onClick={() => setIsFiveWhysExpanded(!isFiveWhysExpanded)}
            className="w-full flex items-center justify-between p-3.5 text-left font-bold text-slate-200 hover:bg-slate-900/50 transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <span>🔍</span>
              <span>
                {language === "pt"
                  ? "Análise de Causa Raiz (Metodologia 5-Whys)"
                  : "Root Cause Analysis (5-Whys Methodology)"}
              </span>
            </span>
            {isFiveWhysExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {isFiveWhysExpanded && (
            <div className="px-3.5 pb-3.5 space-y-2 border-t border-slate-800/80 pt-2.5">
              {incident.five_whys.map((why, idx) => (
                <div key={idx} className="flex items-start gap-2 text-slate-300 text-[11px] leading-relaxed">
                  <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-300 font-mono text-[9px] flex items-center justify-center shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span>{why}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Ações Corretivas e Preventivas Recomendadas (CAPA) */}
        <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-3.5 text-xs">
          <div className="font-bold text-slate-200 mb-2 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>{language === "pt" ? "Plano de Ação Corretivo (CAPA)" : "Corrective Action Plan (CAPA)"}</span>
          </div>
          <div className="space-y-1.5">
            {incident.corrective_actions.map((act, idx) => (
              <div key={idx} className="flex items-start gap-2 text-[11px] text-slate-300">
                <span className="text-emerald-400 mt-0.5">✓</span>
                <span>{act}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Barra de Ações Rápidas (Replay da Caixa Preta, Exportar e Auto-Cura) */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
          <div className="flex items-center gap-2">
            {/* Botão de Replay da Caixa Preta */}
            <button
              onClick={handleRewindReplay}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 transition-all shadow-sm"
              title="Rebobinar a gravação da caixa preta para 5 segundos antes do impacto"
            >
              <Rewind className="w-3.5 h-3.5" />
              <span>{language === "pt" ? "⏪ Ver Replay (-5s)" : "⏪ Watch Replay (-5s)"}</span>
            </button>

            {/* Botão de Exportar Laudo em Markdown */}
            <button
              onClick={handleExportReport}
              disabled={isExporting}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all shadow-sm"
              title="Baixar laudo pericial formal em formato Markdown"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isExporting ? "Baixando..." : language === "pt" ? "Exportar Laudo" : "Export Report"}</span>
            </button>
          </div>

          {/* Botão de Auto-Cura (Self-Healing) */}
          {!incident.is_resolved && (
            <button
              onClick={handleSelfHealing}
              disabled={isHealing}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 shadow-lg shadow-emerald-950/50 transition-all active:scale-95"
            >
              <Sparkles className="w-4 h-4 text-slate-950" />
              <span>
                {isHealing
                  ? "Aplicando..."
                  : language === "pt"
                  ? "Executar Auto-Cura (Self-Healing)"
                  : "Execute Self-Healing"}
              </span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
