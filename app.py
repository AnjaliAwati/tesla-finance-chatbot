import time
import chromadb
import streamlit as st

from common import embed_texts, get_client, pick_text_model

DB_DIR = "chroma_db"
TOP_K = 6

st.set_page_config(page_title="Tesla Filings Chatbot", page_icon="🚗")


@st.cache_resource
def load_collection():
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_collection("tesla")


@st.cache_resource
def load_text_model():
    return pick_text_model()


col = load_collection()
embed_model = col.metadata.get("embed_model", "gemini-embedding-001")
text_model = load_text_model()


@st.cache_data
def list_sources():
    metas = col.get(include=["metadatas"])["metadatas"]
    return sorted({m["source"] for m in metas})


def retrieve(question, source_filter):
    qvec = embed_texts([question], embed_model)[0]
    where = None if source_filter == "All filings" else {"source": source_filter}
    res = col.query(query_embeddings=[qvec], n_results=TOP_K, where=where)
    hits = []
    for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
        hits.append({"text": doc, "source": meta["source"], "page": meta["page"]})
    return hits


def ask_llm(question, hits):
    context = "\n\n".join(
        f"[{h['source']} | page {h['page']}]\n{h['text']}" for h in hits
    )
    prompt = f"""You are an assistant that answers questions about Tesla using ONLY its
official SEC filings, given below as CONTEXT.

RULES:
- Use only the CONTEXT. Do not use outside knowledge.
- If the answer is not in the CONTEXT, reply exactly:
  "I couldn't find that in the loaded filings."
- Copy numbers exactly as written, with units and the period they refer to.
- After each fact, cite the source like (file name, page X).
- Never give investment advice, predictions, or buy/sell opinions.

CONTEXT:
{context}

QUESTION: {question}"""
    resp = None
    for attempt in range(4):
        try:
            resp = get_client().models.generate_content(model=text_model, contents=prompt)
            break
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                time.sleep(5 * (attempt + 1))
            else:
                raise
    if resp is None:
        return "The AI service is busy right now. Please try again in a minute."
    return resp.text or "I couldn't generate an answer. Please try again."


# ---------- Page ----------
st.title("🚗 Tesla Filings Chatbot")
st.caption("Ask questions about Tesla's 10-K and 10-Q filings. Answers include sources.")

with st.sidebar:
    st.header("Settings")
    source_filter = st.selectbox("Search in", ["All filings"] + list_sources())
    st.markdown("**Loaded filings:**")
    for s in list_sources():
        st.markdown(f"- {s}")
    st.warning("For information only. Not investment advice. "
               "Data is only as current as the filings listed above.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.markdown(f"**{s['source']} (page {s['page']})**")
                    st.caption(s["text"][:400] + "...")

question = st.chat_input("e.g. What are Tesla's main risk factors?")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the filings..."):
            try:
                hits = retrieve(question, source_filter)
                answer = ask_llm(question, hits)
            except Exception as e:
                hits, answer = [], f"Something went wrong: {e}"
        st.markdown(answer)
        if hits:
            with st.expander("Sources"):
                for s in hits:
                    st.markdown(f"**{s['source']} (page {s['page']})**")
                    st.caption(s["text"][:400] + "...")
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": hits}
    )