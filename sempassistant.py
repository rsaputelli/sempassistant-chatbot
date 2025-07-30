import streamlit as st
import openai
import csv
from datetime import datetime
from pathlib import Path
from typing import Tuple
import faiss
import pickle
import numpy as np

# --- PAGE SETUP ---
st.set_page_config(page_title="SEMPAssistant", page_icon="🩺", layout="centered")
st.title("👋 Welcome to SEMPAssistant!")
st.write("I'm here to help you with SEMPA membership and event questions. Ask me anything!")

# --- ADMIN CONFIG ---
ADMIN_USERS = ["ray@lutinemanagement.com"]
user_email = getattr(st.experimental_user, "email", None)

# --- LOAD VECTOR STORE ---
with open("sempa_faiss_index.pkl", "rb") as f:
    vector_data = pickle.load(f)
    faiss_index = vector_data["index"]
    documents = vector_data["documents"]
    embeddings = vector_data["embeddings"]

from openai import OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

def query_rag(user_input: str) -> Tuple[str, str]:
    embedding = get_embedding(user_input)
    D, I = faiss_index.search(np.array([embedding]), k=1)
    idx = I[0][0]
    score = D[0][0]
    if score < 0.75:
        return documents[idx], "RAG"
    return None, None

def normalize(text):
    return text.lower().strip()

FAQS = {
    "join or renew": "Visit the [Join or Renew page](https://sempa.site-ym.com/general/register_member_type.asp) to get started with SEMPA membership.",
    "membership categories": "SEMPA offers various membership categories. You can view them all at [https://sempa.org/categories-dues/](https://sempa.org/categories-dues/).",
    "register for events": "Go to the Event Calendar or Education sections at sempa.org to register for events like SEMPA 360.",
    "member discounts": "Yes! Members save up to 40% on events, CME, and partner resources.",
    "access session recordings": "Log in to your SEMPA account and go to the 'My Education' section to find session recordings.",
    "contact sempa": "You can reach SEMPA at sempa@sempa.org or call 877-297-7954."
}

SYNONYM_MAP = {
    "join or renew": ["join", "sign up", "enroll", "become a member", "renew", "renewal"],
    "membership categories": ["categories", "types", "levels", "dues", "cost"],
    "register for events": ["register", "sign up", "attend", "enroll", "conference"],
    "member discounts": ["discount", "save", "benefits", "perks"],
    "access session recordings": ["recordings", "sessions", "videos", "past sessions"],
    "contact sempa": ["contact", "email", "call", "support", "help"]
}

def match_faq(user_input):
    norm_input = normalize(user_input)
    for faq_key, synonyms in SYNONYM_MAP.items():
        if any(s in norm_input for s in synonyms):
            return FAQS[faq_key], "FAQ"
    return None, None

def detect_agent_request(user_input):
    norm_input = normalize(user_input)
    return any(word in norm_input for word in ["agent", "representative", "someone live", "talk to", "speak with"])

def log_token_usage(question, total_tokens):
    cost = round(total_tokens * (0.002 / 1000), 6)
    with open("token_log.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), question, total_tokens, cost])

def log_source(question, source):
    with open("source_log.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), question, source])

# --- MAIN CHAT LOGIC ---
user_input = st.text_input("Ask a question about SEMPA membership or events:")
if user_input:
    if detect_agent_request(user_input):
        st.info("📧 The SEMPA support team is not available for live chat, but if you type your question here we'll get right back to you via email.")
        st.markdown("[Click here to email us directly](mailto:sempa@sempa.org)")
        log_source(user_input, "Email Referral")
    else:
        answer, source = query_rag(user_input)
        if not answer:
            answer, source = match_faq(user_input)
        if not answer:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for SEMPA. Only answer questions about SEMPA membership, events, or support. If unsure, suggest the user contact sempa@sempa.org."},
                        {"role": "user", "content": user_input}
                    ]
                )
                answer = response['choices'][0]['message']['content']
                log_token_usage(user_input, response['usage']['total_tokens'])
                source = "GPT"
            except Exception:
                answer = "I'm not sure — please contact us at [sempa@sempa.org](mailto:sempa@sempa.org)"
                source = "Fallback"
        log_source(user_input, source)
        st.success(answer)

# --- ADMIN DASHBOARD ---
st.sidebar.markdown("🔐 Admin Panel")
if user_email in ADMIN_USERS:
    if st.sidebar.checkbox("Show Admin Tools"):
        st.subheader("📊 Admin Dashboard")
        if Path("token_log.csv").exists():
            with open("token_log.csv", "rb") as f:
                st.download_button("📥 Download Token Log", f, file_name="token_log.csv")
        if Path("source_log.csv").exists():
            with open("source_log.csv", "rb") as f:
                st.download_button("📥 Download Source Log", f, file_name="source_log.csv")
else:
    st.sidebar.caption("Admin access required to view tools.")


