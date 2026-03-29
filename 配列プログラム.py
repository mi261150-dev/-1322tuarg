import streamlit as st
import pandas as pd

# --- 1. レアリティ定義 ---
def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        rarities = {
            101:"LRパラレル", 100:"SRパラレル", 99:"ランダムLR", 98:"ランダムSR",
            1:"LR", 16:"LR", 18:"LR", 27:"LR", 36:"LR", 48:"LR", 55:"LR", 58:"LR",
            7:"LLR", 26:"LLR", 61:"LLR",
            5:"SR", 20:"SR", 24:"SR", 25:"SR", 31:"SR", 33:"SR", 38:"SR", 40:"SR", 42:"SR", 46:"SR", 52:"SR", 63:"SR"
        }
        if n in rarities: return rarities[n]
        return "CP" if 64 <= n <= 77 else "N"
    except: return ""

def is_rare(n):
    r = get_rarity(n)
    return any(x in r for x in ["LR", "LLR", "SR", "CP"])

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
def find_matches(history, L, R, mode="STRICT"):
    if not history: return []
    h_len = len(history)
    results = []
    def match(a, b):
        if a == b: return True
        if mode == "FLEX":
            sets = {4, 7, 9, 14, 17, 19, 24, 27, 29, 34, 37, 39, 44, 47, 49}
            if a in sets and b in sets: return True
        return False

    for side in ["L", "R"]:
        main, sub = (L, R) if side == "L" else (R, L)
        for p in range(len(main)):
            if match(history[0], main[p]):
                for start_s in range(max(0, p-12), min(len(sub), p+13)):
                    curr_m, curr_s = p + 1, start_s
                    possible = True
                    for i in range(1, h_len):
                        if curr_m < len(main) and match(history[i], main[curr_m]):
                            curr_m += 1
                        elif curr_s < len(sub) and match(history[i], sub[curr_s]):
                            curr_s += 1
                        else:
                            possible = False
                            break
                    if possible:
                        results.append({"lp": curr_m if side=="L" else curr_s, "rp": curr_s
