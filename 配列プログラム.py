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
            5:"SR", 20:"SR", 24:"SR", 31:"SR", 33:"SR", 38:"SR", 40:"SR", 42:"SR", 46:"SR", 52:"SR", 63:"SR"
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
        # 有効なカラムを抽出
        valid_cols = [c for c in range(len(df.columns)) if pd.to_numeric(df.iloc[1:, c], errors='coerce').dropna().count() > 3]
        for i in range(0, len(valid_cols) - 1, 2):
            l_idx, r_idx = valid_cols[i], valid_cols[i+1]
            patterns[f"配列 {i//2 + 1}"] = {
                "L": pd.to_numeric(df.iloc[1:, l_idx], errors='coerce').dropna().astype(int).tolist(),
                "R": pd.to_numeric(df.iloc[1:, r_idx], errors='coerce').dropna().astype(int).tolist()
            }
        return patterns
    except: return {}

# --- 3. 探索エンジン (整合性チェック強化版) ---
def find_matches(history, L, R, mode="STRICT"):
    h_len = len(history)
    results = []
    
    def match(a, b):
        if a == b: return True
        if mode == "FLEX":
            sets = {4, 7, 9, 14, 17, 19, 24, 27, 29, 34, 37, 39, 44, 47, 49}
            if a in sets and b in sets: return True
        return False

    # 全位置スキャンの開始
    for side in ["L", "R"]:
        main, sub = (L, R) if side == "L" else (R, L)
        for p in range(len(main)):
            # 1枚目が一致する場所を探す
            if match(history[0], main[p]):
                # サブ（逆サイド）の初期位置候補を前後12枚に限定
                sub_range = range(max(0, p-12), min(len(sub), p+13))
                
                for start_s in sub_range:
                    # 履歴を1枚ずつ、物理的な並び順通りに追跡できるか検証
                    curr_m = p + 1
                    curr_s = start_s
                    possible = True
                    
                    for i in range(1, h_len):
                        # メイン筒の次にあるか？
                        if curr_m < len(main) and match(history[i], main[curr_m]):
                            curr_m += 1
                        # サブ筒の次にあるか？
                        elif curr_s < len(sub) and match(history[i], sub[curr_s]):
                            curr_s += 1
                        else:
                            # どちらの「次の1枚」にも当てはまらない＝データの飛びが発生
                            possible = False
                            break
                    
                    if possible:
                        results.append({
                            "lp": curr_m if side=="L" else curr_s,
                            "rp": curr_s if side=="L" else curr_m
                        })
    return results

# --- 4. UI設定 ---
st.set_page_config(page_title="配列スキャナー", layout="wide")

st.markdown("""
    <style>
    .next-num { font-size: 32px; font-weight: bold; color: #1f77b4; }
    .rarity-tag { font-size: 14px; color: #666; }
    .status-err { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📟 3段階 配列スキャナー")
if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.container():
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        num = st.number_input("引いたカードの番号を入力", min_value=1, max_value=110, step=1, key="input_num")
    with c2:
        st.write("##")
        if st.button("➕ 追加", use_container_width=True):
            st.session_state.history.append(num)
            st.rerun()
    with c3:
        st.write("##")
        if st.button("🧹 リセット", use_container_width=True):
            st.session_state.history = []
            st.rerun()

st.markdown(f"**現在の履歴:** `{' → '.join(map(str, st.session_state.history))}`")
st.divider()

# --- 5. 解析 & 表示 ---
if st.session_state.history and patterns:
    h = st.session_state.history
    has_rare = any(is_rare(n) for n in h)
    route_cols = st.columns(3)
    
    def display_result(col, title, hits, active, color):
        with col:
            st.subheader(title)
            if not active:
                st.caption("⚠️ 条件未達成（枚数不足など）")
                return
            
            if hits:
                res = hits[0] # 最初の候補を表示
                data = patterns[res['name']]
                nl = data['L'][res['lp']] if res['lp'] < len(data['L']) else "END"
                nr = data['R'][res['rp']] if res['rp'] < len(data['R']) else "END"
                
                st.markdown(f"""
                    <div style="border: 2px solid {color}; padding: 15px; border-radius: 10px; background-color: #fff;">
                        <p style="margin:0; font-weight:bold; color:{color};">{res['name']}</p>
                        <hr style="margin: 10px 0;">
                        <div style="display: flex; justify-content: space-around; text-align: center;">
                            <div><p style="margin:0; color:#666;">左 次予測</p><span class="next-num">{nl}</span><br><span class="rarity-tag">{get_rarity(nl)}</span></div>
                            <div><p style="margin:0; color:#666;">右 次予測</p><span class="next-num">{nr}</span><br><span class="rarity-tag">{get_rarity(nr)}</span></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                def get_dist(lst, p):
                    for i in range(p, len(lst)):
                        r = get_rarity(lst[i])
                        if "LR" in r or "LLR" in r: return i-p, lst[i], r
                    return None, None, None
                dl, vl, rl = get_dist(data['L'], res['lp'])
                dr, vr, rr = get_dist(data['R'], res['rp'])
                st.caption(f"💎 LRまで: 左{f'{dl}枚' if dl is not None else '無'} / 右{f'{dr}枚' if dr is not None else '無'}")
            else:
                st.markdown('<p class="status-err">❌ 整合性エラー: データの飛びを検出</p>', unsafe_allow_html=True)

    # 方法1：レア優先
    hits1 = []
    active1 = (has_rare and len(h) >= 2)
    if active1:
        for name, data in patterns.items():
            for hit in find_matches(h, data["L"], data["R"], mode="STRICT"):
                hits1.append({**hit, "name": name})
    display_result(route_cols[0], "🥇 レア優先", hits1, active1, "#FF4B4B")

    # 方法2：N 3枚以上
    hits2 = []
    active2 = (len(h) >= 3)
    if active2:
        for name, data in patterns.items():
            for hit in find_matches(h, data["L"], data["R"], mode="STRICT"):
                hits2.append({**hit, "name": name})
    display_result(route_cols[1], "🥈 N 3枚一致", hits2, active2, "#1f77b4")

    # 方法3：救済
    hits3 = []
    active3 = (len(h) >= 3)
    if active3:
        for name, data in patterns.items():
            for hit in find_matches(h, data["L"], data["R"], mode="FLEX"):
                hits3.append({**hit, "name": name})
    display_result(route_cols[2], "🥉 救済(479系)", hits3, active3, "#ffaa00")

else:
    st.info("👈 カード番号を入力して追加してください。")
