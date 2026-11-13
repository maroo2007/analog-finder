"""Browser chat page for the Planetary Twin Finder chatbot (src/chatbot.py).

    streamlit run src/chat_app.py

The Gemini API key is read from the GEMINI_API_KEY environment variable, or
from .streamlit/secrets.toml (gitignored) as GEMINI_API_KEY = "...", which is
also where Streamlit Community Cloud and Hugging Face Spaces store secrets.
It is never shown on the page.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chat_data  # noqa: E402
from chatbot import Bot  # noqa: E402

EXAMPLES = [
    "Where on Earth is the best twin of Jezero, and why?",
    "Which Mars sites have a twin in Egypt?",
    "Why are the Moon scores so low?",
    "How do you know the method works?",
    "What is Jezero crater, and why does NASA care about it?",
]

st.set_page_config(page_title="Planetary Twin Finder chat", page_icon="🪐")


def api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:  # no secrets file at all
        return None


st.title("Planetary Twin Finder")
st.caption("Ask about NASA's Mars and Moon sites and their twins on Earth. "
           "Numbers come from our results; general knowledge is labelled "
           "\"General background\".")

key = api_key()
if not key:
    st.error("No Gemini API key. Set the GEMINI_API_KEY environment variable, "
             "or put GEMINI_API_KEY in .streamlit/secrets.toml (gitignored), "
             "then reload.")
    st.stop()

if "bot" not in st.session_state:
    st.session_state.bot = Bot(api_key=key)
    st.session_state.messages = []

with st.sidebar:
    cov = chat_data.coverage()
    targets = chat_data.list_targets()
    st.markdown(
        f"**{sum(t['world'] == 'mars' for t in targets)} Mars sites, "
        f"{sum(t['world'] == 'moon' for t in targets)} Moon sites**  \n"
        f"Earth searched: {cov['earth_tiles_ranked']:,} tiles in "
        f"{', '.join(cov['continents'])}")
    st.markdown("**Try asking**")
    for example in EXAMPLES:
        if st.button(example, use_container_width=True):
            st.session_state.pending = example
    if st.button("New conversation"):
        st.session_state.clear()
        st.rerun()
    if st.session_state.bot.model:
        st.caption(f"Model: {st.session_state.bot.model}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])

question = st.chat_input("Ask a question") or st.session_state.pop("pending", None)
if question:
    st.session_state.messages.append({"role": "user", "text": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Looking it up..."):
            try:
                answer = st.session_state.bot.ask(question)
            except Exception as exc:  # show it, keep the page alive
                answer = f"Sorry, the chatbot failed: {exc}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "text": answer})
