# 🤖 AI Warehouse Optimizer: Otimização Logística com Q-Learning

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-05998b.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-ff4b4b.svg)](https://streamlit.io/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checking: Mypy](https://img.shields.io/badge/type%20checking-mypy-blue.svg)](http://mypy-lang.org/)

> **Status do Projeto:** 🚀 Live em Produção  
> 
> **Link da Aplicação:** [https://warehouse-dashboard-zre8.onrender.com](https://warehouse-dashboard-zre8.onrender.com)
> 
> **Link da API:** [https://warehouse-api-upii.onrender.com/docs](https://warehouse-api-upii.onrender.com/docs)

Este projeto implementa um sistema inteligente de roteamento para armazéns logísticos utilizando **Aprendizado por Reforço (Q-Learning)**. O sistema é capaz de encontrar a trajetória mais eficiente entre pontos de coleta e entrega, adaptando-se dinamicamente a obstruções e priorizando pontos intermediários.

---

## 🎯 Destaques Técnicos (Recruiter Focus)

Este repositório demonstra competências de nível **Sênior** em engenharia de software e IA aplicada:

*   **IA em Produção:** Implementação de Q-Learning com persistência de estado (`joblib`) e ciclo de vida resiliente.
*   **Arquitetura de Microserviços:** Separação clara entre **Backend (FastAPI)** e **Frontend (Streamlit)**, garantindo escalabilidade independente.
*   **Observabilidade & Logs:** Uso de `Loguru` para logs estruturados e `Correlation ID` para rastreabilidade de requisições ponta a ponta.
*   **Qualidade de Código:** Pipeline de CI/CD validando tipagem estática com `Mypy`, linting com `Ruff` e testes automatizados com `Pytest`.
*   **DevOps Moderno:** Containerização multi-stage com `Docker`, orquestração via `Docker Compose` e infraestrutura como código (IaC) via `Render Blueprints`.

---

## 🚀 Diferenciais Técnicos & Engenharia de Produção

Diferente de implementações acadêmicas, este projeto foca em **robustez e confiabilidade**:

### 1. Gestão de Ciclo de Vida (Lifespan Management)
A API utiliza o padrão `lifespan` do FastAPI para gerenciar o estado da IA. Implementamos uma lógica de **carregamento resiliente**: se o arquivo de modelo (`.joblib`) não for encontrado (ex: primeiro deploy), o sistema inicia sem cache e treina sob demanda, evitando o crash do container (*Cold Start Resilience*).

### 2. Observabilidade Sênior
*   **Logs Estruturados:** Configuração customizada do `Loguru` para saída padronizada, facilitando a ingestão por ferramentas de monitoramento.
*   **Tracing:** Implementação de `Correlation ID Middleware`, injetando um ID único em cada requisição para rastrear o fluxo de dados entre logs de diferentes serviços.

### 3. Middleware de Performance
Desenvolvimento de um middleware customizado para medir a latência de processamento da IA, injetando o tempo de resposta no header HTTP `X-Process-Time-Ms`.

### 4. Interface Reativa (Streamlit UX)
Uso de `st.session_state` e gerenciamento de chaves de widgets para resolver problemas de reatividade. O dashboard habilita/desabilita campos de entrada instantaneamente com base na lógica de negócio, sem a necessidade de submissão de formulários lentos.

---
## 📂 Estrutura do Projeto
```
warehouse_routing/
├── src/
│   └── warehouse_routing/
│       ├── api/                          # Endpoints FastAPI para rotas e visualizações
│       │   ├── __init__.py               # Inicialização do pacote API
│       │   ├── main.py                   # App FastAPI principal com lifespan, middlewares e rotas (/routes, /visualize, /health)
│       │   └── schemas.py                # Modelos Pydantic para validação de requests/responses (RouteRequest, RouteResponse)
│       ├── core/                         # Lógica central de IA e otimização
│       │   ├── __init__.py               # Inicialização do pacote core
│       │   ├── config.py                 # Configurações globais (LOCATIONS, BASE_REWARDS_MATRIX, settings com Pydantic)
│       │   ├── q_learning.py             # Implementação do WarehouseRouteOptimizer (Q-Learning com treinamento e inferência)
│       │   ├── tuner.py                  # Otimização de hiperparâmetros (gamma, alpha) para o Q-Learning
│       │   └── visualizer.py             # Geração de imagens (grafos e heatmaps da Q-Table com NetworkX/Matplotlib)
│       └── app/                          # Aplicações complementares (ex: dashboard Streamlit)
│           └── dashboard.py              # Interface Streamlit para visualização interativa de rotas
├── tests/                                # Testes unitários e de integração (pytest)
│   ├── conftest.py                       # Fixtures compartilhadas (client FastAPI, optimizer isolado, sample requests)
│   ├── test_api.py                       # Testes de endpoints (rotas, health, visualizações)
│   └── test_optimizer.py                 # Testes do Q-Learning (rotas válidas/inválidas, treinamento)
├── .github/                              # Configurações de CI/CD
│   └── workflows/
│       ├── ci.yml                        # Pipeline de testes, lint (Ruff), tipagem (Mypy) e formatação
│       └── main.yml                      # Workflow principal para deploy e validação
├── docs/                                 # Documentação (opcional, para expansão)
│   └── api.md                            # Especificação da API (endpoints, exemplos de uso)
├── Dockerfile                            # Containerização para deploy (base Python 3.12, uv para dependências)
├── docker-compose.yml                    # Orquestração local (API + Dashboard)
├── render.yaml                           # Configuração de deploy no Render (serviço web com GitHub integration)
├── pyproject.toml                        # Gerenciamento de dependências (uv), Ruff, Mypy e metadados do projeto
├── .pre-commit-config.yaml               # Hooks para lint e formatação automática (Ruff, Mypy)
├── .dockerignore                         # Ignora arquivos desnecessários no build Docker
├── run.py                                # Script de execução local (uvicorn para API)
├── .env.example                          # Template de variáveis de ambiente (API_URL, MODEL_PATH)
├── .gitignore                            # Ignora .venv, __pycache__, .pytest_cache
└── README.md                             # Este arquivo: visão geral, instalação e uso
```

## Como Executar
### Via Docker (Recomendado)
Para subir todo o ecossistema (IA + API + Dashboard) com um único comando:
```
# 1. Clone o repositório
git clone https://github.com/henriquebotelhogomes/warehouse_routing.git

# 2. Suba os containers
docker-compose up --build
```
* **Dashboard**: http://localhost:8501
* **Swagger UI**: http://localhost:8000/docs

## Desenvolvimento Local
```
# Instalar dependências em modo editável
pip install -e ".[dev]"

# Rodar API
uvicorn warehouse_routing.api.main:app --reload

# Rodar Dashboard
streamlit run src/warehouse_routing/app/dashboard.py
```
---
## 🧪 Qualidade e Verificação
```
# Executar suíte de testes
pytest tests/

# Verificar tipagem estática
mypy src/

# Formatação e Linting
ruff check src/
```
---
## 🧠 O Algoritmo: Q-Learning

O motor de decisão utiliza uma Matriz de Recompensas para aprender a topologia do armazém. Através de episódios de treinamento, a IA preenche uma Q-Table que mapeia a melhor ação para cada estado possível. Diferente de algoritmos estáticos, o Q-Learning permite que o sistema se adapte a mudanças dinâmicas no layout do armazém sem necessidade de reprogramação.

$$
Q(s, a) \leftarrow Q(s, a) + \alpha \left[ r + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]
$$

**Explicação dos Termos**:
* **( Q(s, a) )**: Valor Q atual para o estado ( s ) e ação ( a ).
* **( \alpha )**: Taxa de aprendizado (learning rate, entre 0 e 1).
* **( r )**: Recompensa imediata recebida após executar a ação ( a ) no estado ( s ).
* **( \gamma )**: Fator de desconto (discount factor, entre 0 e 1), que pondera recompensas futuras.
* **( s' )**: Próximo estado após a ação ( a ).
* **( \max_{a'} Q(s', a') )**: O melhor valor Q possível no próximo estado ( s' ), considerando todas as ações possíveis ( a' ).

---
## 👨‍💻 Autor
**Henrique Botelho Gomes**

*Engenheiro de Software Sênior | Pós-graduando em IA (UFV)*
* **LinkedIn**: [linkedin.com/in/henriquebotelhogomes]()
* **GitHub**: [github.com/henriquebotelhogomes]()
---
*Este projeto foi desenvolvido com foco em escalabilidade, performance e padrões de engenharia de software modernos.*