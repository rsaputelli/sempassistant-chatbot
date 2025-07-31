import streamlit as st
import openai
import csv
from datetime import datetime
from pathlib import Path
import pickle
import numpy as np

from langchain_community.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.docstore import InMemoryDocstore

# --- PAGE SETUP ---
st.set_page_config(page_title="SEMPAssistant", page_icon="💕", layout="centered")
st.title("👋 Welcome to SEMPAssistant!")
st.write("I'm here to help you with your questions about SEMPA. Ask me anything!")

# --- ADMIN CONFIG ---
ADMIN_USERS = ["ray@lutinemanagement.com"]
user_email = getattr(st.experimental_user, "email", None)

# --- LOAD VECTOR STORE ---
with open("sempa_faiss_index.pkl", "rb") as f:
    data = pickle.load(f)
    index = data["index"]
    documents = data["documents"]

docstore_dict = {str(i): doc for i, doc in enumerate(documents)}
docstore = InMemoryDocstore(docstore_dict)
index_to_docstore_id = {i: str(i) for i in range(len(documents))}

embedding_function = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS(
    index=index,
    docstore=docstore,
    index_to_docstore_id=index_to_docstore_id,
    embedding_function=embedding_function
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

# --- OPENAI CLIENT ---
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- EMBEDDING FUNCTION (optional standalone use) ---
def get_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

from langchain.prompts import PromptTemplate

# Custom prompt to encourage confident, user-friendly responses
custom_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a helpful assistant for SEMPA, the Society of Emergency Medicine Physician Assistants.
Answer the user's question clearly and confidently based on the context provided.

If the context contains the answer, present it in a friendly and conversational way.
If the answer isn't present, don't mention the context or documents — just say you’re not sure and suggest contacting SEMPA.

Question: {question}

Context:
{context}

Helpful Answer:
"""
)

llm = ChatOpenAI(model="gpt-4", temperature=0)

rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    return_source_documents=True,
    chain_type_kwargs={"prompt": custom_prompt}
)

# --- FAQ MAPPING ---
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

def find_best_source(answer, source_docs):
    answer_lower = answer.lower()[:100]
    for doc in source_docs:
        if answer_lower in doc.page_content.lower():
            return doc.metadata.get("source")
    return source_docs[0].metadata.get("source") if source_docs else None

# --- MAIN CHAT LOGIC ---
user_input = st.text_input("Ask a question about SEMPA membership or events:")
if user_input:
    if detect_agent_request(user_input):
        st.info("📧 The SEMPA support team is not available for live chat, but if you type your question here we'll get right back to you via email.")
        st.markdown("[Click here to email us directly](mailto:sempa@sempa.org)")
        log_source(user_input, "Email Referral")
    else:
        try:
            response = rag_chain({"query": user_input})
            answer = response["result"]
            source = "RAG"

            # Improved source attribution using lightweight match
            source_url = None
            if "source_documents" in response and response["source_documents"]:
                source_url = find_best_source(answer, response["source_documents"])

        except Exception:
            answer = None
            source = None
            source_url = None

        if not answer:
            answer, source = match_faq(user_input)
            source_url = None

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
                source_url = None
            except Exception:
                answer = "I'm not sure — please contact us at [sempa@sempa.org](mailto:sempa@sempa.org)"
                source = "Fallback"
                source_url = None

        log_source(user_input, source)

        if answer:
            st.success(answer)
            if source == "RAG" and source_url:
                st.markdown(f"\n\n_Source: [View source]({source_url})_")

# --- ADMIN DASHBOARD ---
st.sidebar.markdown("🔐 Admin Panel")
if user_email in ADMIN_USERS:
    if st.sidebar.checkbox("Show Admin Tools"):
        st.subheader("📊 Admin Dashboard")
        if Path("token_log.csv").exists():
            with open("token_log.csv", "rb") as f:
                st.download_button("📅 Download Token Log", f, file_name="token_log.csv")
        if Path("source_log.csv").exists():
            with open("source_log.csv", "rb") as f:
                st.download_button("📅 Download Source Log", f, file_name="source_log.csv")
else:
    st.sidebar.caption("Admin access required to view tools.")












