import streamlit as st
import pandas as pd

# --- 1. レアリティ設定 ---
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

def is_not_normal(n):
    return get_rarity(n) not in ["N", ""]

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

# --- 3. 判定ロジック (振り分け枚数を特定) ---
def solve_with_counts(h, L, R):
    """履歴がLから何枚、Rから何枚出たかを正確に算出"""
    memo = {}
    def solve_internal(hh, ll, rr):
        state = (len(hh), len(ll), len(rr))
        if state in memo: return memo[state]
        if not hh: return 0, 0, 0 # error, l_used, r_used
        
        res_l = (999, 0, 0)
        if ll:
            score = 0 if hh[0] == ll[0] else (0.2 if hh[0] in {4,7,9} and ll[0] in {4,7,9} else 0.8)
            e, lu, ru = solve_internal(hh[1:], ll[1:], rr)
            res_l = (score + e, lu + 1, ru)
        
        res_r = (999, 0, 0)
        if rr:
            score = 0 if hh[0] == rr[0] else (0.2 if hh[0] in {4,7,9} and rr[0] in {4,7,9} else 0.8)
            e, lu, ru = solve_internal(hh[1:], ll, rr[1:])
            res_r = (score + e, lu, ru + 1)
        
        ans = res_l if res_l[0] <= res_r[0] else res_r
        memo[state] = ans
        return ans
    return solve_internal(h, L, R)

# --- 4. UI部 ---
st.set_page_config(page_title="次予測修正版", layout="centered")
st.title("📱 配列判別 (次予測修正版)")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.form("in_form", clear_on_submit=True):
    num = st.number_input("カード番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"):
        st.session_state.history.append(num)

if st.button("リセット"):
    st.session_state.history = []; st.rerun()

st.write(f"**現在の履歴:** {st.session_state.history}")

if st.session_state.history and patterns:
    all_hits = []
    h_tuple = tuple(st.session_state.history)
    
    # N以外があるかチェック
    rare_found = any(is_not_normal(n) for n in h_tuple)
    
    with st.spinner('解析中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            
            # 全スキャン開始
            for ls in range(len(L_f)):
                # 左右±15枚の制約
                for rs in range(max(0, ls-15), min(len(R_f), ls+16)):
                    # 戦略：1枚目がLかRの開始位置に合致するか、レアカードが含まれる場合のみ詳細計算
                    if rare_found or L_f[ls] == h_tuple[0] or R_f[rs] == h_tuple[0]:
                        err, lu, ru = solve_with_counts(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                        
                        if err < len(h_tuple) * 0.4:
                            all_hits.append({
                                "name": name, "err": err, 
                                "next_l_pos": ls + lu, "next_r_pos": rs + ru,
                                "data": data
                            })

    if all_hits:
        # 最もエラーが少ないものを採用
        best = sorted(all_hits, key=lambda x: x['err'])[0]
        
        st.subheader(f"🔍 判定結果: {best['name']}")
        
        # 次のカード（進んだ後の位置を参照）
        nl = best['data']['L'][best['next_l_pos']] if best['next_l_pos'] < len(best['data']['L']) else "終了"
        nr = best['data']['R'][best['next_r_pos']] if best['next_r_pos'] < len(best['data']['R']) else "終了"
        
        c1, c2 = st.columns(2)
        c1.success(f"**左 次予測**\n\n{nl} ({get_rarity(nl)})")
        c2.info(f"**右 次予測**\n\n{nr} ({get_rarity(nr)})")
        
        # LRカウントダウン
        st.divider()
        def find_rare(lst, start):
            for i in range(start, len(lst)):
                if get_rarity(lst[i]) in ["LR", "LLR", "LRパラレル"]:
                    return i - start, lst[i]
            return None, None

        dl, vl = find_rare(best['data']['L'], best['next_l_pos'])
        dr, vr = find_rare(best['data']['R'], best['next_r_pos'])
        
        cl, cr = st.columns(2)
        with cl:
            if dl is not None: st.metric("左LRまで", f"{dl}枚"); st.caption(f"{vl}")
            else: st.write("左にLRなし")
        with cr:
            if dr is not None: st.metric("右LRまで", f"{dr}枚"); st.caption(f"{vr}")
            else: st.write("右にLRなし")
    else:
        st.error("一致なし。")
