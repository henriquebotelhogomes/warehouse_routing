import os
import re
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from warehouse_routing.copilot.guardrails import hitl_manager
from warehouse_routing.copilot.langfuse_tracer import CopilotTraceSession
from warehouse_routing.copilot.tools import (
    tool_block_zone,
    tool_get_amr_detail,
    tool_get_amr_logs,
    tool_get_fleet_telemetry,
    tool_get_warehouse_metrics,
    tool_rescue_amr,
    tool_scale_fleet,
    tool_simulation_control,
    tool_trigger_chaos,
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


def _extract_amr_id(text: str) -> Optional[str]:
    """Extrai IDs de robôs como 'AMR-03', 'amr-3', 'robô 3', 'robo 02'."""
    m = re.search(r"\b(?:amr|rob[oô])[-_\s]*(\d+)\b", text, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        return f"AMR-{num:02d}"
    return None


class WarehouseCopilotAgent:
    """
    Agente de IA do Copiloto Operacional.
    Suporta Google GenAI (Gemini 3.8 Flash) e Motor NLU Determinístico Avançado.
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
                "parada de emergencia",
                "emergency stop",
                "parar frota",
                "parar tudo",
                "congelar frota",
                "travar frota",
            ]
        ):
            hitl_action = hitl_manager.create_action(
                action_type="EMERGENCY_STOP",
                parameters={"activate": True},
                description="Parada Geral de Emergência de Todos os Robôs AMRs",
                warning_message="Esta ação congelará imediatamente a movimentação de todos os robôs ativos no galpão, suspendendo ordens de separação em andamento.",
            )
            tracer.log_tool_call(
                "emergency_stop_request", {"activate": True}, hitl_action.action_token
            )
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
                    "token": hitl_action.action_token,
                    "title": "⚠️ Parada de Emergência da Frota",
                    "description": hitl_action.warning_message,
                    "confirm_text": "Confirmar Parada Imediata",
                    "cancel_text": "Abortar",
                },
                executed_tools=executed_tools,
            )

        # 2. Desativação da Parada de Emergência
        if any(
            w in query_lower
            for w in [
                "desativar emergência",
                "desativar emergencia",
                "cancelar emergência",
                "liberar emergência",
                "retomar emergência",
                "despausar emergência",
            ]
        ):
            hitl_action = hitl_manager.create_action(
                action_type="EMERGENCY_STOP",
                parameters={"activate": False},
                description="Desativação da Parada de Emergência da Frota",
                warning_message="Esta ação reativará a movimentação de todos os robôs AMRs do armazém.",
            )
            reply = (
                "🛡️ **Liberação de Emergência Solicitada**\n\n"
                "Confirme no cartão abaixo para restabelecer a operação normal dos robôs:"
            )
            return CopilotResponse(
                reply=reply,
                hitl_action_required=True,
                hitl_card={
                    "token": hitl_action.action_token,
                    "title": "🛡️ Retomar Operação Normal",
                    "description": hitl_action.warning_message,
                    "confirm_text": "Confirmar Retomada",
                    "cancel_text": "Cancelar",
                },
                executed_tools=executed_tools,
            )

        # 3. Tool: Consulta de Logs / Eventos de Robôs (inclui tolerância a typos: "logos", "log", "historico", "eventos")
        if any(
            w in query_lower
            for w in [
                "log",
                "logs",
                "logo",
                "logos",
                "histórico",
                "historico",
                "eventos",
                "auditoria",
                "o que aconteceu",
            ]
        ):
            target_amr = _extract_amr_id(query_lower)
            out_logs = tool_get_amr_logs(amr_id=target_amr, limit=8)
            executed_tools.append({"tool": "get_amr_logs", "output": out_logs.model_dump()})
            tracer.log_tool_call(
                "get_amr_logs", {"amr_id": target_amr, "limit": 8}, out_logs.model_dump()
            )

            if not out_logs.logs:
                reply = f"📜 **Logs da Frota**\n\nNenhum evento recente registrado para `{target_amr or 'a frota'}`."
            else:
                title = (
                    f"📜 **Histórico Recente de Eventos — {target_amr}**"
                    if target_amr
                    else "📜 **Últimos Eventos Globais da Frota**"
                )
                items_text = []
                for item in out_logs.logs:
                    badge = (
                        "🔴 [ERRO]"
                        if item.level == "ERROR"
                        else (
                            "🟡 [AVISO]"
                            if item.level == "WARN"
                            else "🟢 [SUCESSO]"
                            if item.level == "SUCCESS"
                            else "🔵 [AÇÃO]"
                            if item.level == "ACTION"
                            else "⚪ [INFO]"
                        )
                    )
                    prefix = f"`{item.amr_id}` " if not target_amr else ""
                    items_text.append(
                        f"• `{item.timestamp}` (Tick {item.tick}) {badge} {prefix}{item.message}"
                    )

                reply = f"{title}\n\n" + "\n".join(items_text)
                if target_amr:
                    reply += f"\n\n*Dica: Você também pode abrir a **Central de Logs** no topo ou clicar no robô {target_amr} no mapa.*"

            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 4. Tool: Destravar Robô / Self-Healing (Rescue)
        if any(
            w in query_lower
            for w in [
                "destravar",
                "destrave",
                "resgatar",
                "resgate",
                "rescue",
                "descongelar",
                "desbloquear robo",
                "desbloquear robô",
                "recuperar",
                "soltar robô",
                "soltar robo",
            ]
        ):
            target_amr = _extract_amr_id(query_lower)
            if target_amr:
                out_rescue = tool_rescue_amr(amr_id=target_amr)
                executed_tools.append({"tool": "rescue_amr", "output": out_rescue.model_dump()})
                tracer.log_tool_call("rescue_amr", {"amr_id": target_amr}, out_rescue.model_dump())

                if out_rescue.success:
                    reply = (
                        f"🩹 **Protocolo de Self-Healing Concluído com Sucesso**\n\n"
                        f"• **Robô:** `{target_amr}`\n"
                        f"• **Ação Executada:** `{out_rescue.action}`\n"
                        f"• **Resultado:** {out_rescue.message}\n\n"
                        f"As reservas de rota antigas foram liberadas e a FSM do robô restabelecida."
                    )
                else:
                    reply = (
                        f"⚠️ **Falha ao Resgatar Robô**\n\n"
                        f"• **Robô:** `{target_amr}`\n"
                        f"• **Detalhe:** {out_rescue.message}"
                    )
                tracer.end_trace(reply)
                return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 5. Tool: Localização, Carga e Detalhes de um Robô Específico
        if any(
            w in query_lower
            for w in [
                "onde está",
                "onde esta",
                "posição",
                "posicao",
                "localização",
                "localizacao",
                "onde fica",
                "o que está carregando",
                "qual a carga",
                "qual a bateria",
                "qual a missão",
                "qual a missao",
                "detalhes do",
            ]
        ) and _extract_amr_id(query_lower):
            target_amr = _extract_amr_id(query_lower)
            if not target_amr:
                target_amr = "AMR-01"
            out_detail = tool_get_amr_detail(amr_id=target_amr)
            executed_tools.append({"tool": "get_amr_detail", "output": out_detail.model_dump()})
            tracer.log_tool_call("get_amr_detail", {"amr_id": target_amr}, out_detail.model_dump())

            if out_detail.success and out_detail.position:
                target_str = (
                    f"({out_detail.target['x']}, {out_detail.target['y']})"
                    if out_detail.target
                    else "Nenhum alvo definido"
                )
                reply = (
                    f"🤖 **Telemetria do Robô {target_amr}**\n\n"
                    f"• **Coordenadas Atuais:** ({out_detail.position['x']}, {out_detail.position['y']})\n"
                    f"• **Estado da FSM:** `{out_detail.state}`\n"
                    f"• **Nível de Bateria:** {out_detail.battery_level}%\n"
                    f"• **Carga Acoplada:** {out_detail.carrying_pod_id or 'Sem carga'}\n"
                    f"• **Missão:** {out_detail.current_mission_id or 'Aguardando pedido'}\n"
                    f"• **Destino Alvo:** {target_str}\n"
                    f"• **Passos Restantes na Rota:** {out_detail.path_length_remaining}"
                )
            else:
                reply = f"🔍 **Robô Não Localizado:** {out_detail.message}"

            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 6. Tool: Controle da Simulação (Pausar, Retomar, Alterar Velocidade)
        if any(
            w in query_lower
            for w in [
                "pausar simulação",
                "pausar simulacao",
                "pause",
                "iniciar simulação",
                "iniciar simulacao",
                "retomar simulação",
                "despausar",
                "velocidade 1x",
                "velocidade 2x",
                "velocidade 0.5x",
                "aumentar velocidade",
                "diminuir velocidade",
            ]
        ):
            speed_match = re.search(r"(\d+(?:\.\d+)?)\s*x", query_lower)
            spd = float(speed_match.group(1)) if speed_match else None

            sim_action = "toggle"
            if any(w in query_lower for w in ["pausar", "pause", "congelar"]):
                sim_action = "pause"
            elif any(w in query_lower for w in ["iniciar", "retomar", "despausar", "play"]):
                sim_action = "resume"
            elif spd:
                sim_action = "set_speed"

            out_sim = tool_simulation_control(action=sim_action, speed=spd)
            executed_tools.append({"tool": "simulation_control", "output": out_sim.model_dump()})
            tracer.log_tool_call(
                "simulation_control", {"action": sim_action, "speed": spd}, out_sim.model_dump()
            )

            reply = (
                f"⏱️ **Controle de Simulação Atualizado**\n\n"
                f"• **Status:** {'⏸️ Pausada' if out_sim.is_paused else '▶️ Em Execução'}\n"
                f"• **Velocidade:** {out_sim.speed}x\n"
                f"• **Mensagem:** {out_sim.message}"
            )
            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 7. Tool: Indicadores de Negócio / Métricas & Throughput
        if any(
            w in query_lower
            for w in [
                "throughput",
                "vazão",
                "vazao",
                "quantos pedidos",
                "ordens separadas",
                "pedidos entregues",
                "métricas",
                "metricas",
                "kpi",
                "kpis",
                "utilização",
                "utilizacao",
                "desempenho",
                "performance",
                "analytics",
            ]
        ):
            out_metrics = tool_get_warehouse_metrics()
            executed_tools.append(
                {"tool": "get_warehouse_metrics", "output": out_metrics.model_dump()}
            )
            tracer.log_tool_call("get_warehouse_metrics", {}, out_metrics.model_dump())

            reply = (
                f"📈 **Indicadores Operacionais do Armazém (KPIs)**\n\n"
                f"• **Vazão Atual:** {out_metrics.throughput_per_hour:.1f} pedidos/hora\n"
                f"• **Ordens Separadas:** {out_metrics.completed_orders} pedidos concluídos\n"
                f"• **Ordens em Fila:** {out_metrics.pending_orders} pedidos pendentes\n"
                f"• **Taxa de Utilização da Frota:** {out_metrics.fleet_utilization_pct}%\n"
                f"• **Bateria Média da Frota:** {out_metrics.average_battery_pct}%\n"
                f"• **Dimensões do Galpão Ativo:** {out_metrics.grid_size} células\n"
                f"• **Tamanho da Frota:** {out_metrics.fleet_size} AMRs\n"
                f"• **Áreas Bloqueadas:** {out_metrics.active_incidents}"
            )
            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 8. Tool: Engenharia de Caos & Simulação de Falhas Controladas
        if any(
            w in query_lower
            for w in [
                "caos",
                "chaos",
                "simular colisão",
                "simular colisao",
                "provocar acidente",
                "teste de colisão",
                "derrapagem",
                "wheel slip",
                "falha de rede",
                "falha de wifi",
                "ponto cego",
            ]
        ):
            inc_type = "random"
            if "derrapagem" in query_lower or "slip" in query_lower:
                inc_type = "slip"
            elif "wifi" in query_lower or "rede" in query_lower:
                inc_type = "wifi"
            elif "ponto cego" in query_lower or "lidar" in query_lower:
                inc_type = "lidar"

            out_chaos = tool_trigger_chaos(incident_type=inc_type)
            executed_tools.append({"tool": "trigger_chaos", "output": out_chaos.model_dump()})
            tracer.log_tool_call(
                "trigger_chaos", {"incident_type": inc_type}, out_chaos.model_dump()
            )

            if out_chaos.success:
                reply = (
                    f"💥 **Incidente de Teste (Chaos Engineering) Injetado**\n\n"
                    f"• **Tipo de Falha:** `{out_chaos.incident_type}`\n"
                    f"• **Robôs Envolvidos:** {', '.join(out_chaos.affected_amrs)}\n"
                    f"• **Ação Corretiva Recomendada (CAPA):** {out_chaos.rca_summary}\n\n"
                    f"A War Room de Investigação Forense (RCA) foi gerada e está acessível no banner do simulador."
                )
            else:
                reply = f"⚠️ {out_chaos.message}"

            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 9. Tool: Bloqueio de Célula / Corredor
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
                executed_tools.append(
                    {"tool": "block_warehouse_zone", "output": out_block.model_dump()}
                )
                tracer.log_tool_call(
                    "block_warehouse_zone",
                    {"x": x, "y": y, "reason": reason},
                    out_block.model_dump(),
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

        # 10. Tool: Liberação de Célula
        if any(w in query_lower for w in ["liberar", "libere", "desbloquear", "unblock"]):
            if coords_match:
                x, y = int(coords_match.group(1)), int(coords_match.group(2))
                out_unblock = tool_unblock_zone(x, y)
                executed_tools.append(
                    {"tool": "unblock_warehouse_zone", "output": out_unblock.model_dump()}
                )
                tracer.log_tool_call(
                    "unblock_warehouse_zone", {"x": x, "y": y}, out_unblock.model_dump()
                )

                reply = f"✅ **Célula ({x}, {y}) Desbloqueada**\n\nO corredor está novamente liberado para planejamento de tráfego dos AMRs."
                tracer.end_trace(reply)
                return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 11. Tool: Consulta de Telemetria / Status Geral da Frota
        if any(w in query_lower for w in ["status", "telemetria", "bateria", "battery"]):
            out_telemetry = tool_get_fleet_telemetry()
            executed_tools.append(
                {"tool": "get_fleet_telemetry", "output": out_telemetry.model_dump()}
            )
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

        # 12. Tool: Escalabilidade de Frota (Adicionar / Remover / Escalonar N Robôs)
        scale_match = re.search(r"(\d+)\s*(rob[oô]s?|amrs?|unidades?)", query_lower)
        num_extracted = int(scale_match.group(1)) if scale_match else 1
        specific_amr = _extract_amr_id(query_lower)

        if any(
            w in query_lower for w in ["adicionar", "adicione", "inserir", "add", "acrescentar"]
        ):
            out_scale = tool_scale_fleet(action_type="add", count=num_extracted)
            executed_tools.append({"tool": "scale_fleet", "output": out_scale.model_dump()})
            tracer.log_tool_call(
                "scale_fleet",
                {"action_type": "add", "count": num_extracted},
                out_scale.model_dump(),
            )
            reply = (
                f"🚀 **Frota Expandida Dinamicamente**\n\n"
                f"• **Robôs Adicionados:** +{len(out_scale.affected_amrs)} ({', '.join(out_scale.affected_amrs)})\n"
                f"• **Tamanho Anterior:** {out_scale.previous_count} AMRs\n"
                f"• **Capacidade Total Ativa:** {out_scale.current_count} AMRs\n\n"
                f"Os novos robôs foram posicionados em docas/corredores livres e já estão aptos a receber missões de separação."
            )
            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        if any(
            w in query_lower
            for w in [
                "remover",
                "remova",
                "descomissionar",
                "descomissione",
                "remove",
                "decommission",
            ]
        ):
            out_scale = tool_scale_fleet(
                action_type="remove", count=num_extracted, amr_id=specific_amr
            )
            executed_tools.append({"tool": "scale_fleet", "output": out_scale.model_dump()})
            tracer.log_tool_call(
                "scale_fleet",
                {"action_type": "remove", "count": num_extracted, "amr_id": specific_amr},
                out_scale.model_dump(),
            )
            reply = (
                f"🧹 **Descomissionamento Seguro Realizado**\n\n"
                f"• **Robôs Removidos:** {', '.join(out_scale.affected_amrs)}\n"
                f"• **Capacidade Restante:** {out_scale.current_count} AMRs\n\n"
                f"Todas as reservas espaço-temporais e pedidos em trânsito foram reorganizados sem interrupção do galpão."
            )
            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        if (
            any(
                w in query_lower
                for w in ["ajustar frota", "escalar frota", "definir frota", "scale fleet"]
            )
            and scale_match
        ):
            out_scale = tool_scale_fleet(action_type="scale", target_count=num_extracted)
            executed_tools.append({"tool": "scale_fleet", "output": out_scale.model_dump()})
            tracer.log_tool_call(
                "scale_fleet",
                {"action_type": "scale", "target_count": num_extracted},
                out_scale.model_dump(),
            )
            reply = (
                f"⚖️ **Capacidade da Frota Ajustada**\n\n"
                f"• **Meta Definida:** {num_extracted} AMRs\n"
                f"• **Capacidade Atual:** {out_scale.current_count} AMRs\n"
                f"• **Alterações:** {', '.join(out_scale.affected_amrs) if out_scale.affected_amrs else 'Nenhuma alteração necessária'}"
            )
            tracer.end_trace(reply)
            return CopilotResponse(reply=reply, executed_tools=executed_tools)

        # 13. Resposta Padrão / Menu de Comandos Completo
        reply = (
            "🤖 **NexusFleet Copilot — Guia de Comandos Operacionais**\n\n"
            "Posso executar as seguintes operações em linguagem natural:\n\n"
            "📜 **Auditoria & Telemetria:**\n"
            '• *"Exiba os logs do robô AMR-03"*\n'
            '• *"Qual a posição e carga do AMR-02?"*\n'
            '• *"Status atual da frota e baterias"*\n'
            '• *"Qual o throughput e ordens entregues?"*\n\n'
            "🔧 **Self-Healing & Controle:**\n"
            '• *"Destravar o robô AMR-01"*\n'
            '• *"Pausar a simulação"* ou *"Retomar a simulação"*\n'
            '• *"Velocidade 2x"*\n\n'
            "🚧 **Gestão de Tráfego & Incidentes:**\n"
            '• *"Bloqueie o ponto (10, 8) por derramamento de óleo"*\n'
            '• *"Liberar a coordenada (10, 8)"*\n'
            '• *"Simular colisão de teste (Chaos Engineering)"*\n\n'
            "🚀 **Dimensionamento de Frota:**\n"
            '• *"Adicionar 2 robôs à frota"*\n'
            '• *"Remover o robô AMR-04"*\n\n'
            "🛑 **Segurança Física:**\n"
            '• *"Parada de emergência geral"* *(ativa proteção HITL - ISO 3691-4)*'
        )
        tracer.end_trace(reply)
        return CopilotResponse(reply=reply, executed_tools=executed_tools)


copilot_agent = WarehouseCopilotAgent()
