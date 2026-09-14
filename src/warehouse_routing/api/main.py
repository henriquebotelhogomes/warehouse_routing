import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from warehouse_routing.api.routes_analytics import (
    router as analytics_router,
)
from warehouse_routing.api.routes_analytics import (
    set_orchestrator_instance as set_analytics_orch,
)
from warehouse_routing.api.routes_chaos import (
    router as chaos_router,
)
from warehouse_routing.api.routes_chaos import (
    set_orchestrator_instance as set_chaos_orch,
)
from warehouse_routing.api.routes_copilot import router as copilot_router
from warehouse_routing.api.routes_fleet import (
    router as fleet_router,
)
from warehouse_routing.api.routes_fleet import (
    set_orchestrator_instance as set_fleet_orch,
)
from warehouse_routing.api.routes_layout import (
    router as layout_router,
)
from warehouse_routing.api.routes_layout import (
    set_orchestrator_instance as set_layout_orch,
)
from warehouse_routing.api.scalar_docs import setup_scalar_docs
from warehouse_routing.api.websocket_hub import WebSocketTelemetryHub
from warehouse_routing.copilot.guardrails import set_orchestrator_instance as set_guardrails_orch
from warehouse_routing.copilot.tools import set_orchestrator_instance as set_tools_orch
from warehouse_routing.core.fleet_orchestrator import FleetOrchestrator
from warehouse_routing.core.grid import WarehouseGrid

# Instâncias globais gerenciadas no ciclo de vida
orchestrator: FleetOrchestrator = None  # type: ignore
ws_hub: WebSocketTelemetryHub = None  # type: ignore
simulation_task: asyncio.Task = None  # type: ignore


async def simulation_loop() -> None:
    """
    Loop assíncrono em background que executa os passos da simulação física
    e transmite os deltas de telemetria via WebSocket a 20 Hz (a cada 50ms).
    """
    logger.info("Simulation Loop iniciado em background.")
    try:
        while True:
            if orchestrator and not orchestrator.is_paused:
                orchestrator.step()
                if ws_hub and ws_hub.active_connections:
                    payload = orchestrator.get_telemetry_payload()
                    await ws_hub.broadcast(payload)

            # Intervalo suave para percepção humana e interpolação fluida (0.45s por tick)
            speed = orchestrator.simulation_speed if orchestrator else 1.0
            delay = max(0.1, 0.45 / speed)
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        logger.info("Simulation Loop cancelado com sucesso.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Ciclo de vida do FastAPI: inicializa o motor de robótica e a simulação."""
    global orchestrator, ws_hub, simulation_task

    logger.info("Inicializando NexusFleet AMR Orchestrator...")
    grid = WarehouseGrid.create_preset_mega_hub()
    orchestrator = FleetOrchestrator(grid=grid, num_amrs=8)
    ws_hub = WebSocketTelemetryHub(orchestrator=orchestrator)

    # Injeta a referência única do orquestrador nos módulos
    set_layout_orch(orchestrator)
    set_analytics_orch(orchestrator)
    set_fleet_orch(orchestrator)
    set_tools_orch(orchestrator)
    set_guardrails_orch(orchestrator)
    set_chaos_orch(orchestrator)

    # Dispara a simulação contínua
    simulation_task = asyncio.create_task(simulation_loop())

    yield

    # Encerramento suave
    logger.info("Encerrando NexusFleet AMR Orchestrator...")
    if simulation_task:
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass


# Instância principal do FastAPI (com docs_url=None para obrigar o uso do Scalar)
app = FastAPI(
    title="NexusFleet AMR Orchestrator",
    description="Plataforma de Coordenação de Robôs Móveis Autônomos com Space-Time MAPF, Digital Twin e Copiloto de IA.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,  # Desativa Swagger tradicional
    redoc_url=None,
)

# Configuração de CORS permissivo para dev e produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração da documentação viva em Scalar
setup_scalar_docs(app)

# Registro dos Routers da API
app.include_router(layout_router)
app.include_router(analytics_router)
app.include_router(fleet_router)
app.include_router(chaos_router)
app.include_router(copilot_router)


@app.get("/health", tags=["System"])
def health_check():
    """Endpoint de verificação de integridade do container."""
    return {
        "status": "healthy",
        "service": "NexusFleet AMR Engine",
        "version": "2.0.0",
        "amrs_active": len(orchestrator.amrs) if orchestrator else 0,
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """Canal WebSocket de telemetria da frota e recebimento de comandos do frontend."""
    if ws_hub is None:
        await websocket.close(code=1013)
        return

    await ws_hub.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_hub.handle_client_message(websocket, data)
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")
        ws_hub.disconnect(websocket)


# Montagem dos arquivos estáticos do frontend (se compilados)
frontend_dist = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "frontend", "dist"
)
if os.path.exists(frontend_dist):
    logger.info(f"Montando arquivos estáticos do frontend a partir de: {frontend_dist}")
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
