# 🤖 Warehouse AI Route Optimizer

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-05998b.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ed.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Warehouse AI Route Optimizer** é uma solução de ponta para logística inteligente, utilizando **Aprendizado por Reforço (Q-Learning)** para otimizar rotas de picking em armazéns dinâmicos. O sistema é capaz de recalcular trajetórias em milissegundos diante de bloqueios em tempo real, oferecendo uma interface visual completa e monitoramento de performance de nível de produção.

---

## 🏗️ Arquitetura do Sistema

O projeto segue padrões modernos de arquitetura de software, separando a inteligência computacional da interface de entrega.
```mermaid
graph TD
    subgraph "Client Layer"
    end

    subgraph "Intelligence Layer (Core)"
        B --> C[Q-Learning Engine]
        C --> D[Optuna Tuner]
        C --> E[NetworkX Graph]
    end

    subgraph "Persistence & Observability"
        C --> F[Joblib Model Storage]
        B --> G[Loguru Structured Logs]
        B --> H[Correlation ID Middleware]
    end
````
---
## 📂 Estrutura do Projeto
```
warehouse_routing/
├── data/                       # Persistência da Q-Table (Inteligência da IA)
├── src/                        # Código-fonte principal (Src Layout)
│   └── warehouse_routing/
│       ├── __init__.py
│       ├── api/                # Camada de Interface HTTP (FastAPI)
│       │   ├── __init__.py
│       │   ├── main.py         # Endpoints e Middlewares
│       │   └── schemas.py      # Contratos Pydantic (Validação)
│       ├── core/               # O Coração do Sistema (Lógica de Negócio)
│       │   ├── __init__.py
│       │   ├── config.py       # Configurações e Matriz de Recompensas
│       │   ├── q_learning.py   # Motor de Reinforcement Learning
│       │   ├── tuner.py        # Otimização com Optuna
│       │   └── visualizer.py   # Geração de Gráficos e Heatmaps
│       └── app/                # Interface Visual (Frontend)
│           ├── __init__.py
│           └── dashboard.py    # Painel Streamlit
├── tests/                      # Testes Unitários e de Integração
├── .dockerignore               # Filtros para imagens Docker
├── .env                        # Variáveis de ambiente (Alpha, Gamma, etc.)
├── docker-compose.yml          # Orquestração de Containers
├── Dockerfile                  # Receita de Build Multi-stage
├── pyproject.toml              # Gestão de Dependências e Tooling (PEP 621)
└── run.py                      # Script de entrada para execução local
```
---
## 🌟 Diferenciais Técnicos (Destaque para Recrutadores)
* **IA Dinâmica**: Implementação de Q-Learning com suporte a alteração de topologia em tempo real (bloqueio de corredores).
* **Otimização de Hiperparâmetros**: Uso de Optuna para encontrar automaticamente os melhores valores de **Alpha** (taxa de aprendizado) e **Gamma** (fator de desconto).
* **Observabilidade Sênior**:

  * Injeção de X-Process-Time-Ms nos headers de resposta.
  * Rastreabilidade total com Correlation IDs em todos os logs.


* **Visualização Científica**: Geração dinâmica de Heatmaps (Seaborn) e Grafos (NetworkX) servidos via Streaming de imagem.
* **Infraestrutura Moderna**: Dockerização multi-stage e orquestração com Docker Compose.
---
## 🧠 O Motor de IA: Q-Learning
O agente aprende a rota ótima maximizando a recompensa acumulada através da equação de Bellman:

**Q(s,a)=Q(s,a)+α[R(s,a)+γmax⁡Q(s′,a′)−Q(s,a)]Q(s, a) = Q(s, a) + \alpha [R(s, a) + \gamma \max Q(s', a') - Q(s, a)]Q(s,a)=Q(s,a)+α[R(s,a)+γmaxQ(s′,a′)−Q(s,a)]** 

Onde:
* **$\alpha$ (Alpha)**: Define o quanto a nova informação sobrescreve a antiga.
* **$\gamma$ (Gamma)**: Define a importância de recompensas futuras (visão de longo prazo).
---
## 🚀 Como Executar (Docker First)
A maneira mais rápida e profissional de rodar o ecossistema completo é via **Docker Compose**.
### Pré-requisitos
* Docker e Docker Compose instalados.
## Passo a Passo
1. Clonar o repositório:
```
   git clone https://github.com/seu-usuario/warehouse-routing.git
   cd warehouse-routing
```
2. Subir o ecossistema:
```
   docker-compose up --build
```
3. Acessar as interfaces:
* **Dashboard Interativo**: http://localhost:8501
* **Documentação API (Swagger)**: http://localhost:8000/docs
---
## 🛠️ Stack Tecnológica

| Categoria                | Tecnologia                               |
|--------------------------|------------------------------------------|
| **Linguagem**            | Python 3.12+                             |
| **Framework API**        | FastAPI                                  |
| **IA / Matemática**      | NumPy, Optuna, Joblib                    |
| **Visualização**         | Streamlit, Matplotlib, Seaborn, NetworkX |
| **Logs / Monitoramento** | Loguru, ASGI Correlation ID              |
| **DevOps**               | Docker, Docker Compose, GitHub Actions   |
---
## 📈 Endpoints Principais
* **POST /api/v1/routes**: Calcula a rota ótima entre dois pontos.
* **PUT /api/v1/warehouse/paths**: Bloqueia ou abre corredores dinamicamente.
* **GET /api/v1/visualize/graph**: Retorna a imagem do mapa atual.
* **POST /api/v1/ai/retrain**: Força o retreino total da inteligência.
---
## 👨‍💻 AutorHenrique Botelho Gomes
_Engenheiro de Software Sênior | Pós-graduando em IA (UFV)_


