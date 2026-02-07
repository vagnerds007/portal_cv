import re
import streamlit as st
import bcrypt
from db_conn import query, execute


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def extract_src(value: str) -> str:
    """Aceita URL ou iframe completo e retorna a URL (src)."""
    value = (value or "").strip()
    m = re.search(r'src="([^"]+)"', value, flags=re.IGNORECASE)
    return m.group(1) if m else value


def render():
    st.title("Administração")

    tab_users, tab_dash, tab_links = st.tabs(["Usuários", "Dashboards", "Vínculos"])

    # =========================
    # TAB: USUÁRIOS
    # =========================
    with tab_users:
        st.subheader("Criar usuário")

        c_username = st.text_input("Usuário (login)", key="c_username").strip()
        c_name = st.text_input("Nome", key="c_name").strip()
        c_password = st.text_input("Senha inicial", type="password", key="c_password")
        c_role = st.selectbox("Perfil", ["user", "admin"], key="c_role")
        c_active = st.checkbox("Ativo", value=True, key="c_active")

        if st.button("Criar usuário", key="btn_create_user"):
            if not c_username or not c_name or not c_password:
                st.warning("Preencha Usuário, Nome e Senha.")
            else:
                try:
                    exists = query("SELECT id FROM users WHERE username=:u", {"u": c_username})
                    if not exists.empty:
                        st.warning("Esse usuário já existe. Use outro username ou edite o usuário abaixo.")
                    else:
                        execute(
                            "INSERT INTO users (username, name, password_hash, role, active) "
                            "VALUES (:username, :name, :ph, :role, :active)",
                            {
                                "username": c_username,
                                "name": c_name,
                                "ph": hash_pw(c_password),
                                "role": c_role,
                                "active": 1 if c_active else 0,
                            },
                        )
                        st.success("Usuário criado.")
                        st.rerun()
                except Exception as e:
                    st.exception(e)

        st.divider()
        st.subheader("Editar / Excluir usuário")

        try:
            users_df = query("SELECT id, username, name, role, active FROM users ORDER BY username")
        except Exception as e:
            st.exception(e)
            st.stop()

        if users_df.empty:
            st.info("Nenhum usuário cadastrado.")
        else:
            user_choice = st.selectbox("Usuário", users_df["username"].tolist(), key="edit_user_sel")
            row = users_df[users_df["username"] == user_choice].iloc[0]
            uid = int(row["id"])

            st.caption(f"Username (fixo): **{row['username']}**")
            e_name = st.text_input("Nome", value=str(row["name"]), key="e_name").strip()
            e_role = st.selectbox(
                "Perfil",
                ["user", "admin"],
                index=0 if row["role"] == "user" else 1,
                key="e_role",
            )
            e_active = st.checkbox("Ativo", value=(int(row["active"]) == 1), key="e_active")

            colA, colB, colC = st.columns(3)

            if colA.button("Salvar alterações", key="btn_save_user"):
                if not e_name:
                    st.warning("Nome não pode ficar vazio.")
                else:
                    try:
                        execute(
                            "UPDATE users SET name=:name, role=:role, active=:active WHERE id=:id",
                            {"name": e_name, "role": e_role, "active": 1 if e_active else 0, "id": uid},
                        )
                        st.success("Usuário atualizado.")
                        st.rerun()
                    except Exception as e:
                        st.exception(e)

            new_pw = st.text_input("Nova senha (reset)", type="password", key="e_new_pw")
            if colB.button("Resetar senha", key="btn_reset_pw"):
                if not new_pw:
                    st.warning("Informe a nova senha.")
                else:
                    try:
                        execute(
                            "UPDATE users SET password_hash=:ph WHERE id=:id",
                            {"ph": hash_pw(new_pw), "id": uid},
                        )
                        st.success("Senha atualizada.")
                    except Exception as e:
                        st.exception(e)

            # Excluir usuário (com confirmação)
            confirm_del_user = st.checkbox("Confirmo excluir este usuário", key="confirm_del_user")
            if colC.button("Excluir usuário", key="btn_del_user"):
                if not confirm_del_user:
                    st.warning("Marque a confirmação para excluir.")
                else:
                    try:
                        # remove vínculos primeiro (por garantia)
                        execute("DELETE FROM user_dashboards WHERE user_id=:uid", {"uid": uid})
                        execute("DELETE FROM users WHERE id=:uid", {"uid": uid})
                        st.success("Usuário excluído.")
                        st.rerun()
                    except Exception as e:
                        st.exception(e)

        st.divider()
        st.subheader("Lista de usuários")
        st.dataframe(
            query("SELECT id, username, name, role, active, created_at FROM users ORDER BY username"),
            use_container_width=True,
        )

    # =========================
    # TAB: DASHBOARDS
    # =========================
    with tab_dash:
        st.subheader("Cadastrar dashboard")

        dname = st.text_input("Nome do dashboard", key="d_name").strip()
        durl_raw = st.text_input("Embed URL (cole a URL do src ou o iframe)", key="d_url").strip()
        durl = extract_src(durl_raw)

        if st.button("Salvar dashboard", key="btn_save_dash"):
            if not dname or not durl:
                st.warning("Preencha Nome e URL.")
            else:
                try:
                    execute(
                        "INSERT INTO dashboards (name, embed_url) VALUES (:n, :u)",
                        {"n": dname, "u": durl},
                    )
                    st.success("Dashboard cadastrado.")
                    st.rerun()
                except Exception as e:
                    st.exception(e)

        st.divider()
        st.subheader("Editar / Excluir dashboard")

        dashes_df = query("SELECT id, name, embed_url FROM dashboards ORDER BY name")

        if dashes_df.empty:
            st.info("Nenhum dashboard cadastrado.")
        else:
            dash_choice = st.selectbox("Dashboard", dashes_df["name"].tolist(), key="edit_dash_sel")
            drow = dashes_df[dashes_df["name"] == dash_choice].iloc[0]
            did = int(drow["id"])

            e_dname = st.text_input("Nome", value=str(drow["name"]), key="e_dname").strip()
            e_durl_raw = st.text_input("URL (src ou iframe)", value=str(drow["embed_url"]), key="e_durl").strip()
            e_durl = extract_src(e_durl_raw)

            col1, col2 = st.columns(2)

            if col1.button("Atualizar dashboard", key="btn_update_dash"):
                if not e_dname or not e_durl:
                    st.warning("Nome e URL são obrigatórios.")
                else:
                    try:
                        execute(
                            "UPDATE dashboards SET name=:n, embed_url=:u WHERE id=:id",
                            {"n": e_dname, "u": e_durl, "id": did},
                        )
                        st.success("Dashboard atualizado.")
                        st.rerun()
                    except Exception as e:
                        st.exception(e)

            confirm_del_dash = st.checkbox("Confirmo excluir este dashboard", key="confirm_del_dash")
            if col2.button("Excluir dashboard", key="btn_del_dash"):
                if not confirm_del_dash:
                    st.warning("Marque a confirmação para excluir.")
                else:
                    try:
                        execute("DELETE FROM user_dashboards WHERE dashboard_id=:id", {"id": did})
                        execute("DELETE FROM dashboards WHERE id=:id", {"id": did})
                        st.success("Dashboard excluído.")
                        st.rerun()
                    except Exception as e:
                        st.exception(e)

        st.divider()
        st.subheader("Lista de dashboards")
        st.dataframe(query("SELECT id, name, embed_url FROM dashboards ORDER BY name"), use_container_width=True)

    # =========================
    # TAB: VÍNCULOS
    # =========================
    with tab_links:
        st.subheader("Vincular dashboards a usuário")

        users_df2 = query("SELECT id, username FROM users ORDER BY username")
        dashes_df2 = query("SELECT id, name FROM dashboards ORDER BY name")

        if users_df2.empty:
            st.info("Nenhum usuário cadastrado.")
            st.stop()

        if dashes_df2.empty:
            st.info("Nenhum dashboard cadastrado.")
            st.stop()

        username_sel = st.selectbox("Usuário", users_df2["username"].tolist(), key="link_user_sel")
        uid = int(users_df2[users_df2["username"] == username_sel].iloc[0]["id"])

        current = query(
            "SELECT d.name FROM dashboards d "
            "JOIN user_dashboards ud ON ud.dashboard_id = d.id "
            "WHERE ud.user_id = :uid",
            {"uid": uid},
        )
        current_names = current["name"].tolist() if not current.empty else []

        selected = st.multiselect(
            "Dashboards disponíveis",
            dashes_df2["name"].tolist(),
            default=current_names,
            key="link_dashes_sel",
        )

        colA, colB = st.columns(2)

        if colA.button("Salvar vínculos", key="btn_save_links"):
            try:
                execute("DELETE FROM user_dashboards WHERE user_id=:uid", {"uid": uid})
                for nm in selected:
                    did = int(dashes_df2[dashes_df2["name"] == nm].iloc[0]["id"])
                    execute(
                        "INSERT INTO user_dashboards (user_id, dashboard_id) VALUES (:uid, :did)",
                        {"uid": uid, "did": did},
                    )
                st.success("Vínculos atualizados.")
            except Exception as e:
                st.exception(e)

        if colB.button("Remover todos vínculos", key="btn_clear_links"):
            try:
                execute("DELETE FROM user_dashboards WHERE user_id=:uid", {"uid": uid})
                st.success("Vínculos removidos.")
                st.rerun()
            except Exception as e:
                st.exception(e)

        st.divider()
        st.subheader("Resumo de vínculos")
        st.dataframe(
            query(
                "SELECT u.username, d.name AS dashboard "
                "FROM users u "
                "LEFT JOIN user_dashboards ud ON ud.user_id = u.id "
                "LEFT JOIN dashboards d ON d.id = ud.dashboard_id "
                "ORDER BY u.username, d.name"
            ),
            use_container_width=True,
        )
