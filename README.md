
# SEMPAssistant Chatbot (Streamlit)

This chatbot answers questions about SEMPA membership and events. It uses:

- Hardcoded FAQ matching for quick answers
- GPT fallback via OpenAI API if no match is found

---

## 🚀 Setup & Deployment

1. **Create your Streamlit app** at https://share.streamlit.io
2. Upload the following files:
   - `sempassistant.py`
   - `requirements.txt`
3. Add your OpenAI key via Streamlit Secrets.

---

## 🔐 Streamlit Secrets Setup

Create a file at `.streamlit/secrets.toml` with API Key

```

---

## ✅ Requirements

Contents of `requirements.txt`:

```txt
streamlit
openai
```

---

## ✉️ Fallback behavior

If the bot doesn’t know the answer, it responds:
> “I'm not sure — please contact us at sempa@sempa.org”

Or uses GPT to generate a helpful reply.

---
