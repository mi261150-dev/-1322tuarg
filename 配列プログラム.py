import streamlit as st
import pandas as pd

# --- 1. レアリティ判定 (N以外をフックにする) ---
def get_rarity(n):
    if n is None: return ""
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

def get_weight(n):
    """カードの重要度を返す。レアカードほど特定能力が高い"""
    r = get_rarity(n)
    if "LR" in r or "LLR" in r: return 5.0  # LR一致は超重要
    if "SR" in r or "CP" in r: return 2.0   # SR/CPも重要
    return 1.0                              # Nは参考程度

# --- 2. 判定ロジック (重み付きスコアリング) ---
def solve_with_trust(h, L, R):
    memo = {}
    def solve_internal(hh, ll, rr):
        state = (len(hh), len(ll), len(rr))
        if state in memo: return memo[state]
        if not hh: return 0, 0, 0
        
        target = hh[0]
        w = get_weight(target)
        
        # 左筒からの排出をシミュレート
        res_l = (999, 0, 0)
        if ll:
            # 一致なら0点、不一致なら重み分のペナルティ
            penalty = 0 if target == ll[0] else w
            # 4,7,9の読み替え救済 (不一致ペナルティを軽減)
            if target != ll[0] and target in {4,7,9} and ll[0] in {4,7,9}:
                penalty = w * 0.2
                
            e, lu, ru = solve_internal(hh[1:], ll[1:], rr)
            res_l = (penalty + e, lu + 1, ru)
            
        # 右筒からの排出をシミュレート
        res_r = (999, 0, 0)
        if rr:
            penalty = 0 if target == rr[0] else w
            if target != rr[0] and target in {4,7,9} and rr[0] in {4,7,9}:
                penalty = w * 0.2
                
            e, lu, ru = solve_internal(hh[1:], ll, rr[1:])
            res_r = (penalty + e, lu, ru + 1)
            
        ans = res_l if res_l[0] <= res_r[0] else res_r
        memo[state] = ans
        return ans
    return solve_internal(h, L, R)

# --- 3. データ読み込み ---
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

# --- 4. メインUI ---
st.set_page_config(page_title="高精度配列サーチ", layout="centered")
st.title("🎯 配列特定 (信頼度正常化版)")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.form("input_area", clear_on_submit=True):
    num = st.number_input("カード番号を入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"):
        st.session_state.history.append(num)

col1, col2 = st.columns(2)
with col1:
    if st.button("1枚消す"):
        if st.session_state.history: st.session_state.history.pop(); st.rerun()
with col2:
    if st.button("全消去"):
        st.session_state.history = []; st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

if st.session_state.history and patterns:
    h_tuple = tuple(st.session_state.history)
    max_penalty_possible = sum(get_weight(n) for n in h_tuple)
    all_results = []
    
    with st.spinner('精密スキャン中...'):
        for name, data in patterns.items():
            L, R = data["L"], data["R"]
            # 物理的にあり得る範囲(±15枚)を全探索
            for ls in range(len(L)):
                for rs in range(max(0, ls-15), min(len(R), ls+16)):
                    # 1枚目が合う場所を起点にする(高速化&精度)
                    if L[ls] == h_tuple[0] or R[rs] == h_tuple[0]:
                        penalty, lu, ru = solve_with_trust(h_tuple, tuple(L[ls:]), tuple(R[rs:]))
                        
                        # 信頼度計算: (1 - ペナルティ合計 / 最大ペナルティ)
                        trust = int((1 - (penalty / max_penalty_possible)) * 100)
                        
                        if trust > 40: # 信頼度が低すぎるゴミデータは除外
                            all_results.append({
                                "name": name, "trust": trust, "lp": ls+lu, "rp": rs+ru, "data": data
                            })

    if all_results:
        # 信頼度が高い順、かつ進み具合が自然な順
        sorted_res = sorted(all_results, key=lambda x: (-x['trust'], abs(x['lp']-x['rp'])))
        
        # 重複排除
        unique_res = []
        seen = set()
        for r in sorted_res:
            key = (r['name'], r['lp'], r['rp'])
            if key not in seen:
                unique_res.append(r)
                seen.add(key)
            if len(unique_res) >= 2: break

        for i, res in enumerate(unique_res):
            st.subheader(f"{'🥇' if i==0 else '🥈'} {res['name']} (信頼度: {res['trust']}%)")
            
            nl = res['data']['L'][res['lp']] if res['lp'] < len(res['data']['L']) else "END"
            nr = res['data']['R'][res['rp']] if res['rp'] < len(res['data']['R']) else "END"
            
            c_l, c_r = st.columns(2)
            c_l.success(f"**左 次予測**\n# {nl}\n({get_rarity(nl)})")
            c_r.info(f"**右 次予測**\n# {nr}\n({get_rarity(nr)})")
            
            # カウントダウン
            with st.expander("この先のLR位置を確認"):
                for side, lst, pos in [("左", res['data']['L'], res['lp']), ("右", res['data']['R'], res['rp'])]:
                    for j in range(pos, len(lst)):
                        rare = get_rarity(lst[j])
                        if "LR" in rare or "LLR" in rare:
                            st.write(f"{side}筒: あと **{j-pos}枚** で {lst[j]}({rare})")
                            break
    else:
        st.error("一致なし。番号が違うか、配列が混ざっている可能性があります。")
