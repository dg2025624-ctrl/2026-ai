import streamlit as st
import anthropic

# 페이지 설정
st.set_page_config(
    page_title="Claude AI 질문 앱",
    page_icon="🤖",
    layout="centered"
)

# 제목
st.title("🤖 Claude AI 질문 앱")
st.markdown("Claude API를 사용하여 AI에게 질문해보세요!")
st.divider()

# API 키 불러오기 (Streamlit Secrets)
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("❌ API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에 ANTHROPIC_API_KEY를 추가해주세요.")
    st.stop()

# 모델 선택
st.subheader("⚙️ 모델 선택")
model_option = st.radio(
    "사용할 Claude 모델을 선택하세요:",
    options=["claude-sonnet-4-5", "claude-opus-4-5"],
    format_func=lambda x: "✨ Claude Sonnet 4.5 (빠르고 효율적)" if x == "claude-sonnet-4-5" else "🚀 Claude Opus 4.5 (강력하고 정교함)",
    horizontal=True
)

st.divider()

# 채팅 히스토리 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "total_input_tokens" not in st.session_state:
    st.session_state.total_input_tokens = 0

if "total_output_tokens" not in st.session_state:
    st.session_state.total_output_tokens = 0

# 사이드바: 사용량 통계
with st.sidebar:
    st.header("📊 토큰 사용량")
    
    input_metric = st.metric(
        label="📥 총 입력 토큰",
        value=f"{st.session_state.total_input_tokens:,}"
    )
    output_metric = st.metric(
        label="📤 총 출력 토큰",
        value=f"{st.session_state.total_output_tokens:,}"
    )
    total_metric = st.metric(
        label="🔢 총 사용 토큰",
        value=f"{st.session_state.total_input_tokens + st.session_state.total_output_tokens:,}"
    )
    
    st.divider()
    
    # 현재 선택된 모델 표시
    st.markdown("**🤖 현재 모델**")
    if model_option == "claude-sonnet-4-5":
        st.info("✨ Claude Sonnet 4.5")
    else:
        st.info("🚀 Claude Opus 4.5")
    
    st.divider()
    
    # 대화 초기화 버튼
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_input_tokens = 0
        st.session_state.total_output_tokens = 0
        st.rerun()

# 채팅 히스토리 표시
st.subheader("💬 대화")

if not st.session_state.messages:
    st.info("👋 아래에 질문을 입력하여 대화를 시작해보세요!")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # AI 메시지에 토큰 사용량 표시
        if message["role"] == "assistant" and "usage" in message:
            usage = message["usage"]
            with st.expander("📊 이 응답의 토큰 사용량"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📥 입력", f"{usage['input_tokens']:,}")
                with col2:
                    st.metric("📤 출력", f"{usage['output_tokens']:,}")
                with col3:
                    st.metric("🔢 합계", f"{usage['input_tokens'] + usage['output_tokens']:,}")

# 질문 입력
if prompt := st.chat_input("질문을 입력하세요..."):
    
    # 사용자 메시지 추가 및 표시
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("🤔 AI가 생각하는 중..."):
            try:
                # Anthropic 클라이언트 생성
                client = anthropic.Anthropic(api_key=api_key)
                
                # API 호출 (히스토리 포함)
                api_messages = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in st.session_state.messages
                    if msg["role"] in ["user", "assistant"]
                ]
                
                response = client.messages.create(
                    model=model_option,
                    max_tokens=4096,
                    messages=api_messages
                )
                
                # 응답 내용 추출
                answer = response.content[0].text
                
                # 토큰 사용량 추출
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                
                # 누적 토큰 업데이트
                st.session_state.total_input_tokens += input_tokens
                st.session_state.total_output_tokens += output_tokens
                
                # 응답 표시
                st.markdown(answer)
                
                # 토큰 사용량 표시
                with st.expander("📊 이 응답의 토큰 사용량"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📥 입력", f"{input_tokens:,}")
                    with col2:
                        st.metric("📤 출력", f"{output_tokens:,}")
                    with col3:
                        st.metric("🔢 합계", f"{input_tokens + output_tokens:,}")
                
                # 히스토리에 저장
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens
                    }
                })
                
                # 사이드바 업데이트를 위해 rerun
                st.rerun()
                
            except anthropic.AuthenticationError:
                st.error("❌ API 키가 유효하지 않습니다. Secrets 설정을 확인해주세요.")
            except anthropic.RateLimitError:
                st.error("⚠️ API 사용 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
            except anthropic.APIError as e:
                st.error(f"❌ API 오류가 발생했습니다: {str(e)}")
            except Exception as e:
                st.error(f"❌ 예상치 못한 오류가 발생했습니다: {str(e)}")
