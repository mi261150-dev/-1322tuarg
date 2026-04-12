import streamlit as st
import pandas as pd

# --- 1. 内部判定 & 色定義 ---
RARE_NUMS = [1, 7, 16, 18, 26, 27, 36, 48, 55, 58, 61, 99]

def get_card_display(n):
    if n is None or n == "" or str(n) == "nan": return "終了"
    try:
        n_int = int(float(n))
        names = {
            1:"カタストロム", 7:"ドーン", 16:"デモンズ", 18:"ぎーつ",
            26:"クウガ", 27:"アギト", 36:"電王", 48:"ゴースト",
            55:"ジ王", 58:"ディケイド", 61:"V3"
        }
        if n_int in names:
            return f"{n_int} {names[n_int]}"
        return str(n_int)
    except: return "不明"

def get_color_and_rarity(n):
    if n is None or n == "" or str(n) == "nan" or n == "終了": return "#FFFFFF", "N"
    try:
        n_int = int(float(n))
        if n_int in [7, 26, 61]: return "#FFD700", "LLR"
        if n_int in [1, 16, 18, 27, 36, 48, 55, 58, 99]: return "#FF4B4B", "LR"
        if n_int in [5, 20, 24, 25, 31, 33, 38, 40, 42, 46, 52, 63, 98]: return "#FFFF00", "SR"
        if 64 <= n_int <= 77: return "#1E90FF", "CP"
        return "#FFFFFF", "N"
    except: return "#FFFFFF", "N"

# --- 2. データ読み込み (配列6個分) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        # 6つの配列（1配列あたり左右2列＝計12列まで対応）
        for i in range(6):
            l_col = i * 2
            r_col = i * 2 + 1
            if l_col < df.shape[1] and r_col < df.shape[1]:
                l_data = pd.to_numeric(df.iloc[1:, l_col], errors='coerce').dropna().astype(int).tolist()
                r_data = pd.to_numeric(df.iloc[1:, r_col], errors='coerce').dropna().astype(int).tolist()
                if l_data or r_data:
                    patterns[f"配列 {i + 1}"] = {"L": l_data, "R": r_data}
        return patterns
    except: return {}

# --- 3. 探索エンジン (跨ぎなし・独立検索) ---
def find_matches(history, L, R):
    if not history: return []
    h_len = len(history)
    results = []
    
    # 履歴が全て「左」にあるか、全て「右」にあるかのみを判定（跨ぎなし）
    for side_name, side_list in [("L", L), ("R", R)]:
        for p in range(len(side_list) - h_len + 1):
            # 履歴とシリンダーの連続した範囲が一致するか
            if side_list[p:p + h_len] == history:
                results.append({
                    "lp": p + h_len if side_name == "L" else 0, # 左で見つかったら左を進める
                    "rp": p + h_len if side_name == "R" else 0, # 右で見つかったら右を進める
                    "match_side": side_name
                })
    return results

# --- 4. UI設定 ---
st.set_page_config(page_title="VR-1弾サーチ", layout="centered")

st.markdown("""
    <style>
    .stButton > button { width: 100%; height: 3.2em; font-weight: bold; }
    .next-rare-box { background: #1a1a1a; padding: 20px; border-radius: 15px; text-align: center; margin: 10px 0; border: 2px solid #FFD700; }
    .rare-label { color: #FFD700; font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .rare-name { font-size: 32px; font-weight: bold; line-height: 1.1; }
    .rare-count { font-size: 20px; color: #FFFFFF; margin-top: 5px; }
    .history-box { background: #262730; color: #ffffff; padding: 12px; border-radius: 8px; font-size: 18px; margin-bottom: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

st.title("VR-1弾配列サーチ")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.container():
    c_in, c_add = st.columns([1, 1], gap="small")
    with c_in: num = st.number_input("番号", min_value=1, max_value=110, value=1, label_visibility="collapsed")
    with c_add:
        if st.button("✅ 確定"):
            st.session_state.history.append(int(num)); st.rerun()
    c_sub_l, c_sub_r = st.columns(2)
    with c_sub_l:
        if st.button("⬅️ 1個消す"):
            if st.session_state.history: st.session_state.history.pop(); st.rerun()
    with c_sub_r:
        if st.button("🗑️ 履歴クリア"):
            st.session_state.history = []; st.rerun()

if st.session_state.history:
    hist_html = [f'<span style="color:{get_color_and_rarity(n)[0]}; font-weight:bold;">{n}</span>' for n in st.session_state.history]
    st.markdown(f'<div class="history-box">履歴: {" > ".join(hist_html)}</div>', unsafe_allow_html=True)

st.divider()

# --- 5. 解析 & 表示 ---
if st.session_state.history and patterns:
    h = st.session_state.history
    all_hits = []
    for name, data in patterns.items():
        res = find_matches(h, data["L"], data["R"])
        for ht in res: all_hits.append({**ht, "name": name, "data": data})

    if all_hits:
        # 複数ヒットした場合は最初のものを表示
        best = all_hits[0]
        d = best['data']
        
        def get_next_rare_info(lst, start_pos):
            if start_pos >= len(lst): return {"name": "終了", "count": "-", "color": "#FFFFFF"}
            for i in range(start_pos, len(lst)):
                if lst[i] in RARE_NUMS:
                    return {"name": get_card_display(lst[i]), "count": i - start_pos + 1, "color": get_color_and_rarity(lst[i])[0]}
            return {"name": "不明", "count": "-", "color": "#FFFFFF"}

        # ヒットした側の位置情報を使って次レアを表示
        # (跨ぎがないため、ヒットしなかった方のシリンダーは現在位置0として計算)
        rare_l = get_next_rare_info(d['L'], best['lp'] if best['match_side'] == "L" else 0)
        rare_r = get_next_rare_info(d['R'], best['rp'] if best['match_side'] == "R" else 0)

        st.subheader(f"📍 {best['name']} ({'左' if best['match_side'] == 'L' else '右'}で一致)")
        
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(f"""<div class="next-rare-box">
                <div class="rare-label">左シリンダー次レア</div>
                <div class="rare-name" style="color:{rare_l['color']};">{rare_l['name']}</div>
                <div class="rare-count">{rare_l['count']}枚目</div>
            </div>""", unsafe_allow_html=True)

        with col_r:
            st.markdown(f"""<div class="next-rare-box">
                <div class="rare-label">右シリンダー次レア</div>
                <div class="rare-name" style="color:{rare_r['color']};">{rare_r['name']}</div>
                <div class="rare-count">{rare_r['count']}枚目</div>
            </div>""", unsafe_allow_html=True)

        st.write("### 📋 配列の続き (15枚表示)")
        detail_data = []
        start_l = best['lp'] if best['match_side'] == "L" else 0
        start_r = best['rp'] if best['match_side'] == "R" else 0
        
        for i in range(15):
            idx_l, idx_r = start_l + i, start_r + i
            l_val = d['L'][idx_l] if idx_l < len(d['L']) else None
            r_val = d['R'][idx_r] if idx_r < len(d['R']) else None
            detail_data.append({
                "左": get_card_display(l_val), 
                "右": get_card_display(r_val)
            })
        st.table(detail_data)
    else:
        st.error("❌ 一致なし（不明）")
else:
    st.info("番号を入力してください")

with st.expander("📊 全配列表の確認"):
    if patterns:
        sel_p = st.selectbox("配列データ選択", list(patterns.keys()))
        t_d = patterns[sel_p]
        max_len = max(len(t_d['L']), len(t_d['R']))
        l_view = [get_card_display(t_d['L'][i]) if i < len(t_d['L']) else "終了" for i in range(max_len)]
        r_view = [get_card_display(t_d['R'][i]) if i < len(t_d['R']) else "終了" for i in range(max_len)]
        df_view = pd.DataFrame({"左": l_view, "右": r_view})
        st.dataframe(df_view, use_container_width=True)
