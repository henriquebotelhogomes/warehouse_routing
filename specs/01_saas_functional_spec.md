# Especificação Funcional do SaaS

## 1) Escopo funcional (MVP SaaS)

### Capacidades obrigatórias

1. **Gestão de organização e usuários**
   - Criação de organização (tenant)
   - Convite de usuários
   - Perfis: Admin, Operações, Leitor

2. **Gestão de warehouses e topologias**
   - Cadastro de warehouses
   - Importação de topologia (JSON/CSV validado)
   - Versionamento de layout com histórico

3. **Roteamento inteligente**
   - Cálculo de rota entre origem e destino (com opcional de ponto intermediário)
   - Replanejamento com bloqueios dinâmicos
   - Retorno de rota + score + explicação resumida

4. **Simulação e comparação**
   - Simular cenários antes de publicar mudanças
   - Comparar rota sugerida vs baseline

5. **Painel operacional**
   - Visão de throughput, latência, erros, economia estimada
   - Filtros por warehouse, turno, período e tenant

6. **API pública + chaves de API**
   - Emissão/rotação/revogação de API keys
   - Quotas por plano

## 2) Funcionalidades para fase Growth

- Webhooks de eventos (rota degradada, bloqueio crítico, falha de integração)
- Relatórios de ROI por período e por warehouse
- Catálogo de integrações (WMS/TMS)
- Sandbox por tenant

## 3) Jornada funcional principal (happy path)

1. Admin cria tenant e convida equipe
2. Operações cadastra warehouse e importa topologia
3. Sistema valida topologia e gera baseline
4. Operações ativa roteamento inteligente
5. API recebe requisições de rota do WMS/TMS
6. Dashboard exibe performance e ganhos
7. Time ajusta topologia conforme eventos reais

## 4) Regras de negócio críticas

- Cada recurso pertence a um único tenant
- Requisição de rota exige warehouse ativo e topologia publicada
- Mudança de topologia cria nova versão e mantém audit trail
- Quotas e rate limit aplicados por tenant/plano
- Logs de auditoria devem registrar "quem", "o quê", "quando" e "por quê"

## 5) Casos de uso priorizados para recrutadores

- **CU-01**: Atualizar bloqueio de corredor e validar replanejamento em segundos
- **CU-02**: Comparar eficiência pré/pós mudança de layout
- **CU-03**: Investigar incidente de rota com trace completo por request
- **CU-04**: Governar acesso por função em ambiente multi-time

## 6) Fora de escopo nesta fase

- Marketplace de plugins
- App mobile nativo
- Otimização multi-objetivo avançada em tempo real com GPU

## 7) Critérios de aceite de produto (alto nível)

- Fluxo E2E funcional: onboarding -> integração -> operação -> análise
- Cada funcionalidade crítica com telemetria e trilha de auditoria
- UX do dashboard permite tomada de decisão sem depender de logs técnicos
- Documentação orientada a integração disponível para usuário técnico

