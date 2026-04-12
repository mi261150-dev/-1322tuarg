import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 名称・色・判定定義 ---
def get_card_display(n):
    if n is None or n == "" or (isinstance(n, float) and np.isnan(n)): return ""
    try:
        n = int(float(n))
        names = {
            1:"LR カタストロム", 7:"LLR ドーン", 16:"LR デモンズ", 18:"LR ぎーつ",
            26:"LLR クウガ", 27:"LR アギト", 36:"LR 電王", 48:"LR ゴースト",
            55:"LR ジ王", 58:"LR ディケイド", 61:"LLR V3"
        }
        if n in names:
            return f"{n} {names[n]}"
        return str(n)
    except: return str(n)

def get_color_and_rarity(n):
    if n is None or n == "" or (isinstance(n, float) and np.isnan(n)): return "#FFFFFF"
    try:
        n = int(float(n))
        if n in [7, 26, 61]: return "#FFD700" # LLR
        if n in [1, 16, 18, 27, 36, 48, 55, 58, 99]: return "#FF4B4B" # LR
        if n in [5, 20, 24, 25, 31, 33, 38, 40, 42, 46, 52, 63, 98]: return "#FFFF00" # SR
        if 64 <= n <= 77: return "#1E90FF" # CP
        return "#FFFFFF"
    except: return "#FFFFFF"

# --- 2. データ読み込み（修正：空セル対策強化） ---
@st.cache_data
def load_data():
    try:
        # csvを文字列として読み込み、欠損値を確実に処理
        df = pd.read_csv("配列.csv", header=None).replace({np.nan: None})
        patterns = {}
        # 2列ペアで回す
        for i in range(0, df.shape[1] - 1, 2):
            # 数値に変換できるものだけ抽出し、リスト化
            l_col = pd.to_numeric(df.iloc[1:, i], errors='coerce').dropna().astype(int).tolist()
            r_col = pd.to_numeric(df.iloc[1:, i+1], errors='coerce').dropna().astype(int).tolist()
            
            if len(l_col) > 0 or len(r_col) > 0:
                patterns[f"配列 {i//2 + 1}"] = {"L": l_col, "R": r_col}
        return patterns
    except Exception as e:
        st.error(f"読み込み失敗: {e}")
        return {}

# --- 3. 探索エンジン ---
def find_matches(history, L, R):
    if not history: return []
    h_len = len(history)
    results = []
    for side in ["L", "R"]:
        main, sub = (L, R) if side == "L" else (R, L)
        for p in range(len(main)):
            if history[0] == main[p]:
                for start_s in range(max(0, p-20), min(len(sub), p+20)):
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
                        results.append({
                            "lp": curr_m if side=="L" else curr_s,
                            "rp": curr_s if side=="L" else curr_m
                        })
    return results

# --- 4. UI設定 ---
st.set_page_config(page_title="VR-1弾サーチ", layout="centered")

st.markdown("""
    <style>
    [data-testid="column"] { padding-left: 2px !important; padding-right: 2px !important; }
    div[data-testid="column"] { display: flex; align-items: flex-end; }
    .stButton > button { width: 100%; height: 3.2em; font-weight: bold; margin-bottom: 2px; }
    .stNumberInput input { height: 3.2em !important; }
    .next-num { font-size: 48px; font-weight: bold; line-height: 1.2; min-height: 60px; }
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
    hist_html = [f'<span style="color:{get_color_and_rarity(n)}; font-weight:bold;">{n}</span>' for n in st.session_state.history]
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
            l_v = target_d['L'][i] if i < len(target_d['L']) else None
            r_v = target_d['R'][i] if i < len(target_d['R']) else None
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
                res_list = find_matches(h, data["L"], data["R"])
                for ht in res_list: hits.append({**ht, "name": name})

            if hits:
                best = hits[0]; d = patterns[best['name']]
                # データがあるか厳密にチェック
                val_l = d['L'][best['lp']] if best['lp'] < len(d['L']) else "終了"
                val_r = d['R'][best['rp']] if best['rp'] < len(d['R']) else "終了"
                
                st.markdown(f"""
                    <div style="border: 3px solid {border_color}; padding: 20px; border-radius: 15px; text-align: center; background: white;">
                        <div style="color: {border_color}; font-weight: bold;">{best['name']}</div>
                        <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                            <div><div style="color: #666;">左・次</div><div class="next-num" style="color:{get_color_and_rarity(val_l)};">{val_l}</div></div>
                            <div style="border-left: 1px solid #ddd;"></div>
                            <div><div style="color: #666;">右・次</div><div class="next-num" style="color:{get_color_and_rarity(val_r)};">{val_r}</div></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                with st.expander("🔍 続きを確認"):
                    detail_data = []
                    for i in range(20):
                        idx_l, idx_r = best['lp'] + i, best['rp'] + i
                        l_v = d['L'][idx_l] if idx_l < len(d['L']) else None
                        r_v = d['R'][idx_r] if idx_r < len(d['R']) else None
                        if l_v is None and r_v is None: break
                        detail_data.append({
                            "左": get_card_display(l_v) if l_v is not None else "終了",
                            "右": get_card_display(r_v) if r_v is not None else "終了"
                        })
                    st.table(detail_data)
            else:
                st.markdown('<div class="status-err">❌ 一致なし</div>', unsafe_allow_html=True)
else:
    st.info("番号を入力してください")
