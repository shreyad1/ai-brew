"""The one place that talks to the LLM. Swap providers by changing only this file."""

import json
import os
import sys
import time
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# Tried in order when a model is overloaded (503) or out of free quota (429).
FALLBACK_MODELS = ["gemini-flash-latest", "gemini-3.5-flash", "gemini-3.1-flash-lite"]
# "Busy" usually clears within minutes, so wait and go round the models again before giving up.
RETRY_WAITS = [30, 90]  # seconds before the 2nd and 3rd rounds


@lru_cache
def get_client() -> genai.Client:
    """Create one Gemini client from the key in .env and reuse it.

    Cached so the client stays alive: a throwaway client gets garbage-collected,
    which closes its connection mid-request.
    """
    key = os.getenv("GEMINI_API_KEY", "")
    if not key or key == "paste-your-key-here":
        raise RuntimeError("Put your Gemini API key in .env as GEMINI_API_KEY=...")
    return genai.Client(api_key=key)


def ask_json(system: str, prompt: str, models: list[str] | None = None, temperature: float = 0.3) -> dict:
    """Send a prompt and get back parsed JSON. Low temperature keeps it factual.

    `models` overrides which models to try, in order (the eval judge uses a different one).
    """
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        temperature=temperature,
        http_options=types.HttpOptions(timeout=180_000),  # ms; don't hang forever
    )
    last_error: Exception | None = None
    for wait in [0, *RETRY_WAITS]:
        if wait:
            print(f"  every model was busy; waiting {wait}s and trying again...")
            time.sleep(wait)
        for model in models or [MODEL, *FALLBACK_MODELS]:
            try:
                response = get_client().models.generate_content(model=model, contents=prompt, config=config)
                print(f"  (written by {model})")
                return json.loads(response.text)
            except (errors.ServerError, errors.ClientError) as error:
                if getattr(error, "code", None) not in (429, 503, 504):
                    raise
                print(f"  {model} unavailable ({error.code}), trying the next model...")
                last_error = error
    raise RuntimeError("Every Gemini model is busy right now. Try again later.") from last_error


if __name__ == "__main__":
    if sys.argv[1:] == ["models"]:
        for model in get_client().models.list():
            if "generateContent" in (model.supported_actions or []):
                print(model.name)
    else:
        print(ask_json("Reply in JSON.", 'Return {"status": "ok", "model": "<your model name>"}'))
