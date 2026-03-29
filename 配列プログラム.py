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

# --- 2. 読み込み (数字が入っている列をすべて取得) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        all_cols = []
        for c in range(len(df.columns)):
            col_data = pd.to_numeric(df.iloc[1:, c], errors='coerce').dropna().astype(int).tolist()
            if len(col_data) > 5:
                all_cols.append(col_data)
        return all_cols
    except: return []

# --- 3. 判定ロジック (2本の筒から履歴を振り分ける) ---
memo = {}
def solve(h, L, R):
    state = (len(h), len(L), len(R))
    if state in memo: return memo[state]
    if not h: return 0, 0, 0
    
    def get_score(inp, tbl):
        if inp == tbl: return 0
        if tbl in {4, 7, 9} and inp in {4, 7, 9}: return 0.1 # 誤記許容
        return 0.8 # その他誤記

    res_l = (999, 0, 0)
    if L:
        e, lu, ru = solve(h[1:], L[1:], R)
        res_l = (get_score(h[0], L[0]) + e, lu + 1, ru)
    res_r = (999, 0, 0)
    if R:
        e, lu, ru = solve(h[1:], L, R[1:])
        res_r = (get_score(h[0], R[0]) + e, lu, ru + 1)
    
    ans = res_l if res_l[0] <= res_r[0] else res_r
    memo[state] = ans
    return ans

# --- 4. UI ---
st.set_page_config(page_title="高精度配列判別", layout="centered")
st.title("📱 配列判別 (隣接2列スキャン版)")

if 'history' not in st.session_state: st.session_state.history = []
all_cols = load_data()

with st.form("in_form", clear_on_submit=True):
    num = st.number_input("カード番号を入力", min_value=1, max_value=
