# Riscos, Premissas e Decisoes Arquiteturais

## 1) Premissas

- O problema de roteamento tem dor real de negócio e disposição de pagamento
- Integração via API é viável sem trocar WMS/TMS do cliente
- Dados de topologia e eventos operacionais terão qualidade mínima aceitável
- O time irá priorizar telemetria e segurança desde o início

## 2) Principais riscos

1. **Risco de produto**: baixa adoção se UX não gerar confiança operacional
2. **Risco técnico**: degradação de latência com aumento de topologias complexas
3. **Risco de dados**: entradas inconsistentes comprometem qualidade de recomendação
4. **Risco de segurança**: exposição indevida em ambiente multi-tenant
5. **Risco de escopo**: tentar construir "enterprise" cedo demais

## 3) Mitigações propostas

- Discovery contínuo com usuários de operações
- Guardrails de performance e testes de carga desde MVP
- Pipeline de validação de topologia e qualidade de dados
- Hardening de authN/authZ e segregação de tenant
- Roadmap incremental com critérios claros de entrada por fase

## 4) Decisoes arquiteturais (ADR resumidas)

### ADR-001: Monolito modular no inicio

- **Decisão**: iniciar com monolito modular, com boundaries explícitos
- **Motivo**: velocidade de entrega e menor complexidade operacional
- **Consequência**: exige disciplina de modularidade para futuras extrações

### ADR-002: Multi-tenancy por isolamento lógico forte

- **Decisão**: tenant_id obrigatório em entidades e políticas de acesso
- **Motivo**: equilíbrio entre custo e escalabilidade no estágio inicial
- **Consequência**: validações e testes de isolamento são mandatórios

### ADR-003: Observabilidade padrao OpenTelemetry

- **Decisão**: padronizar logs, métricas e traces desde a primeira release SaaS
- **Motivo**: reduzir MTTR e aumentar confiabilidade percebida
- **Consequência**: maior esforço inicial, ganho operacional sustentado

### ADR-004: Frontend React/Next.js com BFF

- **Decisão**: adotar Next.js e camada BFF para experiência consistente
- **Motivo**: melhor UX, segurança de sessão e composição de dados
- **Consequência**: requer governança clara de contratos entre BFF e serviços

### ADR-005: Segurança por padrão no SDLC

- **Decisão**: SAST/SCA obrigatórios e gestão de segredos centralizada
- **Motivo**: reduzir riscos críticos e elevar maturidade para mercado enterprise
- **Consequência**: pipeline mais rigoroso e disciplina contínua do time

## 5) Open questions para proxima fase

- Qual recorte de integração terá maior ROI no piloto (WMS A, B ou C)?
- Quais métricas de ganho serão aceitas pelo cliente como prova de valor?
- Quais limites de latência são realmente críticos por contexto operacional?
- Quais requisitos de compliance são obrigatórios no segmento-alvo inicial?

