# SEMPAssistant Chatbot (Streamlit)

This chatbot answers questions about SEMPA membership and events. It uses:

- ✅ Hardcoded FAQ matching for instant answers
- ✅ RAG (Retrieval-Augmented Generation) using a FAISS index built from SEMPA.org content
- ✅ GPT fallback via OpenAI API if no match is found

---

## 🚀 Setup & Deployment

1. **Create your Streamlit app** at https://share.streamlit.io
2. Upload the following files:
   - `sempassistant.py`
   - `sempa_faiss_index.pkl`
   - *(Optional)* `sempa_chunks.pkl` for debugging and auditing
   - `requirements.txt`
3. Add your OpenAI key via Streamlit Secrets.

---

## 🔐 Streamlit Secrets Setup

Create a file at `.streamlit/secrets.toml` with:

```toml
OPENAI_API_KEY = "your-openai-key-here"
```

---

## ✅ Requirements

Contents of `requirements.txt`:

```txt
streamlit
openai
langchain
langchain-community
bs4
faiss-cpu
playwright
tiktoken
```

To install Playwright's Chromium engine (only needed if recrawling):
```bash
playwright install
```

---

## 🧠 Source Content

The chatbot uses a FAISS index built from 40+ live SEMPA.org pages. Crawling and chunking are done with a separate script (`crawl_sempa_chunks.py`). The resulting embeddings power the RAG responses.

The file `sempa_faiss_index.pkl` is a dictionary containing two keys:
- `index`: the FAISS index object
- `documents`: list of LangChain Document objects

**The assistant script reconstructs the FAISS object manually at runtime.**

---

## 🔁 FAISS Loader Block (in `sempassistant.py`)

Replace your existing vectorstore load with:

```python
from langchain_community.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.docstore import InMemoryDocstore

with open("sempa_faiss_index.pkl", "rb") as f:
    data = pickle.load(f)
    index = data["index"]
    documents = data["documents"]

docstore_dict = {str(i): doc for i, doc in enumerate(documents)}
docstore = InMemoryDocstore(docstore_dict)
index_to_docstore_id = {i: str(i) for i in range(len(documents))}

vectorstore = FAISS(
    index=index,
    docstore=docstore,
    index_to_docstore_id=index_to_docstore_id,
    embedding_function=OpenAIEmbeddings()
)

retriever = vectorstore.as_retriever()
```

---

## ✉️ Fallback Behavior

If the bot doesn’t know the answer:
- It tries to match an FAQ synonym
- Then falls back to GPT
- If that also fails, it responds:
  > “I'm not sure — please contact us at sempa@sempa.org”

---

## 🔧 Admin Tools

If logged in as an admin (email matches), the sidebar reveals:
- Downloadable token usage log
- Source tracking log (FAQ, RAG, GPT)
