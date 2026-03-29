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
            col_l = i * 4 + 1
            col_r = i * 4 + 2
            if col_r >= len(df.columns): break
            l = pd.to_numeric(df.iloc[1:, col_l], errors='coerce').dropna().astype(int).tolist()
            r = pd.to_numeric(df.iloc[1:, col_r], errors='coerce').dropna().astype(int).tolist()
            if l or r: patterns[name] = {"L": l, "R": r}
        return patterns
    except: return {}

# メモ化による高速化
memo = {}
def solve(h, L, R):
    state = (len(h), len(L), len(R))
    if state in memo: return memo[state]
    if not h: return 0, 0, 0
    
    # 配列表に間違いがない前提：不一致は即座に大きなペナルティ
    def get_score(inp, tbl):
        return 0 if inp == tbl else 99  # 完全一致以外は実質除外

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

st.set_page_config(page_title="厳密配列判別", layout="centered")
st.title("📱 配列判別 (前後10枚制約版)")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.form("in", clear_on_submit=True):
    num = st.number_input("カード番号", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"): st.session_state.history.append(num)

if st.button("リセット"):
    st.session_state.history = []
    st.rerun()

st.write(f"**現在の履歴:** {st.session_state.history}")

if st.session_state.history and patterns:
    memo = {}
    results = []
    h_tuple = tuple(st.session_state.history)
    
    with st.spinner('解析中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            len_l, len_r = len(L_f), len(R_f)
            
            # 左右の開始位置をスキャン
            for ls in range(len_l):
                # 右筒の開始位置を「左筒の開始位置 ± 10枚」に限定
                rs_start = max(0, ls - 10)
                rs_end = min(len_r, ls + 11)
                
                for rs in range(rs_start, rs_end):
                    # 最初の1枚が左右どちらかに存在するかチェック（高速化）
                    if (L_f[ls:] and L_f[ls] == h_tuple[0]) or (R_f[rs:] and R_f[rs] == h_tuple[0]):
                        err, lu, ru = solve(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                        # エラーが0（完全一致）のものだけを優先的に拾う
                        if err < 1:
                            results.append({
                                "name": name, "err": err, "lp": ls+lu, "rp": rs+ru,
                                "nl": L_f[ls+lu] if ls+lu < len_l else None,
                                "nr": R_f[rs+ru] if rs+ru < len_r else None
                            })

    if results:
        st.subheader("🔍 確定した現在地")
        # 念のためエラーが少ない順に表示
        for m in sorted(results, key=lambda x: x['err'])[:3]:
            with st.expander(f"{m['name']}", expanded=True):
                st.write(f"📍 位置: 左 {m['lp']}枚目 / 右 {m['rp']}枚目")
                st.info(f"**次予測**\n\n左 ➔ {m['nl']} ({get_rarity(m['nl'])})\n\n右 ➔ {m['nr']} ({get_rarity(m['nr'])})")
    else:
        st.error("一致する配列が範囲内にありません。履歴が間違っているか、左右の差が10枚を超えている可能性があります。")
