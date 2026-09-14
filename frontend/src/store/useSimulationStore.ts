import { create } from "zustand";

export interface CellCoordinate {
  x: number;
  y: number;
}

export interface StoragePod {
  id: string;
  x: number;
  y: number;
  sku_category: string;
  item_count: number;
}

export interface WarehouseLayout {
  name: string;
  width: number;
  height: number;
  charging_docks: { x: number; y: number }[];
  picking_stations: { x: number; y: number }[];
  pods: StoragePod[];
  obstacles: { x: number; y: number }[];
}

export interface AMRLogEntry {
  timestamp: string;
  tick: number;
  level: "INFO" | "ACTION" | "WARN" | "ERROR" | "SUCCESS";
  message: string;
}

export interface AMRTelemetry {
  id: string;
  x: number;
  y: number;
  grid_x: number;
  grid_y: number;
  target_x: number | null;
  target_y: number | null;
  state: string;
  battery_level: number;
  carrying_pod_id: string | null;
  current_mission_id: string | null;
  planned_path: { x: number; y: number }[];
  is_crashed?: boolean;
  crash_reason?: string | null;
  recent_logs?: AMRLogEntry[];
}

export interface SimulationMetrics {
  throughput_per_hour: number;
  fleet_utilization_pct: number;
  completed_orders: number;
  pending_orders: number;
  active_incidents: number;
}

export interface SimulationSnapshot {
  tick: number;
  timestamp_ms: number;
  amrs: AMRTelemetry[];
  dynamic_blocks: { x: number; y: number }[];
  throughput_per_hour: number;
  fleet_utilization_pct: number;
  completed_orders_total: number;
}

export interface IncidentImpactMetrics {
  speed_at_impact_ms: number;
  interrupted_orders: string[];
  estimated_sla_delay_seconds: number;
  affected_pods: string[];
  damage_severity: string;
}

export interface IncidentReport {
  incident_id: string;
  timestamp: string;
  tick: number;
  location: { x: number; y: number };
  failure_type: string;
  failure_type_label: string;
  involved_amrs: string[];
  primary_fault_amr: string;
  summary: string;
  root_cause_analysis: string;
  five_whys: string[];
  corrective_actions: string[];
  impact_metrics: IncidentImpactMetrics;
  blackbox_snapshot?: any[];
  is_resolved: boolean;
  resolved_at?: string | null;
  isolation_block_cells?: { x: number; y: number }[];
}

export type ViewMode = "simulator" | "studio" | "analytics";

interface SimulationStore {
  // Conexão
  wsStatus: "connected" | "connecting" | "disconnected";
  setWsStatus: (status: "connected" | "connecting" | "disconnected") => void;

  // Layout
  layout: WarehouseLayout | null;
  setLayout: (layout: WarehouseLayout) => void;

  // Estado da Simulação ao vivo
  tick: number;
  isPaused: boolean;
  emergencyStop: boolean;
  speed: number;
  amrs: AMRTelemetry[];
  dynamicBlocks: { x: number; y: number }[];
  metrics: SimulationMetrics;

  // Visualização e Seleção
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;
  showPaths: boolean;
  setShowPaths: (show: boolean) => void;
  showHeatmap: boolean;
  setShowHeatmap: (show: boolean) => void;
  selectedAmrId: string | null;
  setSelectedAmrId: (id: string | null) => void;

  // Timeline Replay
  timelineBuffer: SimulationSnapshot[];
  isReplayActive: boolean;
  replayIndex: number;
  setIsReplayActive: (active: boolean) => void;
  setReplayIndex: (idx: number) => void;

  // Chaos Engineering & Gestão de Incidentes
  activeIncident: IncidentReport | null;
  setActiveIncident: (incident: IncidentReport | null) => void;
  isWarRoomOpen: boolean;
  setIsWarRoomOpen: (open: boolean) => void;
  incidentsHistory: IncidentReport[];
  setIncidentsHistory: (incidents: IncidentReport[]) => void;
  injectChaos: (failureType?: string, count?: number) => void;
  resolveIncident: (incidentId: string, selfHealing?: boolean) => void;

  // WebSocket actions
  sendWebSocketMessage: (msg: any) => void;
  wsSendRef: ((msg: any) => void) | null;
  setWsSendRef: (fn: (msg: any) => void) => void;

  // Ações de Gestão de Frota & Bloqueios
  addAmrs: (count?: number) => void;
  removeAmrs: (count?: number) => void;
  removeAmr: (amrId: string) => void;
  setFleetSize: (count: number) => void;
  clearAllBlocks: () => void;

  // Logs e Inspeção da Frota
  isLogsModalOpen: boolean;
  setIsLogsModalOpen: (open: boolean) => void;
  logsFilterAmrId: string | null;
  setLogsFilterAmrId: (id: string | null) => void;
  rescueAmr: (amrId: string) => Promise<void>;

  // Métodos de Controle
  updateFromTelemetry: (data: any) => void;
}

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  wsStatus: "connecting",
  setWsStatus: (status) => set({ wsStatus: status }),

  isLogsModalOpen: false,
  setIsLogsModalOpen: (isLogsModalOpen) => set({ isLogsModalOpen }),
  logsFilterAmrId: null,
  setLogsFilterAmrId: (logsFilterAmrId) => set({ logsFilterAmrId }),

  rescueAmr: async (amrId: string) => {
    try {
      await fetch(`/api/v1/fleet/rescue/${amrId}`, { method: "POST" });
    } catch (e) {
      console.error("Erro ao resgatar robô:", e);
    }
  },

  layout: null,
  setLayout: (layout) => set({ layout }),

  tick: 0,
  isPaused: false,
  emergencyStop: false,
  speed: 1.0,
  amrs: [],
  dynamicBlocks: [],
  metrics: {
    throughput_per_hour: 0,
    fleet_utilization_pct: 0,
    completed_orders: 0,
    pending_orders: 0,
    active_incidents: 0,
  },

  activeIncident: null,
  setActiveIncident: (activeIncident) => set({ activeIncident }),
  isWarRoomOpen: false,
  setIsWarRoomOpen: (isWarRoomOpen) => set({ isWarRoomOpen }),
  incidentsHistory: [],
  setIncidentsHistory: (incidentsHistory) => set({ incidentsHistory }),

  viewMode: "simulator",
  setViewMode: (viewMode) => set({ viewMode }),
  showPaths: true,
  setShowPaths: (showPaths) => set({ showPaths }),
  showHeatmap: false,
  setShowHeatmap: (showHeatmap) => set({ showHeatmap }),
  selectedAmrId: null,
  setSelectedAmrId: (selectedAmrId) => set({ selectedAmrId }),

  timelineBuffer: [],
  isReplayActive: false,
  replayIndex: 0,
  setIsReplayActive: (isReplayActive) => set({ isReplayActive }),
  setReplayIndex: (replayIndex) => set({ replayIndex }),

  wsSendRef: null,
  setWsSendRef: (fn) => set({ wsSendRef: fn }),
  sendWebSocketMessage: (msg) => {
    const fn = get().wsSendRef;
    if (fn) fn(msg);
  },

  addAmrs: (count = 1) => {
    get().sendWebSocketMessage({ action: "ADD_AMRS", count });
  },
  removeAmrs: (count = 1) => {
    get().sendWebSocketMessage({ action: "REMOVE_AMRS", count });
  },
  removeAmr: (amrId: string) => {
    get().sendWebSocketMessage({ action: "REMOVE_AMRS", amr_id: amrId });
  },
  setFleetSize: (count: number) => {
    get().sendWebSocketMessage({ action: "SET_FLEET_SIZE", count });
  },
  clearAllBlocks: () => {
    get().sendWebSocketMessage({ action: "CLEAR_ALL_BLOCKS" });
  },

  injectChaos: (failureType = "random", count = 1) => {
    get().sendWebSocketMessage({ action: "INJECT_CHAOS", failure_type: failureType, count });
  },

  resolveIncident: (incidentId: string, selfHealing = true) => {
    get().sendWebSocketMessage({
      action: "RESOLVE_INCIDENT",
      incident_id: incidentId,
      self_healing: selfHealing,
    });
  },

  updateFromTelemetry: (data: any) => {
    if (!data) return;

    set((state) => {
      // Se estiver em modo Replay, não sobrescreve os robôs visíveis com a telemetria ao vivo
      const currentTick = data.tick ?? state.tick;
      const amrs = data.amrs ?? state.amrs;
      const dynamicBlocks = data.dynamic_blocks ?? state.dynamicBlocks;
      const metrics = data.metrics ?? state.metrics;
      const isPaused = data.is_paused ?? state.isPaused;
      const emergencyStop = data.emergency_stop ?? state.emergencyStop;
      const speed = data.speed ?? state.speed;

      const activeIncident =
        data.active_incident !== undefined ? data.active_incident : state.activeIncident;
      const shouldOpenWarRoom =
        Boolean(activeIncident && (!state.activeIncident || state.activeIncident.incident_id !== activeIncident.incident_id));

      let updatedHistory = state.incidentsHistory;
      if (activeIncident && !updatedHistory.some((i) => i.incident_id === activeIncident.incident_id)) {
        updatedHistory = [activeIncident, ...updatedHistory];
      }

      // Adiciona ao buffer circular local para Timeline Replay (até 300 snapshots)
      const newSnapshot: SimulationSnapshot = {
        tick: currentTick,
        timestamp_ms: Date.now(),
        amrs,
        dynamic_blocks: dynamicBlocks,
        throughput_per_hour: metrics.throughput_per_hour,
        fleet_utilization_pct: metrics.fleet_utilization_pct,
        completed_orders_total: metrics.completed_orders,
      };

      const updatedBuffer = [...state.timelineBuffer, newSnapshot];
      if (updatedBuffer.length > 300) {
        updatedBuffer.shift();
      }

      return {
        tick: currentTick,
        isPaused,
        emergencyStop,
        speed,
        amrs: state.isReplayActive ? state.amrs : amrs,
        dynamicBlocks,
        metrics,
        activeIncident,
        isWarRoomOpen: shouldOpenWarRoom ? true : state.isWarRoomOpen,
        incidentsHistory: updatedHistory,
        timelineBuffer: updatedBuffer,
      };
    });
  },
}));
