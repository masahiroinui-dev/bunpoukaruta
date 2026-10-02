import base64
import json
import os
import time
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. ページ初期設定
# ---------------------------------------------------------
st.set_page_config(page_title="助詞かるた大会", page_icon="🎴", layout="centered")


# ---------------------------------------------------------
# 2. 背景画像（.jpg）をCSSに適用する関数
# ---------------------------------------------------------
def set_background(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpeg;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# 3. かるた風基本デザインCSS
# ---------------------------------------------------------
st.markdown(
    """
<style>
    /* 全体フォント */
    html, body, [class*="css"] {
        font-family: 'Hiragino Mincho ProN', 'Yu Mincho', serif;
    }
    
    /* 読み札（問題表示） */
    .yomifuda {
        background-color: rgba(255, 253, 250, 0.93);
        border: 4px solid #8b261d;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        text-align: center;
        color: #2b2b2b;
    }
    .yomifuda-title {
        font-size: 1.1rem;
        color: #8b261d;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }
    .yomifuda-text {
        font-size: 1.8rem;
        font-weight: bold;
        line-height: 1.6;
    }
    .target-highlight {
        color: #d9381e;
        border-bottom: 3px solid #d9381e;
        padding-bottom: 2px;
    }

    /* 取り札（かるたボタン） */
    div.stButton > button {
        background-color: rgba(252, 248, 238, 0.95) !important;
        color: #1a1a1a !important;
        border: 3px solid #1c3d5a !important;
        border-radius: 8px !important;
        height: 100px !important;
        font-size: 1.5rem !important;
        font-weight: bold !important;
        box-shadow: 2px 4px 8px rgba(0,0,0,0.3) !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 4px 8px 12px rgba(0,0,0,0.4) !important;
        background-color: #fff9e6 !important;
        border-color: #8b261d !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 4. 進行状況（JSON）の読み書き処理
# ---------------------------------------------------------
PROGRESS_FILE = "user_progress.json"


def load_all_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_user_progress(user_id, current_index, score, mistakes):
    data = load_all_progress()
    data[user_id] = {
        "current_index": current_index,
        "score": score,
        "mistakes": mistakes,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------
# 5. CSVデータ読み込み & 段位判定
# ---------------------------------------------------------
@st.cache_data
def load_questions(csv_file="questions.csv"):
    df = pd.read_csv(csv_file)
    questions = []
    options = ["格助詞", "接続助詞", "終助詞", "副助詞"]
    for _, row in df.iterrows():
        questions.append(
            {
                "sentence": row["sentence"],
                "target": row["target"],
                "options": options,
                "answer": row["answer"],
            }
        )
    return questions


RANK_LIST = [
    "十級",  # 0~19問
    "九級",  # 20~39問
    "八級",  # 40~59問
    "七級",  # 60~79問
    "六級",  # 80~99問
    "五級",  # 100~119問
    "四級",  # 120~139問
    "三級",  # 140~159問
    "二級",  # 160~179問
    "一級",  # 180~199問
    "初段",  # 200~219問
    "二段",  # 220~239問
    "三段",  # 240~259問
    "四段",  # 260~279問
    "五段",  # 280~299問
]


def calculate_rank(score, total_questions):
    if score >= total_questions and total_questions > 0:
        return "🏆 助詞名人 🏆"
    rank_index = min(score // 20, len(RANK_LIST) - 1)
    return RANK_LIST[rank_index]


# ---------------------------------------------------------
# 6. アプリデータの初期化
# ---------------------------------------------------------
try:
    QUESTIONS = load_questions("questions.csv")
except Exception as e:
    st.error(
        f"`questions.csv` の読み込みに失敗しました。`bunpou_app` フォルダ内にファイルがあるか確認してください。\nエラー: {e}"
    )
    st.stop()

if "game_state" not in st.session_state:
    st.session_state.game_state = "start"
    st.session_state.user_id = ""
    st.session_state.score = 0
    st.session_state.mistakes = 0
    st.session_state.current_index = 0
    st.session_state.start_time = 0

st.markdown(
    "<h1 style='text-align: center; color: #8b261d;'>🎴 助詞かるた選手権</h1>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 7. 画面制御
# ---------------------------------------------------------

# 【スタート画面 / 途中再開選択】
if st.session_state.game_state == "start":
    set_background("title_bg.jpg")  # タイトル背景

    st.markdown(
        f"""
    <div class="yomifuda">
        <h3>【ルール】</h3>
        <p>問題文の<b>「強調された助詞」</b>の種類を見極め、かるたの取り札を選んでください！</p>
        <p>📚 <b>総問題数</b>: 全 {len(QUESTIONS)} 問<br>
        ⏱️ <b>制限時間</b>: 1問につき <b>10秒</b><br>
        ❌ <b>お手つき</b>: <b>2回</b>でゲームオーバー<br>
        🏅 <b>段位認定</b>: <b>20問正解ごとに昇段</b>（十級〜五段）、全問正解で <b>名人</b></p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    user_input = st.text_input(
        "👤 ユーザー名 または 出席番号を入力してください",
        value=st.session_state.user_id,
        placeholder="例: 2J01_tanaka",
    )

    if user_input:
        st.session_state.user_id = user_input.strip()
        all_progress = load_all_progress()

        if st.session_state.user_id in all_progress:
            saved = all_progress[st.session_state.user_id]
            st.info(
                f"🔖 **保存された進捗が見つかりました！**\n\n"
                f"- 前回通過: **第 {saved['current_index'] + 1} 問**\n"
                f"- 正解数: **{saved['score']} 枚** | お手つき: **{saved['mistakes']} / 2**\n"
                f"- 最終更新: {saved.get('updated_at', '不明')}"
            )

            col_resume, col_restart = st.columns(2)
            if col_resume.button("▶️ 続きから再開する"):
                st.session_state.current_index = saved["current_index"]
                st.session_state.score = saved["score"]
                st.session_state.mistakes = saved["mistakes"]
                st.session_state.game_state = "playing"
                st.session_state.start_time = time.time()
                st.rerun()

            if col_restart.button("🔄 最初からやり直す"):
                st.session_state.current_index = 0
                st.session_state.score = 0
                st.session_state.mistakes = 0
                st.session_state.game_state = "playing"
                st.session_state.start_time = time.time()
                st.rerun()
        else:
            if st.button("🎴 はじめから開始する"):
                st.session_state.current_index = 0
                st.session_state.score = 0
                st.session_state.mistakes = 0
                st.session_state.game_state = "playing"
                st.session_state.start_time = time.time()
                st.rerun()
    else:
        st.warning("⚠️ プレイを始めるにはユーザー名・IDを入力してください。")

# 【ゲームプレイ画面】
elif st.session_state.game_state == "playing":
    set_background("game_bg.jpg")  # ゲームプレイ背景

    # 終了判定（全問終了 または 2回ミス）
    if (
        st.session_state.current_index >= len(QUESTIONS)
        or st.session_state.mistakes >= 2
    ):
        st.session_state.game_state = "game_over"
        st.rerun()

    q = QUESTIONS[st.session_state.current_index]

    # タイマー計算
    elapsed = time.time() - st.session_state.start_time
    time_left = max(0.0, 10.0 - elapsed)

    if time_left <= 0:
        st.error("⏰ タイムオーバー！お手つき！")
        st.session_state.mistakes += 1
        st.session_state.current_index += 1

        if st.session_state.user_id:
            save_user_progress(
                st.session_state.user_id,
                st.session_state.current_index,
                st.session_state.score,
                st.session_state.mistakes,
            )

        st.session_state.start_time = time.time()
        time.sleep(1)
        st.rerun()

    # ヘッダー情報 ＆ 中断保存ボタン
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    col1.metric("獲得札数", f"{st.session_state.score} 枚")
    col2.metric("お手つき", f"{st.session_state.mistakes} / 2")
    col3.metric("残り時間", f"{time_left:.1f} 秒")

    if col4.button("💾 保存して中断"):
        if st.session_state.user_id:
            save_user_progress(
                st.session_state.user_id,
                st.session_state.current_index,
                st.session_state.score,
                st.session_state.mistakes,
            )
            st.success("進捗を保存しました！スタート画面に戻ります。")
            time.sleep(1)
            st.session_state.game_state = "start"
            st.rerun()

    st.progress(time_left / 10.0)

    # 問題文表示
    sentence_html = q["sentence"].replace(
        f"**{q['target']}**",
        f"<span class='target-highlight'>{q['target']}</span>",
    )
    st.markdown(
        f"""
    <div class="yomifuda">
        <div class="yomifuda-title">【 第 {st.session_state.current_index + 1} 首 / 全 {len(QUESTIONS)} 首 】 (プレイヤー: {st.session_state.user_id})</div>
        <div class="yomifuda-text">「 {sentence_html} 」</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 取り札配置
    col_a, col_b = st.columns(2)
    cards = [
        (col_a, "格助詞"),
        (col_b, "接続助詞"),
        (col_a, "終助詞"),
        (col_b, "副助詞"),
    ]

    for col, opt_name in cards:
        with col:
            if st.button(f"🎴  {opt_name}", key=f"karuta_{opt_name}"):
                if opt_name == q["answer"]:
                    st.success(f"🎉 お見事！ 「{opt_name}」を取った！")
                    st.session_state.score += 1
                else:
                    st.error(
                        f"💥 お手つき！ 正解は 「{q['answer']}」 でした..."
                    )
                    st.session_state.mistakes += 1

                st.session_state.current_index += 1

                if st.session_state.user_id:
                    save_user_progress(
                        st.session_state.user_id,
                        st.session_state.current_index,
                        st.session_state.score,
                        st.session_state.mistakes,
                    )

                st.session_state.start_time = time.time()
                time.sleep(0.8)
                st.rerun()

    time.sleep(0.1)
    st.rerun()

# 【結果発表画面】
elif st.session_state.game_state == "game_over":
    set_background("title_bg.jpg")

    st.markdown(
        "<h2 style='text-align: center; color: #8b261d;'>📜 大会結果 📜</h2>",
        unsafe_allow_html=True,
    )

    total_q = len(QUESTIONS)
    score = st.session_state.score
    rank = calculate_rank(score, total_q)

    st.markdown(
        f"""
    <div class="yomifuda">
        <p style="font-size: 1.1rem; color: #555;">対局者: <b>{st.session_state.user_id}</b></p>
        <p style="font-size: 1.3rem;">獲得札数: <b>{score} / {total_q} 枚</b></p>
        <p style="font-size: 1.3rem;">到達問題: <b>第 {st.session_state.current_index} 問</b></p>
        <p style="font-size: 1.3rem;">お手つき回数: <b>{st.session_state.mistakes} 回</b></p>
        <hr>
        <p style="font-size: 1.2rem; color: #555;">認定された段位</p>
        <h1 style="color: #8b261d; font-size: 3rem;">{rank}</h1>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🎴 スタート画面に戻る"):
        st.session_state.game_state = "start"
        st.rerun()