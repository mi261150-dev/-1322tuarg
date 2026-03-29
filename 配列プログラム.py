import streamlit as st
import pandas as pd

# 1. レアリティ判定
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

# 2. データ読み込み（1行目に「配列」という文字がある列を自動取得）
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        col_idx = 0
        p_count = 1
        while col_idx < len(df.columns) - 2:
            cell_val = str(df.iloc[0, col_idx])
            if "配列" in cell_val:
                name = f"配列{p_count}"
                l = pd.to_numeric(df.iloc[1:, col_idx+1], errors='coerce').dropna().astype(int).tolist()
                r = pd.to_numeric(df.iloc[1:, col_idx+2], errors='coerce').dropna().astype(int).tolist()
                if l or r:
                    patterns[name] = {"L": l, "R": r}
                p_count += 1
                col_idx += 3
            else:
                col_idx += 1
        return patterns
    except:
        return {}

# 3. 判定ロジック（メモ化）
memo = {}
def solve(h, L, R):
    state = (len(h), len(L), len(R))
    if state in memo: return memo[state]
    if not h: return 0, 0, 0
    
    res_l = (999, 0, 0)
    if L and h[0] == L[0]:
        e, lu, ru = solve(h[1:], L[1:], R)
        res_l = (e, lu + 1, ru)
    
    res_r = (999, 0, 0)
    if R and h[0] == R[0]:
        e, lu, ru = solve(h[1:], L, R[1:])
        res_r = (e, lu, ru + 1)
    
    ans = res_l if res_l[0] <= res_r[0] else res_r
    memo[state] = ans
    return ans

# --- UI設定 ---
st.set_page_config(page_title="配列ツール", layout="centered")
st.title("📱 配列判別ツール")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

# 起動確認
if patterns:
    st.success(f"読み込み完了: {len(patterns)}個の配列")
else:
    st.error("CSVが読めません。『配列』という文字が1行目にありますか？")

# 入力フォーム
with st.form("in_form", clear_on_submit=True):
    num = st.number_input("カード番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"):
        st.session_state.history.append(num)

if st.button("履歴をリセット"):
    st.session_state.history = []
    st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

# 解析実行
if st.session_state.history and patterns:
    memo = {}
    results = []
    h_tuple = tuple(st.session_state.history)
    
    with st.spinner('解析中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            # 物理制約：左右の進み具合の差を10枚以内に限定
            for ls in range(len(L_f)):
                for rs in range(max(0, ls-10), min(len(R_f), ls+11)):
                    # 履歴の1枚目が左右どちらかにあれば解析開始
                    if (L_f[ls:] and L_f[ls] == h_tuple[0]) or (R_f[rs:] and R_f[rs] == h_tuple[0]):
                        err, lu, ru = solve(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                        if err == 0:
                            results.append({
                                "name": name, "lp": ls+lu, "rp": rs+ru,
                                "nl": L_f[ls+lu] if ls+lu < len(L_f) else None,
                                "nr": R_f[rs+ru] if rs+ru < len(R_f) else None
                            })

    if results:
        # 重複カット
        unique_results = []
        seen = set()
        for r in results:
            pos = (r['name'], r['lp'], r['rp'])
            if pos not in seen:
                unique_results.append(r)
                seen.add(pos)

        st.subheader("🔍 解析結果")
        for m in unique_results[:3]:
            with st.expander(f"【{m['name']}】", expanded=True):
                st.write(f"位置: 左筒 {m['lp']}枚目 / 右筒 {m['rp']}枚目")
                c1, c2 = st.columns(2)
                c1.success(f"**左 次予測**\n\n{m['nl']} ({get_rarity(m['nl'])})")
                c2.info(f"**右 次予測**\n\n{m['nr']} ({get_rarity(m['nr'])})")
    else:
        st.error("一致なし。10枚の範囲内に該当する並びがありません。")
        
