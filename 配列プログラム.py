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

def is_rare_tag(n):
    r = get_rarity(n)
    return "LR" in r or "LLR" in r

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

# --- 3. 判定ロジック ---
def solve_with_details(h, L, R):
    memo = {}
    def solve_internal(hh, ll, rr):
        state = (len(hh), len(ll), len(rr))
        if state in memo: return memo[state]
        if not hh: return 0, 0, 0
        
        res_l = (999, 0, 0)
        if ll:
            score = 0 if hh[0] == ll[0] else (0.1 if hh[0] in {4,7,9} and ll[0] in {4,7,9} else 0.8)
            if hh[0] == ll[0] and is_rare_tag(hh[0]): score = -0.2
            e, lu, ru = solve_internal(hh[1:], ll[1:], rr)
            res_l = (score + e, lu + 1, ru)
        
        res_r = (999, 0, 0)
        if rr:
            score = 0 if hh[0] == rr[0] else (0.1 if hh[0] in {4,7,9} and rr[0] in {4,7,9} else 0.8)
            if hh[0] == rr[0] and is_rare_tag(hh[0]): score = -0.2
            e, lu, ru = solve_internal(hh[1:], ll, rr[1:])
            res_r = (score + e, lu, ru + 1)
        
        ans = res_l if res_l[0] <= res_r[0] else res_r
        memo[state] = ans
        return ans
    return solve_internal(h, L, R)

# --- 4. UI ---
st.set_page_config(page_title="次予測・ダブル候補", layout="centered")
st.title("🎯 次に出るカードはこれだ！")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

# 入力フォーム
with st.form("in_form", clear_on_submit=True):
    num = st.number_input("引いたカードの番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("履歴に追加"):
        st.session_state.history.append(num)

col_btns = st.columns(2)
with col_btns[0]:
    if st.button("1つ戻す"):
        if st.session_state.history: st.session_state.history.pop()
        st.rerun()
with col_btns[1]:
    if st.button("リセット"):
        st.session_state.history = []
        st.rerun()

st.info(f"**現在の履歴:** {st.session_state.history}")

# --- 5. 解析 & ダブル表示 ---
if st.session_state.history and patterns:
    all_hits = []
    h_tuple = tuple(st.session_state.history)
    h_len = len(h_tuple)
    
    for name, data in patterns.items():
        L_f, R_f = data["L"], data["R"]
        for ls in range(len(L_f)):
            for rs in range(max(0, ls-15), min(len(R_f), ls+16)):
                # レアカードが含まれるか、1枚目が一致する場合に詳細スキャン
                if L_f[ls] == h_tuple[0] or R_f[rs] == h_tuple[0] or any(is_rare_tag(x) for x in h_tuple):
                    err, lu, ru = solve_with_details(h_tuple, tuple(L_f[ls:]), tuple(R_f[rs:]))
                    if err < h_len * 0.4:
                        all_hits.append({"name":name, "err":err, "lp":ls+lu, "rp":rs+ru, "data":data})

    if all_hits:
        sorted_hits = sorted(all_hits, key=lambda x: (x['err'], abs(x['lp']-x['rp'])))
        
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
            
            with st.expander(f"{label} {res['name']} - 信頼度 {trust}%", expanded=(idx==0)):
                # 次の予測カード
                nl = res['data']['L'][res['lp']] if res['lp'] < len(res['data']['L']) else "なし"
                nr = res['data']['R'][res['rp']] if res['rp'] < len(res['data']['R']) else "なし"
                
                st.subheader("📢 次に引くカードの予測")
                c1, c2 = st.columns(2)
                with c1:
                    st.success(f"**左から出たら...**\n### {nl}\n({get_rarity(nl)})")
                with c2:
                    st.info(f"**右から出たら...**\n### {nr}\n({get_rarity(nr)})")
                
                # レアまでの残り
                st.write("---")
                def find_rare(lst, start):
                    for i in range(start, len(lst)):
                        if is_rare_tag(lst[i]): return i-start, lst[i]
                    return None, None
                dl, vl = find_rare(res['data']['L'], res['lp'])
                dr, vr = find_rare(res['data']['R'], res['rp'])
                
                rl, rr = st.columns(2)
                with rl:
                    if dl is not None: st.metric("左LRまで", f"あと{dl}枚"); st.caption(f"次は {vl}")
                    else: st.write("左にLRなし")
                with rr:
                    if dr is not None: st.metric("右LRまで", f"あと{dr}枚"); st.caption(f"次は {vr}")
                    else: st.write("右にLRなし")
    else:
        st.warning("一致する配列が見つかりません。番号間違いか、10枚以上のズレがないか確認してください。")
