"""Browser chat page for the Planetary Twin Finder chatbot (src/chatbot.py).

    streamlit run src/chat_app.py

One key for everyone. The team's Gemini API key is read from the
GEMINI_API_KEY environment variable, or from Streamlit secrets
(.streamlit/secrets.toml locally, gitignored; the Secrets box on Streamlit
Community Cloud or Hugging Face Spaces when hosted). It stays on the server:
visitors never see it and need no key of their own.

Sharing the free tier. Every visitor uses the same free Gemini quota. There
is deliberately no per-visitor limit (the team decided on 13 November to
watch usage instead). When Google's own free limit is reached, visitors are
told to try again in a minute instead of seeing the raw error.
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chat_data  # noqa: E402
from chatbot import Bot, Busy  # noqa: E402

EXAMPLES = [
    "Where on Earth is the best twin of Jezero, and why?",
    "Which Mars sites have a twin in Egypt?",
    "Why are the Moon scores so low?",
    "How do you know the method works?",
    "What is Jezero crater, and why does NASA care about it?",
]
BUSY_TEXT = ("The chatbot runs on Gemini's free tier and has reached its "
             "limit for the moment. Please try again in a minute.")

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
    st.error("The chatbot is not set up: no Gemini API key on the server. "
             "Set GEMINI_API_KEY as an environment variable or a Streamlit "
             "secret, then reload.")
    st.stop()

state = st.session_state
if "bot" not in state:
    state.bot = Bot(api_key=key)
    state.messages = []

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
            state.pending = example
    if st.button("New conversation"):
        for k in ("bot", "messages", "pending"):
            state.pop(k, None)
        st.rerun()
    if state.bot.model:
        st.caption(f"Model: {state.bot.model}")

for msg in state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])

question = st.chat_input("Ask a question") or state.pop("pending", None)
if question:
    state.messages.append({"role": "user", "text": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Looking it up..."):
            try:
                answer = state.bot.ask(question)
            except Busy:
                answer = BUSY_TEXT
            except Exception:             # never show internals to visitors
                traceback.print_exc()     # the team sees it in the server log
                answer = ("Sorry, something went wrong answering that. "
                          "Please try again.")
        st.markdown(answer)
    state.messages.append({"role": "assistant", "text": answer})
