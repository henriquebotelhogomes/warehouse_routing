import datetime
import random
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChaosFailureType(str, Enum):
    WHEEL_SLIP = "wheel_slip"
    NETWORK_LATENCY = "network_latency"
    SENSOR_BLINDSPOT = "sensor_blindspot"
    RANDOM = "random"


class IncidentImpactMetrics(BaseModel):
    speed_at_impact_ms: float = 1.2
    interrupted_orders: List[str] = Field(default_factory=list)
    estimated_sla_delay_seconds: float = 45.0
    affected_pods: List[str] = Field(default_factory=list)
    damage_severity: str = "MODERATE"  # "MINOR", "MODERATE", "CRITICAL"


class IncidentReport(BaseModel):
    incident_id: str
    timestamp: str
    tick: int
    location: Dict[str, int]
    failure_type: str
    failure_type_label: str
    involved_amrs: List[str]
    primary_fault_amr: str
    summary: str
    root_cause_analysis: str
    five_whys: List[str]
    corrective_actions: List[str]
    impact_metrics: IncidentImpactMetrics
    blackbox_snapshot: List[Dict[str, Any]] = Field(default_factory=list)
    is_resolved: bool = False
    resolved_at: Optional[str] = None
    isolation_block_cells: List[Dict[str, int]] = Field(default_factory=list)


class ChaosEngine:
    """
    Motor de Engenharia do Caos (Chaos Engineering) para Robótica Intralogística.
    Injeta anomalias físicas realistas (derrapagem, latência de rede, falha de sensor),
    executa Análise Forense de Causa Raiz (RCA) e gera laudos periciais auditáveis.
    """

    FAILURE_METADATA: Dict[ChaosFailureType, Dict[str, Any]] = {
        ChaosFailureType.WHEEL_SLIP: {
            "label": "Derrapagem Mecânica (Wheel Slip)",
            "description": "Perda transitória de tração nas rodas motrizes provocada por resíduo no piso. O robô derrapou e avançou 1 célula além do ponto de frenagem seguro.",
            "five_whys": [
                "1. Por que ocorreu a colisão? O robô não freou a tempo no cruzamento e invadiu o espaço do outro AMR.",
                "2. Por que o robô não freou no ponto planejado? O sistema de controle registrou derrapagem (wheel slip) nas rodas tracionárias.",
                "3. Por que as rodas derraparam? Houve redução súbita do coeficiente de atrito no piso daquele corredor.",
                "4. Por que o coeficiente de atrito caiu? Pequeno vazamento de lubrificante não detectado pelo sensor óptico de solo.",
                "5. Por que o vazamento não foi prevenido? Intervalo de limpeza preventiva de piso programado para a cada 4 horas em vez de monitoramento contínuo.",
            ],
            "corrective_actions": [
                "Reduzir velocidade operacional de aproximação em cruzamentos de 1.5 m/s para 1.0 m/s.",
                "Instalar sensores ópticos de reflexão de piso para detecção antecipada de contaminantes líquidos.",
                "Revisar o torque do motor de frenagem regenerativa da frota.",
            ],
            "severity": "MODERATE",
        },
        ChaosFailureType.NETWORK_LATENCY: {
            "label": "Latência de Rede / Perda de Pacotes (Wi-Fi Jitter)",
            "description": "Atraso de 850ms na entrega de telemetria e comando de parada em cruzamento. O robô avançou na janela temporal reservada por outro AMR.",
            "five_whys": [
                "1. Por que ocorreu a colisão? O robô continuou seu avanço enquanto o outro AMR já tinha prioridade de travessia.",
                "2. Por que o robô não aguardou a liberação? O pacote de comando de espera (WAIT) demorou 850ms para ser processado no barramento CAN.",
                "3. Por que o comando atrasou? Houve jitter e saturação momentânea no Access Point Wi-Fi 6 do setor.",
                "4. Por que o Access Point saturou? Handover simultâneo de múltiplos dispositivos móveis e câmeras de monitoramento na mesma banda.",
                "5. Por que os AMRs compartilham a mesma banda? Falha de segmentação de QoS e VLAN industrial prioritária no roteamento de rede.",
            ],
            "corrective_actions": [
                "Configurar QoS prioritário IEEE 802.11ax exclusivo para pacotes de segurança de robótica.",
                "Ativar fail-safe local nos AMRs: se latência > 250ms em cruzamento, frear preventivamente.",
                "Adicionar redundância com protocolo industrial ultraconfiável (5G privado ou dual Wi-Fi).",
            ],
            "severity": "CRITICAL",
        },
        ChaosFailureType.SENSOR_BLINDSPOT: {
            "label": "Ponto Cego de Sensor / Falha de Detecção Óptica",
            "description": "Oclusão parcial do sensor LiDAR de segurança em aproximação a 90°. O subsistema secundário de anti-colisão não acusou a aproximação lateral a tempo.",
            "five_whys": [
                "1. Por que ocorreu a colisão? Os robôs convergiram no cruzamento sem que o sistema de segurança redundante parasse o veículo.",
                "2. Por que o sensor de proximidade não disparou? O scanner de segurança LiDAR possuía ponto cego na angulação de 85° a 95° relativo ao chassi.",
                "3. Por que havia ponto cego nessa angulação? O suporte mecânico do sensor acumulou poeira residual na lente de proteção inferior.",
                "4. Por que o sensor acumulou poeira? Falta de rotina de sopro de ar comprimido nas estações de recarga.",
                "5. Por que a rotina não existia? Não havia alerta de degradação de sinal óptico configurado no firmware do robô.",
            ],
            "corrective_actions": [
                "Implementar autoteste óptico contínuo do LiDAR e alerta de lente suja pré-despacho.",
                "Adicionar sensor ultrassônico lateral complementar para cobrir 360° sem pontos cegos.",
                "Aumentar a margem de segurança temporal da Reservation Table de 1 para 2 passos de tempo.",
            ],
            "severity": "MODERATE",
        },
    }

    @classmethod
    def inject_collision(
        cls,
        orchestrator: Any,
        failure_type: ChaosFailureType = ChaosFailureType.RANDOM,
        target_count: int = 1,
    ) -> IncidentReport:
        """
        Injeta uma colisão física simulada e realista entre AMRs no galpão.
        """
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        incident_id = f"INC-{now.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        if failure_type == ChaosFailureType.RANDOM:
            resolved_type = random.choice(
                [
                    ChaosFailureType.WHEEL_SLIP,
                    ChaosFailureType.NETWORK_LATENCY,
                    ChaosFailureType.SENSOR_BLINDSPOT,
                ]
            )
        else:
            resolved_type = failure_type

        meta = cls.FAILURE_METADATA.get(resolved_type, cls.FAILURE_METADATA[ChaosFailureType.WHEEL_SLIP])

        amrs = list(orchestrator.amrs.values())
        if len(amrs) < 2:
            raise ValueError("São necessários pelo menos 2 robôs na frota para simular uma colisão.")

        # Prioriza robôs que estejam em movimento
        moving_amrs = [a for a in amrs if len(a.path) > a.path_step_idx]
        if len(moving_amrs) >= 2:
            # Encontra os 2 robôs em movimento mais próximos um do outro
            best_pair = None
            min_dist = 9999.0
            for i in range(len(moving_amrs)):
                for j in range(i + 1, len(moving_amrs)):
                    d = abs(moving_amrs[i].grid_x - moving_amrs[j].grid_x) + abs(
                        moving_amrs[i].grid_y - moving_amrs[j].grid_y
                    )
                    if d < min_dist:
                        min_dist = d
                        best_pair = (moving_amrs[i], moving_amrs[j])
            if best_pair:
                fault_amr, victim_amr = best_pair
            else:
                fault_amr, victim_amr = moving_amrs[0], moving_amrs[1]
        elif len(moving_amrs) == 1:
            fault_amr = moving_amrs[0]
            other_amrs = [a for a in amrs if a.id != fault_amr.id]
            victim_amr = other_amrs[0]
        else:
            fault_amr = amrs[0]
            victim_amr = amrs[1]

        # Define a coordenada do ponto de impacto
        # Pega a posição de próximo passo do victim_amr ou do fault_amr
        if victim_amr.path and victim_amr.path_step_idx < len(victim_amr.path):
            cx, cy = victim_amr.path[victim_amr.path_step_idx]
        else:
            cx, cy = victim_amr.grid_x, victim_amr.grid_y

        # Força o fault_amr para a célula do impacto simulando a anomalia física
        fault_amr.grid_x = cx
        fault_amr.grid_y = cy
        fault_amr.x = float(cx)
        fault_amr.y = float(cy)

        # Atualiza a posição do victim_amr para a mesma célula
        victim_amr.grid_x = cx
        victim_amr.grid_y = cy
        victim_amr.x = float(cx)
        victim_amr.y = float(cy)

        # Transição de estado para CRASHED em ambos
        crash_msg = f"Colisão física em ({cx}, {cy}) devido a {meta['label']}"
        fault_amr.force_crash(crash_msg)
        victim_amr.force_crash(crash_msg)

        # Limpa as reservas na Reservation Table para não deixar arestas fantasmas
        orchestrator.reservations.clear_agent(fault_amr.id)
        orchestrator.reservations.clear_agent(victim_amr.id)

        # Coleta pedidos interrompidos
        interrupted_orders = []
        affected_pods = []
        if fault_amr.current_mission_id:
            interrupted_orders.append(fault_amr.current_mission_id)
        if victim_amr.current_mission_id:
            interrupted_orders.append(victim_amr.current_mission_id)
        if fault_amr.carrying_pod_id:
            affected_pods.append(fault_amr.carrying_pod_id)
        if victim_amr.carrying_pod_id:
            affected_pods.append(victim_amr.carrying_pod_id)

        # Extrai snapshot recente da Caixa Preta (Flight Recorder)
        blackbox_history = orchestrator.flight_recorder.get_history(limit=15)
        blackbox_snapshot = [snap.model_dump() for snap in blackbox_history]

        impact_metrics = IncidentImpactMetrics(
            speed_at_impact_ms=round(random.uniform(1.1, 1.6), 2),
            interrupted_orders=interrupted_orders,
            estimated_sla_delay_seconds=round(random.uniform(35.0, 95.0), 1),
            affected_pods=affected_pods,
            damage_severity=str(meta["severity"]),
        )

        summary = (
            f"Colisão física detectada entre {fault_amr.id} e {victim_amr.id} na célula ({cx}, {cy}) "
            f"no tick {orchestrator.current_tick}. Causa preliminar: {meta['label']} com severidade {meta['severity']}."
        )

        root_cause = (
            f"O algoritmo Space-Time MAPF havia alocado a reserva espaço-temporal com sucesso. "
            f"Contudo, uma anomalia física ({meta['label']}) forçou o agente primário {fault_amr.id} "
            f"a violar o envelope cinemático e colidir com {victim_amr.id}. Detalhes: {meta['description']}"
        )

        report = IncidentReport(
            incident_id=incident_id,
            timestamp=timestamp_str,
            tick=orchestrator.current_tick,
            location={"x": cx, "y": cy},
            failure_type=resolved_type.value,
            failure_type_label=str(meta["label"]),
            involved_amrs=[fault_amr.id, victim_amr.id],
            primary_fault_amr=fault_amr.id,
            summary=summary,
            root_cause_analysis=root_cause,
            five_whys=list(meta["five_whys"]),
            corrective_actions=list(meta["corrective_actions"]),
            impact_metrics=impact_metrics,
            blackbox_snapshot=blackbox_snapshot,
            is_resolved=False,
            isolation_block_cells=[{"x": cx, "y": cy}],
        )

        return report

    @classmethod
    def generate_markdown_report(cls, report: IncidentReport) -> str:
        """Gera um laudo pericial formal em Markdown para download/impressão."""
        md = f"""# 🚨 Relatório Pericial de Incidente de Robótica (RCA)
**ID do Incidente:** `{report.incident_id}`  
**Data e Hora:** {report.timestamp} | **Tick da Simulação:** #{report.tick}  
**Status:** {'✅ RESOLVIDO' if report.is_resolved else '⚠️ EM ANÁLISE / ATIVO'}  
**Norma de Referência:** ISO 3691-4 (Requisitos de Segurança para Veículos Industriais Não Guiados)

---

## 📍 Localização e Agentes Envolvidos
* **Coordenada do Impacto:** Célula `X: {report.location['x']} | Y: {report.location['y']}`
* **Agentes Envolvidos:** {', '.join(report.involved_amrs)}
* **Agente Culpado (Infrator Primário):** `{report.primary_fault_amr}`
* **Modo de Falha Identificado:** **{report.failure_type_label}**
* **Severidade do Dano:** `{report.impact_metrics.damage_severity}`

---

## 📊 Métricas de Impacto Operacional
* **Velocidade Relativa no Impacto:** `{report.impact_metrics.speed_at_impact_ms} m/s`
* **Pedidos Interrompidos:** {', '.join(report.impact_metrics.interrupted_orders) if report.impact_metrics.interrupted_orders else 'Nenhum pedido ativo'}
* **Prateleiras / Pods Atingidos:** {', '.join(report.impact_metrics.affected_pods) if report.impact_metrics.affected_pods else 'Nenhum pod carregado no momento'}
* **Atraso Estimado no SLA:** `+{report.impact_metrics.estimated_sla_delay_seconds} segundos`

---

## 🔍 Análise de Causa Raiz (Root Cause Analysis - RCA)
{report.root_cause_analysis}

### Metodologia dos 5 Porquês (5-Whys Industrial)
"""
        for why in report.five_whys:
            md += f"- **{why}**\n"

        md += """
---

## 🛡️ Plano de Ação Corretivo e Preventivo (CAPA)
"""
        for action in report.corrective_actions:
            md += f"1. [ ] {action}\n"

        md += f"""
---

## 📼 Histórico Forense da Caixa Preta (Últimos Ticks)
O registrador *FlightRecorder* arquivou os instantes anteriores ao impacto para análise de telemetria quadro a quadro.
* Total de frames recuperados: `{len(report.blackbox_snapshot)}`

---
*Laudo gerado automaticamente pelo módulo NexusFleet Chaos Engineering & RCA.*
"""
        return md
