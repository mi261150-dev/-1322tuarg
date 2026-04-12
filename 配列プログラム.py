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

def is_target_rare(n):
    r = get_rarity(n)
    return any(x in r for x in ["LR", "LLR"])

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
    <div style="height: {height}px; overflow-y: auto; border: 1px solid #ddd; margin-top: 5px; background: white;">
        <style>
            table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 16px; table-layout: fixed; }}
            th {{ position: sticky; top: 0; background: #f0f2f6; z-index: 5; border: 1px solid #ddd; padding: 8px; text-align: center; }}
            td {{ border: 1px solid #ddd; padding: 8px; text-align: center; background: white; pointer-events: none; }}
        </style>
        {df_html}
    </div>
    """
    st.components.v1.html(html_code, height=height + 10)

# --- 5. UI設定 ---
st.set_page_config(page_title="VR-1弾サーチ", layout="centered")

# 虹色点滅アニメーションと配置CSS
st.markdown("""
    <style>
    @keyframes rainbow {
        0% { background-color: #ffadad; }
        16% { background-color: #ffd6a5; }
        33% { background-color: #fdffb6; }
        50% { background-color: #caffbf; }
        66% { background-color: #9bf6ff; }
        83% { background-color: #bdb2ff; }
        100% { background-color: #ffadad; }
    }
    .stApp {
        animation: rainbow 5s infinite;
    }
    [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
    .history-box { background: #262730; color: #ffffff; padding: 10px; border-radius: 8px; font-size: 16px; border-left: 5px solid #ff4b4b; margin-bottom: 5px; }
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0.5rem !important;
        width: 50% !important;
        min-width: 200px !important;
    }
    [data-testid="column"] { flex: 1 1 0% !important; }
    .stButton > button { width: 100% !important; height: 3rem !important; font-weight: bold !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("VR-1弾配列サーチ")

if 'history' not in st.session_state: st.session_state.history = []
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

patterns = load_data()

# --- 履歴 ---
if st.session_state.history:
    hist_html = [f'<span style="color:{"#ffff00" if is_rare(n) else "#ffffff"}; font-weight:bold;">{n}</span>' for n in st.session_state.history]
    st.markdown(f'<div class="history-box">履歴: {" > ".join(hist_html)}</div>', unsafe_allow_html=True)

# --- 番号入力 ---
st.number_input("番号", min_value=1, max_value=110, value=None, placeholder="番号入力...", 
                key=f"num_in_{st.session_state.reset_counter}", label_visibility="collapsed")

# --- ボタン列 ---
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

st.divider()

# --- 6. 配列表一覧表示 ---
all_patterns_tab = st.expander("📊 配列表一覧")
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
                return f"🌟 {rn}" if "LR" in rn or "LLR
