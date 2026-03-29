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

# --- 読み込み処理を最も堅実な方法に修正 ---
@st.cache_data
def load_data():
    try:
        # header=None で全てのデータを読み込む
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        
        # 1列ずつ中身を確認
        valid_columns = []
        for col in range(len(df.columns)):
            # その列に「2つ以上の数値」が含まれているか確認（タイトル行などを除外するため）
            col_data = pd.to_numeric(df.iloc[:, col], errors='coerce').dropna()
            if len(col_data) > 2:
                valid_columns.append(col)
        
        # 見つかった「数値が入っている列」を2つずつペアにする
        for i in range(0, len(valid_columns) - 1, 2):
            p_idx = (i // 2) + 1
            l_col = valid_columns[i]
            r_col = valid_columns[i+1]
            
            l_list = pd.to_numeric(df.iloc[:, l_col], errors='coerce').dropna().astype(int).tolist()
            r_list = pd.to_numeric(df.iloc[:, r_col], errors='coerce').dropna().astype(int).tolist()
            
            patterns[f"配列{p_idx}"] = {"L": l_list, "R": r_list}
            
        return patterns
    except:
        return {}

# 判定ロジック（データ誤記補正）
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

st.set_page_config(page_title="最強精度配列判別", layout="centered")
st.title("📱 配列判別 (読み込み安定版)")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

# 現在読み込めているデータのプレビューを表示（デバッグ用）
if patterns:
    with st.expander("📊 読み込みデータ確認 (ここが正しくないと判別できません)"):
        for name, data in patterns.items():
            st.write(f"**{name}**: 左{len(data['L'])}枚 / 右{len(data['R'])}枚 読み込み中")
else:
    st.error("CSVデータの数値が読み込めません。")

with st.form("in_form", clear_on_submit=True):
    num = st.number_input("カード番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"):
        st.session_state.history.append(num)

if st.button("リセット"):
    st.session_state.history = []
    st.rerun()

st.write(f"**現在の履歴:** {st.session_state.history}")

if st.session_state.history and patterns:
    memo = {}
    results = []
    h_tuple = tuple(st.session_state.history)
    h_len = len(h_tuple)
    
    with st.spinner('解析中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            for ls in range(len(L_f)):
                for rs in range(max(0, ls-10), min(len(R_f), ls+11)):
                    err, lu, ru = solve(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                    if err < h_len * 0.4:
                        results.append({"name":name, "err":err, "lp":ls+lu, "rp":rs+ru,
                                        "nl":L_f[ls+lu] if ls+lu<len(L_f) else None,
                                        "nr":R_f[rs+ru] if rs+ru<len(R_f) else None})

    if results:
        unique_results = []
        seen = set()
        sorted_res = sorted(results, key=lambda x: (x['err'], abs(x['lp']-x['rp'])))
        for r in sorted_res:
            pos = (r['name'], r['lp'], r['rp'])
            if pos not in seen:
                unique_results.append(r); seen.add(pos)

        st.subheader("🔍 解析結果")
        for m in unique_results[:3]:
            trust = max(0, int(100 - (m['err'] / h_len * 150)))
            with st.expander(f"【{m['name']}】 信頼度: {trust}%", expanded=(trust > 50)):
                st.write(f"位置: 左{m['lp']} / 右{m['rp']}")
                c1, c2 = st.columns(2)
                c1.success(f"**左 次予測**\n\n{m['nl']} ({get_rarity(m['nl'])})")
                c2.info(f"**右 次予測**\n\n{m['nr']} ({get_rarity(m['nr'])})")
    else:
        st.error("一致なし。")
