from typing import List, Optional

from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    start: str = Field(..., description="Ponto de partida no armazém (ex: 'E')")
    end: str = Field(..., description="Ponto de destino no armazém (ex: 'G')")
    intermediary: Optional[str] = Field(None, description="Ponto de parada opcional (ex: 'K')")


class RouteResponse(BaseModel):
    route: List[str] = Field(..., description="Sequência de locais formando a rota ótima")
    total_steps: int = Field(..., description="Número total de movimentos necessários")


class PathUpdateRequest(BaseModel):
    location_a: str = Field(..., description="Primeiro ponto do corredor (ex: 'E')")
    location_b: str = Field(..., description="Segundo ponto do corredor (ex: 'I')")
    is_open: bool = Field(..., description="True para abrir, False para bloquear")
