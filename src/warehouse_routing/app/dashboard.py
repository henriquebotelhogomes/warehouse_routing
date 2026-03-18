import os
from typing import Any, Dict, List, Optional

import requests  # type: ignore
import streamlit as st
from loguru import logger

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# =============================================================================
st.set_page_config(
    page_title="AI Warehouse Optimizer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização customizada com correção de contraste para as métricas
st.markdown(
    """
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    [data-testid="stMetric"] {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
        background-color: #ffffff;
    }
    [data-testid="stMetricValue"] > div {
        color: #1e3a8a !important;
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] > div {
        color: #374151 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# CONFIGURAÇÕES DE AMBIENTE E CONEXÃO
# =============================================================================
DEFAULT_API_URL: str = os.getenv("API_URL", "http://127.0.0.1:8000")

st.sidebar.header("⚙️ Configurações de Sistema")
api_base_url: str = st.sidebar.text_input("Endereço da API", value=DEFAULT_API_URL)

LOCATIONS: List[str] = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]


# =============================================================================
# FUNÇÕES UTILITÁRIAS (PROXY DE DADOS)
# =============================================================================
def fetch_image_from_api(endpoint: str) -> Optional[bytes]:
    """Busca a imagem da API via rede interna (Server-to-Server)."""
    try:
        url: str = f"{api_base_url}{endpoint}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content  # type: ignore
        logger.error(f"Erro na API ({response.status_code}): {endpoint}")
    except Exception as e:
        logger.error(f"Falha crítica de conexão com a API: {e}")
    return None


# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================
st.title("🤖 Warehouse AI Control Center")
st.caption("Otimização de Rotas Logísticas com Aprendizado por Reforço (Q-Learning)")

col_plan, col_viz = st.columns([1, 2], gap="large")

with col_plan:
    st.subheader("📍 Planejamento de Rota")

    with st.form("route_form"):
        st.info("Defina os pontos de movimentação de carga.")
        start_node: str = st.selectbox("Ponto de Partida (Origem)", LOCATIONS, index=0)
        end_node: str = st.selectbox("Ponto de Entrega (Destino)", LOCATIONS, index=6)

        st.markdown("---")
        use_inter: bool = st.checkbox("Incluir Ponto de Coleta Intermediário")

        # Opções para ponto intermediário (pode ser None)
        inter_options: List[Optional[str]] = [None] + list(LOCATIONS)  # type: ignore
        inter_node: Optional[str] = st.selectbox(
            "Ponto de Coleta", options=inter_options, index=0, disabled=not use_inter
        )

        submit: bool = st.form_submit_button("🚀 Calcular Rota Ótima")

    if submit:
        with st.spinner("IA calculando a melhor trajetória..."):
            payload: Dict[str, Any] = {
                "start": start_node,
                "end": end_node,
                "intermediary": inter_node if use_inter else None,
            }
            try:
                res = requests.post(f"{api_base_url}/api/v1/routes", json=payload)
                if res.status_code == 200:
                    data: Dict[str, Any] = res.json()
                    route: List[str] = data["route"]
                    steps: int = data["total_steps"]
                    st.success("✅ Rota calculada com sucesso!")
                    st.markdown("### 🛣️ Trajetória Sugerida:")
                    st.code(" ➔ ".join(route))

                    st.metric(label="Total de Movimentações", value=f"{steps} passos")
                else:
                    error_data: Dict[str, Any] = res.json()
                    error_detail: str = error_data.get("detail", "Erro desconhecido")
                    st.error(f"⚠️ Falha na API: {error_detail}")
            except Exception as e:
                st.error(f"❌ Erro de conexão: {e}")

with col_viz:
    st.subheader("🗺️ Monitoramento Visual")
    tab_map, tab_intel = st.tabs(["🌐 Mapa do Armazém", "🧠 Inteligência da IA"])

    with tab_map:
        graph_img: Optional[bytes] = fetch_image_from_api("/api/v1/visualize/graph")
        if graph_img:
            st.image(
                graph_img,
                caption="Topologia Atual do Armazém",
                width="content",
            )
            if st.button("🔄 Atualizar Mapa"):
                st.rerun()
        else:
            st.warning("Aguardando conexão com a API para carregar o mapa...")

    with tab_intel:
        st.write("Visualize o 'conhecimento' acumulado pela IA.")
        target_heatmap: str = st.selectbox("Selecione o Destino para análise", LOCATIONS, index=6)
        if st.button("📊 Gerar Heatmap de Recompensas"):
            with st.spinner("Gerando visualização da Q-Table..."):
                q_img: Optional[bytes] = fetch_image_from_api(
                    f"/api/v1/visualize/q-table/{target_heatmap}"
                )
                if q_img:
                    st.image(
                        q_img,
                        caption=f"Heatmap para Destino: {target_heatmap}",
                        width="content",
                    )
                else:
                    st.error("Não foi possível gerar o heatmap.")

st.sidebar.markdown("---")
st.sidebar.info(f"**Status:** API {api_base_url} | Python 3.12+")
