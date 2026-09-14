import React from "react";
import {
  Bot,
  LayoutGrid,
  BarChart3,
  ExternalLink,
  Radio,
  AlertTriangle,
  Globe,
} from "lucide-react";
import { useSimulationStore } from "../store/useSimulationStore";
import { useTranslation } from "../i18n/useTranslation";

export const Navbar: React.FC = () => {
  const {
    viewMode,
    setViewMode,
    wsStatus,
    emergencyStop,
    sendWebSocketMessage,
  } = useSimulationStore();
  const { t, language, setLanguage } = useTranslation();

  const handleToggleEmergency = () => {
    sendWebSocketMessage({
      action: "EMERGENCY_STOP",
      activate: !emergencyStop,
    });
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-6 flex items-center justify-between z-30 sticky top-0">
      {/* Brand & Subtitle */}
      <div className="flex items-center gap-4">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20">
          <Bot className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight text-white">
              {t("app_title")}
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              v2.0 MAPF
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            {t("app_subtitle")}
          </p>
        </div>
      </div>

      {/* Navigation Modes */}
      <nav className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
        <button
          onClick={() => setViewMode("simulator")}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            viewMode === "simulator"
              ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Bot className="w-4 h-4" />
          {t("nav_simulator")}
        </button>

        <button
          onClick={() => setViewMode("studio")}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            viewMode === "studio"
              ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <LayoutGrid className="w-4 h-4" />
          {t("nav_studio")}
        </button>

        <button
          onClick={() => setViewMode("analytics")}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            viewMode === "analytics"
              ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          {t("nav_analytics")}
        </button>
      </nav>

      {/* Right Actions: Emergency Stop, Scalar Docs & Language Toggle */}
      <div className="flex items-center gap-3">
        {/* Emergency Stop Button (ISO 3691-4) */}
        <button
          onClick={handleToggleEmergency}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
            emergencyStop
              ? "bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/40"
              : "bg-red-950/40 text-red-400 border border-red-800/60 hover:bg-red-900/60"
          }`}
          title="Parada de emergência imediata da frota de robôs"
        >
          <AlertTriangle className="w-4 h-4" />
          {emergencyStop ? t("sim_emergency_active") : t("sim_emergency_stop")}
        </button>

        {/* Scalar Docs Link */}
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-all border border-slate-700"
          title="Acessar documentação interativa da API via Scalar"
        >
          <span>{t("nav_api_docs")}</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>

        {/* Bilingual Language Selector [PT | EN] */}
        <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
          <Globe className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-1" />
          <button
            onClick={() => setLanguage("pt")}
            className={`px-2 py-0.5 rounded font-bold transition-all ${
              language === "pt"
                ? "bg-slate-800 text-cyan-400"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            PT
          </button>
          <button
            onClick={() => setLanguage("en")}
            className={`px-2 py-0.5 rounded font-bold transition-all ${
              language === "en"
                ? "bg-slate-800 text-cyan-400"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            EN
          </button>
        </div>

        {/* Connection Status Badge */}
        <div
          className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${
            wsStatus === "connected"
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
              : wsStatus === "connecting"
              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
              : "bg-red-500/10 text-red-400 border-red-500/30"
          }`}
        >
          <Radio
            className={`w-3 h-3 ${
              wsStatus === "connected" ? "animate-pulse text-emerald-400" : ""
            }`}
          />
          <span className="capitalize">{t(`nav_${wsStatus}` as any)}</span>
        </div>
      </div>
    </header>
  );
};
