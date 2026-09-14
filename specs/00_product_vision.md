# Plano de Produto - Warehouse Routing Cloud

## 1) Visão

Transformar o motor de roteamento de armazéns com aprendizado por reforço em uma plataforma SaaS B2B para operações logísticas, focada em reduzir tempo de picking, melhorar previsibilidade operacional e acelerar decisões em ambiente dinâmico.

## 2) Problema de negócio

Operações de warehouse ainda usam rotas estáticas, regras manuais e sistemas legados com baixa adaptabilidade a bloqueios, alterações de layout e picos de demanda. Isso gera:

- Maior tempo de ciclo por pedido
- Menor produtividade por operador
- Queda de SLA de expedição
- Dificuldade de provar ROI de otimização

## 3) Proposta de valor

- **Roteamento adaptativo com IA**: rotas recalculadas com contexto operacional (bloqueios, prioridades, congestionamento)
- **Integração rápida**: API-first para acoplar a WMS/TMS sem reescrever sistemas existentes
- **Transparência operacional**: explicabilidade da rota e indicadores de ganho
- **Escalabilidade SaaS**: multi-tenant, observável, seguro e pronto para evolução enterprise

## 4) Público-alvo (ICP)

### Segmento principal

- Operadores logísticos (3PL), e-commerce em crescimento e varejo omnichannel
- Empresas com 1 a 20 armazéns e pressão por eficiência de picking

### Personas

- **Head de Operações**: quer reduzir custo por pedido e cumprir SLA
- **Gerente de Warehouse**: quer visibilidade e resposta rápida a mudanças no chão de armazém
- **Tech Lead/CTO**: quer integração simples, segurança e governança

## 5) Posicionamento de mercado

"Plataforma de inteligência de roteamento para warehouse operations com foco em ganho operacional comprovável e integração rápida em stack legado."

## 6) Diferenciação técnica e de mercado

- **Modelagem híbrida**: regra de negócio + aprendizado por reforço (evita "caixa-preta" pura)
- **Operação em tempo real**: mudança de topologia sem reimplantar modelo
- **Produto orientado a ROI**: cada recomendação de rota ligada a métricas de economia
- **Arquitetura moderna de produto**: telemetria ponta a ponta, trilha de auditoria e readiness para compliance

## 7) Modelo de negócio SaaS (proposta inicial)

- **Starter**: baixo volume, 1 warehouse, onboarding self-service
- **Growth**: múltiplos warehouses, analytics avançada, integrações
- **Enterprise**: SSO, governança avançada, SLA e suporte premium

## 8) Métricas norteadoras

- **Produto**: tempo médio de rota, taxa de sucesso de roteamento, adoção por operador
- **Negócio**: MRR, expansão de conta, churn de logo, LTV/CAC
- **Engenharia**: disponibilidade, latência p95, taxa de erro por tenant

## 9) Critérios de sucesso do projeto de portfólio

- Demonstração clara de arquitetura SaaS real (não só PoC algorítmica)
- Evidência de maturidade de engenharia (segurança, SRE, qualidade, governança)
- Narrativa de produto orientada a impacto de negócio
- Frontend premium com UX profissional e foco em decisão operacional

