import streamlit as st
from openai import OpenAI
import json
import time

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("信用卡回饋比較（AI 即時查詢｜可選卡片＆可選店家）")

# ======================================
# 可選信用卡（5 張）
# ======================================
card_options = [
    "國泰 Cube 卡",
    "富邦 J 卡",
    "中信 英雄聯盟卡",
    "台新 @GoGo 卡",
    "元大 HappyCash 聯名卡"
]

selected_cards = st.multiselect(
    "請選擇你想比較的信用卡（可多選）",
    card_options,
    default=[],
    placeholder="請選擇卡片…"
)

# ======================================
# 可選消費地點（15 個）
# ======================================

merchant_options = [
    "YouTube",
    "Netflix",
    "蝦皮 Shopee",
    "Uber Eats",
    "Foodpanda",
    "星巴克 Starbucks",
    "餐廳 Dining",
    "電影 Movie",
    "英雄聯盟 Riot Games",
    "旅遊平台 Klook",
    "機票 Airline",
    "Apple Store",
    "Google Play",
    "博客來 Books.com.tw",
    "Momo 購物"
]

merchant = st.selectbox(
    "請選擇或搜尋消費地點",
    merchant_options,
    index=None,
    placeholder="請選擇消費地點…"
)

# 也允許使用者輸入自己想要查的
custom_input = st.text_input("或自行輸入消費地點（可選）")

# 有輸入 custom_input 就覆蓋 selectbox
merchant_final = custom_input if custom_input.strip() else merchant



# ======================================
# AI 查詢（含快取、retry、fallback）
# ======================================
@st.cache_data(ttl=3600)
def ask_ai(merchant_query, cards):

    card_list_text = "\n".join([f"- {c}" for c in cards])

    system_prompt = """
    你是一個信用卡回饋 JSON 生產器。
    你只能輸出 JSON，不可以輸出任何解釋、文字或其他符號。
    JSON 必須遵守嚴格格式。
    """

    user_prompt = f"""
    比較以下信用卡在「{merchant_query}」的回饋：
    {card_list_text}

    嚴格輸出以下格式（不可多不可少）：

    {{
      "results": [
        {{
          "card": "",
          "reward_percent": "",
          "note": ""
        }}
      ],
      "best_card": ""
    }}
    """

    # 第一次嘗試：最便宜
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini-quick",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200
        )
        raw = response.choices[0].message.content
    except:
        # 如果失敗就 fallback
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200
        )
        raw = response.choices[0].message.content

    # 清理 AI 回覆，確保只剩 JSON
    cleaned = raw.strip()

    # 若 AI 回覆前後夾雜文字，自動抓出 JSON 主體
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        cleaned = cleaned.replace("json", "").strip()

    # 修正可能出現的結尾多逗號
    cleaned = cleaned.replace(",\n      ]", "\n      ]")
    cleaned = cleaned.replace(",\n    }", "\n    }")

    return cleaned




# ======================================
# 按鈕執行
# ======================================
if st.button("查詢回饋"):

    if not selected_cards:
        st.warning("請至少選擇 1 張信用卡！")
        st.stop()

    if not merchant_final:
        st.warning("請選擇或輸入一個消費地點！")
        st.stop()

    st.info("AI 正在分析信用卡回饋…")

    raw = ask_ai(merchant_final, selected_cards)

    try:
        result = json.loads(raw)
        st.success("以下為推薦結果：")
        st.json(result)

    except:
        st.error("AI 未能輸出正確 JSON，以下為原始內容：")
        st.write(raw)
