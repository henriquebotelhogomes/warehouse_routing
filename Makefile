# ==========================================
# WAREHOUSE ROUTING - MAKEFILE PROFISSIONAL
# ==========================================

.PHONY: help install run-api run-dashboard run-tuner lint format test docker-up docker-down clean-ai clean-all

# Variáveis de Ambiente
PYTHON = python
PIP = pip
STREAMLIT = streamlit
UVICORN = uvicorn
DOCKER_COMPOSE = docker-compose
PYTHONPATH = export PYTHONPATH=src

help: ## Exibe esta mensagem de ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- INSTALAÇÃO ---
install: ## Instala dependências do projeto e ferramentas de desenvolvimento
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]
	@echo "✅ Ambiente configurado com sucesso!"

# --- EXECUÇÃO LOCAL ---
run-api: ## Inicia a API FastAPI localmente (Porta 8000)
	$(PYTHONPATH) && $(PYTHON) run.py

run-dashboard: ## Inicia o Dashboard Streamlit localmente (Porta 8501)
	$(PYTHONPATH) && $(STREAMLIT) run src/warehouse_routing/app/dashboard.py

run-tuner: ## Executa a otimização de hiperparâmetros com Optuna
	$(PYTHONPATH) && $(PYTHON) src/warehouse_routing/core/tuner.py

# --- QUALIDADE E TESTES ---
lint: ## Executa checagem de estilo (Ruff) e tipagem (Mypy)
	ruff check .
	mypy src/

format: ## Formata o código automaticamente usando Ruff
	ruff format .

test: ## Executa os testes unitários e de integração
	$(PYTHONPATH) && pytest tests/

# --- INFRAESTRUTURA (DOCKER) ---
docker-up: ## Sobe todo o ecossistema (API + Dashboard) via Docker Compose
	$(DOCKER_COMPOSE) up --build

docker-down: ## Encerra os containers e limpa a rede
	$(DOCKER_COMPOSE) down

# --- GESTÃO DA INTELIGÊNCIA (IA) ---
clean-ai: ## Remove o modelo treinado (.joblib) para forçar um novo aprendizado
	rm -f warehouse_q_model.joblib
	@echo "🧠 Memória da IA limpa. O próximo treino será do zero."

clean-all: clean-ai ## Limpa caches do Python e arquivos temporários
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "🧹 Limpeza completa realizada."