import streamlit as st
from openai import OpenAI
import os
import time
import base64   # <--- 这行就是关键，加这一行就解决 NameError

# 从环境变量读取
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "asst_0xmUolnfgXKtSVx5bvEXwBKc")

st.set_page_config(
    page_title="ST2U V10 Pro | Stock & Sales AI",
    page_icon="📈",
    layout="centered"
)

st.title("📈 ST2U V10 Pro Assistant")
st.caption("投资·销售·AI工具 | 教育内容，非投资建议")

if not OPENAI_API_KEY:
    st.error("请在环境变量中设置 OPENAI_API_KEY")
    st.stop()

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

# 图像上传
uploaded_file = st.file_uploader("上传 TradingView 图表截图分析？", type=["png", "jpg", "jpeg", "webp"])

# 用户输入
prompt = st.chat_input("问 ST2U、股票、销售技巧？或上传截图分析")

if prompt or uploaded_file:
    user_content = []

    if prompt:
        user_content.append({"type": "text", "text": prompt})

    if uploaded_file is not None:
        # 显示上传的图像
        st.image(uploaded_file, caption="你上传的图表", use_column_width=True)

        # 直接用 uploaded_file.getvalue() 获取字节数据（不用 open 文件）
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')

        # 添加图像到消息（用 image_url + base64）
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{uploaded_file.type};base64,{base64_image}"
            }
        })

        # 自动提示
        if not prompt:
            prompt = "分析这张上传的图表截图，用我的密集型资金攻略解释 P1/P2/V7/V10 和资金标签"

    # 添加用户消息到历史
    st.session_state.messages.append({"role": "user", "content": prompt or "（上传了图表截图）"})
    with st.chat_message("user"):
        if prompt:
            st.markdown(prompt)
        if uploaded_file:
            st.image(uploaded_file, caption="你上传的图表", use_column_width=True)

    # 发送给 Assistant
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("思考中..."):
            try:
                # 发送消息
                client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=user_content
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
