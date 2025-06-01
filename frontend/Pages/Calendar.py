import streamlit as st
from google.auth.exceptions import RefreshError
from backend.google_auth import (
    get_credentials,
    start_auth_flow,
    finish_auth_flow,
    get_token_path,
)
import os

def show_calendar():
    st.title("📅 Google Calendar інтеграція")

    user = st.session_state.get("user")
    if not user:
        st.error("❗ Ви не авторизовані.")
        return

    user_id = user.id
    token_path = get_token_path(user_id)

    # --------------------------
    # 🔐 Перевірка токена
    # --------------------------
    creds = None
    email = None
    if token_path.exists():
        try:
            creds = get_credentials(user_id)
            email = creds.id_token.get("email") if creds.id_token else None
            if email:
                st.success(f"🔓 Токен знайдено. Авторизовано як: **{email}**")
            else:
                st.warning("⚠️ Токен знайдено, але email не визначено.")
        except Exception as e:
            st.warning(f"⚠️ Проблема з токеном: {e}")
    else:
        st.info("🔒 Ви ще не авторизувалися для доступу до Google Calendar.")

    # --------------------------
    # ❌ Видалити токен
    # --------------------------
    if token_path.exists():
        if st.button("🚪 Вийти з Google акаунта"):
            try:
                os.remove(token_path)
                st.success("🔒 Токен видалено. Ви вийшли з акаунта Google.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Не вдалося видалити токен: {e}")

    # --------------------------
    # 🔑 Авторизація
    # --------------------------
    if not creds:
        flow, auth_url = start_auth_flow()
        st.markdown(f"[🔐 Натисніть тут для авторизації Google]({auth_url})")

        code = st.text_input("Вставте код авторизації сюди:")
        if st.button("🔓 Завершити авторизацію"):
            try:
                finish_auth_flow(flow, code, user_id)
                st.success("✅ Авторизацію завершено! Оновлюємо сторінку...")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Помилка авторизації: {e}")

    # --------------------------
    # 🔄 Синхронізація справ
    # --------------------------
    st.markdown("---")
    st.subheader("🔄 Синхронізація активних записів")
    if st.button("🔁 Синхронізувати справи"):
        try:
            from backend.calendar_sync import sync_all_to_calendar
            sync_all_to_calendar(user_id)
            st.success("✅ Справи синхронізовано до Google Calendar.")
        except RefreshError:
            st.error("❌ Потрібна повторна авторизація Google.")
        except Exception as e:
            st.error(f"❌ Помилка синхронізації: {e}")

    # --------------------------
    # 🛑 Небезпечна зона
    # --------------------------
    st.markdown("---")
    with st.expander("🛑 Небезпечна зона"):
        st.markdown("**Очистити всі записи**")
        st.caption("Всі внесені вами дані про активні та відкладені справи та звички будуть видалені.")

        # --- Очистити календар і скинути event_id ---
        from backend.database import fetch_table, update_entry
        from backend.calendar_sync import delete_event_by_id
        if st.button("🧹 Очистити календар (і скинути event_id)"):
            try:
                habits = fetch_table("habits_active", user_id)
                tasks = fetch_table("tasks_active", user_id)
                deleted_count = 0

                for h in habits:
                    event_id = h.get("event_id")
                    if event_id:
                        try:
                            delete_event_by_id(user_id, event_id)
                            update_entry("habits_active", h["id"], {"event_id": None}, user_id)
                            deleted_count += 1
                        except Exception as e:
                            print(f"⚠️ Не вдалося видалити подію звички {event_id}: {e}")

                for t in tasks:
                    event_id = t.get("event_id")
                    if event_id:
                        try:
                            delete_event_by_id(user_id, event_id)
                            update_entry("tasks_active", t["id"], {"event_id": None}, user_id)
                            deleted_count += 1
                        except Exception as e:
                            print(f"⚠️ Не вдалося видалити подію завдання {event_id}: {e}")

                st.success(f"✅ Видалено {deleted_count} подій з Google Calendar та скинуто event_id.")

            except Exception as e:
                st.error(f"❌ Помилка при очищенні календаря: {e}")

        if st.button("🔥 Видалити всі записи з бази"):
            try:
                token = st.session_state.get("token")
                if not token:
                    st.warning("❗ Access token не знайдено.")
                    return

                from backend.database import get_supabase_client_with_token
                client = get_supabase_client_with_token(token)

                tables_to_clear = [
                    "habits_active", "tasks_active",
                    "habits_postponed", "tasks_postponed"
                ]

                for table in tables_to_clear:
                    res = client.table(table).delete().eq("user_id", user_id).execute()
                    print(f"🗑️ Видалено з {table}: {res}")

                st.success("✅ Усі записи користувача видалені з бази даних.")

            except Exception as e:
                st.error(f"❌ Помилка при видаленні записів: {e}")