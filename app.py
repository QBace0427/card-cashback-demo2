import streamlit as st
from openai import OpenAI
import json

# 讀取 Streamlit Secrets 裡的金鑰
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("信用卡回饋比較（AI 即時查詢）")

merchant = st.text_input("請輸入消費地點（如 Netflix / YouTube / 蝦皮）")

if st.button("查詢回饋"):

    prompt = f"""
    你是一位台灣信用卡專家，請根據「{merchant}」的場景，
    比較以下信用卡的回饋：國泰 Cube、富邦 J 卡、中信英雄聯盟卡。

    請務必回傳 JSON 格式：
    {{
      "results": [
        {{"card": "國泰 Cube 卡", "reward_percent": "", "note": ""}},
        {{"card": "富邦 J 卡", "reward_percent": "", "note": ""}},
        {{"card": "中信英雄聯盟卡", "reward_percent": "", "note": ""}}
      ],
      "best_card": ""
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    data = response.choices[0].message.content

    # 嘗試解析 JSON
    try:
        result_json = json.loads(data)
        st.json(result_json)
    except:
        st.write("AI 回覆無法解析成 JSON，以下顯示原始內容：")
        st.write(data)
