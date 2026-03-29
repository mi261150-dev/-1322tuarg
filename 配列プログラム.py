import streamlit as st
import pandas as pd

# --- 1. レアリティ判定 ---
def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        rarities = {
            101:"LRパラレル", 100:"SRパラレル", 99:"ランダムLR", 98:"ランダムSR",
            7:"LLR", 26:"LLR", 61:"LLR",
            1:"LR", 16:"LR", 18:"LR", 27:"LR", 36:"LR", 48:"LR", 55:"LR", 58:"LR"
        }
        if n in rarities: return rarities[n]
        if 5 <= n <= 63: return "SR"
        if 64 <= n <= 77: return "CP"
        return "N"
    except: return ""

def is_rare(n):
    r = get_rarity(n)
    return "LR" in r or "LLR" in r

# --- 2. 読み込み (すべての数値列を個別に取得) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        all_cols = []
        # 全列をスキャンして、数字が入っている列をすべて抽出
        for c in range(len(df.columns)):
            col_data = pd.to_numeric(df.iloc[1:, c], errors='coerce').dropna().astype(int).tolist()
            if len(col_data) > 5: # 5枚以上データがある列を有効とする
                all_cols.append(col_data)
        return all_cols
    except:
        return []

# --- 3. 判定ロジック (高精度・誤記許容) ---
memo = {}
def solve_single(h, col_data):
    """単一の列(シリンダー)に対して履歴がどこに一致するか探す"""
    h_len = len(h)
    best_err = 999
    best_pos = -1
    
    # 列の全位置をスキャン
    for start_pos in range(len(col_data) - h_len + 1):
        current_err = 0
        for i in range(h_len):
            inp = h[i]
            tbl = col_data[start_pos + i]
            if inp == tbl:
                continue
            # 4, 7, 9 の誤記は 0.1点、それ以外は 0.8点のペナルティ
            elif tbl in {4, 7, 9} and inp in {4, 7, 9}:
                current_err += 0.1
            else:
                current_err += 0.8
        
        if current_err < best_err:
            best_err = current_err
            best_pos = start_pos + h_len
            
    return best_err, best_pos

# --- 4. UI ---
st.set_page_config(page_title="全列対応配列判別", layout="centered")
st.title("📱 配列判別 (全列スキャン版)")

if 'history' not in st.session_state: st.session_state.history = []
all_cols = load_data()

with st.form("in_form", clear_on_submit=True):
    num = st.number_input("カード番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"):
        st.session_state.history.append(num)

c1, c2 = st.columns(2)
with c1:
    if st.button("最後を1枚削除"):
        if st.session_state.history: st.session_state.history.pop()
        st.rerun()
with c2:
    if st.button("履歴を全リセット"):
        st.session_state.history = []
        st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

# --- 5. 解析実行 ---
if st.session_state.history and all_cols:
    results = []
    h_tuple = tuple(st.session_state.history)
    
    with st.spinner('すべての列を解析中...'):
        for i, col in enumerate(all_cols):
            err, pos = solve_single(h_tuple, col)
            # 履歴の枚数に対してエラー
