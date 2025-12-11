import streamlit as st
from openai import OpenAI
import os
import time

# 从环境变量读取（Render/Railway/Replit/Vercel 通用）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "asst_0xmUolnfgXKtSVx5bvEXwBKc")  # 默认你的ID

st.set_page_config(
    page_title="ST2U V10 Pro | Stock & Sales AI",
    page_icon="📈",
    layout="centered"
)

st.title("📈 ST2U V10 Pro Assistant")
st.caption("投资·销售·AI工具 | 教育内容，非投资建议")

# 检查 API Key
if not OPENAI_API_KEY:
    st.error("请在环境变量中设置 OPENAI_API_KEY")
    st.stop()

# 初始化 OpenAI 客户端
client = OpenAI(api_key=OPENAI_API_KEY)

# 初始化对话线程
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# 初始化消息历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if prompt := st.chat_input("问 ST2U、股票、销售技巧？"):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 发送给 Assistant
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("思考中..."):
            try:
                # 发送消息
                client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=prompt
                )

                # 创建 run
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=ASSISTANT_ID
                )

                # 轮询状态
                while run.status in ["queued", "in_progress", "cancelling"]:
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )

                # 获取回复
                if run.status == "completed":
                    messages = client.beta.threads.messages.list(
                        thread_id=st.session_state.thread_id
                    )
                    assistant_reply = messages.data[0].content[0].text.value
                    message_placeholder.markdown(assistant_reply)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                else:
                    error_msg = f"AI 思考失败，状态：{run.status}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            except Exception as e:
                error_msg = f"发生错误：{str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
