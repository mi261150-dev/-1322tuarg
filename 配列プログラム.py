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

# --- 4. 表生成関数 ---
def render_custom_table(df_data, height=450):
    df_html = df_data.to_html(index=False, escape=False)
    for n in st.session_state.history:
        target = f'<td>{n}</td>'
        replacement = f'<td><span style="color:red; font-weight:bold;">{n}</span></td>'
        df_html = df_html.replace(target, replacement)
    
    html_code = f"""
    <div style="height: {height}px; overflow-y: auto; border: 1px solid #ddd; margin-top: 5px;">
        <style>
            table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 16px; table-layout: fixed; }}
            th {{ position: sticky; top: 0; background: #f0f2f6; z-index: 5; border: 1px solid #ddd; padding: 8px; }}
            td {{ border: 1px solid #ddd; padding: 8px; text-align: center; background: white; pointer-events: none; }}
        </style>
        {df_html}
    </div>
    """
    st.components.v1.html(html_code, height=height + 10)

# --- 5. UI設定 ---
st.set_page_config(page_title="VR-1弾サーチ", layout="centered")

st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
    .stButton > button { width: 100%; height: 3.5em; font-weight: bold; font-size: 14px; padding: 0 !important; }
    .history-box { background: #262730; color: #ffffff; padding: 10px; border-radius: 8px; font-size: 16px; border-left: 5px solid #ff4b4b; }
    [data-testid="stExpander"] [data-testid="stVerticalBlock"] { gap: 0 !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("VR-1弾配列サーチ")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

# スマホ向けボタン横並びレイアウト
num = st.number_input("番号", min_value=1, max_value=110, value=1, label_visibility="collapsed")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("✅確定"):
        st.session_state.history.append(int(num)); st.rerun()
with col2:
    if st.button("⬅️1消す"):
        if st.session_state.history: st.session_state.history.pop(); st.rerun()
with col3:
    if st.button("🗑️消去"):
        st.session_state.history = []; st.rerun()

if st.session_state.history:
    hist_html = [f'<span style="color:{"#ffff00" if is_rare(n) else "#ffffff"}; font-weight:bold;">{n}</span>' for n in st.session_state.history]
    st.markdown(f'<div class="history-box">履歴: {" > ".join(hist_html)}</div>', unsafe_allow_html=True)

st.divider()

# --- 6. 全配列表表示 ---
all_patterns_tab = st.expander("📊 全データ確認")
with all_patterns_tab:
    if patterns:
        p_names = list(patterns.keys())
        sel_p = st.selectbox("配列選択", p_names, label_visibility="collapsed")
        target_d = patterns[sel_p]
        view_data = []
        for i in range(max(len(target_d['L']), len(target_d['R']))):
            l_v = target_d['L'][i] if i < len(target_d['L']) else None
            r_v = target_d['R'][i] if i < len(target_d['R']) else None
            def get_disp(v):
                if v is None: return ""
                rn = get_rarity(v)
                return f"🌟 {rn}" if "LR" in rn or "LLR" in rn else str(v)
            view_data.append({"左": get_disp(l_v), "右": get_disp(r_v)})
        render_custom_table(pd.DataFrame(view_data))

# --- 7. 解析結果表示 ---
if st.session_state.history and patterns:
    h = st.session_state.history
    has_rare = any(is_rare(n) for n in h)
    tab_res1, tab_res2 = st.tabs(["レアあり探索", "4枚一致探索"])

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
                
                st.markdown(f'<div style="border: 2px solid {color}; padding: 10px; border-radius: 10px; text-align: center; background: white; margin-bottom: 10px;">'
                            f'<div style="color: {color}; font-weight: bold;">{best["name"]} 特定</div>'
                            f'<div style="display: flex; justify-content: space-around; margin-top: 5px;">'
                            f'<div><div style="color:#666; font-size:10px;">左・次</div><div style="font-size:28px; font-weight:bold; color:#1f77b4;">{nl}</div><div style="font-size:10px;">{get_rarity(nl)}</div></div>'
                            f'<div><div style="color:#666; font-size:10px;">右・次</div><div style="font-size:28px; font-weight:bold; color:#1f77b4;">{nr}</div><div style="font-size:10px;">{get_rarity(nr)}</div></div>'
                            f'</div></div>', unsafe_allow_html=True)

                # --- 未来のレアカード表示 ---
                st.write("### 💎 以降のレアカード予測")
                future_rares = []
                for side in ["L", "R"]:
                    curr_pos = best['lp'] if side == "L" else best['rp']
                    track = d[side]
                    for i in range(curr_pos, len(track)):
                        val = track[i]
                        if is_rare(val):
                            future_rares.append({
                                "シリンダー": "左" if side == "L" else "右",
                                "枚数先": f"{i - curr_pos + 1}枚目",
                                "レア名称": get_rarity(val)
                            })
                if future_rares:
                    st.table(pd.DataFrame(future_rares).sort_values("枚数先"))
                else:
                    st.write("この先にレアはありません")

                st.write("### 🔍 配列の続き")
                start_l, start_r = best['orig_lp'], best['orig_rp']
                detail_data = []
                for i in range((best['lp'] - best['orig_lp']) + 20):
                    idx_l, idx_r = start_l + i, start_r + i
                    l_v = d['L'][idx_l] if idx_l < len(d['L']) else None
                    r_v = d['R'][idx_r] if idx_r < len(d['R']) else None
                    def get_detail_disp(v):
                        if v is None: return ""
                        rn = get_rarity(v)
                        return f"🌟 {rn}" if "LR" in rn or "LLR" in rn else str(v)
                    detail_data.append({
                        "枚数": "現在" if idx_l < best['lp'] else f"{idx_l - best['lp'] + 1}枚先",
                        "左": get_detail_disp(l_v), "右": get_detail_disp(r_v)
                    })
                render_custom_table(pd.DataFrame(detail_data), height=350)
            else:
                st.error("一致なし")

    render_result(tab_res1, (has_rare and len(h)>=2), "#FF4B4B")
    render_result(tab_res2, (len(h)>=4), "#1f77b4")
else:
    st.info("番号を入力してください")
