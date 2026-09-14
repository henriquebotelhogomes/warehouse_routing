# Proposta de Arquitetura Moderna

## 1) Princípios arquiteturais

- **API-first e event-aware**: APIs síncronas para operação e eventos para desacoplamento
- **Multi-tenant by design**: isolamento lógico forte desde o modelo de dados
- **Observability-first**: métricas, logs e traces como parte do contrato de engenharia
- **Security-by-default**: autenticação, autorização e criptografia obrigatórias

## 2) Componentes de alto nível

1. **API Gateway / Edge**
   - TLS termination
   - Rate limiting por tenant
   - Autenticação de token/chave

2. **BFF + Frontend Web**
   - Next.js para SSR/ISR, autenticação e composição de dados para UI
   - Reduz acoplamento da UI com múltiplos serviços

3. **Core API Service**
   - CRUD de tenants, usuários, warehouses e topologias
   - Endpoints de roteamento síncrono

4. **Routing Engine Service**
   - Execução do algoritmo e avaliação de rota
   - Evolui separadamente para suportar outros algoritmos

5. **Async Workers**
   - Simulações, retreinamento, relatórios e tarefas pesadas

6. **Data Layer**
   - PostgreSQL + Redis + object storage

7. **Telemetry Stack**
   - OpenTelemetry Collector
   - Prometheus/Grafana (métricas)
   - Tempo/Jaeger (traces)
   - Loki/SIEM (logs)

## 3) Fluxos principais

### Fluxo A - Cálculo de rota em tempo real

1. Cliente envia requisição ao gateway
2. Gateway valida token, aplica limite e injeta trace context
3. Core API valida payload e tenant
4. Routing Engine calcula rota e retorna explicação
5. API grava auditoria e metering
6. Resposta retorna com `request_id` e metadata de diagnóstico

### Fluxo B - Mudança de topologia

1. Operador envia mudança de layout/bloqueio
2. Core API cria nova versão de topologia
3. Worker recalcula baseline de performance
4. Evento publicado para analytics e alertas

## 4) Estratégia de modularidade

- Monólito modular na fase inicial de SaaS (menos overhead)
- Extração incremental para serviços dedicados quando houver gatilhos claros:
  - Latência p95 acima do SLO
  - Carga de jobs assíncronos impactando API
  - Necessidade de escalar componentes de forma independente

## 5) Deploy e ambientes

- Ambientes: `dev`, `staging`, `prod`
- Infra declarativa (IaC)
- Deploy progressivo com rollback automático
- Dados e segredos segregados por ambiente

## 6) Trade-offs conscientes

- Evitar microserviços prematuros para reduzir complexidade operacional
- Preferir consistência forte no domínio transacional e consistência eventual em analytics
- Priorizar clareza arquitetural e rastreabilidade para valor de portfólio

