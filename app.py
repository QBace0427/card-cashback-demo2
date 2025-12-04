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
    "Momo 購物",
]

merchant = st.selectbox(
    "請選擇或搜尋消費地點",
    merchant_options,
    index=None,
    placeholder="請選擇消費地點…"
)

# 自訂輸入
custom_input = st.text_input("或自行輸入消費地點（可選）")
merchant_final = custom_input if custom_input.strip() else merchant


# ======================================
# AI 查詢（含快取、retry、fallback）
# ======================================
@st.cache_data(ttl=3600)
def ask_ai(merchant_query, cards):

    card_list_text = "\n".join([f"- {c}" for c in cards])

    system_prompt = """
    你是一位信用卡回饋分析助手，只能輸出 JSON。
    JSON 格式必須完全正確，不能包含索引（0:,1: 等）。
    """

    user_prompt = f"""
    請比較以下信用卡在「{merchant_query}」的回饋：
    {card_list_text}

    嚴格輸出以下 JSON 格式：

    {{
      "best_card": "",
      "reward_percent": "",
      "note": ""
    }}

    注意：
    - "best_card" 只能是一張卡。
    - "reward_percent" 是該卡對這個通路的回饋%。
    - "note" 請簡短描述理由，例如是否限月份、是否列入活動通路等。
    - 請勿加入 results 陣列、索引編號、評論或其他文字。
    """

    # ===== 第一次：最便宜模型 =====
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini-quick",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=120
        )
        raw = response.choices[0].message.content

    except Exception:
        time.sleep(1)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=120
        )
        raw = response.choices[0].message.content

    cleaned = raw.strip()

    # 去除 ```json 區塊
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1].replace("json", "").strip()

    return cleaned


# ======================================
# 按鈕執行 & 美觀表格呈現
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

        best_card = result.get("best_card", "—")
        reward_percent = result.get("reward_percent", "—")
        note = result.get("note", "—")

        st.success("最佳信用卡推薦如下：")

        # ===== 美觀表格樣式 =====
        st.markdown(f"""
        <style>
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th {{
            background-color: #1f4435;
            color: white;
            padding: 10px;
            text-align: center;
        }}
        td {{
            background-color: #2c5a46;
            color: #f0f0f0;
            padding: 10px;
            text-align: center;
        }}
        </style>

        <table>
            <tr>
                <th>最佳卡片</th>
                <th>回饋</th>
                <th>說明</th>
            </tr>
            <tr>
                <td>{best_card}</td>
                <td><b>{reward_percent}</b></td>
                <td>{note}</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)

    except:
        st.error("AI 無法輸出有效資料，以下為原始內容：")
        st.write(raw)
