import time

import chromadb

from common import embed_texts, get_client, pick_text_model

QUESTIONS = [
    "What was total revenue in Q3 2026?",
    "How did total revenue in Q3 2026 compare with Q3 2025?",
    "What was services and other revenue in Q3 2026?",
    "What was energy generation and storage revenue in Q3 2026?",
    "What was total gross profit in Q3 2026?",
    "What was research and development expense in Q3 2026?",
    "What was automotive regulatory credits revenue in Q3 2026?",
    "What was GAAP net income attributable to common stockholders in Q3 2026?",
    "What were cash, cash equivalents and short-term investments at the end of Q3 2026?",
    "What were total vehicle deliveries in Q3 2026?",
    "What was free cash flow in Q3 2026?",
    "What was total revenue in Q2 2026?",
    "What were total deliveries in Q1 2026?",
    "What will Tesla's stock price be next year?",
    "What was Ford's revenue last quarter?",
]

col = chromadb.PersistentClient(path="chroma_db").get_collection("tesla")
embed_model = col.metadata.get("embed_model", "gemini-embedding-001")
text_model = pick_text_model()
print("Using models:", text_model, "|", embed_model)

PROMPT = """You are an assistant that answers questions about Tesla using ONLY its
official documents, given below as CONTEXT.

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


def answer(question):
    qvec = embed_texts([question], embed_model)[0]
    res = col.query(query_embeddings=[qvec], n_results=6)
    hits = list(zip(res["documents"][0], res["metadatas"][0]))
    context = "\n\n".join(
        f"[{m['source']} | page {m['page']}]\n{d}" for d, m in hits
    )
    prompt = PROMPT.format(context=context, question=question)
    for attempt in range(5):
        try:
            resp = get_client().models.generate_content(model=text_model, contents=prompt)
            return resp.text or "(empty answer)", hits
        except Exception as e:
            msg = str(e)
            if any(w in msg for w in ("503", "UNAVAILABLE", "429", "quota")):
                time.sleep(10 * (attempt + 1))
            else:
                return f"ERROR: {msg}", hits
    return "ERROR: service busy, try again later", hits


with open("test_results.md", "w", encoding="utf-8") as f:
    for i, q in enumerate(QUESTIONS, start=1):
        print(f"Question {i}/{len(QUESTIONS)} ...")
        ans, hits = answer(q)
        sources = ", ".join(sorted({f"{m['source']} p.{m['page']}" for _, m in hits}))
        f.write(f"## Q{i}: {q}\n\n**Bot:** {ans}\n\n**Retrieved from:** {sources}\n\n---\n\n")
        f.flush()
        time.sleep(2)

print("Done! Open test_results.md")