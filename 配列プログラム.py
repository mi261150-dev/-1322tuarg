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
    h_len = len(history)
    results = []
    
    def match(a, b):
        if a == b: return True
        if mode == "FLEX":
            # 4, 7, 9 系の読み替え救済
            sets = {4, 7, 9, 14, 17, 19, 24, 27, 29, 34, 37, 39, 44, 47, 49}
            if a in sets and b in sets: return True
        return False

    # 全位置スキャン
    for side in ["L", "R"]:
        main, sub = (L, R) if side == "L" else (R, L)
        for p in range(len(main)):
            if match(history[0], main[p]):
                # 物理制約：隣の列(sub)の検索範囲を決定 (1枚目の前後12枚)
                sub_range = range(max(0, p-12), min(len(sub), p+13))
                
                # 履歴の振り分けシミュレーション
                memo = {}
                def check(h_i, m_p, s_p):
                    state = (h_i, m_p, s_p)
                    if state in memo: return memo[state]
                    if h_i == h_len: return 0, m_p, s_p
                    
                    res = (999, 0, 0)
                    # メイン側一致
                    if m_p < len(main) and match(history[h_i], main[m_p]):
                        e, final_m, final_s = check(h_i+1, m_p+1, s_p)
                        if e < res[0]: res = (e, final_m, final_s)
                    # サブ側一致
                    if s_p < len(sub) and match(history[h_i], sub[s_p]):
                        e, final_m, final_s = check(h_i+1, m_p, s_p+1)
                        if e < res[0]: res = (e, final_m, final_s)
                    
                    memo[state] = res
                    return res

                for start_s in sub_range:
                    err, end_m, end_s = check(1, p+1, start_s)
                    if err == 0:
                        results.append({
                            "lp": end_m if side=="L" else end_s,
                            "rp": end_s if side=="L" else end_m
                        })
    return results

# --- 4. UI ---
st.set_page_config(page_title="3段階配列検索", layout="wide")
st.title("📱 3段階検索プロセス表示")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.sidebar:
    st.header("入力")
    num = st.number_input("カード番号", min_value=1, max_value=110, step=1)
    if st.button("追加"): st.session_state.history.append(num); st.rerun()
    if st.button("リセット"): st.session_state.history = []; st.rerun()
    st.write(f"履歴: {st.session_state.history}")

if st.session_state.history and patterns:
    h = st.session_state.history
    has_rare = any(is_rare(n) for n in h)
    
    col1, col2, col3 = st.columns(3)

    # --- 方法１：レアカード優先検索 ---
    with col1:
        st.header("1. レア優先")
        if has_rare and len(h) >= 2:
            hits1 = []
            for name, data in patterns.items():
                for hit in find_matches(h, data["L"], data["R"], mode="STRICT"):
                    hits1.append({**hit, "name": name})
            if hits1:
                res = hits1[0]
                st.success(f"発見: {res['name']}")
                st.write(f"左次: **{patterns[res['name']]['L'][res['lp']]}**")
                st.write(f"右次: **{patterns[res['name']]['R'][res['rp']]}**")
            else: st.info("一致なし")
        else: st.warning("レアなし/2枚未満")

    # --- 方法２：Nカード3枚以上検索 ---
    with col2:
        st.header("2. N 3枚以上")
        if not has_rare and len(h) >= 3:
            hits2 = []
            for name, data in patterns.items():
                for hit in find_matches(h, data["L"], data["R"], mode="STRICT"):
                    hits2.append({**hit, "name": name})
            if hits2:
                res = hits2[0]
                st.success(f"発見: {res['name']}")
                st.write(f"左次: **{patterns[res['name']]['L'][res['lp']]}**")
                st.write(f"右次: **{patterns[res['name']]['R'][res['rp']]}**")
            else: st.info("一致なし")
        elif has_rare: st.write("方法1を優先")
        else: st.warning("3枚未満")

    # --- 方法３：読み替え救済検索 ---
    with col3:
        st.header("3. 読み替え(4,7,9)")
        hits3 = []
        for name, data in patterns.items():
            for hit in find_matches(h, data["L"], data["R"], mode="FLEX"):
                hits3.append({**hit, "name": name})
        if hits3:
            res = hits3[0]
            st.error(f"救済発見: {res['name']}")
            st.write(f"左次: **{patterns[res['name']]['L'][res['lp']]}**")
            st.write(f"右次: **{patterns[res['name']]['R'][res['rp']]}**")
        else: st.info("救済でも一致なし")
