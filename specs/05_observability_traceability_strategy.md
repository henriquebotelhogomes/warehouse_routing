# Estratégia de Observabilidade e Rastreabilidade

## 1) Objetivos

- Detectar degradação antes de impactar operação
- Diagnosticar incidentes em minutos (não horas)
- Garantir rastreabilidade completa de decisão de rota

## 2) Modelo de telemetria

### Métricas (RED + USE)

- Request rate por endpoint e tenant
- Error rate por classe de erro
- Duration p50/p95/p99 por tipo de operação
- Utilização de CPU/memória/fila/banco

### Logs estruturados

- JSON padrão com `timestamp`, `level`, `service`, `request_id`, `trace_id`, `tenant_id`, `user_id`
- Campos de domínio: `warehouse_id`, `topology_version`, `route_strategy`

### Tracing distribuído

- Propagação de contexto W3C
- Span para validação, cálculo, consulta de cache, persistência e resposta

## 3) Rastreabilidade funcional

- Toda decisão de rota deve ser vinculada a:
  - Versão de topologia
  - Configuração de algoritmo usada
  - Contexto operacional recebido
  - ID de requisição e ator

## 4) Dashboards operacionais

1. **API Health**: latência, erros e saturação
2. **Routing Quality**: score médio, taxa de fallback, drift de performance
3. **Tenant Operations**: consumo de quota, falhas por integração
4. **Business Impact**: tempo economizado estimado e tendência

## 5) Alertas e resposta a incidentes

- Alertas por SLO (latência, erro, disponibilidade)
- Severidade definida (P1 a P4)
- Runbook por tipo de alerta
- Postmortem sem culpabilização e com ações preventivas

## 6) Governança de telemetria

- Taxonomia de métricas e eventos versionada
- Revisão de observabilidade em toda mudança de endpoint crítico
- Dados sensíveis mascarados em logs e traces

