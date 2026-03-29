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

# --- 3. 核心：三段階・物理制約探索アルゴリズム ---
def professional_search(history, L, R, mode="STRICT"):
    """
    mode "STRICT": 厳密一致
    mode "FLEX": 4,7,9の読み替えを許容
    """
    h_len = len(history)
    results = []
    
    def match_score(a, b):
        if a == b: return True
        if mode == "FLEX":
            sets = [{4, 7, 9, 14, 17, 19, 24, 27, 29, 34, 37, 39, 44, 47, 49}] # 4,7,9系
            for s in sets:
                if a in s and b in s: return True
        return False

    # 1枚目をLかRから探す
    for side in ["L", "R"]:
        main_list = L if side == "L" else R
        sub_list = R if side == "L" else L
        
        for p in range(len(main_list)):
            if match_score(history[0], main_list[p]):
                # 1枚目発見。ここを起点に「履歴全体」が左右±12枚に収まるか検証
                # memo化再帰で全パターンの最小エラーを探す
                memo = {}
                def verify(h_idx, m_pos, s_pos):
                    state = (h_idx, m_pos, s_pos)
                    if state in memo: return memo[state]
                    if h_idx == h_len: return 0, m_pos, s_pos
                    
                    res = (999, 0, 0)
                    # メイン側から出た場合
                    if m_pos < len(main_list) and match_score(history[h_idx], main_list[m_pos]):
                        err, final_m, final_s = verify(h_idx + 1, m_pos + 1, s_pos)
                        if err < res[0]: res = (err, final_m, final_s)
                    
                    # サブ(隣)側から出た場合（メイン開始位置の前後12枚以内という制約）
                    if s_pos < len(sub_list) and abs(s_pos - p) <= 12:
                        if match_score(history[h_idx], sub_list[s_pos]):
                            err, final_m, final_s = verify(h_idx + 1, m_pos, s_pos + 1)
                            if err < res[0]: res = (err, final_m, final_s)
                    
                    memo[state] = res
                    return res

                error, end_m, end_s = verify(1, p + 1, 0) # 2枚目から検証開始
                # サブ側の初期位置(s_pos)はメインのp周辺12枚から自動探索される
                # ここでは初期s_posを全パターン試す必要があるためループ
                for start_s in range(max(0, p-12), min(len(sub_list), p+13)):
                    error, end_m, end_s = verify(1, p + 1, start_s)
                    if error == 0:
                        results.append({
                            "lp": end_m if side=="L" else end_s,
                            "rp": end_s if side=="L" else end_m,
                            "trust": 100
                        })
    return results

# --- 4. メインUI ---
st.set_page_config(page_title="プロ仕様配列スキャン", layout="centered")
st.title("🎯 配列特定アルゴリズム")

if 'history' not in st.session_state: st.session_state.history = []
patterns = load_data()

with st.form("in"):
    num = st.number_input("番号入力", min_value=1, max_value=110, step=1)
    if st.form_submit_button("追加"): st.session_state.history.append(num); st.rerun()

if st.button("リセット"): st.session_state.history = []; st.rerun()

st.write(f"**履歴:** {st.session_state.history}")

if st.session_state.history and patterns:
    h = st.session_state.history
    has_rare = any(is_rare(n) for n in h)
    found_any = []

    # ステップ1 & 2: 厳密検索
    if (has_rare and len(h) >= 2) or (not has_rare and len(h) >= 3):
        for name, data in patterns.items():
            hits = professional_search(h, data["L"], data["R"], mode="STRICT")
            for hit in hits:
                hit["name"] = name
                found_any.append(hit)

    # ステップ3: 柔軟検索 (配列表ミス考慮)
    if not found_any:
        st.warning("厳密一致なし。配列表ミス(4,7,9)を考慮して再検索します...")
        for name, data in patterns.items():
            hits = professional_search(h, data["L"], data["R"], mode="FLEX")
            for hit in hits:
                hit["name"] = name
                hit["trust"] = 70 # 読み替えが発生しているため信頼度を下げる
                found_any.append(hit)

    if found_any:
        # 重複を消して上位2つ
        unique_results = []
        seen = set()
        for f in found_any:
            k = (f['name'], f['lp'], f['rp'])
            if k not in seen:
                unique_results.append(f); seen.add(k)
        
        for idx, res in enumerate(unique_results[:2]):
            st.subheader(f"{'🥇' if idx==0 else '🥈'} {res['name']} (信頼度: {res['trust']}%)")
            data = patterns[res['name']]
            nl = data['L'][res['lp']] if res['lp'] < len(data['L']) else "END"
            nr = data['R'][res['rp']] if res['rp'] < len(data['R']) else "END"
            
            c1, c2 = st.columns(2)
            c1.success(f"**左 次予測**\n# {nl}\n({get_rarity(nl)})")
            c2.info(f"**右 次予測**\n# {nr}\n({get_rarity(nr)})")
            
            # LRまでの距離
            def get_dist(lst, p):
                for i in range(p, len(lst)):
                    if "LR" in get_rarity(lst[i]): return i-p, lst[i]
                return None, None
            dl, vl = get_dist(data['L'], res['lp'])
            dr, vr = get_dist(data['R'], res['rp'])
            st.write(f"💎 **LRまで**: 左 {f'{dl}枚({vl})' if dl is not None else 'なし'} / 右 {f'{dr}枚({vr})' if dr is not None else 'なし'}")
    else:
        st.error("エラー：条件に一致する配列が見つかりません。")
