import streamlit as st
import os
import time
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# Using OpenAI Assistants API with custom assistant

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ASSISTANT_ID = "asst_0xmUolnfgXKtSVx5bvEXwBKc"

st.set_page_config(
    page_title="ST2U V10 Pro | Stock & Sales AI",
    page_icon="📈",
    layout="centered"
)

st.title("📈 ST2U V10 Pro Assistant")
st.caption("投资·销售·AI工具 | 教育内容，非投资建议")

if not OPENAI_API_KEY:
    st.error("Please set your OPENAI_API_KEY in the Secrets tab.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about stock ideas, sales techniques, or ST2U V10 Pro..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )
        
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        with st.spinner("Thinking..."):
            while run.status in ["queued", "in_progress"]:
                time.sleep(0.5)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
        
        if run.status == "completed":
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            
            assistant_message = None
            for msg in messages.data:
                if msg.role == "assistant":
                    assistant_message = msg.content[0].text.value
                    break
            
            if assistant_message:
                message_placeholder.markdown(assistant_message)
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        else:
            error_msg = f"Run failed with status: {run.status}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
