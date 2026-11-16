import os
import sys
import time


try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

from dotenv import load_dotenv
from google import genai

load_dotenv()

_client = None


def get_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        raise RuntimeError("GEMINI_API_KEY not found. Put it in the .env file.")


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=get_api_key())
    return _client


def _actions(model):
    return getattr(model, "supported_actions", None) or []


def pick_text_model():
    """Finds a Gemini 'flash' model your key can use (model names change often)."""
    forced = os.getenv("GEMINI_MODEL")
    if forced:
        return forced
    skip = ("image", "tts", "live", "audio", "native", "robotics", "computer",
            "embedding", "imagen", "veo", "lyria", "gemma", "exp", "learnlm")
    names = []
    for m in get_client().models.list():
        name = m.name.replace("models/", "")
        if "flash" in name and "generateContent" in _actions(m) and not any(s in name for s in skip):
            names.append(name)
    if not names:
        raise RuntimeError("No Gemini flash model found for your key. Check aistudio.google.com")

    def group(n):
        if n == "gemini-flash-latest":
            return 0
        if "preview" in n:
            return 2
        return 1

    names.sort(reverse=True)
    names.sort(key=group)
    return names[0]


def pick_embed_model():
    forced = os.getenv("GEMINI_EMBED_MODEL")
    if forced:
        return forced
    names = [m.name.replace("models/", "") for m in get_client().models.list()
             if "embedContent" in _actions(m)]
    for preferred in ("gemini-embedding-001", "gemini-embedding-2"):
        if preferred in names:
            return preferred
    return names[0] if names else "gemini-embedding-001"


def embed_texts(texts, model, batch_size=50):
    """Turns a list of texts into vectors. Waits and retries if Google says 'too fast'."""
    client = get_client()
    vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for attempt in range(6):
            try:
                res = client.models.embed_content(model=model, contents=batch)
                got = [e.values for e in res.embeddings]
                if len(got) != len(batch):  # safety: embed one by one
                    got = []
                    for t in batch:
                        r = client.models.embed_content(model=model, contents=t)
                        got.append(r.embeddings[0].values)
                vectors.extend(got)
                break
            except Exception as e:
                wait = 15 * (attempt + 1)
                print(f"  Problem: {e}\n  Waiting {wait}s and retrying...")
                time.sleep(wait)
        else:
            raise RuntimeError("Embedding failed too many times.")
        time.sleep(1.5)
    return vectors