import streamlit as st
from openai import OpenAI
import os
import time
import base64

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

# 显示历史消息（包括语音播放按钮）
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # 如果是 assistant 消息，添加语音播放按钮
        if message["role"] == "assistant":
            if st.button("🔊 语音播放", key=f"tts_{idx}"):
                with st.spinner("生成语音中..."):
                    try:
                        response = client.audio.speech.create(
                            model="tts-1",
                            voice="alloy",  # 可换 alloy, echo, fable, onyx, nova, shimmer
                            input=message["content"]
                        )
                        audio_b64 = base64.b64encode(response.content).decode()
                        audio_html = f"""
                        <audio controls autoplay>
                            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                        </audio>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"语音生成失败：{str(e)}")

# 文件上传区：支持图像 + 音频/视频
col1, col2 = st.columns(2)
with col1:
    uploaded_image = st.file_uploader("上传 TradingView 图表截图", type=["png", "jpg", "jpeg", "webp"])
with col2:
    uploaded_media = st.file_uploader("上传语音/视频日记（自动转录）", type=["mp3", "wav", "m4a", "mp4", "mov", "webm"])

# 用户文本输入
prompt = st.chat_input("问 ST2U、股票、销售技巧？或上传截图/语音分析")

# 处理上传和输入
if prompt or uploaded_image or uploaded_media:
    user_content = []

    # 1. 处理文本输入
    if prompt:
        user_content.append({"type": "text", "text": prompt})

    # 2. 处理图像上传（Vision）
    if uploaded_image is not None:
        st.image(uploaded_image, caption="你上传的图表", use_column_width=True)
        with st.spinner("上传图像中..."):
            file_response = client.files.create(
                file=uploaded_image,
                purpose="vision"
            )
            user_content.append({
                "type": "image_file",
                "image_file": {"file_id": file_response.id}
            })
            if not prompt:
                prompt = "分析这张上传的图表截图，用我的密集型资金攻略解释 P1/P2/V7/V10 和资金标签"
            st.success(f"图像上传成功！file_id: {file_response.id}")

    # 3. 处理音频/视频上传（自动转录）
    if uploaded_media is not None:
        with st.spinner("上传并转录语音/视频中..."):
            # 直接上传文件，用于转录或检索
            file_response = client.files.create(
                file=uploaded_media,
                purpose="assistants"  # assistants 支持音频转录
            )
            # 添加文件引用，让 Assistant 能访问并自动转录
            user_content.append({
                "type": "text",
                "text": f"用户上传了语音/视频文件，请先完整转录内容，然后根据内容回答或分析：{uploaded_media.name}"
            })
            # 附件方式让 Assistant 能直接读取文件（推荐）
            # 注意：这里我们用消息附件形式（更稳定）
            st.success(f"语音/视频上传成功！AI 将自动转录并记住：{uploaded_media.name}")

    # 显示用户消息
    display_text = prompt or "（上传了文件）"
    st.session_state.messages.append({"role": "user", "content": display_text})
    with st.chat_message("user"):
        if prompt:
            st.markdown(prompt)
        if uploaded_image:
            st.image(uploaded_image, caption="你上传的图表", use_column_width=True)
        if uploaded_media:
            st.markdown(f"🎤 已上传语音/视频：{uploaded_media.name}")

    # 发送给 Assistant
    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner("AI 思考中..."):
            try:
                # 创建消息（支持多模态内容）
                client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=user_content,
                    # 如果有音频文件，用 attachments 更可靠（可选增强）
                    attachments=[{"file_id": file_response.id, "tools": ["file_search"]}] if uploaded_media else None
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
                    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
                    assistant_reply = messages.data[0].content[0].text.value
                    placeholder.markdown(assistant_reply)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                else:
                    error_msg = f"AI 思考失败，状态：{run.status}"
                    placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            except Exception as e:
                error_msg = f"发生错误：{str(e)}"
                placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
