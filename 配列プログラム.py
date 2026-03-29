import streamlit as st
import pandas as pd

# 1. レアリティ判定
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

# 2. データ読み込み（1行目に「配列」という文字がある列を自動取得）
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        col_idx = 0
        p_count = 1
        while col_idx < len(df.columns) - 2:
            cell_val = str(df.iloc[0, col_idx])
            if "配列" in cell_val:
                name = f"配列{p_count}"
                l = pd.to_numeric(df.iloc[1:, col_idx+1], errors='coerce').dropna().astype(int).tolist()
                r = pd.to_numeric(df.iloc[1:, col_idx+2], errors='coerce').dropna().astype(int).tolist()
                if l or r:
                    patterns[name] = {"L": l, "R": r}
                p_count += 1
                col_idx += 3
            else:
                col_idx += 1
        return patterns
    except:
        return {}

# 3. 判定ロジック（メモ化）
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

# --- UI設定 ---
st.set_page_config(page_title="配列ツール", layout="centered")
st.title("📱 配列判別ツール")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

# 起動確認
if patterns:
    st.success(f"読み込み完了: {len(patterns)}個の配列")
else:
    st.error("CSVが読めません。『配列』という文字が1行目にありますか？")

# 入力フォーム
with st.form("in_form", clear_on_submit=True):
    num = st.number_input("カード番号を入力", min_value
