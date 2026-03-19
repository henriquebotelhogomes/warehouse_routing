from __future__ import annotations

import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, AsyncGenerator

from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger

# ✅ Importação condicional para evitar ImportError em runtime (Docker/Produção)
if TYPE_CHECKING:
    from loguru import Record

from warehouse_routing.api.schemas import PathUpdateRequest, RouteRequest, RouteResponse
from warehouse_routing.core.config import BASE_REWARDS_MATRIX, LOCATIONS, settings
from warehouse_routing.core.q_learning import WarehouseRouteOptimizer
from warehouse_routing.core.visualizer import WarehouseVisualizer

# =============================================================================
# CONFIGURAÇÃO DE LOGS (LOGURU + CORRELATION ID)
# =============================================================================
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "[ID: {extra[request_id]}] - <level>{message}</level>"
)

logger.remove()
logger.add(sys.stdout, format=LOG_FORMAT, level="INFO")


def inject_correlation_id(record: Record) -> None:
    """Injeta o ID de correlação em cada linha de log para rastreabilidade total."""
    record["extra"]["request_id"] = correlation_id.get() or "system"


logger.configure(patcher=inject_correlation_id)

# =============================================================================
# INICIALIZAÇÃO DOS COMPONENTES CORE
# =============================================================================
optimizer = WarehouseRouteOptimizer(
    locations=LOCATIONS,
    rewards_matrix=BASE_REWARDS_MATRIX,
    gamma=settings.gamma,
    alpha=settings.alpha,
)

visualizer = WarehouseVisualizer()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gerencia o startup e shutdown da API de forma resiliente."""
    logger.info("🚀 Iniciando API Warehouse Optimizer...")

    # ✅ Uso de Pathlib para evitar WinError 3 no Windows
    model_path = Path(settings.model_save_path)
    if model_path.parent != Path("."):
        model_path.parent.mkdir(parents=True, exist_ok=True)

    # Tenta carregar o modelo persistido (Cold Start Resilience)
    if model_path.exists():
        try:
            optimizer.load_model(str(model_path))
            logger.info(f"📂 Modelo de IA carregado com sucesso de: {model_path}")
        except Exception as e:
            logger.error(f"❌ Falha ao carregar modelo existente: {e}")
    else:
        logger.warning(f"⚠️ Modelo não encontrado em {model_path}. Iniciando do zero.")

    yield

    # Persiste o conhecimento acumulado ao desligar
    try:
        optimizer.save_model(str(model_path))
        logger.info("💾 Estado da Q-Table persistido com sucesso antes do shutdown.")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar modelo no shutdown: {e}")


# =============================================================================
# CONFIGURAÇÃO DO APP FASTAPI
# =============================================================================
app = FastAPI(
    title="AI Warehouse Optimizer",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware de performance para medir latência de processamento."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000, 2))
    return response


# =============================================================================
# ENDPOINTS DA API
# =============================================================================


@app.post("/api/v1/routes", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """Calcula a rota ótima usando a lógica do Optimizer."""
    logger.info(f"Calculando rota: {request.start} -> {request.end}")

    try:
        if request.intermediary:
            route = optimizer.get_route_with_intermediary(
                request.start, request.intermediary, request.end
            )
        else:
            route = optimizer.get_route(request.start, request.end)

        return RouteResponse(route=route, total_steps=len(route))
    except ValueError as e:
        logger.warning(f"Requisição inválida: {e}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})


@app.get("/api/v1/visualize/graph")
async def get_graph():
    """Retorna a imagem da topologia do armazém."""
    img_bytes = visualizer.get_graph_image(BASE_REWARDS_MATRIX, LOCATIONS)
    return StreamingResponse(img_bytes, media_type="image/png")


@app.get("/api/v1/visualize/q-table/{target}")
async def get_q_table_heatmap(target: str):
    """Gera um heatmap da Q-Table para um destino específico."""
    try:
        q_table = optimizer.train(target)
        img_bytes = visualizer.get_q_table_image(
            q_table, LOCATIONS, f"Q-Table para Destino: {target}"
        )
        return StreamingResponse(img_bytes, media_type="image/png")
    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})


@app.patch("/api/v1/warehouse/path")
async def update_path(request: PathUpdateRequest):
    """Permite bloquear ou liberar corredores dinamicamente."""
    optimizer.update_path(request.location_a, request.location_b, request.is_open)
    logger.info(f"Caminho {request.location_a}-{request.location_b} atualizado.")
    return {"message": "Topologia atualizada com sucesso."}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}
