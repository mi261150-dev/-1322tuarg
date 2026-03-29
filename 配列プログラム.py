import streamlit as st
import pandas as pd

def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        rarities = {
            101:"LRパラレル", 100:"SRパラレル", 99:"ランダムLR", 98:"ランダムSR",
            7:"LLR", 26:"LLR", 61:"LLR",
            1:"LR", 16:"LR", 18:"LR", 27:"LR", 36:"LR", 48:"LR", 55:"LR", 58:"LR",
            5:"SR", 20:"SR", 24:"SR", 25:"SR", 31:"SR", 33:"SR", 38:"SR", 40:"SR", 42:"SR", 46:"SR", 52:"SR", 63:"SR"
        }
        if n in rarities: return rarities[n]
        if 64 <= n <= 77: return "CP"
        return "N"
    except: return ""

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        for i in range(6):
            name = f"配列{i+1}"
            col_l, col_r = i * 4 + 1, i * 4 + 2
            if col_r >= len(df.columns): break
            l = pd.to_numeric(df.iloc[1:, col_l], errors='coerce').dropna().astype(int).tolist()
            r = pd.to_numeric(df.iloc[1:, col_r], errors='coerce').dropna().astype(int).tolist()
            if l or r: patterns[name] = {"L": l, "R": r}
        return patterns
    except: return {}

memo = {}
def solve(h, L, R):
    state = (len(h), len(L), len(R))
    if state in memo: return memo[state]
    if not h: return 0, 0, 0
    
    res_l = (999, 0, 0)
    if L and h[0] == L[0]:
        e, lu, ru = solve(h[1:], L[1:], R)
        res_l = (e, lu + 1, ru)
    res_r = (999, 0, 0)
    if R and h[0] == R[0]:
        e, lu, ru = solve(h[1:], L, R[1:])
        res_r = (e, lu, ru + 1)
    
    ans = res_l if res_l[0] <= res_r[0] else res_r
    memo[state] = ans
    return ans

st.set_page_config(page_title="高精度配列判別", layout="centered")
st.title("📱 配列判別 (片側進行予測対応)")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.form("in", clear_on_submit=True):
    num = st.number_input("カード番号", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"): st.session_state.history.append(num)

if st.button("リセット"):
    st.session_state.history = []
    st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

if st.session_state.history and patterns:
    memo = {}
    results = []
    h_tuple = tuple(st.session_state.history)
    
    with st.spinner('スキャン中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            # 全範囲スキャン
            for ls in range(len(L_f)):
