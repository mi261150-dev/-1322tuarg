import streamlit as st
import pandas as pd

# --- 1. レアリティ判定（個別に正確な番号を登録） ---
def get_rarity(n):
    if n is None or n == "なし": return ""
    try:
        n = int(n)
        # 固有のレアリティ（LR / LLR / SR）
        rarities = {
            101:"LRパラレル", 100:"SRパラレル", 99:"ランダムLR", 98:"ランダムSR",
            1:"LR", 16:"LR", 18:"LR", 27:"LR", 36:"LR", 48:"LR", 55:"LR", 58:"LR",
            7:"LLR", 26:"LLR", 61:"LLR",
            # SR
            5:"SR", 20:"SR", 24:"SR", 25:"SR", 31:"SR", 33:"SR", 38:"SR", 40:"SR", 42:"SR", 46:"SR", 52:"SR", 63:"SR"
        }
        if n in rarities: return rarities[n]
        # CP
        if 64 <= n <= 77: return "CP"
        # それ以外はすべて N
        return "N"
    except: return ""

def is_rare_tag(n):
    r = get_rarity(n)
    return any(x in r for x in ["LR", "LLR", "CP", "SR"])

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

# --- 3. 判定ロジック（スコア制） ---
def solve_with_details(h, L, R):
    memo = {}
    def solve_internal(hh, ll, rr):
        state = (len(hh), len(ll), len(rr))
        if state in memo: return memo[state]
        if not hh: return 0, 0, 0
        
        # 左から出たと仮定
        res_l = (999, 0, 0)
        if ll:
            score = 0 if hh[0] == ll[0] else (0.1 if hh[0] in {4,7,9} and ll[0] in {4,7,9} else 0.8)
            e, lu, ru = solve_internal(hh[1:], ll[1:], rr)
            res_l = (score + e, lu + 1, ru)
        
        # 右から出たと仮定
        res_r = (999, 0, 0)
        if rr:
            score = 0 if hh[0] == rr[0] else (0.1 if hh[0] in {4,7,9} and rr[0] in {4,7,9} else 0.8)
            e, lu, ru = solve_internal(hh[1:], ll, rr[1:])
            res_r = (score + e, lu, ru + 1)
        
        ans = res_l if res_l[0] <= res_r[0] else res_r
        memo[state] = ans
        return ans
    return solve_internal(h, L, R)

# --- 4. UI ---
st.set_page_config(page_title="最強配列判別", layout="centered")
st.title("🎯 次に出るカード番号を予測")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.form("in_form", clear_on_submit=True):
    num = st.number_input("引いたカードの番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("履歴に追加"):
        st.session_state.history.append(num)

c1, c2 = st.columns(2)
with c1:
    if st.button("1つ消す"):
        if st.session_state.history: st.session_state.history.pop(); st.rerun()
with c2:
    if st.button("リセット"):
        st.session_state.history = []; st.rerun()

st.info(f"**現在の履歴:** {st.session_state.history}")

# --- 5. 解析 & ダブル表示 ---
if st.session_state.history and patterns:
    all_hits = []
    h_tuple = tuple(st.session_state.history)
    h_len = len(h_tuple)
    
    with st.spinner('解析中...'):
        for name, data in patterns.items():
            L_f, R_f = data["L"], data["R"]
            # 全スキャン（±15枚の物理制約内）
            for ls in range(len(L_f)):
                for rs in range(max(0, ls-15), min(len(R_f), ls+16)):
                    # 最初の1枚が付近にあるかチェックして高速化
                    if L_f[ls] == h_tuple[0] or R_f[rs] == h_tuple[0]:
                        err, lu, ru = solve_with_details(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                        if err < h_len * 0.4:
                            all_hits.append({"name":name, "err":err, "lp":ls+lu, "rp":rs+ru, "data":data})

    if all_hits:
        sorted_hits = sorted(all_hits, key=lambda x: (x['err'], abs(x['lp']-x['rp'])))
        
        # 上位2つの異なる候補を表示
        display_results = []
        seen = set()
        for h in sorted_hits:
            key = (h['name'], h['lp'], h['rp'])
            if key not in seen:
                display_results.append(h)
                seen.add(key)
            if len(display_results) >= 2: break

        for idx, res in enumerate(display_results):
            label = "🥇 【第1候補】" if idx == 0 else "🥈 【第2候補】"
            trust = max(0, int(100 - (res['err'] / h_len * 200)))
            
            with st.expander(f"{label} {res['name']} (信頼度 {trust}%)", expanded=(idx==0)):
                # 次の予測カード番号
                nl = res['data']['L'][res['lp']] if res['lp'] < len(res['data']['L']) else "なし"
                nr = res['data']['R'][res['rp']] if res['rp'] < len(res['data']['R']) else "なし"
                
                st.markdown("### 📢 次に出る番号の予測")
                col_l, col_r = st.columns(2)
                with col_l:
                    st.success(f"**左から出たら**\n# {nl}\n({get_rarity(nl)})")
                with col_r:
                    st.info(f"**右から出たら**\n# {nr}\n({get_rarity(nr)})")
                
                # LRまでのカウントダウン
                st.write("---")
                def find_rare(lst, start):
                    for i in range(start, len(lst)):
                        r = get_rarity(lst[i])
                        if "LR" in r or "LLR" in r: return i-start, lst[i], r
                    return None, None, None
                
                dl, vl, rl = find_rare(res['data']['L'], res['lp'])
                dr, vr, rr = find_rare(res['data']['R'], res['rp'])
                
                rl_col, rr_col = st.columns(2)
                with rl_col:
                    if dl is not None: st.metric("左LRまで", f"あと{dl}枚"); st.caption(f"{vl}({rl})")
                    else: st.write("左にLRなし")
                with rr_col:
                    if dr is not None: st.metric("右LRまで", f"あと{dr}枚"); st.caption(f"{vr}({rr})")
                    else: st.write("右にLRなし")
    else:
        st.warning("一致する配列がありません。1枚目の番号が間違っていないか確認してください。")
