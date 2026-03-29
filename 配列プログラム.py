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

# 2. 読み込み
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        for i in range(6):
            name = f"配列{i+1}"
            col_l_idx = i * 4 + 1
            col_r_idx = i * 4 + 2
            if col_r_idx >= len(df.columns): break
            
            l = pd.to_numeric(df.iloc[1:, col_l_idx], errors='coerce').dropna().astype(int).tolist()
            r = pd.to_numeric(df.iloc[1:, col_r_idx], errors='coerce').dropna().astype(int).tolist()
            
            if l or r:
                patterns[name] = {"L": l, "R": r}
        return patterns
    except Exception as e:
        st.error(f"読み込みエラー: {e}")
        return {}

# 3. 判定ロジック（配列表側の4,7,9誤記を考慮）
memo = {}
def solve(h, L, R):
    state = (len(h), len(L), len(R))
    if state in memo: return memo[state]
    if not h: return 0, 0, 0
    
    # 比較用スコア計算
    def get_score(input_val, table_val):
        if input_val == table_val: return 0
        # 配列表側(table_val)が4,7,9の場合、打ち間違いの可能性として0.5点（軽いペナルティ）
        typos = {4, 7, 9}
        if table_val in typos and input_val in typos:
            return 0.5
        return 1.0

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

# --- UI ---
st.set_page_config(page_title="高精度配列ツール", layout="centered")
st.title("📱 配列判別ツール (データ誤記対応版)")

if 'history' not in st.session_state: 
    st.session_state.history = []

patterns = load_data()

with st.form("input_form", clear_on_submit=True):
    num = st.number_input("引いたカードの番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"):
        st.session_state.history.append(num)

if st.button("履歴リセット"):
    st.session_state.history = []
    st.rerun()

st.write(f"**確定履歴:** {st.session_state.history}")

if st.session_state.history and patterns:
    memo = {}
    results = []
    with st.spinner('全配列を詳細スキャン中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            # 探索密度を上げるため、全範囲をスキャン
            for ls in range(len(L_f)):
                for rs in range(len(R_f)):
                    # 1枚目が完全に一致、または4,7,9の許容範囲内なら計算開始
                    h0 = st.session_state.history[0]
                    l_match = L_f[ls] == h0 or (h0 in {4,7,9} and L_f[ls] in {4,7,9}) if L_f[ls:] else False
                    r_match = R_f[rs] == h0 or (h0 in {4,7,9} and R_f[rs] in {4,7,9}) if R_f[rs:] else False
                    
                    if l_match or r_match:
                        err, lu, ru = solve(tuple(st.session_state.history), tuple(L_f[ls:]), tuple(R_f[rs:]))
                        # 許容誤差を少し厳しめに（データ誤記を考慮しつつ絞り込む）
                        if err <= len(st.session_state.history) * 0.35:
                            results.append({
                                "name": name, "err": err, "lp": ls+lu, "rp": rs+ru, 
                                "nl": L_f[ls+lu] if ls+lu < len(L_f) else None,
                                "nr": R_f[rs+ru] if rs+ru < len(R_f) else None
                            })

    # 重複を排除してスコア順に表示
    unique_res = sorted(results, key=lambda x: x['err'])[:3]
    
    if unique_res:
        st.subheader("🔍 推定される現在地")
        for m in unique_res:
            with st.expander(f"{m['name']} (信頼度スコア: {max(0, 100-int(m['err']*20))}%)", expanded=True):
                c1, c2 = st.columns(2)
                c1.metric("左筒(L)", f"{m['lp']}枚目")
                c2.metric("右筒(R)", f"{m['rp']}枚目")
                st.info(f"**次に出る可能性が高いカード**\n\n左: {m['nl']} ({get_rarity(m['nl'])})\n\n右: {m['nr']} ({get_rarity(m['nr'])})")
    else:
        st.error("一致する配列が見つかりません。履歴が短いか、配列表に致命的な誤りがある可能性があります。")
