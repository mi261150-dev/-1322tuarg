import streamlit as st
import pandas as pd

# --- 1. レアリティ定義 ---
def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        rarities = {
            101:"LRパラレル", 100:"SRパラレル", 99:"ランダムLR", 98:"ランダムSR",
            1:"LR", 16:"LR", 18:"LR", 27:"LR", 36:"LR", 48:"LR", 55:"LR", 58:"LR",
            7:"LLR", 26:"LLR", 61:"LLR",
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
def find_matches(history, L, R, mode="STRICT"):
    h_len = len(history)
    results = []
    def match(a, b):
        if a == b: return True
        if mode == "FLEX":
            sets = {4, 7, 9, 14, 17, 19, 24, 27, 29, 34, 37, 39, 44, 47, 49}
            if a in sets and b in sets: return True
        return False

    for side in ["L", "R"]:
        main, sub = (L, R) if side == "L" else (R, L)
        for p in range(len(main)):
            if match(history[0], main[p]):
                for start_s in range(max(0, p-12), min(len(sub), p+13)):
                    curr_m, curr_s = p + 1, start_s
                    possible = True
                    for i in range(1, h_len):
                        if curr_m < len(main) and match(history[i], main[curr_m]):
                            curr_m += 1
                        elif curr_s < len(sub) and match(history[i], sub[curr_s]):
                            curr_s += 1
                        else:
                            possible = False
                            break
                    if possible:
                        results.append({"lp": curr_m if side=="L" else curr_s, "rp": curr_s if side=="L" else curr_m})
    return results

# --- 4. UI設定 ---
st.set_page_config(page_title="VR-1弾配列サーチ", layout="wide")
st.markdown("""
    <style>
    .next-num { font-size: 36px; font-weight: bold; color: #1f77b4; }
    .rarity-tag { font-size: 16px; color: #666; }
    .status-err { color: #ff4b4b; font-weight: bold; font-size: 20px; }
    .status-uncertain { color: #ffa500; font-weight: bold; font-size: 20px; }
    .history-text { font-size: 28px; font-weight: bold; background: #f0f2f6; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    .rare-info { font-size: 22px; line-height: 1.8; font-weight: bold; }
    .rare-title { color: #d32f2f; margin-bottom: 8px; text-decoration: underline; font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

st.title("VR-1弾配列サーチ")
if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.container():
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        num = st.number_input("カード番号を入力", min_value=1, max_value=110, step=1, key=f"input_{len(st.session_state.history)}")
    with c2:
        st.write("##")
        if st.button("カード番号を入力", use_container_width=True):
            st.session_state.history.append(num)
            st.rerun()
    with c3:
        st.write("##")
        if st.button("履歴いっこ消す", use_container_width=True):
            if st.session_state.history:
                st.session_state.history.pop()
                st.rerun()
    with c4:
        st.write("##")
        if st.button("履歴を消す", use_container_width=True):
            st.session_state.history = []
            st.rerun()

st.markdown(f'<div class="history-text">履歴: {" → ".join(map(str, st.session_state.history))}</div>', unsafe_allow_html=True)
st.divider()

# --- 5. 解析 & 表示 ---
if st.session_state.history and patterns:
    h = st.session_state.history
    has_rare = any(is_rare(n) for n in h)
    route_cols = st.columns(3)
    
    def display_result(col, title, hits, active, color, check_multiple=False):
        with col:
            st.subheader(title)
            if not active:
                st.caption("枚数不足")
                return
            
            if not hits:
                st.markdown('<p class="status-err">❌ 整合性エラー</p>', unsafe_allow_html=True)
                return

            # 「複数の予測結果」があるかチェック
            if check_multiple:
                # 予測される（次の左, 次の右）のペアをすべて抽出
                predictions = []
                for hit in hits:
                    d = patterns[hit['name']]
                    nl = d['L'][hit['lp']] if hit['lp'] < len(d['L']) else "END"
                    nr = d['R'][hit['rp']] if hit['rp'] < len(d['R']) else "END"
                    predictions.append((nl, nr))
                
                # ユニークな予測の組み合わせが2つ以上あれば「不確定」
                if len(set(predictions)) > 1:
                    st.markdown('<p class="status-uncertain">⚠️ 不確定（複数候補あり）</p>', unsafe_allow_html=True)
                    return

            # ここまで来れば確定、または方法3
            res = hits[0]
            data = patterns[res['name']]
            nl = data['L'][res['lp']] if res['lp'] < len(data['L']) else "END"
            nr = data['R'][res['rp']] if res['rp'] < len(data['R']) else "END"
            
            st.markdown(f"""
                <div style="border: 2px solid {color}; padding: 15px; border-radius: 10px; background-color: #fff; margin-bottom: 15px;">
                    <p style="margin:0; font-weight:bold; color:{color}; font-size: 20px;">{res['name']}</p>
                    <hr style="margin: 10px 0;">
                    <div style="display: flex; justify-content: space-around; text-align: center;">
                        <div><p style="margin:0; color:#666;">左 次予測</p><span class="next-num">{nl}</span><br><span class="rarity-tag">{get_rarity(nl)}</span></div>
                        <div><p style="margin:0; color:#666;">右 次予測</p><span class="next-num">{nr}</span><br><span class="rarity-tag">{get_rarity(nr)}</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            def get_all_rare_dists(lst, p):
                targets = ["LLR", "LR", "SRパラレル", "LRパラレル", "ランダムLR"]
                found = []
                for i in range(p, len(lst)):
                    r = get_rarity(lst[i])
                    found_this_step = [t for t in targets if t in r]
                    if found_this_step:
                        for t in found_this_step:
                            found.append(f"{t}: {i-p}枚 ({lst[i]})")
                            if t in targets: targets.remove(t)
                    if not targets: break
                return found if found else ["なし"]

            st.markdown('<div class="rare-info">', unsafe_allow_html=True)
            st.markdown('<p class="rare-title">左・次以降のレア</p>', unsafe_allow_html=True)
            for x in get_all_rare_dists(data['L'], res['lp']): st.write(f"・{x}")
            st.markdown('<p class="rare-title" style="margin-top:15px;">右・次以降のレア</p>', unsafe_allow_html=True)
            for x in get_all_rare_dists(data['R'], res['rp']): st.write(f"・{x}")
            st.markdown('</div>', unsafe_allow_html=True)

    # 候補リストの作成
    def get_all_hits(mode):
        results = []
        for name, data in patterns.items():
            for hit in find_matches(h, data["L"], data["R"], mode=mode):
                results.append({**hit, "name": name})
        return results

    # 各ルートの実行
    display_result(route_cols[0], "🥇 レアカードある結果", 
                   hits=get_all_hits("STRICT") if (has_rare and len(h)>=2) else [], 
                   active=(has_rare and len(h)>=2), color="#FF4B4B", check_multiple=True)
    
    display_result(route_cols[1], "🥈 ノーマル三枚以上結果", 
                   hits=get_all_hits("STRICT") if (len(h)>=3) else [], 
                   active=(len(h)>=3), color="#1f77b4", check_multiple=True)

    display_result(route_cols[2], "🥉 配列表のミス考慮結果", 
                   hits=get_all_hits("FLEX") if (len(h)>=3) else [], 
                   active=(len(h)>=3), color="#ffaa00", check_multiple=False)

else:
    st.info("カード番号を入力して履歴を開始してください。")
