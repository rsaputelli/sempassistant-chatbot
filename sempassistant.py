
import streamlit as st
import openai

st.set_page_config(page_title="SEMPAssistant Deep Debug", page_icon="🧪", layout="centered")
st.title("🔍 Deep Debug: SEMPAssistant")
st.write("This version shows raw debug info for GPT fallback issues.")

# Attempt to show the key (partial only for security)
api_key = st.secrets.get("OPENAI_API_KEY", None)
if api_key:
    st.success(f"✅ OPENAI_API_KEY loaded: {api_key[:8]}... (hidden)")
else:
    st.error("❌ OPENAI_API_KEY not found in Streamlit secrets.")

# Try a test GPT call
try:
    openai.api_key = api_key
    test_prompt = "What is SEMPA?"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for SEMPA (Society of Emergency Medicine PAs)."},
            {"role": "user", "content": test_prompt}
        ]
    )
    st.success("✅ GPT call succeeded!")
    st.write(response['choices'][0]['message']['content'])
except Exception as e:
    st.error("❌ GPT call failed.")
    st.code(str(e), language='text')

