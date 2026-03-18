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
├── data/                    # Armazenamento persistente do modelo (.joblib)
├── src/
│   └── warehouse_routing/   # Pacote principal
│       ├── api/             # Camada de Exposição (FastAPI)
│       │   ├── main.py      # Entrypoint da API e Lifespan management
│       │   └── schemas.py   # Definições Pydantic (Contratos de Dados)
│       ├── app/             # Camada de Visão (Streamlit)
│       │   └── dashboard.py # Interface interativa e reativa
│       └── core/            # O "Cérebro" (Lógica de Negócio e IA)
│           ├── config.py    # Gestão de configurações e variáveis de ambiente
│           ├── q_learning.py# Implementação do Agente de Reinforcement Learning
│           └── visualizer.py# Engine de geração de grafos e heatmaps
├── tests/                   # Suíte de testes automatizados (Unitários e Integração)
├── Dockerfile               # Build multi-stage otimizado para produção
├── docker-compose.yml       # Orquestração local de múltiplos serviços
├── pyproject.toml           # Gestão moderna de dependências (PEP 518)
└── render.yaml              # Infraestrutura como Código (Blueprint do Render)
```

## Como Executar
### Via Docker (Recomendado)
Para subir todo o ecossistema (IA + API + Dashboard) com um único comando:
```
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

---
## 👨‍💻 Autor
**Henrique Botelho Gomes**

*Engenheiro de Software Sênior | Pós-graduando em IA (UFV)*
* **LinkedIn**: [linkedin.com/in/henriquebotelhogomes]()
* **GitHub**: [github.com/henriquebotelhogomes]()
---
*Este projeto foi desenvolvido com foco em escalabilidade, performance e padrões de engenharia de software modernos.*