import React, { useEffect, useRef } from "react";
import { Navbar } from "./components/Navbar";
import { DigitalTwinCanvas } from "./components/DigitalTwinCanvas";
import { TimelineReplayBar } from "./components/TimelineReplayBar";
import { LayoutStudio } from "./components/LayoutStudio";
import { AnalyticsDashboard } from "./components/AnalyticsDashboard";
import { CopilotDrawer } from "./components/CopilotDrawer";
import { AMRDetailModal } from "./components/AMRDetailModal";
import { useSimulationStore } from "./store/useSimulationStore";

export const App: React.FC = () => {
  const {
    viewMode,
    setLayout,
    setWsStatus,
    setWsSendRef,
    updateFromTelemetry,
  } = useSimulationStore();
  const wsRef = useRef<WebSocket | null>(null);

  // 1. Carrega o layout atual do backend ao montar
  useEffect(() => {
    fetch("/api/v1/layouts/current")
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error("Falha ao buscar layout");
      })
      .then((layout) => setLayout(layout))
      .catch((err) => console.warn("Usando fallback de layout:", err));
  }, [setLayout]);

  // 2. Conexão WebSocket de Alta Performance com Auto-Reconect
  useEffect(() => {
    let reconnectTimeout: ReturnType<typeof setTimeout>;

    const connectWebSocket = () => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.host;
      // Se estiver em dev no Vite porta 5173, usa localhost:8000
      const wsUrl =
        window.location.port === "5173"
          ? "ws://localhost:8080/ws/telemetry"
          : `${protocol}//${host}/ws/telemetry`;

      setWsStatus("connecting");
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setWsStatus("connected");
        setWsSendRef((msg: any) => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(msg));
          }
        });
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          updateFromTelemetry(payload);
        } catch (e) {
          console.error("Erro no parse do WebSocket:", e);
        }
      };

      socket.onclose = () => {
        setWsStatus("disconnected");
        reconnectTimeout = setTimeout(connectWebSocket, 2000);
      };

      socket.onerror = (error) => {
        console.warn("WebSocket error:", error);
        socket.close();
      };
    };

    connectWebSocket();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, [setWsStatus, setWsSendRef, updateFromTelemetry]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-slate-950">
      {/* Barra de Navegação Superior */}
      <Navbar />

      {/* Conteúdo Central Alternável */}
      <main className="flex-1 relative overflow-x-hidden">
        {viewMode === "simulator" && (
          <div className="flex flex-col h-[calc(100vh-4rem)]">
            <DigitalTwinCanvas />
            <TimelineReplayBar />
            <AMRDetailModal />
          </div>
        )}

        {viewMode === "studio" && <LayoutStudio />}

        {viewMode === "analytics" && <AnalyticsDashboard />}

        {/* Copiloto de IA Presente em Todas as Telas */}
        <CopilotDrawer />
      </main>
    </div>
  );
};

export default App;
