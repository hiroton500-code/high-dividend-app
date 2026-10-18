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
    /* 全体背景とフォント設定 */
    .main { background-color: #f8fafc; }
    h1, h2, h3 { font-weight: 800 !important; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* ヘッダーカード */
    .header-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 24px 20px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
        margin-bottom: 24px;
    }
    
    /* メトリクスカードのスタイル拡張 */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-weight: 800 !important;
        color: #0284c7 !important;
    }
    
    /* ボタンのモダンスタイル */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(2, 132, 199, 0.4);
    }
    
    /* タグバッジ */
    .badge-green { background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 20px; font-weight: 700; font-size: 0.75rem; }
    .badge-blue { background-color: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 20px; font-weight: 700; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# 日本語名・セクター完全変換マスター辞書
JP_NAME_MAP = {
    "8306": {"name": "三菱UFJフィナンシャル・グループ", "sector": "銀行業", "consecutive": "4年増配", "progressive": "累進配当宣言"},
    "8316": {"name": "三井住友フィナンシャルグループ", "sector": "銀行業", "consecutive": "5年増配", "progressive": "累進配当宣言"},
    "8411": {"name": "みずほフィナンシャルグループ", "sector": "銀行業", "consecutive": "3年増配", "progressive": "累進配当方針"},
    "8058": {"name": "三菱商事", "sector": "卸売業（総合商社）", "consecutive": "8年増配", "progressive": "累進配当宣言"},
    "8031": {"name": "三井物産", "sector": "卸売業（総合商社）", "consecutive": "6年増配", "progressive": "累進配当宣言"},
    "8001": {"name": "伊藤忠商事", "sector": "卸売業（総合商社）", "consecutive": "11年増配", "progressive": "累進配当宣言"},
    "8002": {"name": "丸紅", "sector": "卸売業（総合商社）", "consecutive": "4年増配", "progressive": "累進配当宣言"},
    "9432": {"name": "NTT（日本電信電話）", "sector": "情報・通信", "consecutive": "13年連続増配", "progressive": "継続増配"},
    "9433": {"name": "KDDI", "sector": "情報・通信", "consecutive": "22年連続増配", "progressive": "累進配当宣言"},
    "9434": {"name": "ソフトバンク", "sector": "情報・通信", "consecutive": "5年増配", "progressive": "高配当維持"},
    "2914": {"name": "JT（日本たばこ産業）", "sector": "食料品", "consecutive": "3年増配", "progressive": "配当性向70%目安"},
    "8591": {"name": "オリックス", "sector": "その他金融", "consecutive": "3年増配", "progressive": "配当性向33%以上"},
    "5401": {"name": "日本製鉄", "sector": "鉄鋼", "consecutive": "業績連動", "progressive": "業績連動配当"},
    "1605": {"name": "INPEX", "sector": "鉱業（エネルギー）", "consecutive": "3年増配", "progressive": "下限配当設定あり"},
    "6301": {"name": "コマツ", "sector": "機械", "consecutive": "4年増配", "progressive": "配当性向40%以上"},
    "7203": {"name": "トヨタ自動車", "sector": "輸送用機器", "consecutive": "3年増配", "progressive": "安定配当継続"},
    "5020": {"name": "ENEOSホールディングス", "sector": "石油・石炭", "consecutive": "2年増配", "progressive": "下限配当設定あり"},
    "9101": {"name": "日本郵船", "sector": "海運業", "consecutive": "業績連動", "progressive": "業績連動・下限あり"},
    "9104": {"name": "商船三井", "sector": "海運業", "consecutive": "業績連動", "progressive": "配当性向30%目安"},
    "8766": {"name": "東京海上ホールディングス", "sector": "保険業", "consecutive": "12年増配", "progressive": "累進配当宣言"}
}

# ヘッダー描画
st.markdown("""
<div class="header-card">
    <div style="font-size:0.85rem; color:#38bdf8; font-weight:700; letter-spacing:1px; margin-bottom:4px;">REALTIME DIVIDEND SCREENER</div>
    <h1 style="font-size:1.6rem; margin:0; color:#ffffff;">高配当株チェッカー PRO</h1>
    <div style="font-size:0.8rem; color:#94a3b8; margin-top:6px;">東証全銘柄・リアルタイム財務データ対応</div>
</div>
""", unsafe_allow_html=True)

# --- 検索フォームエリア ---
with st.form(key='search_form'):
    st.subheader("🔍 スクリーニング条件")
    
    symbol_input = st.text_input(
        "銘柄コード（例: 8306, 8058, 9432 などカンマ区切りで指定可能 / 空白で全件表示）", 
        value=""
    )
    
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
        
    submit_button = st.form_submit_button(label='⚡ リアルタイム条件検索を実行')

DEFAULT_CODES = [f"{k}.T" for k in JP_NAME_MAP.keys()]

@st.cache_data(ttl=300)
def get_stock_data(codes):
    data_list = []
    for code in codes:
        try:
            raw_code = code.replace(".T", "")
            ticker = yf.Ticker(code)
            info = ticker.info
            
            # 日本語名・セクターの変換
            if raw_code in JP_NAME_MAP:
                jp_info = JP_NAME_MAP[raw_code]
                name = jp_info["name"]
                sector = jp_info["sector"]
                consecutive = jp_info["consecutive"]
                progressive = jp_info["progressive"]
            else:
                name = info.get('shortName') or info.get('longName') or f"銘柄コード {raw_code}"
                sector = info.get('sector') or "その他セクター"
                consecutive = "データあり"
                progressive = "方針確認中"

            price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            dividend_yield = (info.get('dividendYield') or 0) * 100
            per = info.get('trailingPE') or 0
            pbr = info.get('priceToBook') or 0
            payout = (info.get('payoutRatio') or 0) * 100
            dividend_rate = info.get('dividendRate') or 0
            roe = (info.get('returnOnEquity') or 0) * 100
            
            data_list.append({
                "コード": raw_code,
                "銘柄名": name,
                "セクター": sector,
                "株価": price,
                "配当利回り(%)": round(dividend_yield, 2),
                "PER": round(per, 2),
                "PBR": round(pbr, 2),
                "配当性向(%)": round(payout, 1),
                "1株配当(円)": dividend_rate,
                "ROE(%)": round(roe, 1),
                "連続増配": consecutive,
                "累進配当": progressive
            })
        except Exception:
            continue
    return pd.DataFrame(data_list)

# 検索結果の表示
if submit_button or 'first_run' not in st.session_state:
    st.session_state['first_run'] = True
    
    if symbol_input.strip():
        raw_codes = [c.strip() for c in symbol_input.split(",") if c.strip()]
        target_codes = [f"{c}.T" if not c.endswith(".T") else c for c in raw_codes]
    else:
        target_codes = DEFAULT_CODES

    with st.spinner('Yahoo Financeからリアルタイムデータを取得中...'):
        df = get_stock_data(target_codes)

    if not df.empty:
        filtered_df = df[
            (df['配当利回り(%)'] >= min_yield) &
            (df['PER'] <= max_per) &
            (df['PBR'] <= max_pbr)
        ]
        
        st.markdown(f"### 該当結果: **{len(filtered_df)}** 件")

        for idx, row in filtered_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background:white; padding:16px; border-radius:16px; border:1px solid #e2e8f0; margin-bottom:12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <span class="badge-blue">{row['コード']}</span>
                            <h3 style="margin:4px 0 2px 0; font-size:1.1rem; color:#0f172a;">{row['銘柄名']}</h3>
                            <div style="font-size:0.75rem; color:#64748b;">{row['セクター']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.2rem; font-weight:800; color:#0f172a;">¥{row['株価']:,}</div>
                            <span class="badge-green">利回り {row['配当利回り(%)']}%</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📊 【{row['銘柄名']}】の詳細分析・高配当指標を見る"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("予想配当利回り", f"{row['配当利回り(%)']}%")
                    c2.metric("PER (割安度)", f"{row['PER']}倍")
                    c3.metric("PBR (資産価値)", f"{row['PBR']}倍")
                    
                    st.divider()
                    st.markdown("##### 📌 高配当投資の核心チェック")
                    
                    d1, d2 = st.columns(2)
                    with d1:
                        st.write(f"・**1株あたり年間配当:** ¥{row['1株配当(円)']}")
                        st.write(f"・**配当性向:** {row['配当性向(%)']}%")
                        st.write(f"・**増配傾向:** {row['連続増配']}")
                    with d2:
                        st.write(f"・**ROE (稼ぐ力):** {row['ROE(%)']}%")
                        st.write(f"・**配当方針:** {row['累進配当']}")
                        st.write(f"・**権利確定月:** 3月 / 9月 (主決算期)")
    else:
        st.warning("条件に該当する銘柄が見つかりませんでした。条件を緩和してお試しください。")
