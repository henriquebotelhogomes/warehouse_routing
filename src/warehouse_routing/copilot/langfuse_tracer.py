import os
import time
from typing import Any, Dict, Optional

from loguru import logger

try:
    from langfuse import Langfuse

    langfuse_client: Any = None
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        langfuse_client = Langfuse()
        logger.info("Langfuse Observability inicializado com sucesso.")
except ImportError:
    langfuse_client = None


class CopilotTraceSession:
    """
    Rastreador de sessão do Copiloto de IA para métricas de FinOps,
    latência e assertividade de Tool Calling.
    """

    def __init__(self, user_query: str, session_id: Optional[str] = None):
        self.user_query = user_query
        self.session_id = session_id or f"sess_{int(time.time())}"
        self.start_time = time.perf_counter()
        self.trace: Any = None

        if langfuse_client:
            try:
                self.trace = langfuse_client.trace(
                    name="copilot_chat_turn",
                    session_id=self.session_id,
                    input=user_query,
                    tags=["nexusfleet", "warehouse-amr"],
                )
            except Exception as e:
                logger.debug(f"Langfuse trace init omitido: {e}")

    def log_tool_call(self, tool_name: str, tool_args: Dict[str, Any], tool_output: Any) -> None:
        """Registra a execução de uma ferramenta determinística."""
        if self.trace:
            try:
                self.trace.span(
                    name=f"tool_{tool_name}",
                    input=tool_args,
                    output=str(tool_output),
                )
            except Exception as e:
                logger.debug(f"Langfuse span error: {e}")

    def end_trace(self, output: str, model: str = "gemini-3.8-flash") -> None:
        """Finaliza o trace computando a latência total."""
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        logger.info(f"Copiloto processou query em {duration_ms:.2f}ms (Modelo: {model})")

        if self.trace:
            try:
                self.trace.update(
                    output=output,
                    metadata={"duration_ms": duration_ms, "model": model},
                )
            except Exception as e:
                logger.debug(f"Langfuse update error: {e}")
