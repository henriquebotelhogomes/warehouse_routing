# Especificação Técnica de Alto Nível

## 1) Stack-alvo (proposta)

- **Backend**: Python + FastAPI (evoluindo base existente), workers assíncronos
- **Frontend**: React + TypeScript + Next.js (App Router)
- **Dados**: PostgreSQL (transacional), Redis (cache/fila curta), object storage para artefatos
- **Mensageria**: fila para tarefas de simulação e jobs de otimização assíncronos
- **Observabilidade**: OpenTelemetry + Prometheus + Grafana + Sentry
- **Infra**: containers, orquestração Kubernetes (ou equivalente gerenciado), IaC

## 2) Domínios técnicos

1. **Identity & Access**
   - Autenticação (OIDC/JWT)
   - Autorização por papéis e políticas

2. **Routing Intelligence**
   - Serviço de cálculo de rota (sync)
   - Serviço de treino/ajuste (async)
   - Serviço de avaliação de qualidade de recomendação

3. **Warehouse Topology**
   - Versionamento de layout
   - Validação semântica da malha

4. **Usage & Billing**
   - Metering por endpoint/tenant
   - Controle de limites e cobrança por plano

5. **Analytics & Reporting**
   - KPIs de operação e ganho estimado
   - Relatórios auditáveis

## 3) Contratos e integração

- API versionada (`/v1`, `/v2`) com compatibilidade retroativa limitada por janela
- Idempotência para operações críticas
- Webhooks assinados para eventos externos
- SDKs oficiais (Python/TypeScript) após estabilização de contrato

## 4) Estratégia de dados

- **OLTP**: PostgreSQL para entidades de produto e auditoria
- **Cache**: Redis para resultados de rota de curta validade e rate limiting
- **Eventos**: trilha de eventos para debugging operacional e analytics
- **Retenção**: política por tipo de dado (telemetria, auditoria, operacional)

## 5) Qualidade e ciclo de entrega

- Trunk-based development com feature flags
- Test pyramid (unitário, integração, contrato, E2E)
- CI com qualidade obrigatória (lint, tipagem, segurança, testes)
- CD com deploy progressivo (canary/blue-green)

## 6) Decisões para alto impacto em portfólio

- Arquitetura orientada a domínio com boundaries explícitos
- Telemetria desenhada desde o início (não pós-fato)
- Segurança por padrão (least privilege, segredos gerenciados)
- Frontend com design system e instrumentação de UX

