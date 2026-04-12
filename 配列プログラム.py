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
        # utf-8やcp932など、環境に合わせてエンコーディングを指定する必要がある場合があります
        df = pd.read_csv("配列.csv", header=None, encoding='utf-8')
        patterns = {}
        valid_cols = [c for c in range(len(df.columns)) if pd.to_numeric(df.iloc[1:, c], errors='coerce').dropna().count() > 3]
        for i in range(0, len(valid_cols) - 1, 2):
            l_idx, r_idx = valid_cols[i], valid_cols[i+1]
            patterns[f"配列 {i//2 + 1}"] = {
                "L": pd.to_numeric(df.iloc[1:, l_idx], errors='coerce').dropna().astype(int).tolist(),
                "R": pd.to_numeric(df.iloc[1:, r_idx], errors='coerce').dropna().astype(int).tolist()
            }
        return patterns
    except FileNotFoundError:
        st.error("「配列.csv」ファイルが見つかりません。")
        return {}
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
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
                # 枝刈り：履歴の長さに対して配列が短すぎる場合はスキップ
                if p + h_len > len(main) + 25: # ある程度の余裕を持たせる
                    continue

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
                        results.append({"lp": curr_m if side=="L" else curr_s, "rp": curr_s if side=="L" else curr_ m, 
                                        "orig_lp": p if side=="L" else start_s, "orig_rp": start_s if side=="L" else p})
    return results

# --- 4. 表生成関数 ---
def render_custom_table(df_data, height=450):
    # インデックス（No.）を非表示にする設定
    df_html = df_data.to_html(index=False, escape=False)
    for n in st.session_state.history:
        target = f'<td>{n}</td>'
        replacement = f'<td><span style="color:#ff4b4b; font-weight:bold;">{n}</span></td>' # 白背景用の赤から、黒背景で見やすい赤に調整
        df_html = df_html.replace(target, replacement)
    
    html_code = f"""
    <div style="height: {height}px; overflow-y: auto; border: 1px solid #444; margin-top: 5px; background: #111; color: #eee; border-radius: 5px;">
        <style>
            table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 16px; table-layout: fixed; color: #eee; }}
            th {{ position: sticky; top: 0; background: #262626; z-index: 5; border: 1px solid #444; padding: 8px; text-align: center; color: #fff; }}
            td {{ border: 1px solid #333; padding: 8px; text-align: center; background: #1a1a1a; pointer-events: none; }}
            /* スクロールバーのスタイル（webkit系） */
            div::-webkit-scrollbar {{ width: 8px; }}
            div::-webkit-scrollbar-track {{ background: #111; }}
            div::-webkit-scrollbar-thumb {{ background: #444; border-radius: 4px; }}
            div::-webkit-scrollbar-thumb:hover {{ background: #555; }}
        </style>
        {df_html}
    </div>
    """
    st.components.v1.html(html_code, height=height + 10)

# --- 5. UI設定 ---
# ページ設定をダークモードベースに
st.set_page_config(page_title="VR-1弾サーチ", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* ベース背景を黒に */
    .stApp {{ background-color: #0e1117; color: #fafafa; }}
    
    /* タイトル文字を白に */
    h1 {{ color: white !important; padding-bottom: 1rem; }}
    
    /* 共通ブロックの隙間調整 */
    [data-testid="stVerticalBlock"] {{ gap: 0.3rem !important; }}
    
    /* 履歴ボックスのスタイル（ダークモード用） */
    .history-box {{ background: #1a1d24; color: #fafafa; padding: 12px; border-radius: 8px; font-size: 16px; border-left: 5px solid #ff4b4b; margin-bottom: 10px; border-right: 1px solid #333; border-top: 1px solid #333; border-bottom: 1px solid #333;}}
    
    /* ボタンエリアの幅と並び設定 */
    div[data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0.5rem !important;
        width: 50% !important;
        min-width: 250px !important; /* 少し幅を持たせる */
        margin-top: 5px;
    }}
    [data-testid="column"] {{
        flex: 1 1 0% !important;
    }}
    /* Streamlit標準ボタンのダークモードカスタマイズ */
    .stButton > button {{
        width: 100% !important;
        height: 3rem !important;
        font-weight: bold !important;
        padding: 0 !important;
        background-color: #262730;
        color: white;
        border: 1px solid #444;
        transition: all 0.2s;
    }}
    .stButton > button:hover {{
        border-color: #ff4b4b;
        color: #ff4b4b;
        background-color: #1a1d24;
    }}
    .stButton > button:active {{
        background-color: #ff4b4b;
        color: white;
    }}
    
    /* 入力欄のスタイル調整 */
    [data-testid="stNumberInput"] label {{ color: #fafafa !important; }}
    [data-testid="stNumberInput"] div[req-cols="1"] div {{ background-color: #262730; color: white; border-color: #444; }}
    
    /* エクスパンダー（全配列表）のスタイル */
    [data-testid="stExpander"] {{ background-color: #1a1d24; border: 1px solid #333; border-radius: 8px; }}
    [data-testid="stExpander"] summary {{ color: white !important; }}
    [data-testid="stExpander"] summary:hover {{ color: #ff4b4b !important; }}

    /* タブのスタイル */
    div[data-testid="stTabs"] button {{ color: #aaa !important; }}
    div[data-testid="stTabs"] button[aria-selected="true"] {{ color: white !important; border-bottom-color: #ff4b4b !important; }}
    
    /* 区切り線 */
    hr {{ border-color: #333 !important; }}
    
    /* セレクトボックス */
    [data-testid="stSelectbox"] div[data-baseweb="select"] {{ background-color: #262730; border-color: #444; color: white; }}
    [data-testid="stSelectbox"] svg {{ fill: white; }}
    
    /* エラー・情報ボックス */
    [data-testid="stNotification"] {{ background-color: #1a1d24; color: white; border: 1px solid #333; }}
    </style>
    """, unsafe_allow_html=True)

st.title("VR-1弾配列サーチ")

if 'history' not in st.session_state: st.session_state.history = []
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

patterns = load_data()

# --- 履歴 ---
if st.session_state.history:
    # レアリティに応じた色付け（ダークモード用）
    hist_html = [f'<span style="color:{"#ffff00" if is_rare(n) else "#fafafa"}; font-weight:bold;">{n}</span>' for n in st.session_state.history]
    st.markdown(f'<div class="history-box">履歴: {" > ".join(hist_html)}</div>', unsafe_allow_html=True)

# --- 番号入力 ---
st.number_input("番号", min_value=1, max_value=110, value=None, placeholder="番号入力...", key=f"num_in_{st.session_state.reset_counter}", label_visibility="collapsed")

# --- ボタン列 ---
c1, c2 = st.columns(2)
with c1:
    if st.button("確定", use_container_width=True):
        input_key = f"num_in_{st.session_state.reset_counter}"
        input_val = st.session_state.get(input_key)
        if input_val is not None:
            st.session_state.history.append(int(input_val))
            # 入力値をクリアするためにカウンターをインクリメント
            st.session_state.reset_counter += 1
            st.rerun()
with c2:
    if st.button("消す", use_container_width=True):
        if st.session_state.history:
            st.session_state.history.pop()
            st.rerun()

st.divider()

# --- 6. 全配列表表示 ---
all_patterns_tab = st.expander("📊 全データ確認")
with all_patterns_tab:
    if patterns:
        p_names = list(patterns.keys())
        # セレクトボックスのラベルを非表示に
        sel_p = st.selectbox("配列選択", p_names, label_visibility="collapsed")
        target_d = patterns[sel_p]
        view_data = []
        for i in range(max(len(target_d['L']), len(target_d['R']))):
            l_v = target_d['L'][i] if i < len(target_d['L']) else None
            r_v = target_d['R'][i] if i < len(target_d['R']) else None
            def get_disp(v):
                if v is None: return ""
                rn = get_rarity(v)
                # LR/LLRは🌟マーク付きで表示
                return f"🌟 {rn}" if "LR" in rn or "LLR" in rn else str(v)
            view_data.append({"左": get_disp(l_v), "右": get_disp(r_v)})
        # pd.DataFrame(view_data) で表示するとStreamlit標準の表になるため、独自関数を使用
        render_custom_table(pd.DataFrame(view_data))
    else:
        st.info("データがありません。")

# --- 7. 解析結果表示 ---
if st.session_state.history and patterns:
    h = st.session_state.history
    has_rare = any(is_rare(n) for n in h)
    
    tab_res1, tab_res2 = st.tabs(["① 4枚一致探索", "② レア探索"])

    def render_result(tab_obj, active_req, color):
        with tab_obj:
            if not active_req:
                st.warning("枚数不足（レア探索はレアを含み2枚、一致探索は4枚以上必要）")
                return
            hits = []
            for name, data in patterns.items():
                res = find_matches(h, data["L"], data["R"])
                for ht in res: hits.append({**ht, "name": name})

            if hits:
                # とりあえず最初の候補を表示
                best = hits[0]; d = patterns[best['name']]
                nl = d['L'][best['lp']] if best['lp'] < len(d['L']) else "終了"
                nr = d['R'][best['rp']] if best['rp'] < len(d['R']) else "終了"
                
                # レア予測（近い順）
                future_rares = []
                for side in ["L", "R"]:
                    curr_pos = best['lp'] if side == "L" else best['rp']
                    track = d[side]
                    for i in range(curr_pos, len(track)):
                        val = track[i]
                        if is_target_rare(val):
                            future_rares.append({"dist": i - curr_pos + 1, "name": get_rarity(val)})
                
                future_rares = sorted(future_rares, key=lambda x: x['dist'])
                # ダークモード用に見やすい色（黄色）でレア予測を表示
                future_texts = [f"💎 <span style='color:#ffff00;'>{r['dist']}枚先</span>: {r['name']}" for r in future_rares]
                rare_predict_html = "<br>".join(future_texts) if future_texts else "なし"

                # 特定結果のボックス（ダークモード用）
                st.markdown(f"""
                    <div style="border: 3px solid {color}; padding: 15px; border-radius: 10px; text-align: center; background: #1a1d24; margin-bottom: 15px; border-right: 1px solid #333; border-top: 1px solid #333; border-bottom: 1px solid #333;">
                        <div style="color: {color}; font-weight: bold; font-size: 20px;">{best['name']} 特定</div>
                        <div style="display: flex; justify-content: space-around; margin-top: 10px; border-bottom: 1px solid #333; padding-bottom: 15px;">
                            <div><div style="color:#aaa; font-size:12px;">左・次</div><div style="font-size:32px; font-weight:bold; color:#ff4b4b;">{nl}</div><div style="font-size:12px; color:#eee;">{get_rarity(nl)}</div></div>
                            <div><div style="color:#aaa; font-size:12px;">右・次</div><div style="font-size:32px; font-weight:bold; color:#ff4b4b;">{nr}</div><div style="font-size:12px; color:#eee;">{get_rarity(nr)}</div></div>
                        </div>
                        <div style="margin-top: 15px; text-align: left; font-size: 14px; color: #eee; line-height: 1.6;">
                            <strong>🔜 以降のLR/LLR予測:</strong><br>
                            {rare_predict_html}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                st.write("### 🔍 配列の続き")
                start_l, start_r = best['orig_lp'], best['orig_rp']
                
                # 最後のレアが出るまでの範囲を表示
                rare_indices_l = [i for i, v in enumerate(d['L']) if is_rare(v)]
                rare_indices_r = [i for i, v in enumerate(d['R']) if is_rare(v)]
                max_pos_l = max(rare_indices_l) if rare_indices_l else best['lp']
                max_pos_r = max(rare_indices_r) if rare_indices_r else best['rp']
                last_rare_dist = max(max_pos_l - start_l, max_pos_r - start_r)
                # 最低でも10枚、最大でもレアが出るまで表示（適宜調整）
                display_range = max(10, last_rare_dist + 1)
                # 念のため配列長を超えないように
                display_range = min(display_range, len(d['L']) - start_l, len(d['R']) - start_r)

                detail_data = []
                for i in range(display_range):
                    idx_l, idx_r = start_l + i, start_r + i
                    l_v = d['L'][idx_l] if idx_l < len(d['L']) else None
                    r_v = d['R'][idx_r] if idx_r < len(d['R']) else None
                    def get_detail_disp(v):
                        if v is None: return ""
                        rn = get_rarity(v)
                        # LR/LLRは🌟マーク付きで表示
                        return f"🌟 {rn}" if "LR" in rn or "LLR" in rn else str(v)
                    detail_data.append({
                        "枚数": "現在" if idx_l < best['lp'] and idx_r < best['rp'] else f"{max(0, idx_l - best['lp'] + 1, idx_r - best['rp'] + 1)}枚先",
                        "左": get_detail_disp(l_v), "右": get_detail_disp(r_v)
                    })
                render_custom_table(pd.DataFrame(detail_data), height=400)
            else:
                # 他の配列も探索（もしfind_matchesを複数返すように変更した場合用）
                hit_names = sorted(list(set([ht['name'] for ht in hits])))
                if hit_names:
                     st.info(f"候補配列: {', '.join(hit_names)}")
                else:
                     st.error("一致する配列が見つかりません。入力ミスか、csvデータ外の可能性があります。")

    # 色の調整（ダークモード用に見やすい青と赤）
    render_result(tab_res1, (len(h)>=4), "#60b4ff") # 一致探索用（青）
    render_result(tab_res2, (has_rare and len(h)>=2), "#ff4b4b") # レア探索用（赤）
else:
    # 履歴がないか、データ読み込み失敗時
    if patterns:
        st.info("番号を入力し「確定」を押してください（レアを含み2枚、または4枚以上入力で解析開始）")
