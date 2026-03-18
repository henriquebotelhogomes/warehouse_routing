import sys
import time
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from loguru import logger

from warehouse_routing.core.config import settings, LOCATIONS, BASE_REWARDS_MATRIX
from warehouse_routing.core.q_learning import WarehouseRouteOptimizer
from warehouse_routing.core.visualizer import WarehouseVisualizer
from warehouse_routing.api.schemas import RouteRequest, RouteResponse, PathUpdateRequest

# =============================================================================
# CONFIGURAÇÃO DE LOGS E OBSERVABILIDADE (PADRÃO SÊNIOR)
# =============================================================================
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | [ID: {extra[request_id]}] - <level>{message}</level>",
    colorize=True,
)


def inject_correlation_id(record) -> None:
    """Injeta o ID de correlação em cada linha de log para rastreabilidade total."""
    record["extra"]["request_id"] = correlation_id.get() or "system"


# Configuração do Loguru com patcher para ID de correlação
logger.configure(patcher=inject_correlation_id)

# Instância global do motor de IA (Singleton na prática da API)
optimizer = WarehouseRouteOptimizer(
    locations=LOCATIONS,
    rewards_matrix=BASE_REWARDS_MATRIX,
    gamma=settings.gamma,
    alpha=settings.alpha,
)


# =============================================================================
# LIFESPAN (Gerenciamento de Ciclo de Vida do App - RESILIENTE)
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o startup e shutdown de forma resiliente para produção.
    Evita que a API quebre se o arquivo de modelo não existir no primeiro deploy.
    """
    logger.info("🚀 Iniciando API...")

    # Verifica se o diretório de dados existe, se não, cria
    os.makedirs(os.path.dirname(settings.model_save_path), exist_ok=True)

    # Tenta carregar o modelo persistido
    if os.path.exists(settings.model_save_path):
        try:
            logger.info(f"📂 Carregando inteligência da IA de: {settings.model_save_path}")
            optimizer.load_model(settings.model_save_path)
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}. A IA iniciará sem cache.")
    else:
        logger.warning(
            f"⚠️ Modelo não encontrado em {settings.model_save_path}. Iniciando treinamento sob demanda."
        )

    yield

    # No shutdown, persiste o conhecimento adquirido
    try:
        logger.info(f"💾 Encerrando API e persistindo conhecimento em: {settings.model_save_path}")
        optimizer.save_model(settings.model_save_path)
    except Exception as e:
        logger.error(f"❌ Erro ao salvar modelo no shutdown: {e}")


# Inicialização do App FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API de Otimização de Rotas Logísticas usando Q-Learning",
    version="1.0.0",
    lifespan=lifespan,
)

# =============================================================================
# MIDDLEWARES (Segurança e Performance)
# =============================================================================

# 1. Configuração de CORS para Produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rastreabilidade de requisições (Correlation ID)
app.add_middleware(CorrelationIdMiddleware)


# 3. Middleware de Performance (Métrica de latência)
@app.middleware("http")
async def perf_middleware(request: Request, call_next) -> Response:
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000

    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    logger.info(f"{request.method} {request.url.path} concluído em {process_time:.2f}ms")
    return response


# =============================================================================
# HANDLERS GLOBAIS DE EXCEÇÃO
# =============================================================================


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError) -> Response:
    """Captura erros de validação de locais e converte em HTTP 400."""
    logger.warning(f"Erro de validação de negócio: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


# =============================================================================
# ENDPOINTS (INTERFACE DE COMUNICAÇÃO)
# =============================================================================


@app.post("/api/v1/routes", response_model=RouteResponse, tags=["Rotas"])
async def get_route(req: RouteRequest) -> RouteResponse:
    """Calcula a rota ótima entre dois pontos."""
    if req.intermediary:
        route = optimizer.get_route_with_intermediary(req.start, req.intermediary, req.end)
    else:
        route = optimizer.get_route(req.start, req.end)

    return RouteResponse(route=route, total_steps=len(route) - 1)


@app.put("/api/v1/warehouse/paths", tags=["Configuração"])
async def update_path(req: PathUpdateRequest) -> dict:
    """Bloqueia ou libera caminhos no armazém dinamicamente."""
    optimizer.update_path(req.location_a, req.location_b, req.is_open)
    optimizer.save_model(settings.model_save_path)
    return {"message": f"Conexão entre {req.location_a} e {req.location_b} atualizada."}


@app.get("/api/v1/visualize/graph", tags=["Visualização"])
async def view_graph() -> StreamingResponse:
    """Retorna a imagem PNG da topologia atual do armazém."""
    img_buffer = WarehouseVisualizer.get_graph_image(optimizer.rewards_matrix, LOCATIONS)
    return StreamingResponse(img_buffer, media_type="image/png")


@app.get("/api/v1/visualize/q-table/{target}", tags=["Visualização"])
async def view_q_table(target: str) -> StreamingResponse:
    """Gera um Heatmap da inteligência da IA para um destino específico."""
    q_table = optimizer.train(target.upper())
    img_buffer = WarehouseVisualizer.get_q_table_image(
        q_table, LOCATIONS, title=f"Inteligência IA - Destino: {target.upper()}"
    )
    return StreamingResponse(img_buffer, media_type="image/png")


@app.post("/api/v1/ai/retrain", tags=["IA Admin"])
async def force_ai_retrain() -> dict:
    """Limpa o cache e força o retreino de todos os locais."""
    logger.warning("Solicitado retreino total da inteligência...")
    optimizer._q_table_cache.clear()
    for loc in LOCATIONS:
        optimizer.train(loc, force_retrain=True)
    optimizer.save_model(settings.model_save_path)
    return {"message": "IA retreinada com sucesso para todos os locais."}
