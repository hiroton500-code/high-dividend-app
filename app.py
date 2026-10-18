import streamlit as st
import yfinance as yf
import pandas as pd

# ページ基本設定
st.set_page_config(
    page_title="高配当株チェッカー PRO",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# モダンUIカスタムCSS
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .header-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    
    div.stButton > button {
        width: 100% !important;
        background: white !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 16px !important;
        text-align: left !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03) !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button:hover {
        border-color: #0284c7 !important;
        background-color: #f0f9ff !important;
        transform: translateY(-1px);
    }
    
    .search-btn div.stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        text-align: center !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 検索対象とする主要・高配当・有名日本株のマスター辞書（コードと日本語名・セクター）
JP_STOCK_MASTER = {
    "8306": {"name": "三菱UFJフィナンシャル・グループ", "sector": "銀行業"},
    "8316": {"name": "三井住友フィナンシャルグループ", "sector": "銀行業"},
    "8411": {"name": "みずほフィナンシャルグループ", "sector": "銀行業"},
    "8058": {"name": "三菱商事", "sector": "卸売業"},
    "8031": {"name": "三井物産", "sector": "卸売業"},
    "8001": {"name": "伊藤忠商事", "sector": "卸売業"},
    "8002": {"name": "丸紅", "sector": "卸売業"},
    "8015": {"name": "豊田通商", "sector": "卸売業"},
    "9432": {"name": "NTT（日本電信電話）", "sector": "情報・通信"},
    "9433": {"name": "KDDI", "sector": "情報・通信"},
    "9434": {"name": "ソフトバンク", "sector": "情報・通信"},
    "2914": {"name": "JT（日本たばこ産業）", "sector": "食料品"},
    "8591": {"name": "オリックス", "sector": "その他金融"},
    "5401": {"name": "日本製鉄", "sector": "鉄鋼"},
    "5411": {"name": "JFEホールディングス", "sector": "鉄鋼"},
    "1605": {"name": "INPEX", "sector": "鉱業"},
    "6301": {"name": "コマツ", "sector": "機械"},
    "7203": {"name": "トヨタ自動車", "sector": "輸送用機器"},
    "5020": {"name": "ENEOSホールディングス", "sector": "石油・石炭"},
    "9101": {"name": "日本郵船", "sector": "海運業"},
    "9104": {"name": "商船三井", "sector": "海運業"},
    "8766": {"name": "東京海上ホールディングス", "sector": "保険業"},
    "8801": {"name": "三井不動産", "sector": "不動産業"},
    "6758": {"name": "ソニーグループ", "sector": "電気機器"},
    "7974": {"name": "任天堂", "sector": "その他製品"},
    "9984": {"name": "ソフトバンクグループ", "sector": "情報・通信"}
}

st.markdown("""
<div class="header-card">
    <h2 style="margin:0; font-size:1.4rem; color:#ffffff;">高配当株チェッカー PRO</h2>
    <div style="font-size:0.8rem; color:#94a3b8; margin-top:4px;">会社名・銘柄コード対応リアルタイム検索</div>
</div>
""", unsafe_allow_html=True)

# 検索フォーム
with st.form(key='search_form'):
    query_input = st.text_input(
        "会社名または銘柄コードで検索", 
        placeholder="例: トヨタ, 三菱商事, 8306, ソニー (空白で全件表示)"
    )
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        min_yield = st.selectbox("最低利回り", [0.0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0], index=3, format_func=lambda x: "全利回り" if x == 0 else f"{x}%~")
    with col_b:
        max_per = st.selectbox("PER上限", [999.0, 15.0, 12.0, 10.0], format_func=lambda x: "制限なし" if x == 999 else f"{x}倍以下")
    with col_c:
        max_pbr = st.selectbox("PBR上限", [999.0, 1.5, 1.0, 0.8], format_func=lambda x: "制限なし" if x == 999 else f"{x}倍以下")
        
    st.markdown('<div class="search-btn">', unsafe_allow_html=True)
    submit_button = st.form_submit_button(label='🔍 検索する')
    st.markdown('</div>', unsafe_allow_html=True)

# 株価データ取得関数（会社名・コードの部分一致対応）
@st.cache_data(ttl=300)
def get_stock_data(search_query):
    # 検索キーワードに一致するコードを抽出
    target_codes = []
    q = search_query.strip().lower()
    
    for code, info in JP_STOCK_MASTER.items():
        if not q or q in code.lower() or q in info["name"].lower() or q in info["sector"].lower():
            target_codes.append(f"{code}.T")
            
    # もし4桁の数字が直接入力され、マスターに無い場合は動的に追加検索
    if len(q) == 4 and q.isdigit() and f"{q}.T" not in target_codes:
        target_codes.append(f"{q}.T")
        
    # キーワードが空の場合は主要全銘柄を対象にする
    if not q and not target_codes:
        target_codes = [f"{code}.T" for code in JP_STOCK_MASTER.keys()]

    data_list = []
    for code in target_codes:
        try:
            raw_code = code.replace(".T", "")
            ticker = yf.Ticker(code)
            info = ticker.info
            
            # マスターから日本語名を取得、無ければAPIから取得
            if raw_code in JP_STOCK_MASTER:
                name = JP_STOCK_MASTER[raw_code]["name"]
                sector = JP_STOCK_MASTER[raw_code]["sector"]
            else:
                name = info.get('shortName') or info.get('longName') or f"銘柄 {raw_code}"
                sector = info.get('sector') or "その他セクター"

            price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            
            raw_yield = info.get('dividendYield') or 0
            dividend_yield = raw_yield if raw_yield > 1.0 else raw_yield * 100
                
            per = info.get('trailingPE') or 0
            pbr = info.get('priceToBook') or 0
            
            raw_payout = info.get('payoutRatio') or 0
            payout = raw_payout * 100 if raw_payout <= 1.0 else raw_payout
            
            dividend_rate = info.get('dividendRate') or 0
            roe = (info.get('returnOnEquity') or 0) * 100
            
            data_list.append({
                "コード": raw_code,
                "銘柄名": name,
                "セクター": sector,
                "株価": price,
                "利回り": round(dividend_yield, 2),
                "PER": round(per, 2),
                "PBR": round(pbr, 2),
                "配当性向": round(payout, 1),
                "1株配当": dividend_rate,
                "ROE": round(roe, 1)
            })
        except Exception:
            continue
            
    return pd.DataFrame(data_list)

# 詳細ダイアログ表示機能
@st.dialog("銘柄詳細・高配当分析")
def show_detail_dialog(row):
    st.subheader(f"【{row['コード']}】{row['銘柄名']}")
    st.caption(f"セクター: {row['セクター']}")
    
    st.divider()
    
    m1, m2 = st.columns(2)
    m1.metric("現在株価", f"¥{row['株価']:,}")
    m2.metric("予想配当利回り", f"{row['利回り']}%")
    
    st.write("---")
    st.markdown("##### 📌 高配当指標")
    c1, c2 = st.columns(2)
    c1.write(f"・**PER (割安度):** {row['PER']}倍")
    c1.write(f"・**PBR (解散価値):** {row['PBR']}倍")
    c2.write(f"・**1株あたり配当:** ¥{row['1株配当']}")
    c2.write(f"・**配当性向:** {row['配当性向']}%")
    c2.write(f"・**ROE (稼ぐ力):** {row['ROE']}%")
    
    st.caption("※権利確定月: 通常3月/9月（主決算期による）")

# 検索実行
if submit_button or 'first_run' not in st.session_state:
    st.session_state['first_run'] = True

    with st.spinner('会社名・リアルタイム株価データを検索中...'):
        df = get_stock_data(query_input)

    if not df.empty:
        filtered_df = df[
            (df['利回り'] >= min_yield) &
            (df['PER'] <= max_per) &
            (df['PBR'] <= max_pbr)
        ]
        
        st.markdown(f"**該当件数: {len(filtered_df)} 件** （銘柄をタップで詳細表示）")

        for idx, row in filtered_df.iterrows():
            btn_label = f"【{row['コード']}】 {row['銘柄名']}  |  ¥{row['株価']:,}  |  利回り: {row['利回り']}%"
            if st.button(btn_label, key=f"btn_{row['コード']}_{idx}"):
                show_detail_dialog(row)
    else:
        st.warning("一致する会社名や条件の銘柄が見つかりませんでした。別のキーワードでお試しください。")
