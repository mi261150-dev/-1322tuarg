import streamlit as st
import pandas as pd

# --- 1. レアリティ判定とLR検索 ---
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
        if 5 <= n <= 63: return "SR" # SRの範囲
        if 64 <= n <= 77: return "CP"
        return "N"
    except: return ""

def is_rare(n):
    """LR系（当たり）かどうかを判定"""
    r = get_rarity(n)
    return "LR" in r or "LLR" in r

# --- 2. 読み込み (2列1ペアを厳守) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        valid_cols = []
        for c in range(len(df.columns)):
            # 数値が一定数以上ある列をデータ列とみなす
            if pd.to_numeric(df.iloc[1:, c], errors='coerce').dropna().count() > 2:
                valid_cols.append(c)
        
        # 2列ペアで独立させて保存
        for i in range(0, len(valid_cols) - 1, 2):
            l_idx, r_idx = valid_cols[i], valid_cols[i+1]
            l_list = pd.to_numeric(df.iloc[1:, l_idx], errors='coerce').dropna().astype(int).tolist()
            r_list = pd.to_numeric(df.iloc[1:, r_idx], errors='coerce').dropna().astype(int).tolist()
            patterns[f"配列{(i//2)+1}"] = {"L": l_list, "R": r_list}
        return patterns
    except: return {}

# --- 3. 判定ロジック (メモ化) ---
memo = {}
def solve(h, L, R):
    state = (len(h), len(L), len(R))
    if state in memo: return memo[state]
    if not h: return 0, 0, 0
    
    def get_score(inp, tbl):
        if inp == tbl: return 0
        if tbl in {4, 7, 9} and inp in {4, 7, 9}: return 0.2
        return 0.8 

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

# --- 4. UI設定 ---
st.set_page_config(page_title="高精度・LRサーチ", layout="centered")
st.title("📱 配列判別 & LRサーチ")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

# サイドバーで読み込み状況確認
with st.sidebar:
    st.write("### 📊 データ確認")
    if patterns:
        for k, v in patterns.items():
            st.write(f"{k}: L{len(v['L'])}枚 / R{len(v['R'])}枚")
    else:
        st.error("CSV読み込み失敗")

with st.form("in_form", clear_on_submit=True):
    num = st.number_input("カード番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"):
        st.session_state.history.append(num)

if st.button("履歴を消去"):
    st.session_state.history = []
    st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

# --- 5. 解析とカウントダウン表示 ---
if st.session_state.history and patterns:
    memo = {}
    results = []
    h_tuple = tuple(st.session_state.history)
    h_len = len(h_tuple)
    
    for name, data in patterns.items():
        L_f, R_f = data["L"], data["R"]
        # その「配列名」の中だけでスキャン（配列跨ぎなし）
        for ls in range(len(L_f)):
            for rs in range(max(0, ls-10), min(len(R_f), ls+11)):
                err, lu, ru = solve(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                if err < h_len * 0.4:
                    results.append({"name":name, "err":err, "lp":ls+lu, "rp":rs+ru, "data":data})

    if results:
        # スコアが良いものを1つ選ぶ
        best = sorted(results, key=lambda x: (x['err'], abs(x['lp']-x['rp'])))[0]
        
        st.subheader(f"🔍 解析結果: {best['name']}")
        
        # 次の予測
        nl = best['data']['L'][best['lp']] if best['lp'] < len(best['data']['L']) else None
        nr = best['data']['R'][best['rp']] if best['rp'] < len(best['data']['R']) else None
        
        c1, c2 = st.columns(2)
        c1.success(f"**左 次予測**\n\n{nl} ({get_rarity(nl)})")
        c2.info(f"**右 次予測**\n\n{nr} ({get_rarity(nr)})")

        # --- LRカウントダウン ---
        st.divider()
        st.subheader("🏆 レアカードまでの残り枚数")
        
        def find_next_rare(lst, current_pos):
            for i in range(current_pos, len(lst)):
                if is_rare(lst[i]):
                    return i - current_pos, lst[i]
            return None, None

        dist_l, val_l = find_next_rare(best['data']['L'], best['lp'])
        dist_r, val_r = find_next_rare(best['data']['R'], best['rp'])

        col_l, col_r = st.columns(2)
        with col_l:
            if dist_l is not None:
                st.metric("左のLRまで", f"{dist_l} 枚")
                st.caption(f"内容: {val_l} ({get_rarity(val_l)})")
            else: st.write("左にLRなし")
        with col_r:
            if dist_r is not None:
                st.metric("右のLRまで", f"{dist_r} 枚")
                st.caption(f"内容: {val_r} ({get_rarity(val_r)})")
            else: st.write("右にLRなし")
    else:
        st.error("一致なし。")
