# 📋 PRD — Product Requirements Document
# Projeto: NexusFleet AMR Orchestrator & Self-Healing Warehouse Digital Twin

---

## 1. Visão Executiva do Produto

O **NexusFleet AMR** é uma plataforma de automação logística de padrão internacional projetada para a coordenação em tempo real de frotas de Robôs Móveis Autônomos (AMRs - *Autonomous Mobile Robots*) em centros de distribuição e armazéns de alta densidade (padrão *Amazon Robotics*, *Mercado Livre Fulfillment*, *Symbotic* e *Ocado*).

O sistema resolve os três maiores desafios da intralogística moderna:
1. **Coordenação Multi-Agente sem Colisões e sem Deadlocks (MAPF):** Roteamento simultâneo de múltiplos robôs através do algoritmo *Space-Time Multi-Agent Path Finding* ($x, y, t$), eliminando congestionamentos mecânicos em corredores estreitos.
2. **Resolução Autônoma de Incidentes via Copiloto de IA (IA Agêntica com HITL):** Um supervisor operacional de IA capaz de gerenciar imprevistos (bloqueios, derramamentos, falhas mecânicas, variações de demanda) em linguagem natural com ferramentas determinísticas (*Tool Calling*) e *Human-in-the-Loop*.
3. **Digital Twin Interativo & Studio com Telemetria a 60 FPS:** Visualização em tempo real do galpão com suporte a *Timeline Replay* (voltar no tempo para auditoria de incidentes), editor visual drag-and-drop de galpões (*Warehouse Layout Studio*) com exportação/importação em JSON, e um painel executivo de Business Intelligence (*Shift Analytics Hub*).

---

## 2. Personas e Dores do Negócio

### 2.1. Diretor / Gerente de Operações Logísticas (Shift Operations Lead)
* **Dores:**
  * Falta de visibilidade em tempo real sobre gargalos de tráfego nos corredores.
  * Lentidão para reconfigurar a operação quando ocorrem incidentes (ex: pallet quebrado interditando corredor).
  * Dificuldade de mensurar o impacto financeiro e o cumprimento de SLAs de entrega (Same-Day / 2h Delivery).
* **Necessidades:**
  * Dashboard executivo com métricas claras de vazão (pedidos/hora), utilização da frota e relatórios de turno em 1 clique.
  * Interface conversacional rápida para resolver incidentes sem precisar navegar por dezenas de telas de ERP/WMS legados.

### 2.2. Engenheiro de Automação & Robótica (Robotics Fleet Engineer)
* **Dores:**
  * Ocorrência de *deadlocks* (impasses mecânicos) onde dois robôs ficam frente a frente travando corredores.
  * Baterias esgotando no meio do trajeto por falta de planejamento preditivo de recarga.
  * Falta de ferramentas de depuração para reproduzir falhas (*Flight Recorder*).
* **Necessidades:**
  * Algoritmo de roteamento espaço-temporal robusto com garantia formal de não-colisão.
  * Máquina de estados clara por robô (FSM com ciclo de vida completo).
  * Recurso de *Timeline Replay* para inspecionar segundo a segundo como um incidente aconteceu.

### 2.3. Recrutador Técnico & CTO / Hiring Manager (Público de Portfólio)
* **Dores:**
  * Avalia dezenas de portfólios com "projetos de brinquedo" (toy problems de 12 nós, dashboards amadores em Streamlit e servidores lentos com cold start de 40 segundos).
* **Necessidades:**
  * Abertura instantânea da aplicação (< 2 segundos) em link público e gratuito.
  * Código limpo, tipado, testado e com governança de software corporativo.
  * Interface visual com acabamento padrão startup do Vale do Silício, bilíngue (PT/EN) e documentação de API moderna com **Scalar**.

---

## 3. Requisitos Funcionais (RF)

### RF01 — Simulação de Tráfego Multi-Agente em Tempo Real (Digital Twin)
* **RF01.1:** O sistema deve simular uma frota de 5 a 30 robôs AMRs navegando simultaneamente em um grid bidimensional configurável.
* **RF01.2:** Cada robô deve seguir uma Máquina de Estados Finita (FSM):
  $$\text{IDLE} \rightarrow \text{MOVING\_TO\_POD} \rightarrow \text{LIFTING\_POD} \rightarrow \text{TRANSITING\_TO\_PICKING} \rightarrow \text{AT\_PICKING\_STATION} \rightarrow \text{RETURNING\_POD} \rightarrow \text{LOWERING\_POD} \rightarrow \text{CHARGING / IDLE}$$
* **RF01.3:** O sistema deve implementar gerenciamento autônomo de energia: robôs com bateria abaixo de 20% devem suspender novas coletas e priorizar rotas para estações de recarga rápida (*Charging Docks*).
* **RF01.4:** A visualização deve rodar a 60 FPS com interpolação suave (LERP) via Canvas HTML5, com suporte a Zoom e Pan.
* **RF01.5:** Deve oferecer camadas visuais alternáveis:
  * Camada Operacional (Robôs, Pods, Baias, Carga).
  * Camada de Projeção de Trajetória (desenho do vetor de rota futura do robô selecionado).
  * Camada de Mapa de Calor (Heatmap de densidade de tráfego por corredor).

### RF02 — Warehouse Layout Studio (Editor Visual Drag-and-Drop)
* **RF02.1:** O usuário deve ser capaz de criar, editar e redimensionar layouts de armazém diretamente no navegador.
* **RF02.2:** O editor deve disponibilizar paleta com: Piso transitável, Prateleiras/Pods (com categorias de SKU), Estações de Picking (bancadas), Docas de Recarga e Paredes/Obstáculos.
* **RF02.3:** O Studio deve validar em tempo real a conectividade do galpão (Flood Fill/BFS), alertando visualmente caso prateleiras ou estações fiquem isoladas ou sem rota navegável.
* **RF02.4:** Suporte completo a exportação e importação de layouts em formato `.json`.
* **RF02.5:** O sistema deve incluir 3 presets de fábrica prontos para demonstração:
  1. *Amazon Mega Fulfillment Center* (Grid denso com múltiplos corredores e baias).
  2. *Micro-Dark Store* (Grid compacto de alta velocidade).
  3. *Testing Sandbox* (Grid de testes para indução de conflitos).

### RF03 — Timeline Replay (Flight Recorder de Incidentes)
* **RF03.1:** O sistema deve manter um buffer circular em memória dos últimos 60 a 120 segundos de simulação.
* **RF03.2:** Uma barra de scrubbing na interface deve permitir pausar a simulação ao vivo e arrastar a agulha do tempo para trás para rever a movimentação exata dos robôs em câmera lenta.

### RF04 — Copiloto Operacional com IA Agêntica (Logistics Copilot)
* **RF04.1:** Chat conversacional em tempo real integrado à interface com streaming de respostas (Server-Sent Events / WebSockets).
* **RF04.2:** O Copiloto deve executar ferramentas determinísticas (*Tool Calling*):
  * `block_zone(coordinates, reason)`: Interditar áreas do galpão.
  * `unblock_zone(coordinates)`: Liberar áreas para tráfego.
  * `get_fleet_status()`: Obter telemetria, baterias e ordens em andamento.
  * `reroute_affected_agents(blocked_cells)`: Disparar re-planejamento de rotas.
  * `inject_order_surge(order_count)`: Simular pico de demanda.
* **RF04.3:** **Human-in-the-Loop (HITL) & Guardrails:** Comandos destrutivos ou de parada total de frota exigem geração de cartão de confirmação no chat antes da execução.
* **RF04.4:** Observabilidade completa de custos, latência e traces de chamadas de LLM via **Langfuse**.

### RF05 — Painel Executivo de Analytics (Shift & Fleet BI)
* **RF05.1:** Visualização interativa com gráficos analíticos via Recharts:
  * Vazão temporal (Throughput de pedidos/hora).
  * Distribuição de status da frota (Donut Chart).
  * Histograma de latência de ciclo de separação ($P_{50}, P_{90}, P_{99}$).
  * Níveis de bateria e consumo energético estimado (kWh).
* **RF05.2:** Tabela dinâmica de incidentes e auditoria com badges de severidade e tempo de resolução (MTTR).
* **RF05.3:** Botão de exportação de dados analíticos (.CSV e impressão de relatório).

### RF06 — Suporte Bilíngue Nativo (i18n)
* **RF06.1:** Todo o frontend, métricas, tooltips, presets e documentação devem ser bilíngues: **Português (padrão)** e **Inglês**.
* **RF06.2:** O Copiloto de IA deve responder de forma fluida no idioma configurado ou no idioma utilizado pelo usuário na mensagem.

---

## 4. Requisitos Não-Funcionais (RNF)

* **RNF01 (Performance de Renderização):** O Digital Twin deve manter taxa estável de **60 FPS** em monitores padrão, sem engasgos de CPU, utilizando desacoplamento do estado via **Zustand** e renderização via Canvas com `requestAnimationFrame`.
* **RNF02 (Latência de Roteamento):** O cálculo de rota espaço-temporal para um agente em grid de até $30 \times 30$ deve ser concluído em menos de **$20\text{ ms}$**.
* **RNF03 (Eficiência de Banda de Rede):** A telemetria via WebSocket deve utilizar compressão de deltas (transmitindo apenas robôs e células com alterações de estado), limitando o tráfego a menos de **$10\text{ KB/s}$**.
* **RNF04 (Zero Cold Start / Baixa Latência de Inicialização):** O tempo de inicialização do container único no Google Cloud Run deve ser inferior a **2.5 segundos** no primeiro acesso (Scale-to-Zero).
* **RNF05 (Custo Operacional FinOps):** A infraestrutura deve operar com custo projetado de **R$ 0,00 / mês**, usufruindo da cota Always Free do Google Cloud Run (2 milhões de requisições/mês) e das assinaturas ativas de IA do usuário (Gemini Pro / OpenCode Go).
* **RNF06 (Documentação de API):** Toda a API deve ser documentada e testável interativamente via **Scalar** (`scalar-fastapi`), com proibição expressa de Swagger UI legado.
* **RNF07 (Padrão de Código e Tipagem):** 100% de cobertura de tipagem estática no backend via **Mypy** (modo estrito) e formatação via **Ruff**. No frontend, TypeScript estrito com **Biome / ESLint**.

---

## 5. Métricas de Sucesso (KPIs & SLAs)

| Métrica | Meta Operacional |
| :--- | :--- |
| **Colisões Físicas entre Robôs** | **0 colisões** (garantia formal do algoritmo Space-Time) |
| **Deadlock Rate** | $< 0.1\%$ de ocorrências, com resolução autônoma em $< 2.0\text{ s}$ |
| **Throughput da Frota** | $\ge 90\%$ de atendimento de janelas de separação de pedidos |
| **Disponibilidade da Frota** | $\ge 85\%$ dos robôs ativos em ciclos produtivos |
| **Latência do Copiloto (TTFT)** | $< 800\text{ ms}$ para primeiro token com Gemini 3.8 Flash |
| **Custo de Hospedagem** | **R$ 0,00 / mês** |

---

## 6. Conformidade e Normas de Indústria

* **ISO 3691-4 (Veículos Industriais sem Condutor):** Respeito às regras de segurança de parada de emergência, desaceleração em cruzamentos cegos e bloqueio manual prioritário.
* **OpenAPI 3.1 & W3C WebSockets:** Padrões abertos de comunicação para fácil integração com sistemas WMS/ERP corporativos (SAP, Manhattan Associates, Blue Yonder).
