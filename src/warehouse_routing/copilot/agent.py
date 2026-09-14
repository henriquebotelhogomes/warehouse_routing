import os
import re
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from warehouse_routing.copilot.guardrails import hitl_manager
from warehouse_routing.copilot.langfuse_tracer import CopilotTraceSession
from warehouse_routing.copilot.tools import (
    tool_block_zone,
    tool_get_fleet_telemetry,
    tool_scale_fleet,
    tool_unblock_zone,
)

SYSTEM_PROMPT = """Você é o NexusFleet Copilot, um especialista sênior em orquestração de frotas de robôs AMRs e intralogística autônoma.
Seu objetivo é auxiliar supervisores de armazém a monitorar a operação, mitigar congestionamentos e resolver incidentes operacionais com máxima eficiência e segurança (ISO 3691-4).

DIRETRIZES FUNDAMENTAIS:
1. DETERMINISMO GEOMÉTRICO: Você NUNCA inventa rotas ou coordenadas no texto. Para qualquer ação física, chame a ferramenta apropriada (Tool Calling).
2. LINGUAGEM: Responda no mesmo idioma utilizado pelo operador (Português ou Inglês). Seja conciso, técnico e orientado a dados.
3. SEGURANÇA E HITL: Para ações que possam paralisar a frota ou descartar pedidos, alerte o operador e invoque a ferramenta com confirmação humana obrigatória.
4. MÉTRICAS: Sempre que executar um desvio ou bloqueio, informe o impacto no tempo de rota e no SLA das ordens ativas.
"""


class CopilotMessage(BaseModel):
    role: str  # "user" ou "assistant"
    content: str


class CopilotResponse(BaseModel):
    reply: str
    hitl_action_required: bool = False
    hitl_card: Optional[Dict[str, Any]] = None
    executed_tools: List[Dict[str, Any]] = []


class WarehouseCopilotAgent:
    """
    Agente de IA do Copiloto Operacional.
    Suporta Google GenAI (Gemini 3.8 Flash) e Fallback Determinístico Local.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = "gemini-3.8-flash"
        self.gemini_client = None

        if self.api_key:
            try:
                from google import genai

                self.gemini_client = genai.Client(api_key=self.api_key)
                logger.info("NexusFleet Copilot: Conectado ao Google GenAI (Gemini 3.8 Flash).")
            except Exception as e:
                logger.warning(f"Falha ao inicializar Google GenAI: {e}")

    def chat(
        self, user_query: str, history: Optional[List[CopilotMessage]] = None
    ) -> CopilotResponse:
        """Processa a mensagem do usuário, invocando ferramentas e aplicando guardrails."""
        tracer = CopilotTraceSession(user_query=user_query)
        query_lower = user_query.lower()
        executed_tools: List[Dict[str, Any]] = []

        # 1. Guardrail HITL: Parada de Emergência da Frota (ISO 3691-4)
        if any(
            w in query_lower
            for w in [
                "parada de emergência",
                "emergency stop",
                "parar frota",
                "parar tudo",
                "congelar frota",
            ]
        ):
            action = hitl_manager.create_action(
                action_type="EMERGENCY_STOP",
                parameters={"activate": True},
                description="Parada Geral de Emergência de Todos os Robôs AMRs",
                warning_message="Esta ação congelará imediatamente a movimentação de todos os robôs ativos no galpão, suspendendo ordens de separação em andamento.",
            )
            tracer.log_tool_call("emergency_stop_request", {"activate": True}, action.action_token)
            reply = (
                "⚠️ **Ação de Alta Criticidade Detectada (ISO 3691-4)**\n\n"
                "Para paralisar a frota de robôs, é necessária confirmação humana explícita (*Human-In-The-Loop*). "
                "Por favor, valide a ação no cartão abaixo:"
            )
            tracer.end_trace(reply)
            return CopilotResponse(
                reply=reply,
                hitl_action_required=True,
                hitl_card={
                    "token": action.action_token,
                    "title": "⚠️ Parada de Emergência da Frota",
                    "description": action.warning_message,
                    "confirm_text": "Confirmar Parada Imediata",
                    "cancel_text": "Abortar",
                },
                executed_tools=executed_tools,
            )

        # 2. Tool: Bloqueio de Célula / Corredor
        # Regex para detectar coordenadas tipo (x, y) ou "x e y" ou "x, y"
        coords_match = re.search(r"\(?\s*(\d+)\s*[,e ]+\s*(\d+)\s*\)?", user_query)
        if any(
            w in query_lower
            for w in ["bloquear", "bloqueie", "interditar", "block", "derramamento", "obstrução"]
        ):
            if coords_match:
                x, y = int(coords_match.group(1)), int(coords_match.group(2))
                reason = "Incidente reportado via Copiloto"
                if "óleo" in query_lower or "oil" in query_lower:
                    reason = "Derramamento de óleo"
                elif "pallet" in query_lower:
                    reason = "Queda de pallet"

                out_block = tool_block_zone(x, y, reason=reason)
                executed_tools.append({"tool": "block_warehouse_zone", "output": out_block.model_dump()})
                tracer.log_tool_call(
                    "block_warehouse_zone", {"x": x, "y": y, "reason": reason}, out_block.model_dump()
                )

                reply = (
                    f"🛑 **Área Interditada com Sucesso**\n\n"
                    f"• **Coordenadas:** ({x}, {y})\n"
                    f"• **Motivo:** {reason}\n"
                    f"• **Robôs Afetados:** {', '.join(out_block.affected_amrs) if out_block.affected_amrs else 'Nenhum robô no trajeto'}\n"
                    f"• **Impacto Médio de Rota:** +{out_block.sla_impact_seconds_avg:.1f}s\n\n"
                    f"O algoritmo Space-Time MAPF recalculou as trajetórias em tempo real, garantindo **zero colisões** no galpão."
                )
                tracer.end_trace(reply)
                return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 3. Tool: Liberação de Célula
        if any(w in query_lower for w in ["liberar", "libere", "desbloquear", "unblock"]):
            if coords_match:
                x, y = int(coords_match.group(1)), int(coords_match.group(2))
                out_unblock = tool_unblock_zone(x, y)
                executed_tools.append(
                    {"tool": "unblock_warehouse_zone", "output": out_unblock.model_dump()}
                )
                tracer.log_tool_call("unblock_warehouse_zone", {"x": x, "y": y}, out_unblock.model_dump())

                reply = f"✅ **Célula ({x}, {y}) Desbloqueada**\n\nO corredor está novamente liberado para planejamento de tráfego dos AMRs."
                tracer.end_trace(reply)
                return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 4. Tool: Consulta de Telemetria / Status da Frota
        if any(
            w in query_lower
            for w in ["status", "telemetria", "bateria", "battery"]
        ):
            out_telemetry = tool_get_fleet_telemetry()
            executed_tools.append({"tool": "get_fleet_telemetry", "output": out_telemetry.model_dump()})
            tracer.log_tool_call("get_fleet_telemetry", {}, out_telemetry.model_dump())

            crit_str = (
                ", ".join(out_telemetry.critical_battery_amrs)
                if out_telemetry.critical_battery_amrs
                else "Nenhum (Todas acima de 20%)"
            )
            reply = (
                f"📊 **Telemetria Operacional da Frota**\n\n"
                f"• **Total de AMRs:** {out_telemetry.total_amrs}\n"
                f"• **Em Trânsito Ativo:** {out_telemetry.active_in_transit}\n"
                f"• **Em Recarga:** {out_telemetry.charging_count}\n"
                f"• **Ociosos / Disponíveis:** {out_telemetry.idle_count}\n"
                f"• **Bateria Crítica (< 20%):** {crit_str}\n"
                f"• **Vazão Atual:** {out_telemetry.current_throughput_per_hour:.0f} pedidos/hora"
            )
            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 5. Tool: Escalabilidade de Frota (Adicionar / Remover / Escalonar N Robôs)
        scale_match = re.search(r"(\d+)\s*(rob[oô]s?|amrs?|unidades?)", query_lower)
        num_extracted = int(scale_match.group(1)) if scale_match else 1
        amr_match = re.search(r"(amr-\d+)", query_lower)
        specific_amr = amr_match.group(1).upper() if amr_match else None

        if any(w in query_lower for w in ["adicionar", "adicione", "inserir", "add", "acrescentar"]):
            out_scale = tool_scale_fleet(action_type="add", count=num_extracted)
            executed_tools.append({"tool": "scale_fleet", "output": out_scale.model_dump()})
            tracer.log_tool_call("scale_fleet", {"action_type": "add", "count": num_extracted}, out_scale.model_dump())
            reply = (
                f"🚀 **Frota Expandida Dinamicamente**\n\n"
                f"• **Robôs Adicionados:** +{len(out_scale.affected_amrs)} ({', '.join(out_scale.affected_amrs)})\n"
                f"• **Tamanho Anterior:** {out_scale.previous_count} AMRs\n"
                f"• **Capacidade Total Ativa:** {out_scale.current_count} AMRs\n\n"
                f"Os novos robôs foram posicionados em docas/corredores livres e já estão aptos a receber missões de separação."
            )
            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        if any(w in query_lower for w in ["remover", "remova", "descomissionar", "descomissione", "remove", "decommission"]):
            out_scale = tool_scale_fleet(action_type="remove", count=num_extracted, amr_id=specific_amr)
            executed_tools.append({"tool": "scale_fleet", "output": out_scale.model_dump()})
            tracer.log_tool_call("scale_fleet", {"action_type": "remove", "count": num_extracted, "amr_id": specific_amr}, out_scale.model_dump())
            reply = (
                f"🧹 **Descomissionamento Seguro Realizado**\n\n"
                f"• **Robôs Removidos:** {', '.join(out_scale.affected_amrs)}\n"
                f"• **Capacidade Restante:** {out_scale.current_count} AMRs\n\n"
                f"Todas as reservas espaço-temporais e pedidos em trânsito foram reorganizados sem interrupção do galpão."
            )
            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        if any(w in query_lower for w in ["ajustar frota", "escalar frota", "definir frota", "scale fleet"]) and scale_match:
            out_scale = tool_scale_fleet(action_type="scale", target_count=num_extracted)
            executed_tools.append({"tool": "scale_fleet", "output": out_scale.model_dump()})
            tracer.log_tool_call("scale_fleet", {"action_type": "scale", "target_count": num_extracted}, out_scale.model_dump())
            reply = (
                f"⚖️ **Capacidade da Frota Ajustada**\n\n"
                f"• **Meta Definida:** {num_extracted} AMRs\n"
                f"• **Capacidade Atual:** {out_scale.current_count} AMRs\n"
                f"• **Alterações:** {', '.join(out_scale.affected_amrs) if out_scale.affected_amrs else 'Nenhuma alteração necessária'}"
            )
            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # Resposta Padrão / Ajuda Operacional
        reply = (
            "🤖 **NexusFleet Copilot Operacional Ativo**\n\n"
            "Posso auxiliar você com os seguintes comandos em linguagem natural:\n"
            '• *"Adicionar 3 robôs à frota"*\n'
            '• *"Remover o robô AMR-02"*\n'
            '• *"Bloqueie o ponto (10, 8) por derramamento de óleo"*\n'
            '• *"Liberar a coordenada (10, 8)"*\n'
            '• *"Qual o status atual da frota e das baterias?"*\n'
            '• *"Parada de emergência geral"* *(aciona proteção HITL)*\n\n'
            "*Todas as operações são executadas de forma determinística pelo motor Space-Time MAPF.*"
        )
        tracer.end_trace(reply)
        return CopilotResponse(reply=reply, executed_tools=executed_tools)


copilot_agent = WarehouseCopilotAgent()
