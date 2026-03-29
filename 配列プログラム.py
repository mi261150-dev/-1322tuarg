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
    num = st.number_input("カード番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"):
        st.session_state.history.append(num)

c1, c2 = st.columns(2)
with c1:
    if st.button("最後を1枚削除"):
        if st.session_state.history: st.session_state.history.pop(); st.rerun()
with c2:
    if st.button("履歴を全リセット"):
        st.session_state.history = []; st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

# --- 5. 解析実行 ---
if st.session_state.history and len(all_cols) >= 2:
    memo = {}
    results = []
    h_tuple = tuple(st.session_state.history)
    h_len = len(h_tuple)
    
    with st.spinner('解析中...'):
        # 隣り合う2列をペア(1-2列目, 3-4列目...)としてスキャン
        for i in range(0, len(all_cols) - 1, 2):
            L_f, R_f = all_cols[i], all_cols[i+1]
            pair_name = f"配列ペア {i//2 + 1}"
            
            for ls in range(len(L_f)):
                # 左右差10枚の物理制約
                for rs in range(max(0, ls-10), min(len(R_f), ls+11)):
                    err, lu, ru = solve(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                    if err < h_len * 0.4:
                        results.append({
                            "name": pair_name, "err": err, "lp": ls+lu, "rp": rs+ru, "L_data": L_f, "R_data": R_f
                        })

    if results:
        best = sorted(results, key=lambda x: (x['err'], abs(x['lp']-x['rp'])))[0]
        trust = max(0, int(100 - (best['err'] / h_len * 200)))
        
        st.subheader(f"🔍 解析結果: {best['name']} (信頼度: {trust}%)")
        
        nl = best['L_data'][best['lp']] if best['lp'] < len(best['L_data']) else None
        nr = best['R_data'][best['rp']] if best['rp'] < len(best['R_data']) else None
        
        col1, col2 = st.columns(2)
        col1.success(f"**左 次予測**\n\n{nl} ({get_rarity(nl)})")
        col2.info(f"**右 次予測**\n\n{nr} ({get_rarity(nr)})")

        # LRカウントダウン
        st.divider()
        st.subheader("🏆 LRまでの残り枚数")
        def find_next(lst, p):
            for i in range(p, len(lst)):
                if is_rare(lst[i]): return i - p, lst[i]
            return None, None

        dl, vl = find_next(best['L_data'], best['lp'])
        dr, vr = find_next(best['R_data'], best['rp'])

        cl, cr = st.columns(2)
        with cl:
            if dl is not None: st.metric("左のLRまで", f"{dl}枚"); st.caption(f"{vl}({get_rarity(vl)})")
            else: st.write("左にLRなし")
        with cr:
            if dr is not None: st.metric("右のLRまで", f"{dr}枚"); st.caption(f"{vr}({get_rarity(vr)})")
            else: st.write("右にLRなし")
    else:
        st.error("一致なし。")
