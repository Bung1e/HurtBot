"""
Main Streamlit application for HurtBot.
"""

import streamlit as st


def main():
    st.title("HurtBot - Inteligentny Doradca Klienta")
    st.write("Witaj w systemie HurtBot! Jak mogę Ci pomóc?")

    # Chat input
    user_input = st.text_input("Twoje pytanie:")

    if user_input:
        st.write(f"Odpowiedź na pytanie: {user_input}")


if __name__ == "__main__":
    main()
