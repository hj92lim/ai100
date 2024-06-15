import os
from openai import OpenAI
import streamlit as st
import time

os.environ["OPENAI_API_KEY"] = st.secrets['API_KEY']
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

st.title('슈퍼 시나리오 봇 🤖')

keyword = st.text_input("키워드를 입력하세요")

if st.button('생성하기'):    
    with st.spinner('생성 중입니다.'):
        chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": keyword,
            },
            {
                "role": "system",
                "content": "입력 받은 키워드에 대한 흥미진진한 300자 이내의 시나리오를 작성해줘.",
            }
        ],
        model="gpt-4o",
        )
        result = chat_completion.choices[0].message.content
    st.write(result)