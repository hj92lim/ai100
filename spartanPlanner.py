import os
import json
import streamlit as st
from openai import OpenAI
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

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
# if st.session_state.page == 1:
if st.session_state.page == 1:
    col1, col2 = st.columns([1, 9])  # 제목과 버튼을 나란히 배치하기 위해 두 개의 컬럼 생성
    with col1:
        if st.button("📈"):
            st.session_state.page = 5
            st.experimental_rerun()
    with col2:
        st.markdown("<h1 class='title'>🗓️ 스파르탄 플래너</h1>", unsafe_allow_html=True)
    # st.markdown("<h1 class='title'>🗓️ 스파르탄 플래너</h1>", unsafe_allow_html=True)
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
    col1, col2 = st.columns([1, 9])  # 제목과 버튼을 나란히 배치하기 위해 두 개의 컬럼 생성
    with col1:
        if st.button("📈"):
            st.session_state.page = 5
            st.experimental_rerun()
    with col2:
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
# elif st.session_state.page == 4:
#     st.markdown("<h1 class='title'>🗓️ 스파르탄 플래너</h1>", unsafe_allow_html=True)
    
elif st.session_state.page == 4:
    col1, col2 = st.columns([1, 9])  # 제목과 버튼을 나란히 배치하기 위해 두 개의 컬럼 생성
    with col1:
        if st.button("📈"):
            st.session_state.page = 5
            st.experimental_rerun()
    with col2:
        st.markdown("<h1 class='title'>🗓️ 스파르탄 플래너</h1>", unsafe_allow_html=True)

    # JSON 데이터 로드
    planner_data = load_json("planner_data.json")
    st.session_state.monthly_goal = planner_data["monthly_goal"]
    st.session_state.weekly_goals = planner_data["weekly_goals"]
    if st.session_state.todo_list is None:
        st.session_state.todo_list = planner_data["todo_list"]
    
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
    if selected_week <= len(st.session_state.weekly_goals):
        st.write(f"{selected_week}주차 목표: {st.session_state.weekly_goals[selected_week - 1]}")
    
    st.write("일별 목표:")
    completed_tasks = 0
    total_tasks = 0
    
    for todo in st.session_state.todo_list:
        if todo['day'] == selected_day:
            for i, task_data in enumerate(todo['tasks'], start=1):
                task = task_data['task']
                key = f"day{todo['day']}_task{i}"
                if key not in st.session_state:
                    st.session_state[key] = task_data['checked']
                checked = st.checkbox(f"{i}. {task}", key=key)
                if checked != task_data['checked']:
                    task_data['checked'] = checked
                    st.session_state.todo_list[todo['day']-1]['tasks'][i-1]['checked'] = checked
                
                if checked:
                    completed_tasks += 1
                total_tasks += 1
    
    # 체크 여부 업데이트
    planner_data["todo_list"] = st.session_state.todo_list
    save_json("planner_data.json", planner_data)
    
    print(total_tasks)
    # 일별 수행 갯수와 미수행 갯수 계산
    uncompleted_tasks = total_tasks - completed_tasks
    # st.write(f"수행된 task 갯수: {completed_tasks}")
    # st.write(f"미수행 task 갯수: {uncompleted_tasks}")
    
    # 진척도 계산
    overall_total_tasks = sum(len(day['tasks']) for day in st.session_state.todo_list)
    overall_completed_tasks = sum(task['checked'] for day in st.session_state.todo_list for task in day['tasks'])
    progress = (overall_completed_tasks / overall_total_tasks) * 100 if overall_total_tasks > 0 else 0
    
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
    st.markdown("</div>", unsafe_allow_html=True)

# 페이지 5: 전체 현황
if st.session_state.page == 5:
    # 가상의 일정 데이터 생성
    def generate_sample_data():
        np.random.seed(0)
        activities = [
            "첫 번째 주 목표: 식이조절 시작과 기초 체력 훈련 적응",
            "두 번째 주 목표: 체력 훈련 강도 증가 및 유산소 운동 추가",
            "세 번째 주 목표: 근력 운동 강화 및 식단 조절 지속",
            "네 번째 주 목표: 높은 강도의 운동 유지와 지속 가능한 식습관 정착"
        ]
        plan_start = np.array([1, 8, 15, 22])  # 각 주의 시작일
        plan_duration = np.array([7, 7, 7, 7])  # 각 목표는 일주일간 지속
        actual_start = plan_start + np.random.randint(-1, 2, size=4)  # 계획 시작일 ± 1일
        actual_duration = plan_duration + np.random.randint(-1, 2, size=4)  # 계획 기간 ± 1일
        percent_complete = np.random.randint(0, 101, size=4)
        data = {
            'Activity': activities,
            'Plan Start': plan_start,
            'Plan Duration': plan_duration,
            'Actual Start': actual_start,
            'Actual Duration': actual_duration,
            'Percent Complete': percent_complete
        }
        return pd.DataFrame(data)

    # 형광색 생성
    fluorescent_colors = [
        "#39FF14", "#FFEA00", "#FF00FF", "#00FFFF", "#FF69B4",
        "#ADFF2F", "#FF4500", "#7CFC00", "#FFD700", "#40E0D0",
        "#FF1493", "#8A2BE2", "#00FF7F", "#DC143C", "#1E90FF"
    ]

    # 데이터 생성
    df = generate_sample_data()

    # 활동별 형광색 설정
    num_activities = len(df['Activity'])
    colors = fluorescent_colors[:num_activities]
    color_map = dict(zip(df['Activity'], colors))

    # 완료되지 않은 작업 수와 완료된 작업수 설정
    completed_tasks = 1
    incomplete_tasks = 2

    # 진척도에 따른 피드백 설정 및 배경색 지정
    if completed_tasks / (completed_tasks + incomplete_tasks) >= 1:
        feedback = "🎉 모든 작업을 완료했습니다! 훌륭해요!"
        background_color = "#b2fab4"  # 연한 파스텔 연두색
    elif completed_tasks / (completed_tasks + incomplete_tasks) >= 2/3:
        feedback = "👏 거의 다 왔어요! 조금만 더 힘내세요!"
        background_color = "#fff9b2"  # 연한 파스텔 노랑색
    elif completed_tasks / (completed_tasks + incomplete_tasks) >= 1/3:
        feedback = "😵 조금 더 노력해봐요!"
        background_color = "#e0b3ff"  # 연한 파스텔 보라색
    else:
        feedback = "🤬 더 열심히 해야겠어요!"
        background_color = "#ffb3d9"  # 연한 파스텔 분홍색

    # # Streamlit 애플리케이션
    # st.markdown("<h1 style='text-align: center;'>🗓️ 스파르타 플래너</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.2, 4, 1])  # 세 개의 컬럼 생성
    with col1:
        if st.button("⬅️ 뒤로"):
            st.session_state.page = 3  # 페이지 3로 이동
            st.experimental_rerun()
    with col2:
        st.markdown("<h1 style='text-align: center;'>🗓️ 스파르탄 플래너</h1>", unsafe_allow_html=True)
    with col3:
        if st.button("홈 🏠"):
            st.session_state.page = 1  # 페이지 1로 이동
            st.experimental_rerun()

    # 작업 개요 표시
    st.write('#### 📌 오늘의 작업 진척도')
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: #333;">{}</h2>
            <p>⭕ 수행완료 작업수</p>
        </div>
        """.format(completed_tasks), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: #333;">{}</h2>
            <p>❌ 미수행 작업수</p>
        </div>
        """.format(incomplete_tasks), unsafe_allow_html=True)

    # 피드백 표시
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 100px;">
        <div style="background-color: {background_color}; padding: 10px 20px; border-radius: 10px; text-align: center; font-size: 16px;">
            💬 오늘의 피드백: {feedback}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # New data integration
    monthly_goal = "체중 3kg 감량과 근육량 증가"
    weekly_goals = [
        "첫 번째 주 목표: 식이조절 시작과 기초 체력 훈련 적응",
        "두 번째 주 목표: 체력 훈련 강도 증가 및 유산소 운동 추가",
        "세 번째 주 목표: 근력 운동 강화 및 식단 조절 지속",
        "네 번째 주 목표: 높은 강도의 운동 유지와 지속 가능한 식습관 정착"
    ]
    todo_list = [
        {
            "day": 1,
            "tasks": [
                {"task": "식단 기록 시작", "checked": False},
                {"task": "30분 걷기", "checked": True},
                {"task": "물 2리터 마시기", "checked": False}
            ]
        },
        # Add the remaining days here as needed
    ]

    # Display todo list for today
    today = datetime.now().day
    today_tasks = next((item['tasks'] for item in todo_list if item['day'] == today), [])
    # st.write('#### 📌 오늘의 할 일')
    for task in today_tasks:
        st.checkbox(task['task'], value=task['checked'])

    # 현재 날짜
    current_date = datetime.now().date()

    # 이번 주의 월요일과 일요일 계산
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # 하루마다 완료된 작업 수 계산
    df_tasks = pd.DataFrame({
        'Date': pd.date_range(start='2024-06-01', periods=30, freq='D'),
        'Completed Tasks': np.random.randint(0, 5, size=30),
        'Activity': np.random.choice(df['Activity'], size=30)
    })

    # 이번 주에 해당하는 데이터 필터링
    df_tasks_week = df_tasks[(df_tasks['Date'] >= pd.Timestamp(start_of_week)) & (df_tasks['Date'] <= pd.Timestamp(end_of_week))]

    # 일별 작업 완료 그래프 생성
    fig_tasks = go.Figure()

    for activity in df['Activity']:
        df_activity = df_tasks_week[df_tasks_week['Activity'] == activity]
        fig_tasks.add_trace(go.Scatter(
            x=df_activity['Date'],
            y=df_activity['Completed Tasks'],
            mode='lines+markers',
            name=activity,
            line=dict(color=color_map[activity], width=5),  # 막대선을 더 두껍게 설정
            hoverinfo='x+y+name',
            showlegend=False  # 각 trace에 대해 showlegend=False 설정
        ))

    st.write('')
    st.write('#### 📌 주간 작업 진척도')

    fig_tasks.update_layout(
        xaxis_title='Date',
        yaxis_title='Number of Completed Tasks',
        legend_title='Activities',
        plot_bgcolor='#f9f9f9',  # Task Overview 컬럼 배경색
        margin=dict(t=10, b=10),  # 상단(t) 및 하단(b) 여백 줄이기
        height=300,  # 그래프 높이 줄이기
        xaxis=dict(
            tickmode='array',
            tickvals=pd.date_range(start=start_of_week, periods=7, freq='D'),
            ticktext=['월', '화', '수', '목', '금', '토', '일'],
            tickfont=dict(size=20)  # 요일 글자 크기 설정
        ),
        yaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=2,  # y축을 2의 배수로 설정
        ),
        annotations=[
            go.layout.Annotation(
                text=f"{start_of_week.strftime('%m/%d')} - {end_of_week.strftime('%m/%d')}",
                xref="paper", yref="paper",
                x=1, y=1.1,
                showarrow=False,
                font=dict(size=12, color="black"),
                bgcolor="#f9f9f9",
                bordercolor="#f9f9f9",  # 바깥 선 제거
                borderwidth=0
            )
        ]
    )

    st.plotly_chart(fig_tasks)

    st.write('')
    st.write('#### 📌 월간 진척도 달력')

    # 달력 생성
    def generate_calendar(year, month):
        cal = calendar.Calendar(firstweekday=6)  # Sunday as first day of the week
        month_days = cal.monthdayscalendar(year, month)
        return month_days

    # 현재 년과 월을 세션 상태로 저장
    if 'current_year' not in st.session_state:
        st.session_state.current_year = current_date.year
    if 'current_month' not in st.session_state:
        st.session_state.current_month = current_date.month

    # 이전 달, 다음 달 버튼
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button('⬅️ 이전달'):
            if st.session_state.current_month == 1:
                st.session_state.current_year -= 1
                st.session_state.current_month = 12
            else:
                st.session_state.current_month -= 1
    with col3:
        if st.button('➡️ 다음달'):
            if st.session_state.current_month == 12:
                st.session_state.current_year += 1
                st.session_state.current_month = 1
            else:
                st.session_state.current_month += 1

    # 현재 년과 월 표시
    with col2:
        st.markdown(f"<h2 style='text-align: center;'>{st.session_state.current_year}-{st.session_state.current_month:02d}</h2>", unsafe_allow_html=True)

    # 달력 데이터 생성
    month_days = generate_calendar(st.session_state.current_year, st.session_state.current_month)

    # 진척도 데이터 생성 (가상의 데이터)
    progress_data = {datetime(st.session_state.current_year, st.session_state.current_month, day).date(): np.random.randint(0, 101) for week in month_days for day in week if day != 0}

    # 달력 그래프 생성
    fig_calendar = go.Figure()

    for week in month_days:
        for day in week:
            if day == 0:
                continue
            date = datetime(st.session_state.current_year, st.session_state.current_month, day).date()
            progress = progress_data.get(date, 0)
            color = f'rgba(0, 128, 0, {progress / 100})'  # 퍼센트에 따라 진한 녹색
            fig_calendar.add_shape(
                type='rect',
                x0=week.index(day),
                y0=len(month_days) - month_days.index(week) - 1,
                x1=week.index(day) + 1,
                y1=len(month_days) - month_days.index(week),
                line=dict(width=1, color='black'),
                fillcolor=color,
            )
            fig_calendar.add_trace(go.Scatter(
                x=[week.index(day) + 0.5],
                y=[len(month_days) - month_days.index(week) - 0.5],
                text=[str(day)],
                mode='text',
                showlegend=False,  # 각 trace에 대해 showlegend=False 설정
                textfont=dict(size=30)  # 날짜 글자 크기 설정
            ))

    fig_calendar.update_layout(
        xaxis=dict(
            side='top',  # x축을 상단으로
            tickmode='array',
            tickvals=list(range(7)),
            ticktext=['일', '월', '화', '수', '목', '금', '토'],
            tickfont=dict(size=20),  # 요일 글자 크기 설정
            showgrid=False
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(month_days))),
            ticktext=[''] * len(month_days),
            showgrid=False
        ),
        plot_bgcolor='#f9f9f9',
        height=400,
        width=700,
        showlegend=False,  # 달력에 대해 showlegend=False 설정
        margin=dict(t=10, b=10),  # 상단(t) 및 하단(b) 여백 줄이기
        font=dict(size=20)
    )

    st.plotly_chart(fig_calendar)

    st.write('')
    st.write('')

    # 차트와 버튼을 한 줄에 배치
    col3, col4 = st.columns([3.2, 1])
    with col3:
        st.markdown("<h3 style='text-align: left; font-size:24px;'>📌 전체 일정표</h3>", unsafe_allow_html=True)
    with col4:
        if st.button('🔍 계획 상세보기'):
            st.session_state.show_data = not st.session_state.get('show_data', False)

    if 'show_data' in st.session_state and st.session_state.show_data:
        st.write('#### 📌 계획 상세정보')
        st.dataframe(df)

    # 차트 생성
    fig = go.Figure()

    # 계획 기간 바 표시 (회색)
    fig.add_trace(go.Bar(
        y=[f'{i+1}번째 주 목표' for i in range(len(df))],  # y축 레이블 수정
        x=df['Plan Duration'],
        base=df['Plan Start'],
        orientation='h',
        marker=dict(color='lightgray'),
        name='계획 기간',
        hoverinfo='skip'
    ))

    # 실제 기간 바 표시 (연한 하늘색)
    fig.add_trace(go.Bar(
        y=[f'{i+1}번째 주 목표' for i in range(len(df))],  # y축 레이블 수정
        x=df['Actual Duration'],
        base=df['Actual Start'],
        orientation='h',
        marker=dict(color='skyblue'),
        name='실제 기간',
        hoverinfo='skip'
    ))

    # 완료 퍼센티지 바 표시 (진한 하늘색)
    fig.add_trace(go.Bar(
        y=[f'{i+1}번째 주 목표' for i in range(len(df))],  # y축 레이블 수정
        x=df['Actual Duration'] * (df['Percent Complete'] / 100),
        base=df['Actual Start'],
        orientation='h',
        marker=dict(color='dodgerblue'),
        name='진척도[%]',
        hoverinfo='skip'
    ))

    # 업데이트 메뉴 추가
    fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [{"visible": [True, False, False]}],
                        "label": "계획 기간",
                        "method": "update",
                    },
                    {
                        "args": [{"visible": [False, True, False]}],
                        "label": "실제 기간",
                        "method": "update",
                    },
                    {
                        "args": [{"visible": [False, False, True]}],
                        "label": "진척도[%]",
                        "method": "update",
                    },
                    {
                        "args": [{"visible": [True, True, True]}],
                        "label": "Show All",
                        "method": "update",
                    },
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.00,  # x 위치 조정
                "xanchor": "left",
                "y": 1.15,  # y 위치 조정
                "yanchor": "top"
            }
        ],
        xaxis=dict(
            range=[1, 14],  # 처음에 1일부터 14일까지 보이게 설정
            tickmode='linear',
            tick0=1,
            dtick=1
        ),
        yaxis=dict(
            title='Activities',
            tickmode='array',
            tickvals=[f'{i+1}번째 주 목표' for i in range(len(df))],  # y축 레이블 수정
            ticktext=[f'{i+1}번째 주 목표' for i in range(len(df))]  # y축 레이블 텍스트 설정
        ),
        barmode='overlay',
        xaxis_title='Days',
        yaxis_title='Activities',
        legend=dict(
            x=0.22,
            y=1.05,
            orientation='h'
        ),
        annotations=[
            dict(
                x=0.96,  # 진척도 [%] 옆에 텍스트를 배치하기 위한 x 위치 조정
                y=1.13,  # 범례와 같은 y 위치
                xref='paper',
                yref='paper',
                text='👈 클릭하세요',
                showarrow=False,
                font=dict(size=18)
            )
        ],
        height=600,
        width=1000,
        showlegend=True,  # 범례 표시
        plot_bgcolor='#f9f9f9',  # Task Overview 컬럼 배경색과 동일하게 설정
        margin=dict(t=20)  # 상단 여백 줄이기
    )

    # 가로 스크롤 바 추가
    fig.update_xaxes(rangeslider_visible=True)

    # 인터랙티브 차트 표시
    st.plotly_chart(fig, use_container_width=True)
