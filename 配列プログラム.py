import streamlit as st
import pandas as pd

# 1. レアリティ判定
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

# 2. 読み込み（エラー対策版）
@st.cache_data
def load_data():
    try:
        # header=Noneで読み込み
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        for i in range(6):
            name = f"配列{i+1}"
            start_col = i * 4
            if start_col + 2 >= len(df.columns): break
            
            l_raw = df.iloc[1:, start_col + 1]
            r_raw = df.iloc[1:, start_col + 2]
            
            l = pd.to_numeric(l_raw, errors='coerce').dropna().astype(int).tolist()
            r = pd.to_numeric(r_raw, errors='coerce').dropna().astype(int).tolist()
            
            if l or r:
                patterns[name] = {"L": l, "R": r}
        return patterns
    except Exception as e:
        st.error(f"CSV読み込みエラー: {e}")
        return {}

# 3. 判定ロジック（高速化：メモ化を追加）
memo = {}
def solve(h, L, R):
    # 計算済みのパターンは再計算しない（フリーズ対策）
    state = (len(h), len(L), len(R))
    if state in memo: return memo[state]
    
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
    
    ans = res_l if res_l[0] <= res_r[0] else res_r
    memo[state] = ans
    return ans

# --- UI表示 ---
st.set_page_config(page_title="配列ツール", layout="centered")
st.title("📱 配列判別ツール")

if 'history' not in st.session_state: 
    st.session_state.history = []

patterns = load_data()

# 履歴リセット時にメモも空にする
def reset_all():
    st.session_state.history = []
    global memo
    memo = {}

# 入力
with st.form("input_form", clear_on_submit=True):
    num = st.number_input("カード番号を入力", min_value=1, max_value=110, step=1)
    submitted = st.form_submit_button("追加")
    if submitted:
        st.session_state.history.append(num)

if st.button("履歴を消去"):
    reset_all()
    st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

# 解析実行
if st.session_state.history and patterns:
    memo = {} # 実行のたびにメモをクリア
    results = []
    
    # 探索範囲を絞って計算負荷を下げる
    with st.spinner('解析中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            # スキャン範囲を直近60枚に制限して高速化
            for ls in range(max(0, len(L_f)-60)):
                for rs in range(max(0, len(R_f)-60)):
                    err, lu, ru = solve(tuple(st.session_state.history), tuple(L_f[ls:]), tuple(R_f[rs:]))
                    if err <= len(st.session_state.history) * 0.4:
                        results.append({
                            "name": name, "err": err, "lp": ls+lu, "rp": rs+ru, 
                            "nl": L_f[ls+lu] if ls+lu < len(L_f) else None,
                            "nr": R_f[rs+ru] if rs+ru < len(R_f) else None
                        })

    sorted_res = sorted(results, key=lambda x: x['err'])[:3]
    
    if sorted_res:
        for m in sorted_res:
            with st.expander(f"{m['name']} (誤差:{m['err']})", expanded=True):
                st.write(f"📍 左:{m['lp']}枚目 / 右:{m['rp']}枚目")
                st.info(f"**次予測**\n\n左: {m['nl']} ({get_rarity(m['nl'])})\n\n右: {m['nr']} ({get_rarity(m['nr'])})")
    else:
        st.error("一致なし。番号を確認してください。")
