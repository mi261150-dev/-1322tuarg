import streamlit as st
import pandas as pd
import re
import os

# --- 1. レアリティ・名称定義 ---
def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        names = {
            1:"LR カタストロム", 7:"LLR ドーン", 16:"LR デモンズ", 18:"LR ぎーつ",
            26:"LLR クウガ", 27:"LR アギト", 36:"LR 電王", 48:"LR ゴースト",
            55:"LR ジ王", 58:"LR ディケイド", 61:"LLR V3",
            101:"ランダムパラレルLLR"
        }
        if n in names: return names[n]
        rarities = {
            99:"ランダムLR", 98:"ランダムSR",
            5:"SR", 20:"SR", 24:"SR", 25:"SR", 31:"SR", 33:"SR", 38:"SR", 40:"SR", 42:"SR", 46:"SR", 52:"SR", 63:"SR"
        }
        if n in rarities: return rarities[n]
        return "CP" if 64 <= n <= 77 else "N"
    except: return ""

def is_rare(n):
    r = get_rarity(n)
    return any(x in r for x in ["LR", "LLR", "SR", "CP"])

def is_target_rare(n):
    r = get_rarity(n)
    return any(x in r for x in ["LR", "LLR"])

# --- 2. データ読み込み ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        valid_cols = [c for c in range(len(df.columns)) if pd.to_numeric(df.iloc[1:, c], errors='coerce').dropna().count() > 3]
        for i in range(0, len(valid_cols) - 1, 2):
            l_idx, r_idx = valid_cols[i], valid_cols[i+1]
            patterns[f"配列 {i//2 + 1}"] = {
                "L": pd.to_numeric(df.iloc[1:, l_idx], errors='coerce').dropna().astype(int).tolist(),
                "R": pd.to_numeric(df.iloc[1:, r_idx], errors='coerce').dropna().astype(int).tolist()
            }
        return patterns
    except: return {}

# --- 3. 探索エンジン ---
def find_matches(history, L, R):
    if not history: return []
    h_len = len(history)
    results = []
    for side in ["L", "R"]:
        main, sub = (L, R) if side == "L" else (R, L)
        for p in range(len(main)):
            if history[0] == main[p]:
                for start_s in range(max(0, p-12), min(len(sub), p+13)):
                    curr_m, curr_s = p + 1, start_s
                    possible = True
                    for i in range(1, h_len):
                        if curr_m < len(main) and history[i] == main[curr_m]:
                            curr_m += 1
                        elif curr_s < len(sub) and history[i] == sub[curr_s]:
                            curr_s += 1
                        else:
                            possible = False
                            break
                    if possible:
                        results.append({"lp": curr_m if side=="L" else curr_s, "rp": curr_s if side=="L" else curr_m, 
                                        "orig_lp": p if side=="L" else start_s, "orig_rp": start_s if side=="L" else p})
    return results

# --- 4. 表生成関数 ---
def render_custom_table(df_data, height=450):
    df_html = df_data.to_html(index=False, escape=False)
    for n in st.session_state.history:
        target = f'<td>{n}</td>'
        replacement = f'<td><span style="color:#ffdd00; font-weight:bold;">{n}</span></td>'
        df_html = df_html.replace(target, replacement)
    
    html_code = f"""
    <div style="height: {height}px; overflow-y: auto; border: 1px solid #555; margin-top: 5px; background: #000; border-radius: 5px;">
        <style>
            table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 15px; table-layout: fixed; color: #fff; }}
            th {{ position: sticky; top: 0; background: #333; z-index: 5; border: 1px solid #555; padding: 10px; text-align: center; color: #00ffcc; }}
            td {{ border: 1px solid #444; padding: 10px; text-align: center; background: #111; pointer-events: none; }}
            td:nth-child(1), th:nth-child(1) {{ width: 45px !important; font-size: 11px; color: #888 !important; }}
        </style>
        {df_html}
    </div>
    """
    st.components.v1.html(html_code, height=height + 10)

# --- 5. UI設定 ---
st.set_page_config(page_title="VR-1弾サーチ", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    h1, h2, h3 { color: #ffffff !important; }
    [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
    .history-box { background: #1a1a1a; color: #ffffff; padding: 12px; border-radius: 8px; font-size: 16px; border: 1px solid #444; border-left: 5px solid #ff4b4b; min-height: 50px; }
    
    /* 入力欄の改善：真っ黒(#000)に強制指定 */
    div[data-testid="stNumberInput"] input {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        caret-color: #000000 !important;
        font-weight: 900 !important;
        font-size: 22px !important;
    }
    
    .half-width-container { width: 50% !important; min-width: 200px; }
    div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }
    .stButton > button { width: 100% !important; height: 3.5rem !important; font-weight: bold !important; font-size: 18px !important; background-color: #333 !important; color: white !important; border: 1px solid #555 !important; }
    .stButton > button:hover { border-color: #ff4b4b !important; color: #ff4b4b !important; }
    .peek-box { border: 2px solid #60b4ff; padding: 10px; border-radius: 10px; text-align: center; background: #111; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("VR-1弾配列サーチ")

if 'history' not in st.session_state: st.session_state.history = []
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

patterns = load_data()

# --- 出たカード (履歴) ---
hist_html = [f'<span style="color:{"#ffff00" if is_rare(n) else "#ffffff"}; font-weight:bold;">{n}</span>' for n in st.session_state.history]
display_text = " > ".join(hist_html) if hist_html else "<span style='color:#666;'>入力待ち...</span>"
st.markdown(f'<div class="history-box">出たカード: {display_text}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 番号入力 ---
st.number_input("番号", min_value=1, max_value=110, value=None, placeholder="ここに番号を入力...", 
                key=f"num_in_{st.session_state.reset_counter}", label_visibility="collapsed")

# --- ボタン列 ---
st.markdown('<div class="half-width-container">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    if st.button("確定", use_container_width=True):
