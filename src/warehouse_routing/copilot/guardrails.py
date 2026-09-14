import time
import uuid
from typing import Any, Dict, Tuple

from loguru import logger
from pydantic import BaseModel

_orchestrator_ref: Any = None


def set_orchestrator_instance(orch: Any) -> None:
    global _orchestrator_ref
    _orchestrator_ref = orch


class PendingHITLAction(BaseModel):
    action_token: str
    action_type: str
    parameters: Dict[str, Any]
    description: str
    warning_message: str
    created_at: float
    expires_at: float


class HITLManager:
    """
    Gerenciador de Ações Críticas e Segurança com Human-in-the-Loop (ISO 3691-4).
    Exige confirmação manual do operador antes de executar ações de alto risco.
    """

    def __init__(self, token_ttl_seconds: int = 120):
        self.ttl = token_ttl_seconds
        self.pending_actions: Dict[str, PendingHITLAction] = {}

    def create_action(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        description: str,
        warning_message: str,
    ) -> PendingHITLAction:
        """Registra uma ação crítica aguardando aprovação humana."""
        token = f"hitl_{uuid.uuid4().hex[:8]}"
        now = time.time()
        action = PendingHITLAction(
            action_token=token,
            action_type=action_type,
            parameters=parameters,
            description=description,
            warning_message=warning_message,
            created_at=now,
            expires_at=now + self.ttl,
        )
        self.pending_actions[token] = action
        logger.warning(f"Ação HITL criada: {token} - {action_type} - {description}")
        return action

    def confirm_action(self, token: str) -> Tuple[bool, str]:
        """Executa a ação pendente após confirmação do operador."""
        self._cleanup_expired()

        action = self.pending_actions.pop(token, None)
        if not action:
            return False, "Token de confirmação inválido ou expirado."

        if action.action_type == "EMERGENCY_STOP":
            if _orchestrator_ref is not None:
                activate = action.parameters.get("activate", True)
                _orchestrator_ref.emergency_stop(activate)
                status_str = "ATIVADA" if activate else "DESATIVADA"
                return (
                    True,
                    f"Parada de emergência da frota {status_str} com sucesso pelo operador.",
                )

        return False, f"Tipo de ação desconhecido: {action.action_type}"

    def _cleanup_expired(self) -> None:
        """Remove tokens expirados."""
        now = time.time()
        expired = [t for t, a in self.pending_actions.items() if a.expires_at < now]
        for t in expired:
            del self.pending_actions[t]


hitl_manager = HITLManager()
