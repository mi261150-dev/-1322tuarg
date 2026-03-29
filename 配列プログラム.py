import streamlit as st
import pandas as pd

# レアリティ判定
def get_rarity(n):
    if not n: return ""
    try:
        n = int(n)
        if n == 101: return "LRパラレル"
        if n == 100: return "SRパラレル"
        if n == 99:  return "ランダムLR"
        if n == 98:  return "ランダムSR"
        if n in [7, 26, 61]: return "LLR"
        if n in [1, 16, 18, 27, 36, 48, 55, 58]: return "LR"
        if n in [5, 20, 24, 25, 31, 33, 38, 40, 42, 46, 52, 63]: return "SR"
        if 64 <= n <= 77: return "CP"
        return "N"
    except: return "不明"

# 読み込み（エラー対策版）
@st.cache_data
def load_data():
    # ヘッダーなしで読み込み、手動で列を指定
    try:
        df = pd.read_csv("配列.csv", header=None)
    except:
        st.error("配列.csvが見つかりません。ファイル名を確認してください。")
        return {}
    
    patterns = {}
    for i in range(6):
        name = f"配列{i+1}"
        # CSVの構造に合わせて列位置を計算 (配列1=1,2列 / 配列2=5,6列 / 配列3=9,10列...)
        start_col = i * 4
        
        try:
            # 1行目はタイトルなので2行目(index: 1)以降を取得
            l_raw = df.iloc[1:, start_col + 1]
            r_raw = df.iloc[1:, start_col + 2]
            
            # 数字以外(文字や空欄)を無視して整数に変換
            l = pd.to_numeric(l_raw, errors='coerce').dropna().astype(int).tolist()
            r = pd.to_numeric(r_raw, errors='coerce').dropna().astype(int).tolist()
            
            if l or r:
                patterns[name] = {"L": l, "R": r}
        except:
            continue
    return patterns

# 判定ロジック
def solve(h, L, R):
    if not h: return
