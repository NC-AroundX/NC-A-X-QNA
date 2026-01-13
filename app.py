import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(
    page_title="글로벌 기업 협업 프로그램 Q&A",
    page_icon="🚀",
    layout="wide"
)

# Gemini API 설정
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-pro')

# 세부관리기준 문서 내용 (document.txt에서 로드)
@st.cache_data
def load_document():
    with open("document.txt", "r", encoding="utf-8") as f:
        return f.read()

document_text = load_document()

# 챗봇 함수
def get_answer(question):
    prompt = f"""
당신은 창업진흥원의 "글로벌 기업 협업 프로그램" 전문 상담사입니다.
아래 세부관리기준 문서를 참고하여 질문에 정확하고 친절하게 답변해주세요.

[답변 규칙]
1. 문서에 있는 내용만 답변하세요.
2. 문서에 없는 내용은 "해당 내용은 세부관리기준에서 확인되지 않습니다. 창업진흥원에 직접 문의해주세요."라고 답변하세요.
3. 관련 조항이 있다면 "제X조(조항명)"를 함께 안내해주세요.
4. 금액, 비율, 기한 등 숫자 정보는 정확하게 답변하세요.

[세부관리기준 문서]
{document_text}

[질문]
{question}

[답변]
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

# UI 구성
st.title("🚀 글로벌 기업 협업 프로그램 Q&A")
st.markdown("**창업진흥원 세부관리기준**에 대해 궁금한 점을 물어보세요!")

st.divider()

# 예시 질문
st.markdown("##### 💡 이런 질문을 해보세요")
col1, col2 = st.columns(2)

with col1:
    if st.button("외주용역비 집행 기준은?", use_container_width=True):
        st.session_state.question = "외주용역비 집행 기준과 심의 절차가 어떻게 되나요?"
    if st.button("인건비는 어떻게 집행하나요?", use_container_width=True):
        st.session_state.question = "창업기업의 인건비 집행 기준은 무엇인가요?"

with col2:
    if st.button("여비 지급 기준은?", use_container_width=True):
        st.session_state.question = "국내외 여비 지급 기준은 어떻게 되나요?"
    if st.button("멘토링비 한도는?", use_container_width=True):
        st.session_state.question = "멘토링비 지급 한도와 기준은 무엇인가요?"

st.divider()

# 질문 입력
question = st.text_input(
    "질문을 입력하세요:",
    value=st.session_state.get("question", ""),
    placeholder="예: 사업비 변경 절차가 어떻게 되나요?"
)

# 답변 생성
if st.button("답변 받기", type="primary", use_container_width=True):
    if question:
        with st.spinner("답변을 생성하고 있습니다..."):
            answer = get_answer(question)
            st.markdown("### 📝 답변")
            st.markdown(answer)
            
            # 초기화
            if "question" in st.session_state:
                del st.session_state.question
    else:
        st.warning("질문을 입력해주세요.")

# 푸터
st.divider()
st.caption("본 챗봇은 AI 기반으로 작동하며, 정확한 내용은 창업진흥원에 확인해주세요.")
