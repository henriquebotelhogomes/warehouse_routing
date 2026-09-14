# 📋 TASKS.md — Roadmap de Execução & Backlog Granular
# Projeto: NexusFleet AMR Orchestrator & Self-Healing Warehouse Digital Twin

---

## 🎯 Status do Projeto: 🚀 TODAS AS FASES CONCLUÍDAS COM SUCESSO

- [x] **Fase 0: Concepção & Governança Sênior**
  - [x] Debate arquitetural e escolha de stack (Space-Time MAPF + React 19 + Canvas 60 FPS + Cloud Run R$ 0/mês)
  - [x] Criação do `PRD.md` (Visão de produto, requisitos funcionais e não-funcionais, KPIs)
  - [x] Criação do `PROJECT_SPEC.md` (Topologia, ADRs, contratos Pydantic v2 e diagramas)
  - [x] Criação do `AGENTS.md` (Catálogo de tools, HITL guardrails, Langfuse)
  - [x] Criação do `TASKS.md` (Backlog granular de execução)

---

## 🚀 Fases de Implementação

### 🔹 Fase 1: Motor de Robótica Autônoma & Algoritmos (Core Engine)
- [x] **1.1. Estrutura Espacial do Galpão (`src/warehouse_routing/core/grid.py`)**
  - [x] Implementar classe `WarehouseGrid` com suporte a dimensões dinâmicas ($10 \times 10$ até $50 \times 50$).
  - [x] Mapeamento de tipos de células: `EMPTY`, `POD`, `PICKING_STATION`, `CHARGING_DOCK`, `OBSTACLE`.
  - [x] Algoritmo de validação de conectividade via BFS / Flood Fill para prevenir zonas isoladas.
- [x] **1.2. Algoritmo Space-Time MAPF (`src/warehouse_routing/core/space_time_mapf.py`)**
  - [x] Implementar `ReservationTable` com reservas espaço-temporais $(x, y, t)$.
  - [x] Implementar algoritmo `SpaceTimeAStar` com heurística de distância Manhattan 3D.
  - [x] Detecção e prevenção de conflitos de vértice (mesma célula) e conflitos de aresta (colisão frontal / cruzamento).
  - [x] Lógica de espera ativa (robô aguarda 1 tick em célula segura caso haja obstrução passageira).
- [x] **1.3. Máquina de Estados Finita do Robô AMR (`src/warehouse_routing/core/amr_agent.py`)**
  - [x] Implementar estados FSM: `IDLE`, `MOVING_TO_POD`, `LIFTING_POD`, `TRANSITING_TO_PICKING`, `AT_PICKING_STATION`, `RETURNING_POD`, `LOWERING_POD`, `CHARGING`.
  - [x] Modelo matemático de consumo de bateria em função da distância percorrida e carga transportada.
  - [x] Protocolo autônomo de retorno à base de recarga quando bateria $< 20\%$.
- [x] **1.4. Orquestrador de Frota & Missões (`src/warehouse_routing/core/fleet_orchestrator.py`)**
  - [x] Fila de pedidos de e-commerce e despacho dinâmico para o robô mais próximo disponível.
  - [x] Resolução de deadlocks via priorização baseada em SLA de pedido.
- [x] **1.5. Flight Recorder / Timeline Buffer (`src/warehouse_routing/core/flight_recorder.py`)**
  - [x] Buffer circular em memória com retenção de snapshots de 120 segundos para scrubbing no frontend.

---

### 🔹 Fase 2: Backend API, WebSockets & Scalar Docs
- [x] **2.1. Configuração da API FastAPI (`src/warehouse_routing/api/main.py`)**
  - [x] Configuração do ciclo de vida assíncrono via `lifespan`.
  - [x] Integração nativa do **Scalar** em `/docs` com tema dark moderno e playground interativo.
- [x] **2.2. WebSocket Telemetry Hub (`src/warehouse_routing/api/websocket_hub.py`)**
  - [x] Endpoint `/ws/telemetry` com streaming de telemetria a 20-30 Hz.
  - [x] Algoritmo de compressão de deltas (transmite apenas robôs e células alteradas).
  - [x] Canais bidirecionais para receber comandos manuais do usuário em tempo real.
- [x] **2.3. Endpoints de Gestão de Layouts (`src/warehouse_routing/api/routes_layout.py`)**
  - [x] `GET /api/v1/layouts/presets`: Retorna os 3 presets oficiais (Amazon Mega Hub, Dark Store, Sandbox).
  - [x] `POST /api/v1/layouts/validate`: Valida acessibilidade do galpão desenhado pelo usuário.
  - [x] `POST /api/v1/layouts/load`: Carrega novo layout dinamicamente na simulação.

---

### 🔹 Fase 3: Copiloto de IA Agêntica & Observabilidade
- [x] **3.1. Ferramentas Determinísticas (`src/warehouse_routing/copilot/tools.py`)**
  - [x] Implementar `block_warehouse_zone`, `unblock_warehouse_zone`, `get_fleet_telemetry`, `emergency_stop_fleet`.
  - [x] Schemas de validação estritos com Pydantic v2.
- [x] **3.2. Orquestrador Agêntico (`src/warehouse_routing/copilot/agent.py`)**
  - [x] Integração com **Gemini Pro (google-genai)** e fallback para LiteLLM.
  - [x] Reducers de contexto (janela de 6 mensagens, sem vazamento de dados de telemetria).
  - [x] Endpoint `POST /api/v1/copilot/chat` com respostas estruturadas.
- [x] **3.3. Guardrails e Human-in-the-Loop (HITL) (`src/warehouse_routing/copilot/guardrails.py`)**
  - [x] Interceptação de comandos destrutivos e emissão de tokens de confirmação assinados.
  - [x] Endpoint `POST /api/v1/copilot/actions/confirm`.
- [x] **3.4. Rastreamento com Langfuse (`src/warehouse_routing/copilot/langfuse_tracer.py`)**
  - [x] Tracing de latência, tokens, chamadas de tools e feedback de usuários.

---

### 🔹 Fase 4: Frontend Moderno (React 19 + TypeScript + Canvas 60 FPS)
- [x] **4.1. Setup do Frontend (`frontend/`)**
  - [x] Inicialização com Vite + React 19 + TypeScript estrito + Tailwind CSS + Lucide Icons.
  - [x] Sistema de internacionalização i18n com dicionários tipados (`pt-BR` padrão e `en-US`).
- [x] **4.2. Estado Global & Store Atômica (`frontend/src/store/useSimulationStore.ts`)**
  - [x] Configuração do Zustand para receber deltas do WebSocket sem forçar re-render da árvore React.
- [x] **4.3. Digital Twin Canvas (`frontend/src/components/DigitalTwinCanvas.tsx`)**
  - [x] Loop de renderização a 60 FPS com `requestAnimationFrame`.
  - [x] Interpolação suave (LERP) das coordenadas contínuas dos robôs.
  - [x] Suporte nativo a Zoom (mouse wheel) e Pan (arraste).
  - [x] Toggles de visualização: Operação normal, Projeção de rota e Heatmap de calor.
  - [x] Interação: Clique no robô abre telemetria; clique em célula cria bloqueio de emergência.
- [x] **4.4. Timeline Replay Bar (`frontend/src/components/TimelineReplayBar.tsx`)**
  - [x] Slider de scrubbing para pausar o tempo e rever os últimos 120 segundos em câmera lenta.
- [x] **4.5. Warehouse Layout Studio (`frontend/src/components/LayoutStudio.tsx`)**
  - [x] Toolbar com paleta de pintura (Piso, Pod, Picking, Carregador, Parede).
  - [x] Pintura com clique e arraste no grid.
  - [x] Validação visual em tempo real com contornos de erro em áreas inacessíveis.
  - [x] Botões de Exportar JSON e Importar JSON com upload imediato.
- [x] **4.6. Executive Analytics Hub (`frontend/src/components/AnalyticsDashboard.tsx`)**
  - [x] Cards executivos de Throughput, MTTR, Utilização da Frota e Economia de Energia.
  - [x] Gráficos interativos com Recharts (Área temporal, Donut de frota, Histograma de lead time).
  - [x] Tabela viva de incidentes com badges de severidade e histórico de ações do Copiloto.
- [x] **4.7. Copiloto Drawer (`frontend/src/components/CopilotDrawer.tsx`)**
  - [x] Chat lateral retrátil com streaming de texto em Markdown.
  - [x] Pills com sugestões rápidas de prompt para recrutadores.
  - [x] Renderização de cards de ação HITL com botão de confirmação física.

---

### 🔹 Fase 5: Dockerfile Multi-Stage & Cloud Run Deploy (FinOps $0/mês)
- [x] **5.1. Dockerfile Unificado**
  - [x] Stage 1: Build de produção do Frontend Vite/React.
  - [x] Stage 2: Runtime Python 3.12 com FastAPI servindo arquivos estáticos em `/`.
- [x] **5.2. Testes de Cold Start & Otimização de Imagem**
  - [x] Imagem ultraleve (< 180 MB) para cold start de $< 2.5\text{ s}$ no Cloud Run.
- [x] **5.3. Configuração de Deploy Google Cloud Run**
  - [x] Scripts `deploy_gcp.sh` e `deploy_gcp.ps1` com `min-instances = 0` para custo R$ 0,00/mês.

---

### 🔹 Fase 6: Qualidade, Testes & Documentação Executiva
- [x] **6.1. Suíte de Testes Automatizados**
  - [x] 12 testes unitários e de integração (Space-Time MAPF, FSM, WebSockets, Layouts, Copilot e Static Serving) 100% passando.
- [x] **6.2. Hooks de Pré-Commit (`.pre-commit-config.yaml`)**
  - [x] Configurados: Ruff, Mypy, check-yaml, check-json, trailing-whitespace, end-of-file-fixer.
- [x] **6.3. Novo README.md Executivo**
  - [x] Hero section moderna com badges, diagramas Mermaid, visão da arquitetura, 5 diferenciais técnicos e guia quickstart.
