import os
import socket
import sys

import uvicorn
from loguru import logger

# Garante UTF-8 no console do Windows para emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# Garante que a pasta src está no sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Verifica se uma porta já está ocupada por outro processo."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def find_available_port(preferred_port: int = 8080) -> int:
    """Retorna a porta preferencial ou uma alternativa livre (8080, 8001, etc.)."""
    if not is_port_in_use(preferred_port):
        return preferred_port

    logger.warning(f"Porta {preferred_port} já está em uso por outro processo.")
    for alt in [8080, 8081, 8001, 8002]:
        if not is_port_in_use(alt):
            logger.info(f"Porta alternativa disponível selecionada: {alt}")
            return alt

    return preferred_port


def main() -> None:
    port = find_available_port(preferred_port=8080)

    print("\n" + "=" * 60)
    print("      🚀 NEXUSFLEET AMR ORCHESTRATOR & DIGITAL TWIN v2.0")
    print("=" * 60)
    print(f"  🎮 Plataforma / Digital Twin: http://localhost:{port}")
    print(f"  📑 Scalar API Docs:          http://localhost:{port}/docs")
    print(f"  ⚡ WebSocket Telemetry:       ws://localhost:{port}/ws/telemetry")
    print("=" * 60 + "\n")

    uvicorn.run(
        "warehouse_routing.api.main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
