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
        
        # CSVの列をスキャンして「左」「右」のペアを自動で見つける
        # 1行目に「配列」という文字がある列を探し、その右2列をL, Rとする
        col_idx = 0
        p_count = 1
        while col_idx < len(df.columns) - 2:
            cell_val = str(df.iloc[0, col_idx])
            if "配列" in cell_val:
                name = f"配列{p_count}"
                # 2行目以降の数字を取得
                l = pd.to_numeric(df.iloc[1:, col_idx + 1], errors='coerce').dropna().astype(int).tolist()
                r = pd.to_numeric(df.iloc[1:, col_idx + 2], errors='coerce').dropna().astype(int).tolist()
                if l or r:
                    patterns[name] = {"L": l, "R": r}
                p_count += 1
                col_idx += 3 # 最低3列は飛ばす
            else:
                col_idx += 1 # 「配列」の文字が見つかるまで1列ずつずらす
        return patterns
    except Exception as e:
        st.error(f"読み込みエラー: {e}")
        return {}

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

st.set_page_config(page_title="高精度配列判別", layout="centered")
st.title("📱 配列判別 (CSV自動解析版)")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

# 読み込めた配列の数を確認表示
if patterns:
    st.success(f"データ確認完了: {list(patterns.keys())} を読み込みました")
else:
    st.error("配列データが正しく読み込めていません。1行目に『配列』という文字があるか確認してください。")

with st.form("in", clear_on_submit=True):
    num = st.number_input("カード番号", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"): st.session_state.history.append(num)

if st.button("リセット"):
    st.session_state.history = []
    st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

if st.session_state.history and patterns:
    memo = {}
    results = []
    h_tuple = tuple(st.session_state.history)
    
    with st.spinner('解析中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            # 全範囲スキャン
            for ls in range(len(L_f)):
                # 左右の差が10枚以内の範囲のみ
                for rs in range(max(0, ls-10), min(len(R_f), ls+11)):
                    err, lu, ru = solve(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                    if err == 0:
                        results.append({
                            "name": name, "lp": ls+lu, "rp": rs+ru,
                            "nl": L_f[ls+lu] if ls+lu < len(L_f) else None,
                            "nr": R_f[rs+ru] if rs+ru < len(R_f) else None
                        })

    if results:
        unique_results = []
        seen = set()
        for r in results:
            pos = (r['name'], r['lp'], r['rp'])
            if pos not in seen:
                unique_results.append(r)
                seen.add(pos)

        for m in unique_results[:3]:
            with st.expander(f"【{m['name']}】", expanded=True):
                st.write(f"📍 現在位置: 左 {m['lp']}枚目 / 右 {m['rp']}枚目")
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"**左 次予測**\n\n{m['nl']} ({get_rarity(m['nl'])})")
                with col2:
                    st.info(f"**右 次予測**\n\n{m['nr']} ({get_rarity(m['nr'])})")
    else:
        st.error("一致なし。データ内に『75→47→17』と並ぶ箇所がありません。")    if state in memo: return memo[state]
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

st.set_page_config(page_title="高精度配列判別", layout="centered")
st.title("📱 配列判別 (片側進行予測対応)")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.form("in", clear_on_submit=True):
    num = st.number_input("カード番号", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"): st.session_state.history.append(num)

if st.button("リセット"):
    st.session_state.history = []
    st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

if st.session_state.history and patterns:
    memo = {}
    results = []
    h_tuple = tuple(st.session_state.history)
    
    with st.spinner('スキャン中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            # 全範囲スキャン
            for ls in range(len(L_f)):
                # 左右の差が10枚以内の範囲のみ
                for rs in range(max(0, ls-10), min(len(R_f), ls+11)):
                    err, lu, ru = solve(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                    if err == 0: # 完全一致のみ
                        results.append({
                            "name": name, "lp": ls+lu, "rp": rs+ru,
                            "nl": L_f[ls+lu] if ls+lu < len(L_f) else None,
                            "nr": R_f[rs+ru] if rs+ru < len(R_f) else None
                        })

    if results:
        # 重複を排除（同じ現在地の候補をまとめる）
        unique_results = []
        seen = set()
        for r in results:
            pos = (r['name'], r['lp'], r['rp'])
            if pos not in seen:
                unique_results.append(r)
                seen.add(pos)

        for m in unique_results[:3]:
            with st.expander(f"【{m['name']}】", expanded=True):
                st.write(f"📍 現在位置: 左 {m['lp']}枚目 / 右 {m['rp']}枚目")
                
                # 特定の筒が進んでいない場合の警告
                h_len = len(st.session_state.history)
                # 全て右から出た場合（lu=0）など
                if (m['lp'] - (m['lp'] - h_len)) == 0 or (m['rp'] - (m['rp'] - h_len)) == 0:
                    st.warning("⚠️ 片側の筒しか進んでいないため、もう一方は予測範囲です（誤差±10枚）")

                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"**左 次予測**\n\n{m['nl']} ({get_rarity(m['nl'])})")
                with col2:
                    st.info(f"**右 次予測**\n\n{m['nr']} ({get_rarity(m['nr'])})")
    else:
        st.error("一致なし。10枚以上のズレがあるか、番号間違い、あるいは別の配列です。")
