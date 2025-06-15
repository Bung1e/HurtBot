import streamlit as st
import requests
import os

# Pobranie API_URL z .env lub użycie lokalnego endpointu
API_URL = os.getenv("API_URL", "http://localhost:7071/api/ask_rag")

st.set_page_config(page_title="🧠 HurtBot – Chat B2B", layout="centered")
st.title("🧠 HurtBot – Chatbot B2B (lokalnie)")

# Historia dialogu
if "history" not in st.session_state:
    st.session_state.history = []

# Pole do wpisywania pytania
query = st.text_input("Twoje pytanie:", key="input")
if st.button("Wyślij") and query:
    st.session_state.history.append({"user": query})
    with st.spinner("Bot się zastanawia…"):
        try:
            resp = requests.post(
                API_URL,
                json={"question": query},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if resp.ok:
                bot_ans = resp.json().get("answer", "").strip()
            else:
                bot_ans = f"❗ Błąd API: {resp.status_code}"
        except Exception as e:
            bot_ans = f"❗ Błąd połączenia: {e}"
        st.session_state.history.append({"bot": bot_ans})
    st.rerun()

# Wyświetlanie historii czatu
for msg in st.session_state.history:
    if "user" in msg:
        st.markdown(f"**Ty:** {msg['user']}")
    else:
        st.markdown(f"**Bot:** {msg['bot']}")

# Przycisk do czyszczenia historii
if st.button("🗑️ Wyczyść czat"):
    st.session_state.history.clear()
    st.rerun()
