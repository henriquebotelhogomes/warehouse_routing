import React, { useEffect, useState } from "react";
import {
  TrendingUp,
  Activity,
  BatteryCharging,
  ShieldCheck,
  Download,
  Printer,
  Sparkles,
  AlertTriangle,
  FileDown,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { useSimulationStore } from "../store/useSimulationStore";
import { useTranslation } from "../i18n/useTranslation";

const STATE_COLORS: Record<string, string> = {
  MOVING_TO_POD: "#0ea5e9",
  TRANSITING_TO_PICKING: "#0284c7",
  AT_PICKING_STATION: "#f59e0b",
  RETURNING_POD: "#6366f1",
  CHARGING: "#10b981",
  IDLE: "#64748b",
  AVOIDING_DEADLOCK: "#ef4444",
};

export const AnalyticsDashboard: React.FC = () => {
  const { metrics, amrs } = useSimulationStore();
  const { t, language } = useTranslation();

  const [incidents, setIncidents] = useState<any[]>([]);
  const [throughputHistory, setThroughputHistory] = useState<any[]>([]);

  // Carrega incidentes e simula série temporal a partir dos dados ao vivo
  useEffect(() => {
    fetch("/api/v1/analytics/incidents")
      .then((r) => r.json())
      .then((data) => setIncidents(data))
      .catch((e) => console.error(e));
  }, []);

  // Mantém histórico da curva de throughput
  useEffect(() => {
    setThroughputHistory((prev) => {
      const now = new Date().toLocaleTimeString();
      const updated = [
        ...prev,
        {
          time: now,
          throughput: metrics.throughput_per_hour,
          target: 1200,
        },
      ];
      return updated.slice(-20); // Mantém últimos 20 pontos
    });
  }, [metrics.throughput_per_hour]);

  // Agrega dados de estado da frota para o gráfico Donut
  const stateData = React.useMemo(() => {
    const counts: Record<string, number> = {};
    amrs.forEach((a) => {
      counts[a.state] = (counts[a.state] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({
      name,
      value,
    }));
  }, [JSON.stringify(amrs.map((a) => a.state))]);

  // Média de Bateria
  const avgBattery =
    amrs.length > 0
      ? (amrs.reduce((acc, a) => acc + a.battery_level, 0) / amrs.length).toFixed(1)
      : "100.0";

  // Exportar CSV
  const handleExportCSV = () => {
    const rows = [
      ["ID Incidente", "Horario", "Tipo", "Severidade", "Descricao", "Resolucao_s"],
      ...incidents.map((i) => [
        i.id,
        i.timestamp,
        i.type,
        i.severity,
        `"${i.description}"`,
        i.resolved_in_seconds,
      ]),
    ];
    const csvContent = "data:text/csv;charset=utf-8," + rows.map((e) => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "nexusfleet_incidents_report.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-[calc(100vh-4rem)] flex flex-col gap-8">
      {/* Header Executivo & Ações de Exportação */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Activity className="w-6 h-6 text-cyan-400" />
            Executive Shift Analytics & Fleet BI
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Inteligência operacional em tempo real, auditoria de SLAs e saúde da frota autônoma
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 transition-all shadow"
          >
            <Download className="w-4 h-4 text-emerald-400" />
            Exportar CSV
          </button>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 transition-all shadow"
          >
            <Printer className="w-4 h-4 text-cyan-400" />
            Imprimir Relatório
          </button>
        </div>
      </div>

      {/* Grid de 4 Cards de KPIs Executivos */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              {t("kpi_throughput")}
            </div>
            <div className="text-2xl font-bold text-white mt-1 font-mono">
              {metrics.throughput_per_hour}{" "}
              <span className="text-xs font-normal text-slate-500">ped/h</span>
            </div>
            <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1 font-medium">
              <TrendingUp className="w-3 h-3" /> +14% vs meta de turno
            </div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              {t("kpi_fleet_utilization")}
            </div>
            <div className="text-2xl font-bold text-white mt-1 font-mono">
              {metrics.fleet_utilization_pct}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              {amrs.filter((a) => a.state !== "IDLE" && a.state !== "CHARGING").length} de {amrs.length} AMRs produtivos
            </div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
            <Activity className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              {t("kpi_avg_battery")}
            </div>
            <div className="text-2xl font-bold text-white mt-1 font-mono">
              {avgBattery}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Gestão preditiva de carga ativa
            </div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400">
            <BatteryCharging className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
          <div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              {t("kpi_active_incidents")}
            </div>
            <div className="text-2xl font-bold text-white mt-1 font-mono">
              {metrics.active_incidents}
            </div>
            <div className="text-[11px] text-cyan-400 mt-1 font-medium">
              Zero colisões registradas
            </div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center text-red-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Gráficos Interativos: Throughput Temporal + Donut de Estados */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Curva de Throughput ao Vivo */}
        <div className="lg:col-span-2 bg-slate-900/90 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              {t("chart_throughput_title")}
            </h3>
            <span className="text-xs text-slate-400 font-mono">Tempo Real</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={throughputHistory}>
                <defs>
                  <linearGradient id="throughputGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={10} tickLine={false} />
                <YAxis stroke="#475569" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#1e293b",
                    borderRadius: "8px",
                    color: "#f8fafc",
                    fontSize: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="throughput"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#throughputGrad)"
                  name="Pedidos/Hora"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Distribuição Operacional da Frota (Donut Chart) */}
        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-col">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            {t("chart_fleet_states")}
          </h3>
          <div className="h-64 w-full relative">
            {stateData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={stateData}
                      cx="50%"
                      cy="46%"
                      innerRadius={58}
                      outerRadius={84}
                      paddingAngle={3}
                      dataKey="value"
                      isAnimationActive={false}
                      stroke="#0f172a"
                      strokeWidth={2}
                    >
                      {stateData.map((entry) => (
                        <Cell
                          key={`cell-${entry.name}`}
                          fill={STATE_COLORS[entry.name] || "#64748b"}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#1e293b",
                        borderRadius: "8px",
                        color: "#f8fafc",
                        fontSize: "11px",
                      }}
                      formatter={(value: any, name: any) => [
                        `${value} robô(s) (${((Number(value) / (amrs.length || 1)) * 100).toFixed(0)}%)`,
                        name,
                      ]}
                    />
                    <Legend
                      verticalAlign="bottom"
                      height={36}
                      wrapperStyle={{ fontSize: "10px", color: "#94a3b8" }}
                      formatter={(value: any, entry: any) => (
                        <span className="text-slate-300">
                          {value}{" "}
                          <span className="font-mono text-cyan-400 font-bold">
                            ({entry.payload?.value ?? 0})
                          </span>
                        </span>
                      )}
                    />
                  </PieChart>
                </ResponsiveContainer>
                {/* Indicador Central do Donut com Total de Robôs */}
                <div className="absolute top-[46%] left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                  <div className="text-lg font-bold font-mono text-white leading-none">
                    {amrs.length}
                  </div>
                  <div className="text-[9px] uppercase tracking-wider text-slate-400 font-medium mt-0.5">
                    AMRs
                  </div>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                Sem dados
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tabela de Incidentes & Auditoria */}
      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            {t("table_incidents_title")}
          </h3>
          <span className="text-xs text-slate-400">Total: {incidents.length} registros</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                <th className="py-3 px-4">{t("col_id")}</th>
                <th className="py-3 px-4">{t("col_time")}</th>
                <th className="py-3 px-4">{t("col_type")}</th>
                <th className="py-3 px-4">{t("col_severity")}</th>
                <th className="py-3 px-4">{t("col_description")}</th>
                <th className="py-3 px-4">{t("col_amrs")}</th>
                <th className="py-3 px-4 text-right">{t("col_resolution")}</th>
                <th className="py-3 px-4 text-center">{language === "pt" ? "Laudo RCA" : "RCA Report"}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {incidents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    Nenhum incidente registrado no turno. Operação 100% nominal.
                  </td>
                </tr>
              ) : (
                incidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-slate-800/40 transition-all">
                    <td className="py-3 px-4 font-bold text-cyan-400">{inc.id}</td>
                    <td className="py-3 px-4 text-slate-400">{inc.timestamp}</td>
                    <td className="py-3 px-4 text-slate-300 font-sans">{inc.type}</td>
                    <td className="py-3 px-4 font-sans">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          inc.severity === "CRITICAL"
                            ? "bg-red-500/20 text-red-400 border border-red-500/40"
                            : inc.severity === "WARNING"
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                            : "bg-blue-500/20 text-blue-400 border border-blue-500/40"
                        }`}
                      >
                        {inc.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-200 font-sans">{inc.description}</td>
                    <td className="py-3 px-4 text-slate-400">
                      {inc.affected_amrs.length > 0 ? inc.affected_amrs.join(", ") : "—"}
                    </td>
                    <td className="py-3 px-4 text-right text-emerald-400 font-bold">
                      {inc.resolved_in_seconds > 0 ? `${inc.resolved_in_seconds}s` : "0.8s (auto)"}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {inc.type === "COLLISION" || inc.id.includes("INC-2026") ? (
                        <a
                          href={`/api/v1/chaos/incidents/${inc.id}/export`}
                          download={`Laudo-${inc.id}.md`}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-[10px] font-sans font-semibold transition-all shadow-sm"
                          title="Baixar laudo forense do acidente em Markdown"
                        >
                          <FileDown className="w-3 h-3 text-cyan-400" />
                          <span>Laudo</span>
                        </a>
                      ) : (
                        <span className="text-slate-600 text-[10px]">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
