import streamlit as st
import yfinance as yf
import pandas as pd

# ページ設定（スマホで見やすいようワイドレイアウト＆タイトル設定）
st.set_page_config(page_title="高配当株チェッカー PRO", layout="centered", initial_sidebar_state="collapsed")

st.title("📈 高配当株チェッカー PRO")
st.caption("東証全銘柄・リアルタイム対応（Yahoo Finance連携）")

# --- 検索条件入力エリア ---
with st.form(key='search_form'):
    st.subheader("🔍 スクリーニング条件")
    
    symbol_input = st.text_input("銘柄コード（例: 8306, 8058, 9432 などカンマ区切りで複数可 / 空白で主要高配当株全検索）", value="")
    
    min_yield = st.selectbox(
        "最低予想配当利回り", 
        [0.0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0], 
        index=3, 
        format_func=lambda x: "指定なし" if x == 0 else f"{x}% 以上"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        max_per = st.selectbox("PER (割安度)", [999.0, 15.0, 12.0, 10.0], format_func=lambda x: "指定なし" if x == 999 else f"{x}倍 以下")
    with col2:
        max_pbr = st.selectbox("PBR (解散価値)", [999.0, 1.5, 1.0, 0.8], format_func=lambda x: "指定なし" if x == 999 else f"{x}倍 以下")
        
    submit_button = st.form_submit_button(label='🔍 この条件でリアルタイム検索する')

# 代表的な主要高配当銘柄（銘柄コード指定がない場合の基本リスト）
DEFAULT_CODES = [
    "8306.T", "8316.T", "8411.T", "8058.T", "8031.T", "8001.T", "8002.T",
    "9432.T", "9433.T", "9434.T", "2914.T", "8591.T", "5401.T", "1605.T",
    "6301.T", "7203.T", "5020.T", "9101.T", "9104.T", "8766.T"
]

@st.cache_data(ttl=300) # 5分キャッシュ（連続アクセス制限回避のため）
def get_stock_data(codes):
    data_list = []
    for code in codes:
        try:
            ticker = yf.Ticker(code)
            info = ticker.info
            
            # 株価・指標取得
            price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            dividend_yield = (info.get('dividendYield') or 0) * 100
            per = info.get('trailingPE') or 0
            pbr = info.get('priceToBook') or 0
            name = info.get('shortName') or info.get('longName') or code
            sector = info.get('sector') or '不明'
            payout = (info.get('payoutRatio') or 0) * 100
            dividend_rate = info.get('dividendRate') or 0
            roe = (info.get('returnOnEquity') or 0) * 100
            
            data_list.append({
                "コード": code.replace(".T", ""),
                "銘柄名": name,
                "セクター": sector,
                "株価": price,
                "配当利回り(%)": round(dividend_yield, 2),
                "PER": round(per, 2),
                "PBR": round(pbr, 2),
                "配当性向(%)": round(payout, 1),
                "1株配当(円)": dividend_rate,
                "ROE(%)": round(roe, 1),
                "raw_info": info
            })
        except Exception as e:
            continue
    return pd.DataFrame(data_list)

# 検索実行時
if submit_button or 'first_run' not in st.session_state:
    st.session_state['first_run'] = True
    
    # 対象銘柄コードのリスト作成
    if symbol_input.strip():
        raw_codes = [c.strip() for c in symbol_input.split(",") if c.strip()]
        target_codes = [f"{c}.T" if not c.endswith(".T") else c for c in raw_codes]
    else:
        target_codes = DEFAULT_CODES

    with st.spinner('東証から最新株価・財務データをリアルタイム取得中...'):
        df = get_stock_data(target_codes)

    if not df.empty:
        # スクリーニング条件の適用
        filtered_df = df[
            (df['配当利回り(%)'] >= min_yield) &
            (df['PER'] <= max_per) &
            (df['PBR'] <= max_pbr)
        ]
        
        st.success(f"検索結果: {len(filtered_df)} 件見つかりました")

        # 銘柄一覧表示
        for idx, row in filtered_df.iterrows():
            with st.expander(f"【{row['コード']}】{row['銘柄名']} | 利回り: {row['配当利回り(%)']}% (株価: ¥{row['株価']:,})"):
                st.markdown(f"**セクター:** {row['セクター']}")
                
                # 主要指標グリッド
                c1, c2, c3 = st.columns(3)
                c1.metric("配当利回り", f"{row['配当利回り(%)']}%")
                c2.metric("PER", f"{row['PER']}倍")
                c3.metric("PBR", f"{row['PBR']}倍")
                
                st.divider()
                st.markdown("##### 📌 高配当詳細・安全度情報")
                
                d1, d2 = st.columns(2)
                with d1:
                    st.write(f"・**1株あたり年間配当:** ¥{row['1株配当(円)']}")
                    st.write(f"・**配当性向:** {row['配当性向(%)']}%")
                with d2:
                    st.write(f"・**ROE (稼ぐ力):** {row['ROE(%)']}%")
                    st.write(f"・**権利確定月:** 3月/9月 (※銘柄決算期による)")
                
                # 詳細データリンク
                st.caption("※配当履歴や増配方針の詳細はIR情報またはYahoo Financeで確認できます")
    else:
        st.warning("指定された銘柄または条件に該当するデータが見つかりませんでした。")
