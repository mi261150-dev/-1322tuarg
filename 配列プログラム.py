import streamlit as st
import pandas as pd

# --- 1. 内部判定 & 色定義 ---
def get_card_display(n):
    if not n: return ""
    try:
        n = int(n)
        # レアカードのみ名前を定義
        names = {
            1:"カタストロム", 7:"ドーン", 16:"デモンズ", 18:"ぎーつ",
            26:"クウガ", 27:"アギト", 36:"電王", 48:"ゴースト",
            55:"ジ王", 58:"ディケイド", 61:"V3"
        }
        if n in names:
            return f"{n} {names[n]}"
        return str(n)
    except: return str(n)

def get_color_and_rarity(n):
    if not n: return "#FFFFFF", "N"
    try:
        n = int(n)
        # LLR: 金, LR: 赤, SR: 黄, CP: 青, その他: 白
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
    [data-testid="column"] { padding-left: 2px !important; padding-right: 2px !important; }
    div[data-testid="column"] { display: flex; align-items: flex-end; }
    .stButton > button { width: 100%; height: 3.2em; font-weight: bold; margin-bottom: 2px; }
    .stNumberInput input { height: 3.2em !important; }
    .next-num { font-size: 48px; font-weight: bold; line-height: 1.2; }
    .history-box { background: #262730; color: #ffffff; padding: 12px; border-radius: 8px; font-size: 20px; font-weight: bold; margin-bottom: 10px; border-left: 5px solid #ff4b4b; }
    .status-err { color: #ff4b4b; font-weight: bold; font-size: 22px; text-align: center; padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("VR-1弾配列サーチ")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.container():
    c_in, c_add = st.columns([1, 1], gap="small")
    with c_in:
        num = st.number_input("番号入力", min_value=1, max_value=110, value=1, step=1, label_visibility="collapsed")
    with c_add:
        if st.button("✅ 確定"):
            st.session_state.history.append(int(num)); st.rerun()
    c_sub_l, c_sub_r = st.columns(2, gap="small")
    with c_sub_l:
        if st.button("⬅️ 1個消す"):
            if st.session_state.history: st.session_state.history.pop(); st.rerun()
    with c_sub_r:
        if st.button("🗑️ 履歴クリア"):
            st.session_state.history = []; st.rerun()

if st.session_state.history:
    hist_html = []
    for n in st.session_state.history:
        color, _ = get_color_and_rarity(n)
        hist_html.append(f'<span style="color:{color}; font-weight:bold;">{n}</span>')
    st.markdown(f'<div class="history-box">履歴: {" > ".join(hist_html)}</div>', unsafe_allow_html=True)

st.divider()

# --- 5. 解析 & 表示 ---
all_patterns_exp = st.expander("📊 配列表データ")
with all_patterns_exp:
    if patterns:
        sel_p = st.selectbox("配列選択", list(patterns.keys()))
        target_d = patterns[sel_p]
        view_list = []
        for i in range(max(len(target_d['L']), len(target_d['R']))):
            l_v = target_d['L'][i] if i < len(target_d['L']) else ""
            r_v = target_d['R'][i] if i < len(target_d['R']) else ""
            
            # レアのみ名前を付与
            l_txt = get_card_display(l_v)
            r_txt = get_card_display(r_v)
            
            l_disp = f"⭐ {l_txt}" if l_v in st.session_state.history else l_txt
            r_disp = f"⭐ {r_txt}" if r_v in st.session_state.history else r_txt
            view_list.append({"左": l_disp, "右": r_disp})
        st.dataframe(pd.DataFrame(view_list), use_container_width=True, hide_index=True)

if st.session_state.history and patterns:
    h = st.session_state.history
    tab_res1, tab_res2 = st.tabs(["① レアあり", "② 4枚一致"])

    def render_result(tab_obj, active_req, border_color):
        with tab_obj:
            if not active_req:
                st.warning("枚数不足")
                return
            hits = []
            for name, data in patterns.items():
                res = find_matches(h, data["L"], data["R"])
                for ht in res: hits.append({**ht, "name": name})

            if hits:
                best = hits[0]; d = patterns[best['name']]
                nl = d['L'][best['lp']] if best['lp'] < len(d['L']) else "終了"
                nr = d['R'][best['rp']] if best['rp'] < len(d['R']) else "終了"
                color_l, _ = get_color_and_rarity(nl)
                color_r, _ = get_color_and_rarity(nr)
                
                st.markdown(f"""
                    <div style="border: 3px solid {border_color}; padding: 20px; border-radius: 15px; text-align: center; background: white;">
                        <div style="color: {border_color}; font-weight: bold;">{best['name']}</div>
                        <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                            <div><div style="color: #666;">左・次</div><div class="next-num" style="color:{color_l};">{nl}</div></div>
                            <div style="border-left: 1px solid #ddd;"></div>
                            <div><div style="color: #666;">右・次</div><div class="next-num" style="color:{color_r};">{nr}</div></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                with st.expander("🔍 続きを確認"):
                    detail_data = []
                    for i in range(best['lp'], min(best['lp']+20, len(d['L']))):
                        l_v = d['L'][i]; r_v = d['R'][i] if i < len(d['R']) else ""
                        # テーブル内でもレアのみ名前を表示
                        detail_data.append({
                            "左": get_card_display(l_v), 
                            "右": get_card_display(r_v)
                        })
                    st.table(detail_data)
            else:
                st.markdown('<div class="status-err">❌ 一致なし</div>', unsafe_allow_html=True)

    render_result(tab_res1, (len(h)>=2), "#FF4B4B")
    render_result(tab_res2, (len(h)>=4), "#1f77b4")
