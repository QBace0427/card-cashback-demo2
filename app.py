import streamlit as st
import openai
import json

openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("信用卡回饋比較（AI 即時查詢）")

card_list = ["國泰 Cube", "富邦 J 卡", "中信 LINE Pay 卡", "中國信託 英雄聯盟卡"]
merchant = st.text_input("請輸入消費地點（如 Netflix / YouTube / 蝦皮）")

if st.button("查詢回饋"):
    prompt = f"""
    你是一個台灣信用卡專家，請根據最新公開資訊比較以下信用卡在「{merchant}」的回饋。

    請務必回傳 JSON 格式：
    {{
      "results": [
        {{"card": "", "reward_percent": "", "note": ""}}
      ],
      "best_card": ""
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}]
    )

    data = response["choices"][0]["message"]["content"]

    try:
        result_json = json.loads(data)
        st.json(result_json)
    except:
        st.write("AI 回覆格式有問題，原始內容如下：")
        st.write(data)
