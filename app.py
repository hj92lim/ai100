import os
import json
import streamlit as st
from openai import OpenAI
from datetime import datetime, timedelta

os.environ["OPENAI_API_KEY"] = st.secrets['API_KEY']
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

st.set_page_config(page_title="스파르타 플래너", layout="centered", initial_sidebar_state="collapsed")

# CSS 스타일 추가
st.markdown("""
    <style>
    .chat-container {
        max-width: 800px;
        margin: auto;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        background-color: #f9f9f9;
    }
    .chat-bubble {
        border-radius: 20px;
        padding: 10px 20px;
        margin: 10px 0;
        width: fit-content;
        max-width: 75%;
    }
    .chat-bubble.user {
        background-color: #87CEEB; /* 연한 하늘색 */
        color: white;
        align-self: flex-end;
    }
    .chat-bubble.bot {
        background-color: #FFC0CB; /* 연한 분홍색 */
        color: black;
        align-self: flex-start;
    }
    .stTextInput > div > input {
        border: 2px solid #87CEEB; /* 연한 하늘색 */
        border-radius: 5px;
        padding: 10px;
    }
    .stButton > button {
        background-color: #87CEEB; /* 연한 하늘색 */
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stButton > button:hover {
        background-color: #76C7C0; /* hover 시 조금 더 진한 하늘색 */
    }
    </style>
""", unsafe_allow_html=True)


# 페이지 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = 1
    st.session_state.messages = []
    st.session_state.start_date = None
    st.session_state.end_date = None
    st.session_state.todo_list = None
    st.session_state.final_goal = None

# JSON 파일 저장 함수
def save_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json_string = json.dumps(data, ensure_ascii=False, indent=4)
        f.write(json_string)

# JSON 파일 로드 함수
def load_json(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# 페이지 1: 소개 페이지
if st.session_state.page == 1:
    st.markdown("<div class='centered'>", unsafe_allow_html=True)
    st.title("🗓️ 스파르타 플래너")
    st.markdown("<h3 style='color: grey;'>인간이 AI에게 명령하는 시대는 갔다.<br>이제 AI에게 명령을 받는 시대다!</h3>", unsafe_allow_html=True)
    if st.button("시작하기 ➡️", key='next', help="Next", use_container_width=True):
        st.session_state.page = 2
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 페이지 2: AI 코치 선택 페이지
elif st.session_state.page == 2:
    st.markdown("<div class='centered'>", unsafe_allow_html=True)
    st.title("🗓️ 스파르타 플래너")
    st.title("AI 코치를 선택하세요")
    
    # 각 코치에 해당하는 이모지
    coach_emojis = {
        "피지컬 트레이너": "💪",
        "웨딩 플래너": "💍",
        "코딩 GURU": "💻",
        "여행 플래너": "🌍",
        "주식 전문가": "📈",
        "스타트업 멘토": "🚀",
        "독서 도우미": "📚"
    }

    # 코치 리스트 생성
    coaches = list(coach_emojis.keys())
    
    for coach in coaches:
        # 이모지를 포함한 버튼 텍스트 생성
        button_text = f"{coach_emojis[coach]} {coach}"
        if st.button(button_text, key=coach, use_container_width=True):
            st.session_state.page = 3
            st.session_state.coach = coach
            st.experimental_rerun()
    
    if st.button("⬅️ 뒤로", key='back_intro', help="Back", use_container_width=True):
        st.session_state.page = 1
        st.experimental_rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

    
# 페이지 3: 대화창 페이지
elif st.session_state.page == 3:
    # st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    st.title("🗓️ 스파르타 플래너")
    
    # 날짜 선택
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.start_date = st.date_input("목표 시작일을 선택하세요", value=datetime.now().date())
    with col2:
        st.session_state.end_date = st.date_input("목표 종료일을 선택하세요", value=(datetime.now() + timedelta(days=30)).date())
    
    if st.session_state.start_date > st.session_state.end_date:
        st.error("시작일은 종료일 이전이어야 합니다.")
    else:
        st.write(f"선택한 목표 기간: {st.session_state.start_date} - {st.session_state.end_date}")
        
        # 초기 인사말 추가
        if not st.session_state.get('messages'):
            st.session_state.messages = []
            initial_message = f"당신의 목표를 말해보게. {st.session_state.coach}로써 특훈 해주지"
            st.session_state.messages.append({"role": "bot", "content": initial_message})
        
        # 대화창
        for message in st.session_state.messages:
            if message['role'] == 'user':
                st.markdown(f"<div class='chat-bubble user'>{message['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bubble bot'>{message['content']}</div>", unsafe_allow_html=True)
        
        # 사용자 입력
        user_input = st.text_input("대화를 입력하세요", key='user_input')
        if st.button("전송", key='send_button'):
            if not user_input.strip():
                st.warning("유효한 입력을 제공해주세요.")
            else:
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # AI 코치에게 질문
                target_days = (st.session_state.end_date - st.session_state.start_date).days + 1
                prompt = f"""
                당신은 {st.session_state.coach}입니다. 스파르타 군인과 같은 기세로 정중한 반말로 대답해주세요. 그리고 목표는 특훈하듯이 세워주세요
                선택한 목표 기간은 {target_days}일입니다. 사용자의 고민을 듣고, 해당 기간 동안의 월간 목표, 주간 목표, 일별 목표를 만들어주세요.

                응답은 반드시 다음과 같은 JSON 형식으로 제공해주세요:

                {{
                    "monthly_goal": "월간 목표",
                    "weekly_goals": [
                        "첫 번째 주 목표",
                        "두 번째 주 목표",
                        "세 번째 주 목표",
                        "네 번째 주 목표"
                    ],
                    "todo_list": [
                        {{
                            "day": 1,
                            "tasks": [
                                {{
                                    "task": "Task 1",
                                    "checked": false
                                }},
                                {{
                                    "task": "Task 2",
                                    "checked": false
                                }},
                                {{
                                    "task": "Task 3",
                                    "checked": false
                                }}
                            ]
                        }},
                        {{
                            "day": 2,
                            "tasks": [
                                {{
                                    "task": "Task 1",
                                    "checked": false
                                }},
                                {{
                                    "task": "Task 2",
                                    "checked": false
                                }},
                                {{
                                    "task": "Task 3",
                                    "checked": false
                                }}
                            ]
                        }},
                        ...
                        {{
                            "day": {target_days},
                            "tasks": [
                                {{
                                    "task": "Task 1",
                                    "checked": false
                                }},
                                {{
                                    "task": "Task 2",
                                    "checked": false
                                }},
                                {{
                                    "task": "Task 3",
                                    "checked": false
                                }}
                            ]
                        }}
                    ]
                }}
                """
                
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    with st.spinner('AI 코치의 응답을 기다리는 중...'):
                        try:
                            chat_completion = client.chat.completions.create(
                                messages=[
                                    {"role": "system", "content": prompt},
                                    {"role": "user", "content": user_input}
                                ],
                                model="gpt-4o",
                                response_format={"type": "json_object"}
                            )
                            response = chat_completion.choices[0].message.content
                            
                            # JSON 형식 검증
                            response_json = json.loads(response)
                            if "monthly_goal" not in response_json or "weekly_goals" not in response_json or "todo_list" not in response_json:
                                raise ValueError("Invalid JSON format")
                            
                            st.session_state.monthly_goal = response_json["monthly_goal"]
                            st.session_state.weekly_goals = response_json["weekly_goals"]
                            st.session_state.todo_list = response_json["todo_list"]
                            
                            # 페이지 3에서 AI 코치의 응답 처리 부분 수정
                            # JSON 데이터 저장
                            save_json("planner_data.json", {
                                "monthly_goal": st.session_state.monthly_goal,
                                "weekly_goals": st.session_state.weekly_goals,
                                "todo_list": st.session_state.todo_list
                            })
                            
                            # 자연어 모델이 JSON 데이터를 설명
                            todo_list_str = "\n".join([f"Day {todo['day']}: " + ", ".join([task['task'] for task in todo['tasks']]) for todo in st.session_state.todo_list])
                            explanation_prompt = f"""
                            다음은 사용자의 월간 목표, 주간 목표, 일별 목표입니다:

                            월간 목표: {st.session_state.monthly_goal}

                            주간 목표:
                            {chr(10).join(st.session_state.weekly_goals)}

                            일별 목표:
                            {todo_list_str}

                            이 정보를 바탕으로, 사용자에게 계획을 간단히 요약해서 설명해주세요. 간결하고 핵심만 설명해주세요. 답장은 반드시 스파르타 군인과 같은 기세로 말하세요.
                            그리고 월간, 주간, 일별 목표를 선택할 때 줄 바꿈을 적절하게 사용해서 글이 깔끔해 보이도록 설명하세요. 또한 주간, 일별 목표에서 각각 주간, 일간을 나타낼때도 줄바꿈하세요.
                            """

                            explanation_completion = client.chat.completions.create(
                                messages=[
                                    {"role": "system", "content": explanation_prompt}
                                ],
                                model="gpt-4o"
                            )
                            explanation = explanation_completion.choices[0].message.content

                            st.session_state.messages.append({"role": "bot", "content": explanation})
                            break
                        except Exception as e:
                            retry_count += 1
                            if retry_count < max_retries:
                                st.warning(f"AI 코치의 응답 형식이 유효하지 않습니다. 다시 시도합니다. (시도 {retry_count}/{max_retries})")
                            else:
                                st.error(f"AI 코치의 응답 형식이 유효하지 않습니다. 최대 시도 횟수({max_retries})를 초과했습니다.")
                                break
                
                st.experimental_rerun()

    # Buttons aligned with '다음' button on the far right
    col3, _, col4 = st.columns([2, 8, 2])
    with col3:
        if st.button("⬅️ 뒤로", key='back_coach'):
            st.session_state.page = 2
            st.experimental_rerun()
    with col4:
        if st.button("다음 ➡️", key='next_page'):
            st.session_state.page = 4
            st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# 페이지 4: 월간 목표, 주간 목표, 일별 목표 페이지
elif st.session_state.page == 4:
    st.title("🗓️ 스파르타 플래너")
    
    # JSON 데이터 로드
    planner_data = load_json("planner_data.json")
    monthly_goal = planner_data["monthly_goal"]
    weekly_goals = planner_data["weekly_goals"]
    todo_list = planner_data["todo_list"]
    
    # 목표 시작 연도와 월 표시
    start_date = st.session_state.start_date
    st.header(f"{start_date.year}년 {start_date.month}월")
    
    # 총 계획 일 수 계산
    total_days = (st.session_state.end_date - st.session_state.start_date).days + 1
    st.write(f"총 계획 일 수: {total_days}일")
    
    # 슬라이더로 날짜 선택
    selected_day = st.slider("날짜를 선택하세요", 1, total_days)
    selected_date = start_date + timedelta(days=selected_day - 1)
    st.write(f"선택한 날짜: {selected_date.strftime('%Y-%m-%d')}")
    
    # 선택한 날짜의 주간 목표 및 일별 목표 표시
    selected_week = (selected_day - 1) // 7 + 1
    if selected_week <= len(weekly_goals):
        st.write(f"{selected_week}주차 목표: {weekly_goals[selected_week - 1]}")
    
    st.write("일별 목표:")
    for todo in todo_list:
        if todo['day'] == selected_day:
            for i, task_data in enumerate(todo['tasks'], start=1):
                task = task_data['task']
                checked = task_data['checked']
                if st.checkbox(f"{i}. {task}", key=f"day{todo['day']}_task{i}", value=checked):
                    todo['tasks'][i-1]['checked'] = True
                else:
                    todo['tasks'][i-1]['checked'] = False
    
    # 체크 여부 업데이트
    planner_data["todo_list"] = todo_list
    save_json("planner_data.json", planner_data)
    
    if st.button("⬅️ 뒤로", key='back_chat'):
        st.session_state.page = 3
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)
