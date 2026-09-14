import json
from typing import List, Set

from fastapi import WebSocket
from loguru import logger

from warehouse_routing.core.fleet_orchestrator import FleetOrchestrator


class WebSocketTelemetryHub:
    """
    Hub de WebSockets para transmissão de telemetria da frota em tempo real
    e recebimento de comandos do frontend (Play, Pause, Bloqueio Manual).
    """

    def __init__(self, orchestrator: FleetOrchestrator) -> None:
        self.orchestrator = orchestrator
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Aceita uma nova conexão WebSocket e registra no pool."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Cliente WebSocket conectado. Conexões ativas: {len(self.active_connections)}")

        # Envia o estado atual imediatamente no handshake inicial
        initial_payload = self.orchestrator.get_telemetry_payload()
        await websocket.send_text(json.dumps(initial_payload))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a conexão do pool de transmissão."""
        self.active_connections.discard(websocket)
        logger.info(
            f"Cliente WebSocket desconectado. Conexões ativas: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict) -> None:
        """Transmite dados para todos os clientes conectados."""
        if not self.active_connections:
            return

        payload_str = json.dumps(message)
        dead_connections: List[WebSocket] = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload_str)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    async def handle_client_message(self, websocket: WebSocket, data: str) -> None:
        """
        Interpreta comandos de controle enviados pelo frontend:
        - TOGGLE_PAUSE
        - SET_SPEED
        - BLOCK_CELL
        - UNBLOCK_CELL
        - EMERGENCY_STOP
        """
        try:
            command = json.loads(data)
            action = command.get("action")

            if action == "TOGGLE_PAUSE":
                self.orchestrator.is_paused = not self.orchestrator.is_paused
                logger.info(f"Simulação {'Pausada' if self.orchestrator.is_paused else 'Retomada'}")

            elif action == "SET_SPEED":
                speed = float(command.get("speed", 1.0))
                self.orchestrator.simulation_speed = max(0.25, min(5.0, speed))

            elif action == "BLOCK_CELL":
                x = int(command.get("x"))
                y = int(command.get("y"))
                reason = command.get("reason", "Bloqueio manual via interface")
                success, affected, impact = self.orchestrator.block_area(x, y, reason)
                logger.warning(
                    f"Comando BLOCK_CELL ({x}, {y}): {affected} robôs re-roteados ({impact}s)"
                )

            elif action == "UNBLOCK_CELL":
                x = int(command.get("x"))
                y = int(command.get("y"))
                self.orchestrator.unblock_area(x, y)
                logger.info(f"Comando UNBLOCK_CELL ({x}, {y}) executado")

            elif action == "CLEAR_ALL_BLOCKS":
                for b in list(self.orchestrator.grid.dynamic_blocks):
                    self.orchestrator.unblock_area(b[0], b[1])
                logger.info("Comando CLEAR_ALL_BLOCKS executado: todas as interdições foram liberadas.")

            elif action == "ADD_AMRS":
                count = int(command.get("count", 1))
                added = self.orchestrator.add_amrs(count)
                logger.info(f"Comando ADD_AMRS: {len(added)} robôs adicionados ({', '.join(added)})")

            elif action == "REMOVE_AMRS":
                count = int(command.get("count", 1))
                specific_id = command.get("amr_id")
                specific_ids = [specific_id] if specific_id else None
                removed = self.orchestrator.remove_amrs(count=count, specific_ids=specific_ids)
                logger.info(f"Comando REMOVE_AMRS: {len(removed)} robôs removidos ({', '.join(removed)})")

            elif action == "SET_FLEET_SIZE":
                count = int(command.get("count", 8))
                res = self.orchestrator.set_fleet_size(count)
                logger.info(f"Comando SET_FLEET_SIZE para {count}: {res}")

            elif action == "EMERGENCY_STOP":
                activate = bool(command.get("activate", True))
                self.orchestrator.emergency_stop(activate)

            elif action == "INJECT_CHAOS":
                failure_type = command.get("failure_type", "random")
                count = int(command.get("count", 1))
                report = self.orchestrator.inject_chaos(failure_type=failure_type, count=count)
                logger.warning(f"Comando INJECT_CHAOS executado via WebSocket: {report.incident_id}")

            elif action == "RESOLVE_INCIDENT":
                incident_id = command.get("incident_id")
                self_healing = bool(command.get("self_healing", True))
                if incident_id:
                    self.orchestrator.resolve_incident(incident_id=incident_id, self_healing=self_healing)
                    logger.info(f"Comando RESOLVE_INCIDENT executado via WebSocket: {incident_id}")

            # Envia atualização imediata após qualquer comando
            await self.broadcast(self.orchestrator.get_telemetry_payload())

        except Exception as e:
            logger.error(f"Erro ao processar comando WebSocket: {e}")
