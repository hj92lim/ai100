import os
import json
import streamlit as st
from openai import OpenAI
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import calendar
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

import os
import json
import streamlit as st
from openai import OpenAI
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import calendar
import numpy as np
import plotly.express as px
import pandas as pd

os.environ["OPENAI_API_KEY"] = st.secrets['API_KEY']
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

st.set_page_config(page_title="스파르탄 플래너", layout="centered", initial_sidebar_state="collapsed")

# CSS 스타일 추가
st.markdown("""
    <style>
    .main-container {
        max-width: 1000px;
        margin: auto;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        background-color: #ffffff;
    }
    .centered {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .title {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #333333;
        text-align: center;
    }
    .subtitle {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 400;
        color: #666666;
        text-align: center;
    }
    .button {
        background-color: #5A9;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        margin: 10px 0;
        transition: background-color 0.3s ease;
    }
    .button:hover {
        background-color: #48a;
    }
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
        background-color: #87CEEB;
        color: white;
        align-self: flex-end;
    }
    .chat-bubble.bot {
        background-color: #FFC0CB;
        color: black;
        align-self: flex-start;
    }
    .stTextInput > div > input {
        border: 2px solid #87CEEB;
        border-radius: 5px;
        padding: 10px;
    }
    .stButton > button {
        background-color: #87CEEB;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        margin: 10px 0;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #76C7C0;
    }
    .progress-bar {
        width: 100%;
        background-color: #e0e0e0;
        border-radius: 25px;
        margin: 20px 0;
    }
    .progress-bar-fill {
        height: 20px;
        background-color: #5A9;
        border-radius: 25px;
        text-align: center;
        color: white;
        line-height: 20px;
        transition: width 0.3s ease;
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
    st.session_state.selected_day = None  # selected_day 초기화 추가

if 'todo_list' not in st.session_state:
    st.session_state.todo_list = None

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

# 코치별 질문지
coach_questions = {
    "피지컬 트레이너": [
        "하루에 운동할 수 있는 시간을 알려줘.",
        "현재 운동 수준과 목표 수준을 말해줘.",
        "어떤 운동에 관심이 있는지 구체적으로 적어줘."
    ],
    "코딩 GURU": [
        "하루와 주간 몇 시간씩 공부할 수 있는지 구체적으로 말해줘.",
        "현재 본인의 프로그래밍 수준을 상세히 설명하고, 바라는 수준이 어느 정도인지 알려줘.",
        "코딩 학습에서 궁금한 점들을 가능한 상세히 적어줘."
    ],
    "웨딩 플래너": [
        "결혼 준비를 위해 하루에 할애할 수 있는 시간을 알려줘.",
        "현재 준비된 사항과 목표 상태를 설명해줘.",
        "결혼 준비 과정에서 어떤 점들이 궁금한지 구체적으로 적어줘."
    ],
    "여행 플래너": [
        "여행 준비를 위해 하루에 할애할 수 있는 시간을 알려줘.",
        "여행 준비 상태와 목표 상태를 설명해줘.",
        "여행 준비 과정에서 어떤 점들이 궁금한지 구체적으로 적어줘."
    ],
    "주식 전문가": [
        "주식 공부를 위해 하루에 할애할 수 있는 시간을 알려줘.",
        "현재 주식 투자 수준과 목표 수준을 설명해줘.",
        "주식 투자 과정에서 어떤 점들이 궁금한지 구체적으로 적어줘."
    ],
    "스타트업 멘토": [
        "스타트업 준비를 위해 하루에 할애할 수 있는 시간을 알려줘.",
        "현재 스타트업 준비 상태와 목표 상태를 설명해줘.",
        "스타트업 과정에서 어떤 점들이 궁금한지 구체적으로 적어줘."
    ],
    "독서 도우미": [
        "독서를 위해 하루에 할애할 수 있는 시간을 알려줘.",
        "현재 독서 수준과 목표 수준을 설명해줘.",
        "독서 과정에서 어떤 점들이 궁금한지 구체적으로 적어줘."
    ]
}


# 잔소리 메시지
def get_nagging_message(progress_diff):
    if progress_diff < -40:
        return "이게 뭐야? 이렇게 해서 목표 달성할 수 있을 것 같아? 정신 차려!"
    elif progress_diff < -35:
        return "정신 차려! 이러다 목표 놓쳐! 지금이라도 시작해!"
    elif progress_diff < -30:
        return "너무 느려! 이러다 목표 못 이뤄!"
    elif progress_diff < -25:
        return "좀 더 열심히 해야 할 것 같아. 분발하자!"
    elif progress_diff < -20:
        return "아직 멀었어! 조금 더 노력해!"
    elif progress_diff < -15:
        return "조금 더 힘내! 할 수 있어!"
    elif progress_diff < -10:
        return "좋아지고 있어, 조금만 더 힘내자!"
    elif progress_diff < -8:
        return "계속 가자! 조금 더 집중하자!"
    elif progress_diff < -5:
        return "잘하고 있어, 조금만 더 노력해!"
    elif progress_diff < -2:
        return "좋아, 계속 이렇게 해!"
    elif progress_diff < 0:
        return "아주 잘하고 있어! 이대로 쭉 가자!"
    elif progress_diff < 2:
        return "아주 잘하고 있어! 계속 유지해!"
    elif progress_diff < 5:
        return "멋져! 목표에 점점 가까워지고 있어!"
    elif progress_diff < 8:
        return "너무 잘하고 있어! 조금만 더 힘내자!"
    elif progress_diff < 10:
        return "훌륭해! 목표를 향해 계속 가자!"
    elif progress_diff < 12:
        return "대단해! 이 기세를 유지하자!"
    elif progress_diff < 15:
        return "훌륭해! 거의 목표에 도달했어!"
    elif progress_diff < 20:
        return "너무 멋져! 거의 다 왔어!"
    elif progress_diff < 25:
        return "환상적이야! 목표 달성이 바로 눈앞이야!"
    elif progress_diff < 30:
        return "정말 잘했어! 이제 조금만 더 하면 돼!"
    else:
        return "환상적이야! 목표를 완전히 달성했어!"
    
# 페이지 1: 소개 페이지
if st.session_state.page == 1:
    st.markdown("<h1 class='title'>🗓️ 스파르탄 플래너</h1>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
            <img src="https://github.com/hj92lim/ai100/blob/main/sparta_img.png?raw=true" alt="AI Coach" style="width: 40px; height: 40px; border-radius: 50%; vertical-align: middle; margin-right: 5px;">
            <h3 class='subtitle' style="color: #000000; font-weight: bold;">인간이 AI에게 명령하는 시대는 갔다.<br>이제 AI에게 명령을 받는 시대다!</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Add the image here
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://github.com/hj92lim/ai100/blob/main/vincentj.png?raw=true" style="width: 600px; height: auto;">
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # 시작하기 버튼
    if st.button("시작하기 ➡️", key='next', help="Next", use_container_width=True):
        st.session_state.page = 2
        st.experimental_rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)



# 페이지 2: AI 코치 선택 페이지
elif st.session_state.page == 2:
    # st.markdown("<div class='main-container centered'>", unsafe_allow_html=True)
    st.markdown("<h1 class='title'>🗓️ 스파르탄 플래너</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='subtitle'>AI 코치를 선택하세요</h2>", unsafe_allow_html=True)
    
    # 각 코치에 해당하는 이모지
    coach_emojis = {
        "피지컬 트레이너": "💪",
        "코딩 GURU": "💻",
        "웨딩 플래너": "💍",
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
    st.markdown("<h1 class='title'>🗓️ 스파르탄 플래너</h1>", unsafe_allow_html=True)

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
            coach_questions_text = " ".join(coach_questions[st.session_state.coach])
            initial_message = f"{st.session_state.coach}로써 특훈 해주지. {coach_questions_text}"
            st.session_state.messages.append({"role": "bot", "content": initial_message})

        # 대화창
        for message in st.session_state.messages:
            if message['role'] == 'user':
                st.markdown(f"<div class='chat-bubble user'>{message['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='chat-bubble bot'>
                    <img src="https://github.com/hj92lim/ai100/blob/main/sparta_img.png?raw=true" alt="AI Coach" style="width: 40px; height: 40px; border-radius: 50%; vertical-align: middle; margin-right: 10px;">
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)

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
                            그리고 주간, 일간 등의 플랜을 설명할 때 굵은 글씨체와 일간 설명은 날마다 줄바꿈을 적절히 사용하며 최대한 깔끔하고 가독성 있게 글을 작성하세요.
                            """
    
                            explanation_completion = client.chat.completions.create(
                                messages=[                                    {"role": "system", "content": explanation_prompt}                                ],
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
    col3, col4 = st.columns([1, 1])
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
    # Week and Day Mapping
    def create_week_day_mapping(start_date, end_date):
        total_days = (end_date - start_date).days + 1
        week_day_mapping = {}
        current_week = 1
        current_week_days = []

        for day in range(1, total_days + 1):
            current_date = start_date + timedelta(days=day - 1)
            if current_date.weekday() == 5 or day == total_days:  # Saturday or last day
                current_week_days.append(day)
                week_day_mapping[f"week{current_week}"] = current_week_days
                current_week += 1
                current_week_days = []
            else:
                current_week_days.append(day)
        
        return week_day_mapping

    # Task Check Count Mapping
    def create_task_check_mapping(todo_list):
        task_check_mapping = {}

        for todo in todo_list:
            checked_count = sum(task['checked'] for task in todo['tasks'])
            task_check_mapping[f"day{todo['day']}"] = checked_count
        
        return task_check_mapping

    # Update Task Check Count Mapping
    def update_task_check_mapping():
        st.session_state.task_check_mapping = create_task_check_mapping(st.session_state.todo_list)
        save_json("planner_data.json", planner_data)

    # JSON 데이터 로드
    planner_data = load_json("planner_data.json")
    st.session_state.monthly_goal = planner_data["monthly_goal"]
    st.session_state.weekly_goals = planner_data["weekly_goals"]
    if st.session_state.todo_list is None:
        st.session_state.todo_list = planner_data["todo_list"]

    # 목표 시작 연도와 월 표시
    start_date = st.session_state.start_date
    end_date = st.session_state.end_date

    st.header(f"{start_date.year}년 {start_date.month}월")

    # 총 계획 일 수 계산
    total_days = (end_date - start_date).days + 1
    st.write(f"총 계획 일 수: {total_days}일")

    # 슬라이더로 날짜 선택
    selected_day = st.slider("날짜를 선택하세요", 1, total_days)
    selected_date = start_date + timedelta(days=selected_day - 1)
    st.write(f"선택한 날짜: {selected_date.strftime('%Y-%m-%d')}")

    # Week-Day Mapping
    week_day_mapping = create_week_day_mapping(start_date, end_date)

    # Task Check Count Mapping
    if 'task_check_mapping' not in st.session_state:
        st.session_state.task_check_mapping = create_task_check_mapping(st.session_state.todo_list)

    # 선택한 날짜의 주간 목표 및 일별 목표 표시
    selected_week = (selected_day - 1) // 7 + 1
    if selected_week <= len(st.session_state.weekly_goals):
        st.write(f"{selected_week}주차 목표: {st.session_state.weekly_goals[selected_week - 1]}")

    st.write("일별 목표:")
    for todo in st.session_state.todo_list:
        if todo['day'] == selected_day:
            for i, task_data in enumerate(todo['tasks'], start=1):
                task = task_data['task']
                key = f"day{todo['day']}_task{i}"
                if key not in st.session_state:
                    st.session_state[key] = task_data['checked']
                checked = st.checkbox(f"{i}. {task}", key=key, on_change=update_task_check_mapping)
                if checked != task_data['checked']:
                    task_data['checked'] = checked
                    st.session_state.todo_list[todo['day']-1]['tasks'][i-1]['checked'] = checked
                    update_task_check_mapping()

    # 진척도 계산
    total_tasks = sum(len(day['tasks']) for day in st.session_state.todo_list)
    completed_tasks = sum(task['checked'] for day in st.session_state.todo_list for task in day['tasks'])
    progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    # 예상 진척도 계산
    days_elapsed = (selected_date - st.session_state.start_date).days + 1
    expected_progress = (days_elapsed / total_days) * 100 if total_days > 0 else 0

    # 진척도 차이 계산
    progress_diff = progress - expected_progress

    # 잔소리 메시지
    nagging_message = get_nagging_message(progress_diff)

    st.write(f"진척도: {progress:.2f}% (예상 진척도: {expected_progress:.2f}%)")
    st.markdown(f"<div class='progress-bar'><div class='progress-bar-fill' style='width: {progress:.2f}%'>{progress:.2f}%</div></div>", unsafe_allow_html=True)

    st.markdown(f"<div class='centered'>{nagging_message}</div>", unsafe_allow_html=True)

    if st.button("⬅️ 뒤로", key='back_chat'):
        st.session_state.page = 3
        st.experimental_rerun()

    if st.button("다음 ➡️", key='next_page'):
        st.session_state.page = 5
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)



# Week-Day Mapping 함수
def create_week_day_mapping(start_date, end_date):
    total_days = (end_date - start_date).days + 1
    week_day_mapping = {}
    current_week = 1
    current_week_days = []

    for day in range(1, total_days + 1):
        current_date = start_date + timedelta(days=day - 1)
        if current_date.weekday() == 5 or day == total_days:  # Saturday or last day
            current_week_days.append(day)
            week_day_mapping[f"week{current_week}"] = current_week_days
            current_week += 1
            current_week_days = []
        else:
            current_week_days.append(day)
    
    return week_day_mapping

# Task Check Count Mapping 함수
def create_task_check_mapping(todo_list):
    task_check_mapping = {}

    for todo in todo_list:
        checked_count = sum(task['checked'] for task in todo['tasks'])
        task_check_mapping[f"day{todo['day']}"] = checked_count
    
    return task_check_mapping

# 페이지 5: 현황 그래프 페이지
if st.session_state.page == 5:
    st.markdown("<h1 class='title'>🗓️ 스파르탄 플래너</h1>", unsafe_allow_html=True)

    # 총 계획 일 수 계산
    total_days = (st.session_state.end_date - st.session_state.start_date).days + 1
    total_tasks = sum(len(day['tasks']) for day in st.session_state.todo_list)
    completed_tasks = sum(task['checked'] for day in st.session_state.todo_list for task in day['tasks'])
    incomplete_tasks = total_tasks - completed_tasks
    progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    # Week-Day Mapping
    week_day_mapping = create_week_day_mapping(st.session_state.start_date, st.session_state.end_date)
    
    # Progress per week
    weekly_progress = []
    for week, days in week_day_mapping.items():
        week_tasks = sum(len(st.session_state.todo_list[day-1]['tasks']) for day in days)
        week_completed_tasks = sum(task['checked'] for day in days for task in st.session_state.todo_list[day-1]['tasks'])
        weekly_progress.append((week_completed_tasks / week_tasks) * 100 if week_tasks > 0 else 0)

    # 상단 작업 진척도 메모장 스타일
    st.markdown("### 📌작업 진척도")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div style="padding: 10px; background-color: #fffacd; border-radius: 5px; border: 1px solid #ddd; position: relative;">
                <div style="background: repeating-linear-gradient(#fffacd, #fffacd 24px, #d3d3d3 25px); position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.7; pointer-events: none;"></div>
                <h3 style="text-align: center; color: #333; position: relative; z-index: 1;">완료한 작업</h3>
                <p style="text-align: center; font-size: 24px; font-weight: bold; position: relative; z-index: 1;">{}</p>
            </div>
        """.format(completed_tasks), unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div style="padding: 10px; background-color: #fffacd; border-radius: 5px; border: 1px solid #ddd; position: relative;">
                <div style="background: repeating-linear-gradient(#fffacd, #fffacd 24px, #d3d3d3 25px); position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.7; pointer-events: none;"></div>
                <h3 style="text-align: center; color: #333; position: relative; z-index: 1;">미수행 작업</h3>
                <p style="text-align: center; font-size: 24px; font-weight: bold; position: relative; z-index: 1;">{}</p>
            </div>
        """.format(incomplete_tasks), unsafe_allow_html=True)

    # 전체 목표 진척도 도넛 차트
    fig = px.pie(
        values=[completed_tasks, incomplete_tasks],
        names=['완료된 작업', '미수행 작업'],
        hole=0.7,
        color_discrete_sequence=['#87CEEB', '#FFC0CB']  # 연한 하늘색과 연한 분홍색
    )
    fig.update_traces(textinfo='percent+label', showlegend=False)

    fig.update_layout(
        title={"text": "전체 진척도", "x": 0.5, "xanchor": "center"},
        annotations=[dict(text=f'{progress:.2f}%', x=0.5, y=0.5, font_size=20, showarrow=False)],
        template='plotly_white',
        height=300,  # 그래프 높이 조정
        width=300   # 그래프 너비 조정
    )

    # 주간 목표 진척도
    colors = px.colors.qualitative.Plotly
    weekly_fig = px.bar(
        x=[f"주 {i+1}" for i in range(len(weekly_progress))],
        y=weekly_progress,
        labels={'x': '주', 'y': '진척도 (%)'},
        title="주간 진척도",
        color=[f"주 {i+1}" for i in range(len(weekly_progress))],  # 색상 추가
        color_discrete_sequence=colors
    )

    # Layout 조정
    weekly_fig.update_layout(
        template='plotly_white',
        title={'x': 0.5, 'xanchor': 'center'},
        xaxis_title="주",
        yaxis_title="진척도 (%)",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14),
        height=300,  # 그래프 높이 조정
        width=300   # 그래프 너비 조정
    )

    # 그래프를 가로로 나란히 표시
    st.markdown("<div style='display: flex; justify-content: space-around;'>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        st.plotly_chart(weekly_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # # 월별 달력 생성
    # st.markdown("### 월별 달력")

    # # 현재 달을 설정
    # if 'current_month' not in st.session_state:
    #     st.session_state.current_month = st.session_state.start_date.month

    # current_month = st.session_state.current_month
    # current_year = st.session_state.start_date.year

    # # 월 변경 버튼
    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     if st.button("⬅️ 이전 달"):
    #         st.session_state.current_month -= 1
    #         if st.session_state.current_month < 1:
    #             st.session_state.current_month = 12
    #             st.session_state.start_date = st.session_state.start_date.replace(year=st.session_state.start_date.year - 1)
    # with col3:
    #     if st.button("다음 달 ➡️"):
    #         st.session_state.current_month += 1
    #         if st.session_state.current_month > 12:
    #             st.session_state.current_month = 1
    #             st.session_state.start_date = st.session_state.start_date.replace(year=st.session_state.start_date.year + 1)

    # current_month = st.session_state.current_month
    # current_year = st.session_state.start_date.year

    # # 달력 데이터 생성
    # calendar_data = []

    # for day in st.session_state.todo_list:
    #     date = st.session_state.start_date + timedelta(days=day['day'] - 1)
    #     completed_tasks = sum(task['checked'] for task in day['tasks'])
    #     calendar_data.append({
    #         '날짜': date,
    #         '완료된 작업': completed_tasks,
    #         '총 작업': len(day['tasks'])
    #     })

    # df_calendar = pd.DataFrame(calendar_data)
    # df_calendar['날짜'] = pd.to_datetime(df_calendar['날짜'])

    # # 일간 진척도를 위한 그라데이션 색상
    # def task_color(completed_tasks):
    #     if completed_tasks == 0:
    #         return 'white'
    #     elif completed_tasks == 1:
    #         return '#e0ffe0'  # 연한 초록색
    #     elif completed_tasks == 2:
    #         return '#a3e4a3'  # 중간 초록색
    #     elif completed_tasks == 3:
    #         return '#52b788'  # 진한 초록색
    #     return 'white'

    # df_calendar['color'] = df_calendar['완료된 작업'].apply(task_color)

    # # 달력 스타일
    # cal = calendar.Calendar()
    # month_days = cal.monthdayscalendar(current_year, current_month)

    # days_in_week = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    # # 요일 헤더 표시
    # cols = st.columns(7)
    # for i, day in enumerate(days_in_week):
    #     cols[i].markdown(f"<div style='text-align: center; color: white; background-color: lightpink; border-radius: 5px; padding: 10px 0;'>{day}</div>", unsafe_allow_html=True)

    # # 달력 표시
    # for week in month_days:
    #     cols = st.columns(7)
    #     for i, day in enumerate(week):
    #         if day == 0:
    #             cols[i].markdown(f"<div style='height: 50px; border: 1px solid lightgrey; border-radius: 5px;'></div>", unsafe_allow_html=True)
    #         else:
    #             date = datetime(current_year, current_month, day)
    #             if date in df_calendar['날짜'].values:
    #                 completed_tasks = df_calendar.loc[df_calendar['날짜'] == date, '완료된 작업'].values[0]
    #                 if completed_tasks == 3:
    #                     color_class = 'background-color: #52b788;'
    #                 elif completed_tasks == 2:
    #                     color_class = 'background-color: #a3e4a3;'
    #                 elif completed_tasks == 1:
    #                     color_class = 'background-color: #e0ffe0;'
    #                 else:
    #                     color_class = 'background-color: white;'
    #             else:
    #                 color_class = 'background-color: white;'

    #             if cols[i].button(f"{day}", key=f'day_{day}', help=f'{day}일', use_container_width=True):
    #                 st.session_state.selected_day = day
    #                 st.session_state.page = 4
    #                 st.experimental_rerun()

    #             cols[i].markdown(f"<div style='height: 50px; text-align: center; {color_class} border: 1px solid lightgrey; border-radius: 5px;'>{day}</div>", unsafe_allow_html=True)

    # 이전 버튼 
    if st.button("⬅️ 뒤로", key='back_progress'):
        st.session_state.page = 4
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)