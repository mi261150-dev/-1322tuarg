
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 設定・色・カード名の定義 ---
RARE_NUMS = [1, 7, 16, 18, 26, 27, 36, 48, 55, 58, 61, 99]

def get_card_display(n):
    if n is None or n == "" or str(n) == "nan": return "終了"
    try:
        n_int = int(float(n))
        names = {
            1:"カタストロム(LR)", 7:"ドーン(LLR)", 16:"デモンズ(LR)", 18:"ギーツ(LR)",
            26:"クウガ(LLR)", 27:"アギト(LR)", 36:"電王(LR)", 48:"ゴースト(LR)",
            55:"ジオウ(LR)", 58:"ディケイド(LR)", 61:"V3(LLR)"
        }
        return f"{n_int} {names[n_int]}" if n_int in names else str(n_int)
    except: return "不明"

def get_color(n):
    try:
        n_int = int(float(n))
        if n_int in [7, 26, 61]: return "#FFD700"  # LLR
        if n_int in [1, 16, 18, 27, 36, 48, 55, 58, 99]: return "#FF4B4B"  # LR
        if n_int in [5, 20, 24, 25, 31, 33, 38, 40, 42, 46, 52, 63, 98]: return "#FFFF00"  # SR
        if 64 <= n_int <= 77: return "#1E90FF"  # CP
    except: pass
    return "#FFFFFF"

# --- 2. CSVデータ読み込み (6配列 = 12列) ---
@st.cache_data
def load_csv_data():
    try:
        # header=Noneで読み込み、全ての行をデータとして扱う
        df = pd.read_csv("配列.csv", header=None)
        patterns = {}
        # 最大6ペア(12列)をループ
        for i in range(6):
            l_idx, r_idx = i * 2, i * 2 + 1
            if l_idx < df.shape[1]:
                l_list = pd.to_numeric(df.iloc[:, l_idx], errors='coerce').dropna().astype(int).tolist()
                r_list = pd.to_numeric(df.iloc[:, r_idx], errors='coerce').dropna().astype(int).tolist() if r_idx < df.shape[1] else []
                if l_list or r_list:
                    patterns[f"配列 {i+1}"] = {"L": l_list, "R": r_list}
        return patterns
    except:
        st.error("配列.csvが見つからないか、形式が正しくありません。")
        return {}

# --- 3. 検索エンジン (跨ぎなし・シリンダー独立) ---
def find_matches(history, L, R):
    if not history: return []
    results = []
    h_len = len(history)
    # 左、右それぞれで連続一致をチェック
    for side_name, side_list in [("L", L), ("R", R)]:
        for p in range(len(side_list) - h_len + 1):
            if side_list[p : p + h_len] == history:
                results.append({
                    "lp": p + h_len if side_name == "L" else 0,
                    "rp": p + h_len if side_name == "R" else 0,
                    "side": side_name
                })
    return results

# --- 4. UI設定 ---
st.set_page_config(page_title="VR-1弾 配列サーチ", layout="centered")
st.markdown("""
    <style>
    .stButton > button { width: 100%; font-weight: bold; height: 3em; }
    .rare-card { background: #1a1a1a; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #FFD700; margin-bottom: 10px; }
    .rare-title { color: #FFD700; font-size: 0.9em; font-weight: bold; }
    .rare-name { font-size: 2em; font-weight: bold; margin: 5px 0; }
    .rare-dist { font-size: 1.2em; color: white; }
    .hist-box { background: #262730; padding: 10px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("VR-1弾 配列サーチ")
if 'history' not in st.session_state: st.session_state.history = []
patterns = load_csv_data()

# 入力
with st.container():
    c1, c2 = st.columns([1, 1])
    with c1: num = st.number_input("番号", 1, 110, 1, label_visibility="collapsed")
    with c2: 
        if st.button("✅ 確定"):
            st.session_state.history.append(int(num)); st.rerun()
    c3, c4 = st.columns(2)
    with c3:
        if st.button("⬅️ 1つ消す"):
            if st.session_state.history: st.session_state.history.pop(); st.rerun()
    with c4:
        if st.button("🗑️ クリア"):
            st.session_state.history = []; st.rerun()

if st.session_state.history:
    tags = [f'<span style="color:{get_color(n)};">{n}</span>' for n in st.session_state.history]
    st.markdown(f'<div class="hist-box">履歴: {" > ".join(tags)}</div>', unsafe_allow_html=True)

st.divider()

# --- 5. 結果表示 ---
if st.session_state.history and patterns:
    h = st.session_state.history
    found = False
    for name, data in patterns.items():
        hits = find_matches(h, data["L"], data["R"])
        if hits:
            found = True
            hit = hits[0]
            st.subheader(f"📍 {name} ({'左' if hit['side'] == 'L' else '右'}一致)")
            
            def get_rare(lst, pos):
                for i in range(pos, len(lst)):
                    if lst[i] in RARE_NUMS:
                        return {"name": get_card_display(lst[i]), "dist": i-pos+1, "color": get_color(lst[i])}
                return {"name": "不明", "dist": "-", "color": "white"}

            # 表示位置の決定
            pos_l = hit['lp'] if hit['side'] == "L" else 0
            pos_r = hit['rp'] if hit['side'] == "R" else 0
            r_l, r_r = get_rare(data["L"], pos_l), get_rare(data["R"], pos_r)

            col1, col2 = st.columns(2)
            for c, side, res in zip([col1, col2], ["左", "右"], [r_l, r_r]):
                with c:
                    st.markdown(f"""<div class="rare-card">
                        <div class="rare-title">{side}シリンダー次レア</div>
                        <div class="rare-name" style="color:{res['color']};">{res['name']}</div>
                        <div class="rare-dist">{res['dist']} 枚目</div>
                    </div>""", unsafe_allow_html=True)

            st.write("### 📋 配列の続き (15枚)")
            rows = []
            for i in range(15):
                l_v = data["L"][pos_l + i] if (pos_l + i) < len(data["L"]) else None
                r_v = data["R"][pos_r + i] if (pos_r + i) < len(data["R"]) else None
                if l_v is None and r_v is None: break
                rows.append({"左": get_card_display(l_v), "右": get_card_display(r_v)})
            st.table(rows)
            break
    if not found: st.error("❌ 一致する配列がありません")
else:
    st.info("番号を入力してください")

with st.expander("📊 全配列表データ（CSV）"):
    if patterns:
        sel = st.selectbox("配列選択", list(patterns.keys()))
        d = patterns[sel]
        m = max(len(d['L']), len(d['R']))
        st.dataframe({
            "左": [get_card_display(d['L'][i]) if i < len(d['L']) else "" for i in range(m)],
            "右": [get_card_display(d['R'][i]) if i < len(d['R']) else "" for i in range(m)]
        }, use_container_width=True)
