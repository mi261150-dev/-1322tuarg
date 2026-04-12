import streamlit as st
import pandas as pd
import re

# --- 1. レアリティ・名称定義 ---
def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        names = {
            1:"LR カタストロム", 7:"LLR ドーン", 16:"LR デモンズ", 18:"LR ぎーつ",
            26:"LLR クウガ", 27:"LR アギト", 36:"LR 電王", 48:"LR ゴースト",
            55:"LR ジ王", 58:"LR ディケイド", 61:"LLR V3",
            101:"パラレルLLR ドーン"
        }
        if n in names: return names[n]

        rarities = {
            99:"ランダムLR", 98:"ランダムSR",
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
                        results.append({"lp": curr_m if side=="L" else curr_s, "rp": curr_s if side=="L" else curr_m, 
                                        "orig_lp": p if side=="L" else start_s, "orig_rp": start_s if side=="L" else p})
    return results

# --- 4. 赤字変換ロジック ---
def highlight_numbers(val):
    if not val: return ""
    str_val = str(val)
    # 数字のみ抽出して履歴チェック
    num_match = re.search(r'\d+', str_val)
    if num_match:
        if int(num_match.group()) in st.session_state.history:
            return f'<span style="color:red; font-weight:bold;">{str_val}</span>'
    return str_val

# --- 5. UI設定 ---
st.set_page_config(page_title="VR-1弾サーチ", layout="centered")

st.markdown("""
    <style>
    [data-testid="column"] { padding-left: 2px !important; padding-right: 2px !important; }
    div[data-testid="column"] { display: flex; align-items: flex-end; }
    .stButton > button { width: 100%; height: 3.2em; font-weight: bold; margin-bottom: 2px; }
    .stNumberInput input { height: 3.2em !important; }
    .next-num { font-size: 42px; font-weight: bold; color: #1f77b4; line-height: 1; }
    .rarity-tag { font-size: 18px; color: #d32f2f; font-weight: bold; }
    .history-box { background: #262730; color: #ffffff; padding: 12px; border-radius: 8px; font-size: 20px; font-weight: bold; margin-bottom: 10px; border-left: 5px solid #ff4b4b; }
    
    /* スクロールエリア */
    .scroll-box { height: 450px; overflow-y: auto; border: 1px solid #444; background: #0e1117; }
    
    /* st.tableの空白列(Index)を消すCSS */
    div[data-testid="stTable"] table thead tr th:first-child { display: none !important; }
    div[data-testid="stTable"] table tbody tr td:first-child { display: none !important; }
    
    /* テーブルスタイル */
    div[data-testid="stTable"] table { width: 100% !important; font-size: 20px !important; border-collapse: collapse; }
    div[data-testid="stTable"] th { background-color: #333 !important; color: white !important; pointer-events: none !important; text-align: center !important; }
    div[data-testid="stTable"] td { padding: 8px !important; border: 1px solid #444 !important; text-align: center !important; }
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
        if st.button("✅ 上の番号で確定"):
            st.session_state.history.append(int(num)); st.rerun()

    c_sub_l, c_sub_r = st.columns(2, gap="small")
    with c_sub_l:
        if st.button("⬅️ 1個消す"):
            if st.session_state.history: st.session_state.history.pop(); st.rerun()
    with c_sub_r:
        if st.button("🗑️ 履歴を消す"):
            st.session_state.history = []; st.rerun()

if st.session_state.history:
    hist_html = [f'<span style="color:{"#ffff00" if is_rare(n) else "#ffffff"}; font-weight:bold;">{n}</span>' for n in st.session_state.history]
    st.markdown(f'<div class="history-box">出たカード: {" > ".join(hist_html)}</div>', unsafe_allow_html=True)

st.divider()

# --- 6. 全配列表表示 ---
all_patterns_tab = st.expander("📊 すべての配列表データを見る")
with all_patterns_tab:
    if patterns:
        p_names = list(patterns.keys())
        sel_p = st.selectbox("表示する配列を選択", p_names)
        target_d = patterns[sel_p]
        view_data = []
        for i in range(max(len(target_d['L']), len(target_d['R']))):
            l_v = target_d['L'][i] if i < len(target_d['L']) else None
            r_v = target_d['R'][i] if i < len(target_d['R']) else None
            def get_disp(v):
                if v is None: return ""
                r_name = get_rarity(v)
                txt = f"🌟 {r_name}" if "LR" in r_name or "LLR" in r_name else str(v)
                return highlight_numbers(txt)
            view_data.append({"左": get_disp(l_v), "右": get_disp(r_v)})
        
        st.markdown('<div class="scroll-box">', unsafe_allow_html=True)
        st.markdown(pd.DataFrame(view_data).to_html(index=False, escape=False), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 解析結果表示 ---
if st.session_state.history and patterns:
    h = st.session_state.history
    has_rare = any(is_rare(n) for n in h)
    tab_res1, tab_res2 = st.tabs(["① レアあり探索", "② 4枚一致探索"])

    def render_result(tab_obj, active_req, color):
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
                
                st.markdown(f'<div style="border: 3px solid {color}; padding: 20px; border-radius: 15px; text-align: center; background: white; margin-bottom: 20px;">'
                            f'<div style="color: {color}; font-weight: bold;">{best["name"]} 特定</div>'
                            f'<div style="display: flex; justify-content: space-around; margin-top: 15px;">'
                            f'<div><div style="color: #666;">左・次</div><div class="next-num">{nl}</div><div class="rarity-tag">{get_rarity(nl)}</div></div>'
                            f'<div style="border-left: 1px solid #ddd;"></div>'
                            f'<div><div style="color: #666;">右・次</div><div class="next-num">{nr}</div><div class="rarity-tag">{get_rarity(nr)}</div></div>'
                            f'</div></div>', unsafe_allow_html=True)

                st.write("### 🔍 この配列の続きを確認")
                start_l, start_r = best['orig_lp'], best['orig_rp']
                detail_data = []
                display_range = (best['lp'] - best['orig_lp']) + 20
                for i in range(display_range):
                    idx_l, idx_r = start_l + i, start_r + i
                    l_v = d['L'][idx_l] if idx_l < len(d['L']) else None
                    r_v = d['R'][idx_r] if idx_r < len(d['R']) else None
                    def get_detail_disp(v):
                        if v is None: return ""
                        r_name = get_rarity(v)
                        txt = f"🌟 {r_name}" if "LR" in r_name or "LLR" in r_name else str(v)
                        return highlight_numbers(txt)

                    detail_data.append({
                        "枚数": "現在" if idx_l < best['lp'] else f"{idx_l - best['lp'] + 1}枚先",
                        "左": get_detail_disp(l_v),
                        "右": get_detail_disp(r_v)
                    })
                
                st.markdown('<div class="scroll-box">', unsafe_allow_html=True)
                st.markdown(pd.DataFrame(detail_data).to_html(index=False, escape=False), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.write("### 💎 以降のレアカード一覧")
                rare_list = []
                for side in ["L", "R"]:
                    current_p = best['lp'] if side == "L" else best['rp']
                    target_list = d[side]
                    for i in range(current_p, len(target_list)):
                        v = target_list[i]
                        if is_rare(v):
                            rare_list.append({"シリンダー": "左" if side == "L" else "右", "枚数先": i - current_p + 1, "カード名": get_rarity(v)})
                if rare_list:
                    st.table(pd.DataFrame(rare_list).sort_values("枚数先"))
            else:
                st.markdown('<div style="color: #ff4b4b; font-weight: bold; font-size: 22px; text-align: center; padding: 20px;">❌ 一致なし</div>', unsafe_allow_html=True)

    render_result(tab_res1, (has_rare and len(h)>=2), "#FF4B4B")
    render_result(tab_res2, (len(h)>=4), "#1f77b4")
else:
    st.info("カード番号を入力してください")
