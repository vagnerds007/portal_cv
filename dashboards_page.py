import re
import streamlit as st
from db_conn import query


def extract_src(value: str) -> str:
    value = (value or "").strip()
    m = re.search(r'src="([^"]+)"', value, flags=re.IGNORECASE)
    return m.group(1) if m else value


def add_powerbi_params(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return url

    sep = "&" if "?" in url else "?"
    if "filterPaneEnabled=" not in url:
        url += f"{sep}filterPaneEnabled=false"
        sep = "&"
    if "navContentPaneEnabled=" not in url:
        url += f"{sep}navContentPaneEnabled=false"
    return url


def render():
    st.set_page_config(page_title="Dashboards", layout="wide")

    # Mantemos o header visível para NÃO perder a setinha de expandir/recolher sidebar
    # Só reduzimos paddings para ganhar espaço na tela.
    st.markdown(
    """
    <style>
      /* Mantém o header do Streamlit visível (para o botão da sidebar) */
      header[data-testid="stHeader"] {
          height: auto;
          min-height: 3.5rem;
      }

      /* Ajusta o espaçamento do conteúdo sem esmagar o título */
      .block-container {
          padding-top: 1.2rem;
          padding-bottom: 0.5rem;
      }

      /* Ajusta o título principal */
      h1 {
          margin-top: 0rem;
          padding-top: 0rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
    )


    if "user" not in st.session_state or st.session_state.user is None:
        st.error("Você precisa estar logado.")
        st.stop()

    # Botão opcional dentro da página (não depende do header)
    # Serve como "plano B" caso o usuário queira controlar o menu facilmente.
    if "show_hint" not in st.session_state:
        st.session_state.show_hint = True

    top = st.container()
    with top:
        col1, col2 = st.columns([1, 8])
        with col1:
            st.button("☰ Menu", help="Use a setinha do Streamlit no topo para recolher/expandir. Este botão é apenas um atalho visual.")
        with col2:
            st.title("Seus dashboards")

    uid = st.session_state.user["id"]

    rows = query(
        """
        SELECT d.name, d.embed_url
        FROM dashboards d
        JOIN user_dashboards ud ON ud.dashboard_id = d.id
        WHERE ud.user_id = :uid
        ORDER BY d.name
        """,
        {"uid": uid},
    )

    if rows.empty:
        st.info("Nenhum dashboard atribuído a você.")
        st.stop()

    name_to_url = dict(zip(rows["name"], rows["embed_url"]))
    choice = st.selectbox("Selecione um dashboard", list(name_to_url.keys()))

    embed_url = extract_src(name_to_url[choice])
    embed_url = add_powerbi_params(embed_url)

    # Iframe sem rolagem (aumente height se precisar)
    st.components.v1.iframe(embed_url, height=950, scrolling=False)
