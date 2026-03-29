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
            5:"SR", 20:"SR", 24:"SR", 25:"SR", 31:"SR", 33:"SR", 38:"SR", 40:"SR", 42:"SR", 46:"SR", 52:"SR", 63:"SR"
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
        valid_cols = [c for c in range(len(df.columns)) if pd.to_numeric(df.iloc[1:, c], errors='coerce').dropna().count() > 3]
        for i in range(0, len(valid_cols) - 1, 2):
            l_idx, r_idx = valid_cols[i], valid_cols[i+1]
            patterns[f"配列 {i//2 + 1}"] = {
                "L": pd.to_numeric(df.iloc[1:, l_idx], errors='coerce').dropna().astype(int).tolist(),
                "R": pd.to_numeric(df.iloc[1:, r_idx], errors='coerce').dropna().astype(int).tolist()
            }
        return patterns
    except: return {}

# --- 3. 厳密探索エンジン（データの飛びを許さない） ---
def find_matches_strict(history, L, R, mode="STRICT"):
    h_len = len(history)
    results = []
    
    def match(a, b):
        if a == b: return True
        if mode == "FLEX": # 方法3のみ使用
            sets = {4, 7, 9, 14, 17, 19, 24, 27, 29, 34, 37, 39, 44, 47, 49}
            if a in sets and b in sets: return True
        return False

    # 1枚目の位置を特定
    for side in ["L", "R"]:
        main, sub = (L, R) if side == "L" else (R, L)
        for p in range(len(main)):
            if match(history[0], main[p]):
                # サブ側の初期位置も前後12枚を全探索
                sub_range = range(max(0, p-12), min(len(sub), p+13))
                
                for start_s in sub_range:
                    # 履歴を1枚ずつシミュレート
                    m_idx, s_idx = p + 1, start_s
                    possible = True
                    
                    # 2枚目以降、必ず「現在のLの次」か「現在のRの次」のどちらかでなければならない
                    for h_i in range(1, h_len):
                        found_step = False
                        # メイン列の次にあるか？
                        if m_idx < len(main) and match(history[h_i], main[m_idx]):
                            m_idx += 1
                            found_step = True
                        # サブ列の次にあるか？
                        elif s_idx < len(sub) and match(history[h_i], sub[s_idx]):
                            s_idx += 1
                            found_step = True
                        
                        # どちらにもなかった場合、それは「データの飛び」なので即座に却下
                        if not found_step:
                            possible = False
                            break
                    
                    if possible:
                        results.append({
                            "lp": m_idx if side=="L" else s_idx,
                            "rp": s_idx if side=="L" else m_idx
                        })
    return results

# --- 4. UI ---
st.set_page_config(page_title="厳密配列スキャナー", layout="wide")
st.title("📟 配列スキャナー（整合性チェック強化版）")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

# サイドバー：入力
with st.sidebar:
    st.header("カード入力")
    num = st.number_input("番号", min_value=1, max_value=110, step=1)
    if st.button("追加"): st.session_state.history.append(num); st.rerun()
    if st.button("最後を消す"):
        if st.session_state.history: st.session_state.history.pop(); st.rerun()
    if st.button("全リセット"): st.session_state.history = []; st.rerun()
    st.info(f"履歴: {st.session_state.history}")

# メイン表示
if st.session_state.history and patterns:
    h = st.session_state.history
    has_rare = any(is_rare(n) for n in h)
    cols = st.columns(3)

    # 共通表示関数
    def render_route(col, title, hits, active, color):
        with col:
            st.markdown(f"### {title}")
            if not active:
                st.caption("待機中...")
                return
            if hits:
                res = hits[0]
                data = patterns[res['name']]
                nl, nr = data['L'][res['lp']], data['R'][res['rp']]
                st.markdown(f"""
                    <div style="border: 2px solid {color}; padding: 15px; border-radius: 10px;">
                        <p style="color:{color}; font-weight:bold;">{res['name']}</p>
                        <div style="display: flex; justify-content: space-between;">
                            <div style="text-align:center;">左予測<br><b style="font-size:24px;">{nl}</b></div>
                            <div style="text-align:center;">右予測<br><b style="font-size:24px;">{nr}</b></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("❌ 整合性エラー\n(データの飛びを検出)")

    # 1. レア優先
    hits1 = []
    if has_rare and len(h) >= 2:
        for n, d in patterns.items():
            for ht in find_matches_strict(h, d["L"], d["R"], "STRICT"):
                hits1.append({**ht, "name": n})
    render_route(cols[0], "🥇 レア優先", hits1, (has_rare and len(h)>=2), "#FF4B4B")

    # 2. N 3枚
    hits2 = []
    if len(h) >= 3:
        for n, d in patterns.items():
            for ht in find_matches_strict(h, d["L"], d["R"], "STRICT"):
                hits2.append({**ht, "name": n})
    render_route(cols[1], "🥈 N 3枚一致", hits2, (len(h)>=3), "#1f77b4")

    # 3. 救済
    hits3 = []
    if len(h) >= 3:
        for n, d in patterns.items():
            for ht in find_matches_strict(h, d["L"], d["R"], "FLEX"):
                hits3.append({**ht, "name": n})
    render_route(cols[2], "🥉 救済(479系)", hits3, (len(h)>=3), "#ffaa00")

else:
    st.write("カード番号を入力してください。")
