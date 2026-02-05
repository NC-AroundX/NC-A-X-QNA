import os
import re
import time
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
model = genai.GenerativeModel("gemini-2.5-flash")

DOCUMENT_PATH = "document.txt"

# ✅ 문서 로드: 파일 수정시간(mtime)을 캐시 키로 사용 → document.txt 바꾸면 자동 갱신
@st.cache_data(show_spinner=False)
def load_document(path: str, mtime: float) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_document_text() -> str:
    mtime = os.path.getmtime(DOCUMENT_PATH)
    return load_document(DOCUMENT_PATH, mtime)

document_text = get_document_text()

# ✅ document.txt의 FAQ_KV 라인을 파싱해서 (키워드 → 정답) 룰로 사용
def parse_faq_kv(text: str):
    rules = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("FAQ_KV|"):
            continue

        parts = line.split("|")
        data = {}
        for p in parts[1:]:
            if "=" in p:
                k, v = p.split("=", 1)
                data[k.strip()] = v.strip()

        if "keywords" in data and "answer" in data:
            keywords = [kw.strip() for kw in data["keywords"].split(",") if kw.strip()]
            rules.append({
                "id": data.get("id", ""),
                "keywords": keywords,
                "answer": data["answer"]
            })
    return rules

FAQ_RULES = parse_faq_kv(document_text)

def match_faq_rule(question: str):
    q = re.sub(r"\s+", "", question)
    for rule in FAQ_RULES:
        for kw in rule["keywords"]:
            kw2 = re.sub(r"\s+", "", kw)
            if kw2 and kw2 in q:
                return rule
    return None

# 챗봇 함수
def get_answer(question: str) -> str:
    # ✅ 1) 비목/분류 질문은 FAQ_KV로 먼저 “정답 직출”
    rule = match_faq_rule(question)
    if rule:
        # 회계감사비 같은 핵심 질문도 여기서 100% 고정됨
        return f"문서 FAQ 기준으로 **{rule['answer']}**로 설정하시면 됩니다."

    # ✅ 2) 그 외 질문만 Gemini에 질의 (온도 0으로 추측 최소화)
    prompt = f"""
당신은 창업진흥원의 "글로벌 기업 협업 프로그램" 전문 상담사입니다.
아래 세부관리기준 문서를 참고하여 질문에 정확하고 친절하게 답변해주세요.

[답변 규칙]
1. 문서에 있는 내용만 답변하세요.
2. 문서에 없는 내용은 "해당 내용은 세부관리기준에서 확인되지 않습니다. 창업진흥원에 직접 문의해주세요."라고 답변하세요.
3. 관련 조항이 있다면 "제X조(조항명)"를 함께 안내해주세요.
4. 금액, 비율, 기한 등 숫자 정보는 정확하게 답변하세요.
5. (중요) 문서에 없는 용어/항목(예: '사업운영비')을 새로 만들어 답하지 마세요.

[세부관리기준 문서]
{document_text}

[질문]
{question}

[답변]
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0}
        )
        answer = response.text.strip()

        # ✅ 3) “특정 환각 단어” 방지: 문서에 없는 '사업운영비'가 답에 들어가면 차단
        if ("사업운영비" in answer) and ("사업운영비" not in document_text):
            return "해당 내용은 세부관리기준에서 확인되지 않습니다. 창업진흥원에 직접 문의해주세요."

        return answer

    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

# UI 구성
st.title("🚀 글로벌 기업 협업 프로그램 Q&A")
st.markdown("**창업진흥원 세부관리기준**에 대해 궁금한 점을 물어보세요!")

st.divider()

# (선택) 디버그: 문서 갱신시간 확인 (초보자 확인용)
with st.sidebar:
    st.caption("문서 최신 반영 확인")
    try:
        st.write("document.txt 수정시간:", time.ctime(os.path.getmtime(DOCUMENT_PATH)))
    except:
        st.write("document.txt 수정시간 확인 불가")

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

question = st.text_input(
    "질문을 입력하세요:",
    value=st.session_state.get("question", ""),
    placeholder="예: 사업비 변경 절차가 어떻게 되나요?"
)

if st.button("답변 받기", type="primary", use_container_width=True):
    if question:
        with st.spinner("답변을 생성하고 있습니다..."):
            answer = get_answer(question)
            st.markdown("### 📝 답변")
            st.markdown(answer)

            if "question" in st.session_state:
                del st.session_state.question
    else:
        st.warning("질문을 입력해주세요.")

st.divider()
st.caption("본 챗봇은 AI 기반으로 작동하며, 정확한 내용은 창업진흥원에 확인해주세요.")
