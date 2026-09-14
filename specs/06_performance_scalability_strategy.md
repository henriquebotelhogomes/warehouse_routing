# Estratégia de Performance e Escalabilidade

## 1) Metas de performance por fase

### MVP

- p95 de rota síncrona <= 300 ms
- cold start controlado com cache de modelos
- throughput estável em picos de operação planejados

### Growth

- Escala horizontal automática por métrica de fila e CPU
- Redução de tail latency com otimizações de caminho crítico

## 2) Táticas de performance

- Cache de resultados de rota de curta duração por contexto válido
- Pré-aquecimento de topologias e modelos mais usados
- Uso de pool de conexão de banco e tuning de queries
- Offload de tarefas pesadas para workers assíncronos
- Limites de payload e validações cedo (fail fast)

## 3) Estratégia de escalabilidade

- API stateless com auto scaling
- Workers dedicados por tipo de job (simulação, treino, relatório)
- Filas separadas por prioridade para proteger operações críticas
- Particionamento lógico por tenant conforme crescimento

## 4) Gestão de capacidade

- Planejamento com cenários de pico (turnos, sazonalidade)
- Testes de carga e stress periódicos
- Capacity review mensal com tendências e margem de segurança

## 5) Performance engineering no ciclo de entrega

- Benchmarks de endpoint crítico no CI (smoke de performance)
- Regressão de latência bloqueando release quando ultrapassar limite
- Perfilamento contínuo de hotspots do algoritmo

## 6) Estratégia de custo x desempenho

- Classe de serviço por plano (Starter/Growth/Enterprise)
- Políticas de quota e burst para evitar noisy neighbor
- Escala orientada a custo unitário por requisição

