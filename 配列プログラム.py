import streamlit as st
import pandas as pd
import re
import os

# --- 1. レアリティ・名称定義 ---
def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        names = {
            1:"LR カタストロム", 7:"LLR ドーン", 16:"LR デモンズ", 18:"LR ぎーつ",
            26:"LLR クウガ", 27:"LR アギト", 36:"LR 電王", 48:"LR ゴースト",
            55:"LR ジ王", 58:"LR ディケイド", 61:"LLR V3",
            101:"ランダムパラレルLLR"
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

def is_target_rare(n):
    r = get_rarity(n)
    return any(x in r for x in ["LR", "LLR"])

# --- 2. データ読み込み ---
@st.cache_data
def load_data():
    try:
        if not os.path.exists("配列.csv"): return {}
        df = pd.read_csv("配列.csv", header=None, low_memory=False)
        patterns = {}
        valid_cols = []
        for c in range(df.shape[1]):
            col_data = pd.to_numeric(df.iloc[1:, c], errors='coerce').dropna()
            if len(col_data) >= 3:
                valid_cols.append(c)
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
    history = [int(x) for x in history]
    for side in ["L", "R"]:
        main, sub = (L, R) if side == "L" else (R, L)
        for p in range(len(main)):
            if history[0] == main[p]:
                for start_s in range(max(0, p-15), min(len(sub), p+16)):
                    curr_m, curr_s = p + 1, start_s
                    possible = True
                    for i in range(1, h_len):
                        if curr_m < len(main) and history[i] == main[curr_m]: curr_m += 1
                        elif curr_s < len(sub) and history[i] == sub[curr_s]: curr_s += 1
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
        target = rf'<td>{n}</td>'
        replacement = f'<td><span style="color:#ffdd00; font-weight:bold;">{n}</span></td>'
        df_html = re.sub(rf'(<td>.*?</td>\s*){target}', rf'\1{replacement}', df_html)

    html_code = f"""
    <div style="height: {height}px; overflow-y: auto; border: 1px solid #555; margin-top: 5px; background: #000; border-radius: 5px;">
        <style>
            table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 15px; table-layout: fixed; color: #fff; }}
            th {{ position: sticky; top: 0; background: #333; z-index: 5; border: 1px solid #555; padding: 10px; text-align: center; color: #00ffcc; }}
            td {{ border: 1px solid #444; padding: 10px; text-align: center; background: #111; pointer-events: none; }}
            td:nth-child(1), th:nth-child(1) {{ width: 55px !important; font-size: 14px; color: #888 !important; }}
        </style>
        {df_html}
    </div>
    """
    st.components.v1.html(html_code, height=height + 10)

# --- 5. UI設定 ---
st.set_page_config(page_title="VR-1弾サーチ", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    h1, h2, h3 { color: #ffffff !important; }
    [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
    .history-box { background: #1a1a1a; color: #ffffff; padding: 12px; border-radius: 8px; font-size: 16px; border: 1px solid #444; border-left: 5px solid #ff4b4b; min-height: 50px; }
    [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; align-items: flex-start !important; }
    [data-testid="stColumn"] { min-width: 0px !important; }
    .half-width-container { width: 50% !important; min-width: 200px; }
    .peek-box { border: 2px solid #60b4ff; padding: 10px; border-radius: 10px; text-align: center; background: #111; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("VR-1弾配列サーチ")

if 'history' not in st.session_state: st.session_state.history = []
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

patterns = load_data()

hist_html = [f'<span style="color:{"#ffff00" if is_rare(n) else "#ffffff"}; font-weight:bold;">{n}</span>' for n in st.session_state.history]
display_text = " > ".join(hist_html) if hist_html else "<span style='color:#666;'></span>"
st.markdown(f'<div class="history-box">出たカード: {display_text}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.number_input("番号", min_value=1, max_value=110, value=None, placeholder="ここに番号を入力...", 
                key=f"num_in_{st.session_state.reset_counter}", label_visibility="collapsed")

st.markdown('<div class="half-width-container">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    if st.button("確定", use_container_width=True):
        input_key = f"num_in_{st.session_state.reset_counter}"
        input_val = st.session_state.get(input_key)
        if input_val is not None:
            st.session_state.history.append(int(input_val))
            st.session_state.reset_counter += 1
            st.rerun()
with c2:
    if st.button("消す", use_container_width=True):
        if st.session_state.history:
            st.session_state.history.pop()
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

if st.session_state.history and patterns:
    h = st.session_state.history
    has_rare = any(is_rare(n) for n in h)
    tab_res1, tab_res2 = st.tabs(["① ４枚から検索", "② レアから検索"])

    def render_result(tab_obj, active_req, req_count, color):
        with tab_obj:
            if not active_req:
                st.warning(f"🔍 あと {req_count - len(h)} 枚入力が必要")
                return
            hits = []
            for name, data in patterns.items():
                res = find_matches(h, data["L"], data["R"])
                for ht in res: hits.append({**ht, "name": name})

            if hits:
                best = hits[0]; d = patterns[best['name']]
                nl = d['L'][best['lp']] if best['lp'] < len(d['L']) else "終了"
                nr = d['R'][best['rp']] if best['rp'] < len(d['R']) else "終了"
                
                future_rares = []
                for side in ["L", "R"]:
                    curr_pos, track = (best['lp'], d['L']) if side=="L" else (best['rp'], d['R'])
                    for i in range(curr_pos, len(track)):
                        if is_target_rare(track[i]): future_rares.append({"dist": i - curr_pos + 1, "name": get_rarity(track[i])})
                
                future_rares = sorted(future_rares, key=lambda x: x['dist'])
                rare_predict_html = "<br>".join([f"💎 <span style='color:#00ffcc;'>{r['dist']}枚先</span>: {r['name']}" for r in future_rares]) if future_rares else "なし"

                st.markdown(f"""
<div style="border: 2px solid {color}; padding: 15px; border-radius: 10px; text-align: center; background: #111; margin-bottom: 10px;">
    <div style="color: #fff; font-weight: bold; font-size: 20px; margin-bottom:10px;">{best['name']}</div>
    <div style="display: flex; justify-content: space-around; border-bottom: 1px solid #444; padding-bottom: 15px;">
        <div style="flex:1;"><div style="color:#aaa; font-size:12px;">左・次</div><div style="font-size:32px; font-weight:bold; color:#ff4b4b;">{nl}</div><div style="font-size:11px; color:#eee;">{get_rarity(nl)}</div></div>
        <div style="width:1px; background:#444; margin:0 10px;"></div>
        <div style="flex:1;"><div style="color:#aaa; font-size:12px;">右・次</div><div style="font-size:32px; font-weight:bold; color:#ff4b4b;">{nr}</div><div style="font-size:11px; color:#eee;">{get_rarity(nr)}</div></div>
    </div>
    <div style="margin-top: 15px; text-align: left; font-size: 14px; color: #eee; background:#000; padding:10px; border-radius:5px;">
        <strong style="color:#00ffcc;">🔜 レア予測:</strong><br>{rare_predict_html}
    </div>
</div>
""", unsafe_allow_html=True)

                st.write("### 🔍 配列の続き")
                detail_data = []
                for i in range(30):
                    idx_l, idx_r = best['orig_lp'] + i, best['orig_rp'] + i
                    l_v = d['L'][idx_l] if idx_l < len(d['L']) else None
                    r_v = d['R'][idx_r] if idx_r < len(d['R']) else None
                    def get_detail_disp(v):
                        if v is None: return ""
                        rn = get_rarity(v)
                        return f"🌟 {rn}" if ("LR" in rn or "LLR" in rn) else str(v)
                    detail_data.append({"No.": idx_l + 1, "枚数": "現在" if idx_l < best['lp'] and idx_r < best['rp'] else f"{max(0, idx_l - best['lp'] + 1, idx_r - best['rp'] + 1)}枚先", "左": get_detail_disp(l_v), "右": get_detail_disp(r_v)})
                render_custom_table(pd.DataFrame(detail_data), height=400)
            else:
                st.error("一致なし")

    render_result(tab_res1, len(h)>=4, 4, "#60b4ff")
    render_result(tab_res2, has_rare and len(h)>=2, 2, "#ff4b4b")

st.divider()

all_patterns_tab = st.expander("📊 配列表一覧")
with all_patterns_tab:
    if patterns:
        p_names = list(patterns.keys())
        sel_p = st.selectbox("配列選択", p_names, label_visibility="collapsed")
        target_d = patterns[sel_p]
        
        max_len = max(len(target_d['L']), len(target_d['R']))
        view_data = []
        for i in range(max_len):
            # 修正箇所：IndexErrorを防ぐための判定
            l_val = target_d['L'][i] if i < len(target_d['L']) else None
            r_val = target_d['R'][i] if i < len(target_d['R']) else None
            
            def get_list_disp(v):
                if v is None: return ""
                return f"🌟 {get_rarity(v)}" if is_target_rare(v) else str(v)
                
            view_data.append({
                "No.": i+1, 
                "左": get_list_disp(l_val), 
                "右": get_list_disp(r_val)
            })
        render_custom_table(pd.DataFrame(view_data))

peek_expander = st.expander("👀配列のぞき見用")
with peek_expander:
    if patterns:
        for p_name, data in patterns.items():
            l_last, r_last = data["L"][-1], data["R"][-1]
            st.markdown(f'<div class="peek-box">{p_name}</div>', unsafe_allow_html=True)
            c_img_l, c_img_r = st.columns(2)
            with c_img_l:
                p_l = f"images/{l_last}.jpg"
                if os.path.exists(p_l): st.image(p_l, use_container_width=True)
                st.markdown(f"<div style='text-align:center; color:#aaa; font-size:13px; font-weight:bold;'>左末尾: No.{l_last}</div>", unsafe_allow_html=True)
            with c_img_r:
                p_r = f"images/{r_last}.jpg"
                if os.path.exists(p_r): st.image(p_r, use_container_width=True)
                st.markdown(f"<div style='text-align:center; color:#aaa; font-size:13px; font-weight:bold;'>右末尾: No.{r_last}</div>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            with st.expander("出現レア", expanded=False):
                rares = []
                for s_k in ["L", "R"]:
                    for idx, v in enumerate(data[s_k]):
                        if is_target_rare(v): rares.append({"pos": idx+1, "n": get_rarity(v), "s": "左" if s_k=="L" else "右"})
                for r in sorted(rares, key=lambda x: x['pos']): st.markdown(f"📍 {r['pos']} ({r['s']}): {r['n']}")
    else: st.info("データなし")
