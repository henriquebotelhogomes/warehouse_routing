from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from warehouse_routing.copilot.agent import (
    CopilotMessage,
    CopilotResponse,
    copilot_agent,
)
from warehouse_routing.copilot.guardrails import hitl_manager

router = APIRouter(prefix="/api/v1/copilot", tags=["Copilot & IA Agêntica"])


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[CopilotMessage]] = None


class HITLConfirmRequest(BaseModel):
    action_token: str


class HITLConfirmResponse(BaseModel):
    success: bool
    message: str


@router.post("/chat", response_model=CopilotResponse)
def copilot_chat(request: ChatRequest) -> CopilotResponse:
    """
    Endpoint de chat operacional do Copiloto de IA.
    Suporta Tool Calling determinístico para controle da frota e guardrails HITL.
    """
    return copilot_agent.chat(user_query=request.message, history=request.history)


@router.post("/actions/confirm", response_model=HITLConfirmResponse)
def confirm_hitl_action(request: HITLConfirmRequest) -> HITLConfirmResponse:
    """
    Confirma e executa uma ação de alto risco (ex: parada de emergência)
    aprovada conscientemente pelo operador humano (Human-In-The-Loop).
    """
    success, message = hitl_manager.confirm_action(request.action_token)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return HITLConfirmResponse(success=success, message=message)
