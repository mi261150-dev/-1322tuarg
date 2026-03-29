import streamlit as st
import pandas as pd

# --- 1. レアリティ判定（個別に正確な番号を登録） ---
def get_rarity(n):
    if n is None or n == "なし": return ""
    try:
        n = int(n)
        # 固有のレアリティ（LR / LLR / SR）
        rarities = {
            101:"LRパラレル", 100:"SRパラレル", 99:"ランダムLR", 98:"ランダムSR",
            1:"LR", 16:"LR", 18:"LR", 27:"LR", 36:"LR", 48:"LR", 55:"LR", 58:"LR",
            7:"LLR", 26:"LLR", 61:"LLR",
            # SR
            5:"SR", 20:"SR", 24:"SR", 25:"SR", 31:"SR", 33:"SR", 38:"SR", 40:"SR", 42:"SR", 46:"SR", 52:"SR", 63:"SR"
        }
        if n in rarities: return rarities[n]
        # CP
        if 64 <= n <= 77: return "CP"
        # それ以外はすべて N
        return "N"
    except: return ""

def is_rare_tag(n):
    r = get_rarity(n)
    return any(x in r for x in ["LR", "LLR", "CP", "SR"])

# --- 2. データ読み込み ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        valid_cols = []
        for c in range(len(df.columns)):
            col_data = pd.to_numeric(df.iloc[1:, c], errors='coerce').dropna()
            if len(col_data) > 3:
                valid_cols.append(col_data.astype(int).tolist())
        for i in range(0, len(valid_cols) - 1, 2):
            patterns[f"配列 {i//2 + 1}"] = {"L": valid_cols[i], "R": valid_cols[i+1]}
        return patterns
    except: return {}

# --- 3. 判定ロジック（スコア制） ---
def solve_with_details(h, L, R):
    memo = {}
    def solve_internal(hh, ll, rr):
        state = (len(hh), len(ll), len(rr))
        if state in memo: return memo[state]
        if not hh: return 0, 0, 0
        
        # 左から出たと仮定
        res_l = (999, 0, 0)
        if ll:
            score = 0 if hh[0] == ll[0] else (0.1 if hh[0] in {4,7,9} and ll[0] in {4,7,9} else 0.8)
            e, lu, ru = solve_internal(hh[1:], ll[1:], rr)
            res_l = (score + e, lu + 1, ru)
        
        # 右から出たと仮定
        res_r = (999, 0, 0)
        if rr:
            score = 0 if hh[0] == rr[0] else (0.1 if hh[0] in {4,7,9} and rr[0] in {4,7,9} else 0.8)
            e, lu, ru = solve_internal(hh[1:], ll, rr[1:])
            res_r = (score + e, lu, ru + 1)
        
        ans = res_l if res_l[0] <= res_r[0] else res_r
        memo[state] = ans
        return ans
    return solve_internal(h, L, R)

# --- 4. UI ---
st.set_page_config(page_title="最強配列判別", layout="centered")
st.title("🎯 次に出るカード番号を予測")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_
