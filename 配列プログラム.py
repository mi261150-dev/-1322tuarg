import streamlit as st
import pandas as pd

# --- 1. レアリティ・名称定義 ---
def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        names = {
            1:"LR カタストロム", 7:"LLR ドーン", 16:"LR デモンズ", 18:"LR ぎーつ",
            26:"LLR クウガ", 27:"LR アギト", 36:"LR 電王", 48:"LR ゴースト",
            55:"LR ジ王", 58:"LR ディケイド", 61:"LLR V3",
            101:"パラレルLLR ドーン" # 101番を追加
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
    .next-num { font-size: 42px; font-weight: bold; color: #1f77b4; line-height: 1; }
    .rarity-tag { font-size: 18px; color: #d32f2f; font-weight: bold; }
    .history-box { background: #262730; color: #ffffff; padding: 12px; border-radius: 8px; font-size: 20px; font-weight: bold; margin-bottom: 10px; border-left: 5px solid #ff4b4b; }
    .rare-card { background: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-top: 10px; }
    .status-err { color: #ff4b4b; font-weight: bold; font-size: 22px; text-align: center; padding: 20px; }
    .rare-highlight { color: #ff4b4b !important; font-weight: bold !important; }
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
    hist_html = []
    for n in st.session_state.history:
        if is_rare(n):
            hist_html.append(f'<span style="color:#ffff00; font-weight:bold;">{n}</span>')
        else:
            hist_html.append(str(n))
    st.markdown(f'<div class="history-box">出たカード: {" > ".join(hist_html)}</div>', unsafe_allow_html=True)

st.divider()

# --- 5. 解析 & 表示 ---
all_patterns_tab = st.expander("📊 すべての配列表データを見る")
with all_patterns_tab:
    if patterns:
        p_names = list(patterns.keys())
        sel_p = st.selectbox("表示する配列を選択", p_names)
        target_d = patterns[sel_p]
        
        view_data = []
        for i in range(max(len(target_d['L']), len(target_d['R']))):
            l_v = target_d['L'][i] if i < len(target_d['L']) else ""
            r_v = target_d['R'][i] if i < len(target_d['R']) else ""
            
            l_rare_name = get_rarity(l_v)
            r_rare_name = get_rarity(r_v)
            
            # 履歴にある番号を赤くする処理
            def get_col_display(v, rare_name):
                if not v: return ""
                
                # 表示テキストの決定（レアなら名称、それ以外は番号）
                display_text = f"🌟 {rare_name}" if ("LR" in rare_name or "LLR" in rare_name) else str(v)
                
                # 履歴に含まれる場合は赤色にする
                if v in st.session_state.history:
                    return f'<span style="color: red; font-weight: bold;">{display_text}</span>'
                return display_text

            view_data.append({
                "左": get_col_display(l_v, l_rare_name),
                "右": get_col_display(r_v, r_rare_name)
            })
        
        # HTMLを表示できるように unsafe_allow_html を使って表示（DataFrameだとタグがそのまま出るため）
        # ただしDataFrameのままで色を付けたい場合はst.dataframeのcolumn_configやstyleを使いますが、
        # 今回のロジック維持のため、最もシンプルなMarkdownテーブル形式に変換します。
        df_html = pd.DataFrame(view_data).to_html(escape=False, index=False)
        st.write(df_html, unsafe_allow_html=True)

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
                
                st.markdown(f"""
                    <div style="border: 3px solid {color}; padding: 20px; border-radius: 15px; text-align: center; background: white;">
                        <div style="color: {color}; font-weight: bold;">{best['name']} 特定</div>
                        <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                            <div><div style="color: #666;">左・次</div><div class="next-num">{nl}</div><div class="rarity-tag">{get_rarity(nl)}</div></div>
                            <div style="border-left: 1px solid #ddd;"></div>
                            <div><div style="color: #666;">右・次</div><div class="next-num">{nr}</div><div class="rarity-tag">{get_rarity(nr)}</div></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                with st.expander("🔍 この配列の続きを確認"):
                    detail_data = []
                    for i in range(best['lp'], min(best['lp']+20, len(d['L']))):
                        l_v = d['L'][i]; r_v = d['R'][i] if i < len(d['R']) else ""
                        l_r = get_rarity(l_v); r_r = get_rarity(r_v)
                        
                        # 検索結果の表でも、履歴にある番号を赤く表示
                        l_disp = f'<span style="color:red;">{l_v}</span>' if l_v in st.session_state.history else str(l_v)
                        r_disp = f'<span style="color:red;">{r_v}</span>' if r_v in st.session_state.history else str(r_v)
                        
                        detail_data.append({
                            "枚数先": i - best['lp'] + 1,
                            "左": l_disp, "左レア度": f"🌟 {l_r}" if is_rare(l_v) else l_r,
                            "右": r_disp, "右レア度": f"🌟 {r_r}" if is_rare(r_v) else r_r
                        })
                    st.write(pd.DataFrame(detail_data).to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-err">❌ 一致なし</div>', unsafe_allow_html=True)

    render_result(tab_res1, (has_rare and len(h)>=2), "#FF4B4B")
    render_result(tab_res2, (len(h)>=4), "#1f77b4")
else:
    st.info("カード番号を入力してください")
