"""A Gemini chatbot that explains our results and answers background questions.

How it stays honest:
  * Background facts about the method come from chatbot_knowledge.md.
  * Every specific number (a score, a rank, a twin's location) comes from
    the tools in chat_data.py, which read the same JSON the website shows.
    Gemini calls them itself (automatic function calling) whenever a
    question needs one.
  * The system prompt tells it to mark general knowledge, which is not from
    our data, as "General background" so the two are never confused.

The API key is read from the GEMINI_API_KEY environment variable (or, in the
Streamlit app, from Streamlit secrets). It is never written to any file in
this repository.

Models are tried in order (MODELS, or GEMINI_MODEL to force one), moving to
the next when one is overloaded or unavailable. Thinking is set to "low":
on 13 November 2026 that cut a reply from about 50 s to about 4 s with the
same answer.

    python src/chatbot.py          chat in the terminal (type "quit" to stop)
    streamlit run src/chat_app.py  chat in the browser
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import chat_data

MODELS = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
THINKING = "low"
KNOWLEDGE = Path(__file__).resolve().parent / "chatbot_knowledge.md"

# Errors worth moving to the next model for: overloaded (503), rate limited
# (429), model retired or unknown (404), deadline exceeded (504). A request
# that takes longer than TIMEOUT_MS also moves on: one turn took 68 s on
# 13 November while the next model answered in seconds.
RETRY_CODES = {404, 429, 503, 504}
TIMEOUT_MS = 40_000

RULES = """\
You are the assistant of Planetary Twin Finder, a NASA Space Apps 2026
project. You help judges, scientists and the public understand which places
on Earth best match NASA's proposed Mars and Moon sites, and why.

Rules:
1. For any specific number or place from our project (a score, rank, twin
   location, country, feature value), call a tool. Never guess or invent
   one. If the tools do not have it, say so plainly.
2. You may also answer general questions (Mars and Moon geology, analog
   sites, missions, remote sensing). When an answer, or part of one, is
   general knowledge rather than our data, start that part with
   "General background:" so readers can tell the two apart.
3. Be honest about limits: Moon sites are matched on terrain only and their
   scores are not comparable with Mars scores (quote the rank instead); only
   the continents in the coverage note were searched; no twin has been
   checked on the ground yet.
4. When you give a twin's location, include its latitude, longitude, country
   and the map link from the tool.
5. Keep answers short and clear for a non-specialist: a few sentences or a
   short list. Answer in the language the user writes in.
6. Reply with the answer only. Never include your reasoning, plans,
   requirement checks or notes to yourself.
7. Our data gives coordinates and countries, not region names. Do not name
   the region a twin lies in (a desert, a mountain range) unless the
   background facts above name it; give the coordinates and map link
   instead. (On 13 November the bot called Western Desert twins "Eastern
   Desert and Sinai".)
"""


def system_prompt() -> str:
    """Rules, background facts, what was searched, and a one-line summary of
    every site, so the model knows the site names without a tool call."""
    cov = chat_data.coverage()
    lines = [f"- {t['name']} ({t['world']}, {t['lat']:.1f}, {t['lon']:.1f}): "
             f"best score {t['best_score']}"
             for t in chat_data.list_targets()]
    return "\n\n".join([
        RULES,
        KNOWLEDGE.read_text(encoding="utf-8"),
        (f"Coverage note: Earth tiles searched so far: "
         f"{cov['earth_tiles_ranked']:,} Mars-possible tiles in "
         f"{', '.join(cov['continents'])}."),
        "Sites in our data:\n" + "\n".join(lines),
    ])


def _worth_retrying(exc: Exception) -> bool:
    """True for errors another model may not have: busy, rate limited,
    retired, or too slow (a timeout raises httpx's ReadTimeout, which has
    no status code)."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    return code in RETRY_CODES or "timeout" in type(exc).__name__.lower()


class Bot:
    """One conversation. Keeps its own history so it can switch models
    mid-conversation when one is overloaded."""

    def __init__(self, api_key: str | None = None, models: list[str] | None = None):
        from google import genai
        from google.genai import types

        self._types = types
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("Set GEMINI_API_KEY to a Gemini API key "
                               "(from Google AI Studio). Never commit it.")
        self._client = genai.Client(
            api_key=key, http_options=types.HttpOptions(timeout=TIMEOUT_MS))
        forced = os.environ.get("GEMINI_MODEL")
        self.models = models or ([forced] if forced else list(MODELS))
        self.model = None           # the model that answered last
        self._history = []          # chat turns so far, kept across models
        self._config = types.GenerateContentConfig(
            system_instruction=system_prompt(),
            tools=chat_data.TOOLS,
            thinking_config=types.ThinkingConfig(thinking_level=THINKING),
            temperature=0.3,
        )

    def ask(self, message: str) -> str:
        """Send one message and return the reply text."""
        last, failed = None, []
        for model in list(self.models):
            chat = self._client.chats.create(model=model, config=self._config,
                                             history=self._history)
            try:
                reply = chat.send_message(message)
            except Exception as exc:  # noqa: BLE001 - checked below
                if not _worth_retrying(exc):
                    raise
                last = exc
                failed.append(model)
                continue
            # A model that just failed goes to the back of the queue for the
            # rest of the conversation, so a busy model is not retried (and
            # waited for) on every message.
            self.models = ([m for m in self.models if m not in failed]
                           + failed)
            self._history = chat.get_history()
            self.model = model
            return reply.text or "(no answer)"
        raise RuntimeError(f"Every model failed; the last error was: {last}")


def main() -> int:
    bot = Bot()
    print("Planetary Twin Finder chatbot. Type 'quit' to stop.\n")
    while True:
        try:
            question = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if question.lower() in {"quit", "exit", "q"}:
            return 0
        if question:
            answer = bot.ask(question)
            print(f"\nbot ({bot.model})> {answer}\n")


if __name__ == "__main__":
    sys.exit(main())
