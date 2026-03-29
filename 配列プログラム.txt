

import streamlit as st
import pandas as pd

# レアリティ判定
def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        if n == 101: return "LRパラレル"
        if n == 100: return "SRパラレル"
        if n == 99:  return "ランダムLR"
        if n == 98:  return "ランダムSR"
        if n in [7, 26, 61]: return "LLR"
        if n in [1, 16, 18, 27, 36, 48, 55, 58]: return "LR"
        if n in [5, 20, 24, 25, 31, 33, 38, 40, 42, 46, 52, 63]: return "SR"
        if 64 <= n <= 77: return "CP"
        return "N"
    except: return "不明"

# 読み込み
@st.cache_data
def load_data():
    # ファイル名はGitHubに上げる名前と一致させる
    df = pd.read_csv("配列.csv") 
    patterns = {}
    for i in range(6):
        name = f"配列{i+1}"
        # 1列目タイトル、2列目左、3列目右を想定
        l = df.iloc[:, i*3 + 1].dropna().astype(int).tolist()
        r = df.iloc[:, i*3 + 2].dropna().astype(int).tolist()
        patterns[name] = {"L": l, "R": r}
    return patterns

# 判定ロジック（簡易・高速版）
def solve(h, L, R):
    if not h: return 0, 0, 0
    res_l = (999, 0, 0)
    if L:
        e, lu, ru = solve(h[1:], L[1:], R)
        score = (0 if h[0]==L[0] else (0.5 if h[0] in [4,7,9] and L[0] in [4,7,9] else 1))
        res_l = (score + e, lu + 1, ru)
    res_r = (999, 0, 0)
    if R:
        e, lu, ru = solve(h[1:], L, R[1:])
        score = (0 if h[0]==R[0] else (0.5 if h[0] in [4,7,9] and R[0] in [4,7,9] else 1))
        res_r = (score + e, lu, ru + 1)
    return res_l if res_l[0] <= res_r[0] else res_r

st.title("📱 配列判別ツール")
if 'history' not in st.session_state: st.session_state.history = []

patterns = load_data()
num = st.number_input("カード番号", min_value=1, max_value=110, step=1)
if st.button("追加"): st.session_state.history.append(num)
if st.button("リセット"): 
    st.session_state.history = []
    st.rerun()

st.write(f"履歴: {st.session_state.history}")

if st.session_state.history:
    results = []
    for name, data in patterns.items():
        L_f, R_f = data["L"], data["R"]
        for ls in range(max(0, len(L_f)-40)):
            for rs in range(max(0, len(R_f)-40)):
                err, lu, ru = solve(st.session_state.history, L_f[ls:], R_f[rs:])
                if err <= len(st.session_state.history) * 0.4:
                    results.append({"name":name, "err":err, "lp":ls+lu, "rp":rs+ru, 
                                    "nl":L_f[ls+lu] if ls+lu<len(L_f) else None,
                                    "nr":R_f[rs+ru] if rs+ru<len(R_f) else None})
    
    for m in sorted(results, key=lambda x: x['err'])[:2]:
        st.success(f"{m['name']} (誤差:{m['err']})")
        st.write(f"次 ➔ 左:{m['nl']}({get_rarity(m['nl'])}) / 右:{m['nr']}({get_rarity(m['nr'])})")