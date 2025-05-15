import streamlit as st
from frontend.auth import require_login, get_current_user, update_display_name, update_password

def show_profile():
    user = require_login()
    st.title("👤 Профіль користувача")

    user_info = {
        "name": user.user_metadata.get("name", "Без імені"),
        "email": user.email,
        "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else "Невідомо",
    }

    st.subheader("📄 Інформація про аккаунт")
    st.markdown(f"**Ім'я:** {user_info['name']}")
    st.markdown(f"**Email:** {user_info['email']}")
    st.markdown(f"**Дата створення:** {user_info['created_at']}")

    st.subheader("✏️ Оновити ім'я")
    new_name = st.text_input("Нове ім’я", value=user_info["name"])
    if st.button("Зберегти ім’я"):
        update_display_name(new_name)
        st.success("Ім’я оновлено!")
        st.rerun()

    st.subheader("🔒 Змінити пароль")
    new_password = st.text_input("Новий пароль", type="password")
    if st.button("Змінити пароль"):
        if new_password:
            update_password(new_password)
            st.success("Пароль оновлено!")
        else:
            st.warning("Введіть новий пароль.")
