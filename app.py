import streamlit as st
from auth import login

st.set_page_config(page_title="Portal", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = login(u, p)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Usuário/senha inválidos ou usuário inativo.")
    st.stop()

st.sidebar.write(f"Logado: **{st.session_state.user['name']}**")

# ✅ Sem callback → sem aviso
if st.sidebar.button("Sair"):
    st.session_state.user = None
    st.rerun()

menu = ["Dashboards"]
if st.session_state.user["role"] == "admin":
    menu.append("Admin")

page = st.sidebar.radio("Menu", menu)

if page == "Dashboards":
    import dashboards_page
    dashboards_page.render()
else:
    import admin_page
    admin_page.render()
