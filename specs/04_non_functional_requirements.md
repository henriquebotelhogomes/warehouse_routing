# Requisitos Nao Funcionais (NFR)

## 1) Disponibilidade e confiabilidade

- SLO de disponibilidade da API: **99.9%** mensal
- Error budget definido por plano (interno no MVP, contratual no enterprise)
- Estratégias: health checks, retries com backoff, circuit breaker, rollback automático

## 2) Performance

- Latência alvo rota síncrona: p95 <= 300 ms (sem retreinamento)
- p99 <= 700 ms para payload padrão
- Throughput alvo inicial: 200 RPS agregado com escala horizontal

## 3) Escalabilidade

- Escala horizontal stateless para API/BFF
- Workers escaláveis por fila e tipo de job
- Separação de read/write em banco quando houver necessidade

## 4) Segurança

- TLS obrigatório em trânsito
- Criptografia em repouso para dados sensíveis
- Segredos em cofre gerenciado
- Princípio de menor privilégio para serviços e operadores

## 5) Observabilidade

- Cobertura de telemetria para 100% dos endpoints críticos
- Traces distribuídos com correlação por `request_id` e `tenant_id`
- Alertas com runbooks para incidentes comuns

## 6) Manutenibilidade

- Cobertura mínima de testes para domínio crítico >= 80%
- Padrões de arquitetura e código documentados
- Versionamento semântico para APIs públicas

## 7) Qualidade de dados e governança

- Auditoria imutável para ações administrativas
- Política de retenção por categoria de dado
- Catálogo básico de eventos e métricas de produto

## 8) Conformidade (meta progressiva)

- MVP: baseline de boas práticas (LGPD-aware)
- Growth: controles para trilhas de auditoria e gestão de consentimento
- Enterprise: preparação para SOC 2 tipo I/II (quando fizer sentido comercial)

