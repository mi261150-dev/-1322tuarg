import streamlit as st
import pandas as pd

# --- 1. 内部判定 & 色定義 ---
RARE_NUMS = [1, 7, 16, 18, 26, 27, 36, 48, 55, 58, 61, 99]

def get_card_display(n):
    if n is None or n == "" or n == "終了": return "終了"
    try:
        n = int(n)
        names = {
            1:"カタストロム", 7:"ドーン", 16:"デモンズ", 18:"ぎーつ",
            26:"クウガ", 27:"アギト", 36:"電王", 48:"ゴースト",
            55:"ジ王", 58:"ジ王", 61:"V3"
        }
        if n in names:
            return f"{n} {names[n]}"
        return str(n)
    except: return str(n)

def get_color_and_rarity(n):
    if n is None or n == "" or n == "終了": return "#FFFFFF", "N"
    try:
        n = int(n)
        if n in [7, 26, 61]: return "#FFD700", "LLR"
        if n in [1, 16, 18, 27, 36, 48, 55, 58, 99]: return "#FF4B4B", "LR"
        if n in [5, 20, 24, 25, 31, 33, 38, 40, 42, 46, 52, 63, 98]: return "#FFFF00", "SR"
        if 64 <= n <= 77: return "#1E90FF", "CP"
        return "#FFFFFF", "N"
    except: return "#FFFFFF", "N"

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

# --- 3. 探索エンジン ---
def find_matches(history, L, R):
    if not history: return []
    h_len = len(history)
    results = []
    for side in ["L", "R"]:
        main, sub = (L, R) if side == "L" else (R, L)
        for p in range(len(main)):
            if history[0] == main[p]:
                for start_s in range(max(0, p-12), min(len(sub), p+13)):
                    curr_m, curr_s = p + 1, start_s
                    possible = True
                    for i in range(1, h_len):
                        if curr_m < len(main) and history[i] == main[curr_m]:
                            curr_m += 1
                        elif curr_s < len(sub) and history[i] == sub[curr_s]:
                            curr_s += 1
                        else:
                            possible = False
                            break
                    if possible:
                        results.append({"lp": curr_m if side=="L" else curr_s, "rp": curr_s if side=="L" else curr_m})
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

# 入力部
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
    # メインサーチ（レアあり優先）
    all_hits = []
    for name, data in patterns.items():
        res = find_matches(h, data["L"], data["R"])
        for ht in res: all_hits.append({**ht, "name": name})

    if all_hits:
        best = all_hits[0]
        d = patterns[best['name']]
        
        # レア検索関数
        def get_next_rare_info(lst, start_pos):
            for i in range(start_pos, len(lst)):
                if lst[i] in RARE_NUMS:
                    return {"name": get_card_display(lst[i]), "count": i - start_pos + 1, "color": get_color_and_rarity(lst[i])[0]}
            return {"name": "不明", "count": "-", "color": "#FFFFFF"}

        rare_l = get_next_rare_info(d['L'], best['lp'])
        rare_r = get_next_rare_info(d['R'], best['rp'])

        st.subheader(f"📍 {best['name']}")
        
        # 目立たせるレア表示
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(f"""<div class="next-rare-box">
                <div class="rare-label">左シリンダー次レア</div>
                <div class="rare-name" style="color:{rare_l['color']};">{rare_l['name']}</div>
                <div class="rare-count">{rare_l['count']}枚目</div>
            </div>""", unsafe_allow_html=True)
            st.caption(f"直後の番号: {get_card_display(d['L'][best['lp']] if best['lp'] < len(d['L']) else '終了')}")

        with col_r:
            st.markdown(f"""<div class="next-rare-box">
                <div class="rare-label">右シリンダー次レア</div>
                <div class="rare-name" style="color:{rare_r['color']};">{rare_r['name']}</div>
                <div class="rare-count">{rare_r['count']}枚目</div>
            </div>""", unsafe_allow_html=True)
            st.caption(f"直後の番号: {get_card_display(d['R'][best['rp']] if best['rp'] < len(d['R']) else '終了')}")

        # 続きを表示（隠さない）
        st.write("### 📋 配列の続き")
        detail_data = []
        for i in range(20):
            idx_l, idx_r = best['lp'] + i, best['rp'] + i
            l_v = d['L'][idx_l] if idx_l < len(d['L']) else None
            r_v = d['R'][idx_r] if idx_r < len(d['R']) else None
            if l_v is None and r_v is None: break
            detail_data.append({
                "左": get_card_display(l_v), 
                "右": get_card_display(r_v)
            })
        st.table(detail_data)
    else:
        st.error("❌ 一致する配列が不明です")
else:
    st.info("カード番号を入力してください")

# 配列表データ（全確認用）
with st.expander("📊 全配列表の確認"):
    if patterns:
        sel_p = st.selectbox("配列データ選択", list(patterns.keys()))
        t_d = patterns[sel_p]
        st.dataframe(pd.DataFrame({
            "左": [get_card_display(x) for x in t_d['L']],
            "右": [get_card_display(x) for x in t_d['R']]
        }), use_container_width=True)
