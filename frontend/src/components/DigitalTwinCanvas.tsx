import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  Play,
  Pause,
  FastForward,
  Flame,
  Route,
  Maximize2,
  HelpCircle,
  RotateCcw,
  Zap,
} from "lucide-react";
import { useSimulationStore, type AMRTelemetry } from "../store/useSimulationStore";
import { useTranslation } from "../i18n/useTranslation";
import { FleetSidebar } from "./FleetSidebar";
import { LegendCard } from "./LegendCard";
import { IncidentWarRoomModal } from "./IncidentWarRoomModal";
import { getAmrColor, hexToRgba } from "../utils/robotColors";

export const DigitalTwinCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const {
    layout,
    amrs,
    dynamicBlocks,
    isPaused,
    speed,
    showPaths,
    setShowPaths,
    showHeatmap,
    setShowHeatmap,
    selectedAmrId,
    setSelectedAmrId,
    activeIncident,
    isWarRoomOpen,
    setIsWarRoomOpen,
    injectChaos,
    sendWebSocketMessage,
  } = useSimulationStore();
  const { language } = useTranslation();
  const [isChaosMenuOpen, setIsChaosMenuOpen] = useState(false);

  // Painel lateral de robôs (aberto por padrão para guiar o usuário)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [showTutorialBanner, setShowTutorialBanner] = useState(true);

  // Estado de Câmera (Pan & Zoom) e Robô Seguido
  const [zoom, setZoom] = useState(0.85);
  const [offset, setOffset] = useState({ x: 380, y: 50 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [followedAmrId, setFollowedAmrId] = useState<string | null>(null);
  const [hoveredCoord, setHoveredCoord] = useState<{ x: number; y: number } | null>(null);

  const cameraOffsetRef = useRef({ x: 380, y: 50 });
  const cameraZoomRef = useRef(0.85);
  const hoveredCoordRef = useRef<{ x: number; y: number } | null>(null);
  const dragStartClientRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const hasMovedSignificantlyRef = useRef<boolean>(false);

  useEffect(() => {
    cameraOffsetRef.current = offset;
  }, [offset]);

  useEffect(() => {
    cameraZoomRef.current = zoom;
  }, [zoom]);

  // Posições interpoladas para 60 FPS suave (LERP)
  const smoothAmrPositions = useRef<Map<string, { x: number; y: number }>>(
    new Map()
  );
  // Buffer de calor para o Heatmap
  const trafficHeatmap = useRef<Map<string, number>>(new Map());

  // Centraliza o galpão automaticamente na tela
  const handleAutoFit = useCallback(() => {
    if (!layout || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const cellSize = 32;
    const gridW = layout.width * cellSize;
    const gridH = layout.height * cellSize;

    // Se a sidebar estiver aberta, desconta a largura dela (340px)
    const availableW = isSidebarOpen ? canvas.width - 340 : canvas.width;
    const padding = 65;

    const scaleX = (availableW - padding * 2) / gridW;
    const scaleY = (canvas.height - padding * 2) / gridH;
    const fitZoom = Math.min(1.4, Math.max(0.35, Math.min(scaleX, scaleY)));

    const startX = isSidebarOpen ? 340 : 0;
    const centerX = startX + (availableW - gridW * fitZoom) / 2;
    const centerY = (canvas.height - gridH * fitZoom) / 2;

    const newOffset = { x: Math.max(45, centerX), y: Math.max(35, centerY) };
    setZoom(fitZoom);
    setOffset(newOffset);
    cameraZoomRef.current = fitZoom;
    cameraOffsetRef.current = newOffset;
    setFollowedAmrId(null);
  }, [layout, isSidebarOpen]);

  // Sincroniza o tamanho interno do canvas com as dimensões reais da tela
  useEffect(() => {
    const updateCanvasSize = () => {
      if (canvasRef.current && canvasRef.current.parentElement) {
        canvasRef.current.width = canvasRef.current.parentElement.clientWidth;
        canvasRef.current.height = canvasRef.current.parentElement.clientHeight;
        handleAutoFit();
      }
    };
    updateCanvasSize();
    window.addEventListener("resize", updateCanvasSize);
    return () => window.removeEventListener("resize", updateCanvasSize);
  }, [handleAutoFit]);

  // Executa auto-fit quando o layout carrega pela primeira vez
  useEffect(() => {
    if (layout) {
      handleAutoFit();
    }
  }, [layout, handleAutoFit]);

  // Foca a câmera em um robô específico e ativa o rastreamento contínuo
  const handleFocusAmr = (amr: AMRTelemetry) => {
    setSelectedAmrId(amr.id);
    setFollowedAmrId(amr.id);
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const cellSize = 32;
    const targetZoom = 1.35;

    const startX = isSidebarOpen ? 340 : 0;
    const availableW = isSidebarOpen ? canvas.width - 340 : canvas.width;

    const amrPixelX = amr.x * cellSize * targetZoom;
    const amrPixelY = amr.y * cellSize * targetZoom;

    const newOffsetX = startX + availableW / 2 - amrPixelX;
    const newOffsetY = canvas.height / 2 - amrPixelY;

    setZoom(targetZoom);
    setOffset({ x: newOffsetX, y: newOffsetY });
    cameraZoomRef.current = targetZoom;
    cameraOffsetRef.current = { x: newOffsetX, y: newOffsetY };
  };

  // Atualiza mapa de calor com dissipação temporal dinâmica (evaporative cooling)
  useEffect(() => {
    // 1. Resfriamento contínuo: dissipa calor das células não utilizadas a cada tick (~12s para esfriar totalmente)
    trafficHeatmap.current.forEach((heat, key) => {
      const decayed = heat * 0.94 - 0.4;
      if (decayed <= 1.0) {
        trafficHeatmap.current.delete(key);
      } else {
        trafficHeatmap.current.set(key, decayed);
      }
    });

    // 2. Acumula calor proporcionalmente onde os robôs estão circulando agora
    amrs.forEach((amr) => {
      const key = `${Math.round(amr.x)},${Math.round(amr.y)}`;
      const currentVal = trafficHeatmap.current.get(key) || 0;
      trafficHeatmap.current.set(key, Math.min(100, currentVal + 14));
    });
  }, [amrs]);

  // Loop de Renderização a 60 FPS
  useEffect(() => {
    let animationFrameId: number;

    const render = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const width = canvas.width;
      const height = canvas.height;

      // Fundo industrial suave
      ctx.fillStyle = "#090d16";
      ctx.fillRect(0, 0, width, height);

      if (!layout) {
        ctx.fillStyle = "#64748b";
        ctx.font = "14px monospace";
        ctx.fillText("Carregando topologia do galpão...", 380, 100);
        animationFrameId = requestAnimationFrame(render);
        return;
      }

      const cellSize = 32;

      // Se estiver acompanhando um robô, a câmera segue suavemente a cada frame (60 FPS)
      if (followedAmrId) {
        const smoothPos = smoothAmrPositions.current.get(followedAmrId);
        if (smoothPos) {
          const targetPixelX = smoothPos.x * cellSize + cellSize / 2;
          const targetPixelY = smoothPos.y * cellSize + cellSize / 2;
          const startX = isSidebarOpen ? 340 : 0;
          const availableW = isSidebarOpen ? width - 340 : width;
          const desiredOffsetX = startX + availableW / 2 - targetPixelX * cameraZoomRef.current;
          const desiredOffsetY = height / 2 - targetPixelY * cameraZoomRef.current;

          cameraOffsetRef.current.x += (desiredOffsetX - cameraOffsetRef.current.x) * 0.1;
          cameraOffsetRef.current.y += (desiredOffsetY - cameraOffsetRef.current.y) * 0.1;
        }
      }

      ctx.save();
      ctx.translate(cameraOffsetRef.current.x, cameraOffsetRef.current.y);
      ctx.scale(cameraZoomRef.current, cameraZoomRef.current);

      const gridPixelW = layout.width * cellSize;
      const gridPixelH = layout.height * cellSize;

      // 1. Piso do Galpão com borda de segurança industrial
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(0, 0, gridPixelW, gridPixelH);

      ctx.strokeStyle = "#1e293b";
      ctx.lineWidth = 1;
      for (let x = 0; x <= layout.width; x++) {
        ctx.beginPath();
        ctx.moveTo(x * cellSize, 0);
        ctx.lineTo(x * cellSize, gridPixelH);
        ctx.stroke();
      }
      for (let y = 0; y <= layout.height; y++) {
        ctx.beginPath();
        ctx.moveTo(0, y * cellSize);
        ctx.lineTo(gridPixelW, y * cellSize);
        ctx.stroke();
      }

      // Moldura externa do armazém
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 2;
      ctx.strokeRect(0, 0, gridPixelW, gridPixelH);

      // Destaque visual da célula sob o cursor do mouse
      const activeHover = hoveredCoordRef.current;
      if (activeHover) {
        ctx.fillStyle = "rgba(56, 189, 248, 0.15)";
        ctx.fillRect(activeHover.x * cellSize, activeHover.y * cellSize, cellSize, cellSize);
        ctx.strokeStyle = "rgba(56, 189, 248, 0.7)";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(activeHover.x * cellSize, activeHover.y * cellSize, cellSize, cellSize);
      }

      // 2. Heatmap Térmico com Gradiente Multi-Espectral
      if (showHeatmap) {
        trafficHeatmap.current.forEach((heat, key) => {
          const [hx, hy] = key.split(",").map(Number);
          let color: string;

          if (heat >= 75) {
            // Congestionamento Crítico / Gargalo (Vermelho vibrante)
            const alpha = Math.min(0.85, 0.55 + 0.3 * ((heat - 75) / 25));
            color = `rgba(239, 68, 68, ${alpha})`;
          } else if (heat >= 45) {
            // Tráfego Intenso (Âmbar / Laranja)
            const alpha = 0.45 + 0.25 * ((heat - 45) / 30);
            color = `rgba(245, 158, 11, ${alpha})`;
          } else if (heat >= 20) {
            // Tráfego Moderado (Verde Esmeralda)
            const alpha = 0.35 + 0.2 * ((heat - 20) / 25);
            color = `rgba(16, 185, 129, ${alpha})`;
          } else {
            // Tráfego Leve / Recente (Ciano / Azul Celeste)
            const alpha = 0.2 + 0.2 * (heat / 20);
            color = `rgba(56, 189, 248, ${alpha})`;
          }

          ctx.fillStyle = color;
          ctx.fillRect(hx * cellSize, hy * cellSize, cellSize, cellSize);
        });
      }

      // 3. Paredes e Obstáculos Fixos
      layout.obstacles.forEach((obs) => {
        ctx.fillStyle = "#334155";
        ctx.fillRect(obs.x * cellSize + 2, obs.y * cellSize + 2, cellSize - 4, cellSize - 4);
        ctx.strokeStyle = "#475569";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(obs.x * cellSize + 2, obs.y * cellSize + 2, cellSize - 4, cellSize - 4);
      });

      // 4. Docas de Recarga (Charging Docks)
      layout.charging_docks.forEach((dock) => {
        ctx.fillStyle = "rgba(16, 185, 129, 0.25)";
        ctx.fillRect(dock.x * cellSize, dock.y * cellSize, cellSize, cellSize);
        ctx.strokeStyle = "#10b981";
        ctx.lineWidth = 2;
        ctx.strokeRect(dock.x * cellSize + 2, dock.y * cellSize + 2, cellSize - 4, cellSize - 4);

        ctx.fillStyle = "#10b981";
        ctx.font = "bold 12px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("⚡", dock.x * cellSize + cellSize / 2, dock.y * cellSize + 21);
      });

      // 5. Bancadas de Separação (Picking Stations)
      layout.picking_stations.forEach((station) => {
        ctx.fillStyle = "rgba(245, 158, 11, 0.25)";
        ctx.fillRect(station.x * cellSize, station.y * cellSize, cellSize, cellSize);
        ctx.strokeStyle = "#f59e0b";
        ctx.lineWidth = 2;
        ctx.strokeRect(station.x * cellSize + 2, station.y * cellSize + 2, cellSize - 4, cellSize - 4);

        ctx.fillStyle = "#f59e0b";
        ctx.font = "bold 10px monospace";
        ctx.textAlign = "center";
        ctx.fillText("PICK", station.x * cellSize + cellSize / 2, station.y * cellSize + 20);
      });

      // 6. Prateleiras Estáticas (Pods)
      layout.pods.forEach((pod) => {
        const isBeingCarried = amrs.some((a) => a.carrying_pod_id === pod.id);
        if (isBeingCarried) return;

        ctx.fillStyle = "#1e293b";
        ctx.fillRect(pod.x * cellSize + 4, pod.y * cellSize + 4, cellSize - 8, cellSize - 8);
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(pod.x * cellSize + 4, pod.y * cellSize + 4, cellSize - 8, cellSize - 8);

        ctx.fillStyle = "#38bdf8";
        ctx.font = "11px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("📦", pod.x * cellSize + cellSize / 2, pod.y * cellSize + 21);
      });

      // 7. Bloqueios de Emergência (Hazard Zones)
      dynamicBlocks.forEach((block) => {
        ctx.fillStyle = "rgba(239, 68, 68, 0.45)";
        ctx.fillRect(block.x * cellSize, block.y * cellSize, cellSize, cellSize);
        ctx.strokeStyle = "#ef4444";
        ctx.lineWidth = 2;
        ctx.strokeRect(block.x * cellSize + 1, block.y * cellSize + 1, cellSize - 2, cellSize - 2);

        ctx.fillStyle = "#ef4444";
        ctx.font = "13px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("⚠️", block.x * cellSize + cellSize / 2, block.y * cellSize + 21);
      });

      // 8. Projeção de Trajetória com cor única atribuída a cada robô
      if (showPaths) {
        amrs.forEach((amr) => {
          if (!amr.planned_path || amr.planned_path.length === 0) return;
          const isSelected = selectedAmrId === amr.id;
          const amrColor = getAmrColor(amr.id);

          ctx.beginPath();
          ctx.strokeStyle = isSelected ? amrColor : hexToRgba(amrColor, 0.65);
          ctx.lineWidth = isSelected ? 3.5 : 2.0;
          ctx.setLineDash(isSelected ? [6, 3] : [4, 4]);

          const currPos = smoothAmrPositions.current.get(amr.id) || {
            x: amr.x,
            y: amr.y,
          };
          ctx.moveTo(
            currPos.x * cellSize + cellSize / 2,
            currPos.y * cellSize + cellSize / 2
          );

          amr.planned_path.forEach((step) => {
            ctx.lineTo(
              step.x * cellSize + cellSize / 2,
              step.y * cellSize + cellSize / 2
            );
          });
          ctx.stroke();
          ctx.setLineDash([]);

          // Marcador de destino final da rota na cor correspondente do robô
          const targetStep = amr.planned_path[amr.planned_path.length - 1];
          if (targetStep) {
            ctx.beginPath();
            ctx.arc(
              targetStep.x * cellSize + cellSize / 2,
              targetStep.y * cellSize + cellSize / 2,
              isSelected ? 5.5 : 4,
              0,
              Math.PI * 2
            );
            ctx.fillStyle = amrColor;
            ctx.fill();
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 1.5;
            ctx.stroke();
          }
        });
      }

      // 9. Robôs AMRs com Cores Únicas e Identificação Visual Clara
      amrs.forEach((amr) => {
        let currentPos = smoothAmrPositions.current.get(amr.id);
        if (!currentPos) {
          currentPos = { x: amr.x, y: amr.y };
          smoothAmrPositions.current.set(amr.id, currentPos);
        }

        // LERP suave
        const lerpFactor = 0.22;
        currentPos.x += (amr.x - currentPos.x) * lerpFactor;
        currentPos.y += (amr.y - currentPos.y) * lerpFactor;

        const pixelX = currentPos.x * cellSize + cellSize / 2;
        const pixelY = currentPos.y * cellSize + cellSize / 2;
        const radius = cellSize * 0.42;

        const isSelected = selectedAmrId === amr.id;
        const amrColor = getAmrColor(amr.id);

        // Halo pulsante para robô selecionado ou seguido
        if (isSelected || followedAmrId === amr.id) {
          ctx.beginPath();
          ctx.arc(pixelX, pixelY, radius + 7, 0, Math.PI * 2);
          ctx.strokeStyle = amrColor;
          ctx.lineWidth = 3;
          ctx.stroke();
        }

        // Corpo do Robô preenchido com sua cor exclusiva
        ctx.beginPath();
        ctx.arc(pixelX, pixelY, radius, 0, Math.PI * 2);
        ctx.fillStyle = amrColor;
        ctx.fill();

        // Anel de acabamento com alto contraste
        ctx.strokeStyle = isSelected ? "#ffffff" : hexToRgba(amrColor, 0.9);
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Se estiver carregando pod, sobrepõe a prateleira amarela em cima
        if (amr.carrying_pod_id) {
          ctx.fillStyle = "rgba(250, 204, 21, 0.95)";
          ctx.fillRect(pixelX - 8, pixelY - 8, 16, 16);
          ctx.strokeStyle = "#ca8a04";
          ctx.lineWidth = 1.5;
          ctx.strokeRect(pixelX - 8, pixelY - 8, 16, 16);
        }

        // Se estiver recarregando, exibe o ícone de raio
        if (amr.state === "CHARGING") {
          ctx.fillStyle = "#ffffff";
          ctx.font = "bold 10px sans-serif";
          ctx.textAlign = "center";
          ctx.fillText("⚡", pixelX, pixelY + 3);
        }

        // Barra de Bateria
        const barW = 24;
        const barH = 4;
        const barX = pixelX - barW / 2;
        const barY = pixelY - radius - 7;

        ctx.fillStyle = "#0f172a";
        ctx.fillRect(barX, barY, barW, barH);
        ctx.fillStyle =
          amr.battery_level > 50
            ? "#10b981"
            : amr.battery_level > 20
            ? "#f59e0b"
            : "#ef4444";
        ctx.fillRect(
          barX,
          barY,
          (barW * Math.max(0, amr.battery_level)) / 100,
          barH
        );

        // Identificador Rápido AMR-XX em texto branco com contraste e sombra
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 9px sans-serif";
        ctx.textAlign = "center";
        ctx.shadowColor = "rgba(0, 0, 0, 0.9)";
        ctx.shadowBlur = 4;
        ctx.fillText(amr.id, pixelX, pixelY + (amr.carrying_pod_id ? 14 : 3));
        ctx.shadowBlur = 0;

        // Se estiver no estado de colisão física (CRASHED / Chaos)
        if (amr.state === "CRASHED") {
          const pulse = (Math.sin(Date.now() / 100) + 1) / 2;
          ctx.beginPath();
          ctx.arc(pixelX, pixelY, radius + 8 + pulse * 6, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(239, 68, 68, ${0.5 + pulse * 0.5})`;
          ctx.lineWidth = 3;
          ctx.stroke();

          ctx.font = "bold 16px sans-serif";
          ctx.textAlign = "center";
          ctx.fillText("💥", pixelX, pixelY - 14);
        }
      });

      // Efeito Visual de Ondas de Choque no Ponto de Colisão (Chaos Engineering)
      if (activeIncident && !activeIncident.is_resolved) {
        const cx = activeIncident.location.x;
        const cy = activeIncident.location.y;
        const impactPixelX = cx * cellSize + cellSize / 2;
        const impactPixelY = cy * cellSize + cellSize / 2;

        const time = (Date.now() / 350) % 1;
        const ringRadius = 10 + time * (cellSize * 1.5);
        const ringAlpha = (1 - time) * 0.9;

        ctx.beginPath();
        ctx.arc(impactPixelX, impactPixelY, ringRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(239, 68, 68, ${ringAlpha})`;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        ctx.fillStyle = "rgba(239, 68, 68, 0.3)";
        ctx.fillRect(cx * cellSize, cy * cellSize, cellSize, cellSize);
        ctx.strokeStyle = "#ef4444";
        ctx.lineWidth = 2;
        ctx.strokeRect(cx * cellSize, cy * cellSize, cellSize, cellSize);
      }

      // 8. Réguas Coordenadas dos Eixos X (Colunas) e Y (Linhas)
      const rulerBg = "rgba(15, 23, 42, 0.96)";
      const rulerBorder = "#334155";
      const rulerTick = "#475569";
      const rulerHighlight = "#38bdf8";
      const rulerText = "#94a3b8";

      // 4 Cantos decorativos da moldura industrial
      ctx.fillStyle = rulerBg;
      ctx.fillRect(-28, -24, 28, 24);
      ctx.fillRect(gridPixelW, -24, 28, 24);
      ctx.fillRect(-28, gridPixelH, 28, 24);
      ctx.fillRect(gridPixelW, gridPixelH, 28, 24);

      ctx.strokeStyle = rulerBorder;
      ctx.lineWidth = 1;
      ctx.strokeRect(-28, -24, 28, 24);
      ctx.strokeRect(gridPixelW, -24, 28, 24);
      ctx.strokeRect(-28, gridPixelH, 28, 24);
      ctx.strokeRect(gridPixelW, gridPixelH, 28, 24);

      // Rótulo da Origem X/Y
      ctx.fillStyle = rulerHighlight;
      ctx.font = "bold 9px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("X/Y", -14, -12);

      // Régua Superior do Eixo X (Colunas)
      ctx.fillStyle = rulerBg;
      ctx.fillRect(0, -24, gridPixelW, 24);
      ctx.strokeStyle = rulerBorder;
      ctx.strokeRect(0, -24, gridPixelW, 24);

      // Régua Inferior do Eixo X (Colunas)
      ctx.fillStyle = rulerBg;
      ctx.fillRect(0, gridPixelH, gridPixelW, 24);
      ctx.strokeStyle = rulerBorder;
      ctx.strokeRect(0, gridPixelH, gridPixelW, 24);

      // Régua Esquerda do Eixo Y (Linhas)
      ctx.fillStyle = rulerBg;
      ctx.fillRect(-28, 0, 28, gridPixelH);
      ctx.strokeStyle = rulerBorder;
      ctx.strokeRect(-28, 0, 28, gridPixelH);

      // Régua Direita do Eixo Y (Linhas)
      ctx.fillStyle = rulerBg;
      ctx.fillRect(gridPixelW, 0, 28, gridPixelH);
      ctx.strokeStyle = rulerBorder;
      ctx.strokeRect(gridPixelW, 0, 28, gridPixelH);

      // Números e Marcadores do Eixo X (Colunas 0..layout.width-1)
      for (let x = 0; x < layout.width; x++) {
        const cellCenterX = x * cellSize + cellSize / 2;
        const isMajor = x % 5 === 0;
        const isHoveredCol = activeHover && activeHover.x === x;

        // Ticks verticais
        ctx.strokeStyle = isHoveredCol ? rulerHighlight : (isMajor ? rulerBorder : rulerTick);
        ctx.lineWidth = isMajor || isHoveredCol ? 1.5 : 1;
        ctx.beginPath();
        ctx.moveTo(x * cellSize, -6);
        ctx.lineTo(x * cellSize, 0);
        ctx.moveTo(x * cellSize, gridPixelH);
        ctx.lineTo(x * cellSize, gridPixelH + 6);
        ctx.stroke();

        // Rótulo numérico da coluna
        ctx.fillStyle = isHoveredCol ? "#ffffff" : (isMajor ? rulerHighlight : rulerText);
        ctx.font = isHoveredCol ? "bold 11px monospace" : (isMajor ? "bold 10px monospace" : "9px monospace");
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        ctx.fillText(String(x), cellCenterX, -12);
        ctx.fillText(String(x), cellCenterX, gridPixelH + 12);
      }

      // Números e Marcadores do Eixo Y (Linhas 0..layout.height-1)
      for (let y = 0; y < layout.height; y++) {
        const cellCenterY = y * cellSize + cellSize / 2;
        const isMajor = y % 5 === 0;
        const isHoveredRow = activeHover && activeHover.y === y;

        // Ticks horizontais
        ctx.strokeStyle = isHoveredRow ? rulerHighlight : (isMajor ? rulerBorder : rulerTick);
        ctx.lineWidth = isMajor || isHoveredRow ? 1.5 : 1;
        ctx.beginPath();
        ctx.moveTo(-6, y * cellSize);
        ctx.lineTo(0, y * cellSize);
        ctx.moveTo(gridPixelW, y * cellSize);
        ctx.lineTo(gridPixelW + 6, y * cellSize);
        ctx.stroke();

        // Rótulo numérico da linha
        ctx.fillStyle = isHoveredRow ? "#ffffff" : (isMajor ? rulerHighlight : rulerText);
        ctx.font = isHoveredRow ? "bold 11px monospace" : (isMajor ? "bold 10px monospace" : "9px monospace");
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        ctx.fillText(String(y), -14, cellCenterY);
        ctx.fillText(String(y), gridPixelW + 14, cellCenterY);
      }

      ctx.restore();
      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animationFrameId);
  }, [layout, amrs, dynamicBlocks, showPaths, showHeatmap, selectedAmrId, zoom, offset, followedAmrId, isSidebarOpen]);

  // Manipuladores de Zoom e Pan
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom((prev) => {
      const next = Math.min(2.5, Math.max(0.35, prev * zoomFactor));
      cameraZoomRef.current = next;
      return next;
    });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setFollowedAmrId(null); // Solta a câmera ao arrastar livremente
    setDragStart({ x: e.clientX - cameraOffsetRef.current.x, y: e.clientY - cameraOffsetRef.current.y });
    dragStartClientRef.current = { x: e.clientX, y: e.clientY };
    hasMovedSignificantlyRef.current = false;
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      if (Math.hypot(e.clientX - dragStartClientRef.current.x, e.clientY - dragStartClientRef.current.y) > 5) {
        hasMovedSignificantlyRef.current = true;
      }
      const newOffset = {
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      };
      cameraOffsetRef.current = newOffset;
      setOffset(newOffset);
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas || !layout) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const mouseCanvasX = (e.clientX - rect.left) * scaleX;
    const mouseCanvasY = (e.clientY - rect.top) * scaleY;

    const clickX = (mouseCanvasX - cameraOffsetRef.current.x) / cameraZoomRef.current;
    const clickY = (mouseCanvasY - cameraOffsetRef.current.y) / cameraZoomRef.current;
    const cellSize = 32;

    const gridX = Math.floor(clickX / cellSize);
    const gridY = Math.floor(clickY / cellSize);

    if (gridX >= 0 && gridX < layout.width && gridY >= 0 && gridY < layout.height) {
      if (!hoveredCoordRef.current || hoveredCoordRef.current.x !== gridX || hoveredCoordRef.current.y !== gridY) {
        const coord = { x: gridX, y: gridY };
        hoveredCoordRef.current = coord;
        setHoveredCoord(coord);
      }
    } else {
      if (hoveredCoordRef.current !== null) {
        hoveredCoordRef.current = null;
        setHoveredCoord(null);
      }
    }
  };

  const handleMouseLeave = () => {
    setIsDragging(false);
    if (hoveredCoordRef.current !== null) {
      hoveredCoordRef.current = null;
      setHoveredCoord(null);
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  // Clique no Canvas com escala 1:1 rigorosa
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    // Se o usuário arrastou a tela, não dispara bloqueio acidental
    if (hasMovedSignificantlyRef.current) {
      hasMovedSignificantlyRef.current = false;
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas || !layout) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const clickCanvasX = (e.clientX - rect.left) * scaleX;
    const clickCanvasY = (e.clientY - rect.top) * scaleY;

    const clickX = (clickCanvasX - cameraOffsetRef.current.x) / cameraZoomRef.current;
    const clickY = (clickCanvasY - cameraOffsetRef.current.y) / cameraZoomRef.current;
    const cellSize = 32;

    const gridX = Math.floor(clickX / cellSize);
    const gridY = Math.floor(clickY / cellSize);

    // 1. Verifica se clicou em algum robô
    const clickedAmr = amrs.find(
      (a) => Math.round(a.x) === gridX && Math.round(a.y) === gridY
    );
    if (clickedAmr) {
      setSelectedAmrId(clickedAmr.id === selectedAmrId ? null : clickedAmr.id);
      return;
    }

    // 2. Se clicou em célula navegável livre, alterna bloqueio de emergência
    if (gridX >= 0 && gridX < layout.width && gridY >= 0 && gridY < layout.height) {
      const isBlocked = dynamicBlocks.some((b) => b.x === gridX && b.y === gridY);
      if (isBlocked) {
        sendWebSocketMessage({ action: "UNBLOCK_CELL", x: gridX, y: gridY });
      } else {
        sendWebSocketMessage({
          action: "BLOCK_CELL",
          x: gridX,
          y: gridY,
          reason: "Bloqueio manual via clique no Digital Twin",
        });
      }
    }
  };

  return (
    <div className="relative w-full h-[calc(100vh-8rem)] bg-slate-950 overflow-hidden flex items-center justify-center">
      {/* Barra Lateral da Frota com Lista de Robôs e Botão "Seguir" */}
      <FleetSidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onFocusAmr={handleFocusAmr}
        followedAmrId={followedAmrId}
        onStopFollow={() => setFollowedAmrId(null)}
      />

      {/* Indicador Flutuante de Robô Seguido */}
      {followedAmrId && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-20 bg-slate-900/95 border border-cyan-500/60 backdrop-blur-md px-3.5 py-1.5 rounded-full text-xs font-medium text-cyan-300 shadow-xl flex items-center gap-2.5 animate-in fade-in duration-200">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          <span>
            {language === "pt"
              ? `Câmera acompanhando ${followedAmrId}`
              : `Camera tracking ${followedAmrId}`}
          </span>
          <button
            onClick={() => setFollowedAmrId(null)}
            className="ml-1 px-2 py-0.5 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-semibold border border-slate-700 transition-all"
          >
            {language === "pt" ? "Soltar Câmera" : "Release"}
          </button>
        </div>
      )}

      {/* Banner Tutorial no Topo para Fácil Compreensão */}
      {showTutorialBanner && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 bg-slate-900/90 backdrop-blur-md px-4 py-2 rounded-xl border border-cyan-500/40 text-xs text-slate-300 flex items-center gap-3 shadow-2xl animate-in fade-in duration-300">
          <HelpCircle className="w-4 h-4 text-cyan-400 flex-shrink-0" />
          <span>
            {language === "pt"
              ? "👋 Os robôs pegam prateleiras, levam até as bancadas de separação (amarelas) e devolvem ao estoque. Clique em 'Seguir' na barra lateral para acompanhar qualquer robô!"
              : "👋 Robots pick storage pods, take them to picking bays (yellow), and return them to storage. Click 'Follow' in the sidebar to track any AMR!"}
          </span>
          <button
            onClick={() => setShowTutorialBanner(false)}
            className="text-slate-400 hover:text-white font-bold ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Barra de Controles Flutuante no Topo */}
      <div
        className={`absolute top-4 z-20 flex items-center gap-2 bg-slate-900/90 backdrop-blur-md p-1.5 rounded-xl border border-slate-800 shadow-xl transition-all ${
          isSidebarOpen ? "left-88" : "left-12"
        }`}
      >
        <button
          onClick={() => sendWebSocketMessage({ action: "TOGGLE_PAUSE" })}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
            isPaused
              ? "bg-emerald-500 text-slate-950 hover:bg-emerald-400"
              : "bg-amber-500 text-slate-950 hover:bg-amber-400"
          }`}
        >
          {isPaused ? <Play className="w-3.5 h-3.5 fill-current" /> : <Pause className="w-3.5 h-3.5 fill-current" />}
          {isPaused ? "Play" : "Pausar"}
        </button>

        {/* Velocidade da Simulação */}
        <div className="flex items-center bg-slate-950 px-1.5 py-1 rounded-lg border border-slate-800 text-xs font-mono text-slate-400">
          <FastForward className="w-3 h-3 mr-1 text-cyan-400" />
          {[0.5, 1.0, 2.0].map((s) => (
            <button
              key={s}
              onClick={() => sendWebSocketMessage({ action: "SET_SPEED", speed: s })}
              className={`px-1.5 py-0.5 rounded transition-all ${
                speed === s
                  ? "bg-cyan-500 text-slate-950 font-bold"
                  : "hover:text-white"
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        <div className="h-4 w-px bg-slate-800 mx-1" />

        {/* Botão Centralizar Galpão */}
        <button
          onClick={handleAutoFit}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all"
          title="Centralizar e ajustar tamanho do galpão na tela"
        >
          <Maximize2 className="w-3.5 h-3.5 text-cyan-400" />
          <span>Centralizar</span>
        </button>

        {/* Toggle de Trajetórias */}
        <button
          onClick={() => setShowPaths(!showPaths)}
          className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            showPaths
              ? "bg-slate-800 text-cyan-400 border border-cyan-500/30"
              : "text-slate-400 hover:text-white"
          }`}
          title="Exibir ou ocultar linhas de rota projetadas dos robôs"
        >
          <Route className="w-3.5 h-3.5" />
          <span className="hidden md:inline">Rotas</span>
        </button>

        {/* Toggle de Heatmap e Botão Zerar */}
        <div className="flex items-center">
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              showHeatmap
                ? "bg-red-500/20 text-red-400 border border-red-500/40"
                : "text-slate-400 hover:text-white"
            }`}
            title="Exibir mapa de calor térmico"
          >
            <Flame className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Heatmap</span>
          </button>

          {showHeatmap && (
            <button
              onClick={() => {
                trafficHeatmap.current.clear();
              }}
              className="ml-1 flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all shadow-sm animate-in fade-in"
              title={
                language === "pt"
                  ? "Zerar e limpar histórico de calor do mapa"
                  : "Reset and clear traffic heatmap history"
              }
            >
              <RotateCcw className="w-3 h-3 text-red-400" />
              <span className="hidden sm:inline">
                {language === "pt" ? "Zerar" : "Reset"}
              </span>
            </button>
          )}
        </div>

        <div className="h-4 w-px bg-slate-800 mx-1" />

        {/* Botão Adicionar Caos com Menu de Modos de Falha */}
        <div className="relative">
          <button
            onClick={() => setIsChaosMenuOpen(!isChaosMenuOpen)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-red-600/30 to-amber-600/30 hover:from-red-600/50 hover:to-amber-600/50 text-amber-300 border border-amber-500/40 shadow-sm transition-all active:scale-95"
            title="Injetar falha física e simular colisão (Chaos Engineering)"
          >
            <Zap className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            <span>{language === "pt" ? "Adicionar Caos" : "Inject Chaos"}</span>
          </button>

          {isChaosMenuOpen && (
            <div className="absolute top-full mt-2 left-0 z-50 w-64 bg-slate-900/98 backdrop-blur-xl border border-slate-700/80 rounded-xl shadow-2xl p-2 text-xs space-y-1 animate-in fade-in zoom-in-95">
              <div className="px-2 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                {language === "pt" ? "Modo de Falha Industrial" : "Industrial Failure Mode"}
              </div>

              <button
                onClick={() => {
                  injectChaos("random", 1);
                  setIsChaosMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-800 text-left text-slate-200 transition-colors"
              >
                <span className="text-base">🎲</span>
                <div>
                  <div className="font-semibold text-white">
                    {language === "pt" ? "Caos Rápido (Aleatório)" : "Quick Chaos (Random)"}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {language === "pt" ? "Seleciona o cruzamento mais crítico" : "Auto-selects nearest intersection"}
                  </div>
                </div>
              </button>

              <button
                onClick={() => {
                  injectChaos("wheel_slip", 1);
                  setIsChaosMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-800 text-left text-slate-200 transition-colors"
              >
                <span className="text-base">🌧️</span>
                <div>
                  <div className="font-semibold text-white">
                    {language === "pt" ? "Derrapagem (Wheel Slip)" : "Wheel Slip (Low Friction)"}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {language === "pt" ? "Atrito nulo por óleo no piso" : "Zero traction due to oil spill"}
                  </div>
                </div>
              </button>

              <button
                onClick={() => {
                  injectChaos("network_latency", 1);
                  setIsChaosMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-800 text-left text-slate-200 transition-colors"
              >
                <span className="text-base">📶</span>
                <div>
                  <div className="font-semibold text-white">
                    {language === "pt" ? "Latência Wi-Fi (Jitter)" : "Wi-Fi Jitter / Packet Drop"}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {language === "pt" ? "Atraso de 850ms no sinal de parada" : "850ms delay in stop signal"}
                  </div>
                </div>
              </button>

              <button
                onClick={() => {
                  injectChaos("sensor_blindspot", 1);
                  setIsChaosMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-slate-800 text-left text-slate-200 transition-colors"
              >
                <span className="text-base">👁️</span>
                <div>
                  <div className="font-semibold text-white">
                    {language === "pt" ? "Ponto Cego (LiDAR 90°)" : "LiDAR Blindspot (90°)"}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {language === "pt" ? "Oclusão óptica em cruzamento" : "Optical sensor occlusion"}
                  </div>
                </div>
              </button>
            </div>
          )}
        </div>

        {/* Botão de Limpar Todos os Bloqueios se houver algum ativo */}
        {dynamicBlocks.length > 0 && (
          <>
            <div className="h-4 w-px bg-slate-800 mx-1" />
            <button
              onClick={() => sendWebSocketMessage({ action: "CLEAR_ALL_BLOCKS" })}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/40 shadow-sm transition-all animate-in fade-in"
              title={
                language === "pt"
                  ? "Remover todas as áreas interditadas do galpão"
                  : "Remove all hazard blocks from the warehouse"
              }
            >
              <span>⚠️</span>
              <span>
                {language === "pt"
                  ? `Limpar Bloqueios (${dynamicBlocks.length})`
                  : `Clear Blocks (${dynamicBlocks.length})`}
              </span>
            </button>
          </>
        )}
      </div>

      {/* Legenda do Galpão */}
      <LegendCard />

      {/* Indicador Flutuante de Coordenada e Conteúdo da Célula sob o Mouse (HUD Inferior Centralizado) */}
      {hoveredCoord && (() => {
        const hx = hoveredCoord.x;
        const hy = hoveredCoord.y;

        const amrOnCell = amrs.find(
          (a) => Math.round(a.x) === hx && Math.round(a.y) === hy
        );
        const isCellBlocked = dynamicBlocks.some((b) => b.x === hx && b.y === hy);
        const podOnCell = layout?.pods.find((p) => p.x === hx && p.y === hy);
        const isPickingStation = layout?.picking_stations.some((s) => s.x === hx && s.y === hy);
        const isChargingDock = layout?.charging_docks.some((d) => d.x === hx && d.y === hy);
        const isObstacle = layout?.obstacles.some((o) => o.x === hx && o.y === hy);

        return (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 bg-slate-900/95 border border-slate-700/80 backdrop-blur-md px-4 py-2 rounded-xl text-xs font-mono text-slate-200 shadow-2xl flex items-center gap-3 pointer-events-none animate-in fade-in duration-150 border-t-cyan-500/50">
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  isCellBlocked
                    ? "bg-red-500 animate-ping"
                    : amrOnCell
                    ? "bg-purple-400"
                    : podOnCell
                    ? "bg-sky-400"
                    : isPickingStation
                    ? "bg-amber-400"
                    : isChargingDock
                    ? "bg-emerald-400"
                    : "bg-cyan-400"
                }`}
              />
              <span className="text-slate-400 font-sans">{language === "pt" ? "Célula:" : "Cell:"}</span>
              <span className="text-cyan-300 font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                X: {hx} | Y: {hy}
              </span>
            </div>

            <div className="h-4 w-px bg-slate-700" />

            {/* Conteúdo / Estado da Célula */}
            {isCellBlocked && (
              <span className="text-red-400 font-bold flex items-center gap-1.5 animate-pulse">
                <span>⚠️</span>
                <span>
                  {language === "pt"
                    ? "Área Interditada (Clique para liberar passagem)"
                    : "Hazard Block (Click to unblock)"}
                </span>
              </span>
            )}

            {!isCellBlocked && amrOnCell && (
              <span className="text-purple-300 font-bold flex items-center gap-1.5">
                <span>🤖</span>
                <span>{amrOnCell.id}</span>
                <span className="text-[10px] text-slate-400 font-normal">
                  ({amrOnCell.state})
                </span>
              </span>
            )}

            {!isCellBlocked && !amrOnCell && podOnCell && (
              <span className="text-sky-300 font-medium flex items-center gap-1.5">
                <span>📦</span>
                <span>{language === "pt" ? "Prateleira:" : "Pod:"} {podOnCell.id}</span>
              </span>
            )}

            {!isCellBlocked && !amrOnCell && isPickingStation && (
              <span className="text-amber-300 font-medium flex items-center gap-1.5">
                <span>🎯</span>
                <span>{language === "pt" ? "Bancada de Separação (Picking)" : "Picking Bay"}</span>
              </span>
            )}

            {!isCellBlocked && !amrOnCell && isChargingDock && (
              <span className="text-emerald-300 font-medium flex items-center gap-1.5">
                <span>⚡</span>
                <span>{language === "pt" ? "Doca de Recarga Automática" : "Charging Dock"}</span>
              </span>
            )}

            {!isCellBlocked && !amrOnCell && isObstacle && (
              <span className="text-slate-400 font-medium flex items-center gap-1.5">
                <span>🧱</span>
                <span>{language === "pt" ? "Pilar / Parede Fixa" : "Wall / Column"}</span>
              </span>
            )}

            {!isCellBlocked && !amrOnCell && !podOnCell && !isPickingStation && !isChargingDock && !isObstacle && (
              <span className="text-slate-400 font-normal flex items-center gap-1">
                <span className="text-emerald-400">●</span>
                <span>
                  {language === "pt"
                    ? "Corredor Livre (Clique para interditar)"
                    : "Free Corridor (Click to block)"}
                </span>
              </span>
            )}
          </div>
        );
      })()}

      {/* Banner Flutuante de Incidente de Colisão Ativo (Chaos) */}
      {activeIncident && !activeIncident.is_resolved && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-40 bg-slate-900/95 border border-red-500/70 backdrop-blur-xl px-4 py-2.5 rounded-2xl shadow-2xl shadow-red-950/50 flex items-center gap-3 animate-in fade-in slide-in-from-top-3 border-t-red-400">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
            <span className="text-xs font-bold text-red-200">
              {language === "pt"
                ? `🚨 Colisão Detectada: ${activeIncident.involved_amrs.join(" e ")} em (${activeIncident.location.x}, ${activeIncident.location.y})`
                : `🚨 Collision Detected: ${activeIncident.involved_amrs.join(" & ")} at (${activeIncident.location.x}, ${activeIncident.location.y})`}
            </span>
          </div>

          <button
            onClick={() => setIsWarRoomOpen(true)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white shadow-md transition-all active:scale-95"
          >
            <span>🔍</span>
            <span>{language === "pt" ? "Ver Investigação (RCA)" : "Open RCA War Room"}</span>
          </button>
        </div>
      )}

      {/* Modal da War Room de Investigação Forense de Incidente */}
      {isWarRoomOpen && activeIncident && (
        <IncidentWarRoomModal
          incident={activeIncident}
          onClose={() => setIsWarRoomOpen(false)}
        />
      )}

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onClick={handleCanvasClick}
        className="w-full h-full cursor-grab active:cursor-grabbing block"
      />
    </div>
  );
};
