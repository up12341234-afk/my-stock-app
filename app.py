import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import timedelta
import FinanceDataReader as fdr
import json
import os

# ─────────────────────────────────────────────
# 1. 페이지 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="나의 주식 분석기", layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────
# 2. 트레이딩뷰 스타일 전역 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── 흰색 라이트 테마: 전체 텍스트 가시성 강제 적용 ── */

/* 전체 배경 및 기본 글씨색 */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="block-container"],
.main, .block-container {
    background-color: #ffffff !important;
    color: #131722 !important;
    font-family: 'Trebuchet MS', 'Inter', sans-serif;
}

/* Streamlit 내부 모든 p, span, div 글씨를 어둡게 강제 */
p, span, div, label, h1, h2, h3, h4, h5, h6, li {
    color: #131722 !important;
}

/* 헤더/툴바 숨김 */
[data-testid="stToolbar"], header, [data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
    visibility: hidden !important; display: none !important;
}

/* 사이드바 */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div { background-color: #f8f9fa !important; }

/* selectbox 드롭다운 배경 및 글씨 */
[data-testid="stSelectbox"] label { color: #787b86 !important; font-size: 0.82em !important; }
[data-testid="stSelectbox"] > div > div {
    background-color: #ffffff !important;
    color: #131722 !important;
    border: 1px solid #e0e3eb !important;
}
[data-testid="stSelectbox"] svg { fill: #131722 !important; }

/* 라디오 버튼 */
[data-testid="stRadio"] label {
    background-color: #f8f9fa !important; border: 1px solid #e0e3eb !important;
    border-radius: 6px !important; padding: 4px 14px !important;
    color: #5d606b !important; font-weight: 600; transition: all 0.15s;
    font-size: 0.88em !important;
}
[data-testid="stRadio"] label:hover { border-color: #2196f3 !important; color: #2196f3 !important; }
[data-testid="stRadio"] > label { color: #787b86 !important; font-size: 0.8em !important; }

/* 체크박스 */
[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] p { color: #131722 !important; }

/* 메트릭 카드 */
[data-testid="metric-container"] {
    background-color: #f8f9fa !important; border: 1px solid #e0e3eb !important;
    border-radius: 8px; padding: 12px 16px;
}
[data-testid="stMetricLabel"] p { color: #787b86 !important; font-size: 0.78em !important; }
[data-testid="stMetricValue"]  { color: #131722 !important; font-size: 1.2em !important; font-weight: 700; }
[data-testid="stMetricDelta"]  { font-size: 0.82em !important; }

/* 탭 */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 2px solid #e0e3eb !important; background: #ffffff;
}
[data-testid="stTabs"] [role="tab"] {
    background: transparent !important; color: #787b86 !important;
    border: none !important; font-weight: 600; font-size: 1em; padding: 10px 24px !important;
}
[data-testid="stTabs"] [role="tab"] p { color: #787b86 !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"],
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p {
    color: #2196f3 !important; border-bottom: 2px solid #2196f3 !important;
}

/* 버튼 */
[data-testid="stButton"] > button {
    background-color: #f8f9fa !important; color: #131722 !important;
    border: 1px solid #e0e3eb !important; border-radius: 6px !important;
    font-weight: 600; transition: all 0.15s; font-size: 0.85em !important;
}
[data-testid="stButton"] > button p { color: #131722 !important; }
[data-testid="stButton"] > button:hover { background-color: #e8f0fe !important; border-color: #2196f3 !important; }
[data-testid="stButton"] > button:hover p { color: #2196f3 !important; }
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stButton"] > button[kind="primary"] p {
    background-color: #2196f3 !important; border-color: #2196f3 !important; color: #fff !important;
}

/* 스피너, 알림 */
[data-testid="stSpinner"]   p { color: #787b86 !important; }
[data-testid="stAlert"]       { background-color: #f8f9fa !important; border-color: #e0e3eb !important; }
[data-testid="stAlert"]     p { color: #131722 !important; }

/* 구분선 */
hr { border-color: #e0e3eb !important; }

/* dataframe */
[data-testid="stDataFrame"] { border: 1px solid #e0e3eb; border-radius: 8px; }

/* Markdown 내 모든 텍스트 */
[data-testid="stMarkdown"] p,
[data-testid="stMarkdown"] span,
[data-testid="stMarkdown"] li { color: #131722 !important; }
</style>
""", unsafe_allow_html=True)

WATCHLIST_FILE = "watchlist.json"

# ─────────────────────────────────────────────
# 3. 관심목록 로드/저장
# ─────────────────────────────────────────────
def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_watchlist(wl):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(wl, f, ensure_ascii=False)

# ─────────────────────────────────────────────
# 4. 캐시된 데이터 함수들
# ─────────────────────────────────────────────
@st.cache_data(ttl=86400)
def load_ticker_universe():
    df_krx    = fdr.StockListing('KRX')
    df_sp500  = fdr.StockListing('S&P500')
    df_nasdaq = fdr.StockListing('NASDAQ')
    options    = []
    ticker_map = {}
    market_map = {}
    for _, row in df_krx.iterrows():
        market = str(row.get('Market', 'KRX'))
        code   = row['Code']
        name   = row['Name']
        suffix = ".KS" if "KOSPI" in market else ".KQ"
        t      = f"{code}{suffix}"
        dn     = f"{name} ({t})"
        options.append(dn); ticker_map[dn] = t; market_map[dn] = "KRX (국내)"
    for _, row in df_sp500.iterrows():
        code = row['Symbol']; name = row['Name']; dn = f"{name} ({code})"
        options.append(dn); ticker_map[dn] = code; market_map[dn] = "US (미국)"
    for _, row in df_nasdaq.head(500).iterrows():
        code = row['Symbol']; name = row['Name']; dn = f"{name} ({code})"
        if dn not in ticker_map:
            options.append(dn); ticker_map[dn] = code; market_map[dn] = "US (미국)"
    ticker_map["Bitcoin (BTC-USD)"] = "BTC-USD"
    market_map["Bitcoin (BTC-USD)"] = "Crypto (암호화폐)"
    options.append("Bitcoin (BTC-USD)")
    reverse_map = {v: k for k, v in ticker_map.items()}
    return options, ticker_map, market_map, reverse_map


@st.cache_data(ttl=3600)
def fetch_data(t: str, p: str = "max") -> pd.DataFrame:
    df = yf.download(t, period=p, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df


@st.cache_data(ttl=300)  # 관심목록 배치 조회는 5분 캐시 (비교적 빠른 갱신)
def fetch_watchlist_prices(tickers: tuple) -> dict:
    """관심목록 종목들의 현재가/등락률을 yfinance로 일괄 조회한다.
    tuple로 받는 이유: st.cache_data는 list를 해시할 수 없기 때문이다."""
    result = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).fast_info
            # fast_info는 API 부하가 낮아 빠르게 현재가를 가져올 수 있다
            price     = getattr(info, 'last_price', None)
            prev      = getattr(info, 'previous_close', None)
            if price and prev:
                change = price - prev
                pct    = (change / prev) * 100
            else:
                change = pct = 0
            result[t] = {'price': price, 'change': change, 'pct': pct}
        except Exception:
            result[t] = {'price': None, 'change': 0, 'pct': 0}
    return result


@st.cache_data(ttl=3600)
def fetch_info(t: str) -> dict:
    try:
        return yf.Ticker(t).info
    except Exception:
        return {}


@st.cache_data(ttl=86400)
def fetch_financials(t: str) -> pd.DataFrame:
    try:
        if "BTC" in t: return pd.DataFrame()
        return yf.Ticker(t).income_stmt
    except Exception:
        return pd.DataFrame()


# ─────────────────────────────────────────────
# 5. 세션 상태 초기화
# ─────────────────────────────────────────────
with st.spinner("종목 데이터를 준비 중입니다..."):
    all_options, ticker_map, market_map, reverse_map = load_ticker_universe()

if 'search_box' not in st.session_state:
    default = "Apple Inc. (AAPL)"
    st.session_state['search_box'] = default if default in all_options else all_options[0]
if 'watchlist_data' not in st.session_state:
    st.session_state['watchlist_data'] = load_watchlist()
# 메인 탭 전환을 위한 상태값 (0=차트, 1=관심목록)
# 버튼 클릭으로 탭을 바꿀 때 이 값을 변경하면 화면이 전환됨
if 'active_main_tab' not in st.session_state:
    st.session_state['active_main_tab'] = 0


def on_shortcut_click(yf_ticker: str):
    """단축버튼 클릭 시: 종목 선택 + 차트 탭으로 자동 이동."""
    display = reverse_map.get(yf_ticker)
    if display and display in all_options:
        st.session_state['search_box'] = display
    st.session_state['active_main_tab'] = 0  # 차트 탭으로 전환

def switch_to_chart(display_name: str):
    """관심목록에서 '차트 보기' 클릭 시: 종목 선택 + 차트 탭으로 전환."""
    if display_name in all_options:
        st.session_state['search_box'] = display_name
    st.session_state['active_main_tab'] = 0


# ─────────────────────────────────────────────
# 6. 앱 헤더 + 메인 네비게이션 탭
# ─────────────────────────────────────────────
st.markdown(
    "<h2 style='text-align:center;margin-bottom:4px;color:#d1d4dc;letter-spacing:0.04em;'>"
    "📈 주식 분석 대시보드</h2>"
    "<p style='text-align:center;color:#787b86;margin-top:0;font-size:0.9em;'>"
    "TradingView Style · 실시간 시장 데이터</p>",
    unsafe_allow_html=True
)

# 메인 탭 - st.tabs의 선택을 active_main_tab 세션 상태와 동기화하기 위한 구조
# (버튼 클릭으로 탭을 프로그래밍적으로 전환하기 위해 session_state를 사용함)
TABS = ["📊 차트", "⭐ 관심목록"]
main_tab_objs = st.tabs(TABS)

# ─────────────────────────────────────────────────────────────────────────────
#  탭 0: 차트 화면
# ─────────────────────────────────────────────────────────────────────────────
with main_tab_objs[0]:
    # 검색 UI
    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        market_filter = st.radio(
            "시장별 필터", ["전체보기", "KRX (국내)", "US (미국)", "Crypto (암호화폐)"],
            horizontal=True, label_visibility="collapsed"
        )

    filtered_options = all_options if market_filter == "전체보기" else [
        opt for opt in all_options if market_map[opt] == market_filter
    ]
    if st.session_state['search_box'] not in filtered_options and filtered_options:
        st.session_state['search_box'] = filtered_options[0]

    selected_display = st.selectbox(
        "종목 검색", options=filtered_options,
        key='search_box', label_visibility="collapsed"
    )

    sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
    sc1.button("🍎 AAPL",        use_container_width=True, on_click=on_shortcut_click, args=("AAPL",))
    sc2.button("🟢 NVDA",        use_container_width=True, on_click=on_shortcut_click, args=("NVDA",))
    sc3.button("⚡ TSLA",        use_container_width=True, on_click=on_shortcut_click, args=("TSLA",))
    sc4.button("🇰🇷 삼성전자",   use_container_width=True, on_click=on_shortcut_click, args=("005930.KS",))
    sc5.button("🇰🇷 SK하이닉스", use_container_width=True, on_click=on_shortcut_click, args=("000660.KS",))
    sc6.button("₿ 비트코인",     use_container_width=True, on_click=on_shortcut_click, args=("BTC-USD",))
    st.markdown("<hr style='margin:8px 0;border-color:#2a2e39;'>", unsafe_allow_html=True)

    # 데이터 로드
    ticker = ticker_map[selected_display]
    if   ticker.endswith(".KS"): bench_ticker, bench_name = "^KS11", "KOSPI"
    elif ticker.endswith(".KQ"): bench_ticker, bench_name = "^KQ11", "KOSDAQ"
    else:                        bench_ticker, bench_name = "^GSPC", "S&P 500"

    with st.spinner(f"{selected_display} 로딩 중..."):
        data      = fetch_data(ticker)
        bench_max = fetch_data(bench_ticker)
        info      = fetch_info(ticker)
        inc_data  = fetch_financials(ticker)

    def slice_recent(df, days):
        if df.empty: return df
        return df[df.index >= df.index[-1] - timedelta(days=days)]

    data_1y  = slice_recent(data,      365)
    bench_1y = slice_recent(bench_max, 365)

    if not data.empty:
        close_s       = data['Close'].squeeze()
        current_price = float(close_s.iloc[-1])
        prev_price    = float(close_s.iloc[-2]) if len(close_s) >= 2 else current_price
        daily_change     = current_price - prev_price
        daily_change_pct = (daily_change / prev_price * 100) if prev_price else 0

        currency   = "USD" if "BTC" in ticker else info.get('currency', 'USD')
        symbol     = info.get('symbol', ticker)
        short_name = info.get('shortName', selected_display.split('(')[0].strip())
        price_color = "#ef5350" if daily_change < 0 else "#26a69a"
        sign        = "+" if daily_change > 0 else ""
        curr_sym    = "₩" if currency == "KRW" else "$"

        title_col, watch_col = st.columns([4, 1])
        with title_col:
            st.markdown(
                f"<div><span style='font-size:1.8em;font-weight:700;color:#d1d4dc;'>{short_name}</span>"
                f"<span style='color:#787b86;background:#1e222d;border:1px solid #2a2e39;border-radius:4px;"
                f"padding:2px 8px;margin-left:8px;font-size:0.9em;'>{symbol}</span></div>"
                f"<div style='font-size:2.2em;font-weight:700;color:{price_color};margin:2px 0;'>"
                f"{curr_sym}{current_price:,.2f} "
                f"<span style='font-size:0.55em;'>{sign}{curr_sym}{abs(daily_change):,.2f}"
                f" ({sign}{daily_change_pct:.2f}%)</span></div>",
                unsafe_allow_html=True
            )
        with watch_col:
            st.write("")
            is_watched = selected_display in st.session_state['watchlist_data']
            btn_label  = "❌ 관심해제" if is_watched else "⭐ 관심추가"
            if st.button(btn_label, type="secondary" if is_watched else "primary", use_container_width=True):
                if is_watched:
                    st.session_state['watchlist_data'].remove(selected_display)
                else:
                    st.session_state['watchlist_data'].append(selected_display)
                save_watchlist(st.session_state['watchlist_data'])
                st.rerun()

        # ── 차트 + 컨트롤 ──
        col1, col2 = st.columns([4, 1])

        with col2:
            st.markdown("<div style='color:#787b86;font-size:0.8em;letter-spacing:0.08em;margin-top:8px;'>CHART CONTROLS</div>", unsafe_allow_html=True)
            scale_type = st.radio("Y축 스케일", ["Linear", "Log"], horizontal=True)
            st.markdown("<div style='color:#787b86;font-size:0.8em;letter-spacing:0.08em;margin-top:12px;'>MOVING AVERAGES</div>", unsafe_allow_html=True)
            show_ma5   = st.checkbox("MA 5",   value=True)
            show_ema21 = st.checkbox("EMA 21", value=True)
            show_ma50  = st.checkbox("MA 50",  value=True)
            show_ma60  = st.checkbox("MA 60",  value=False)
            show_ma120 = st.checkbox("MA 120", value=False)
            show_ma200 = st.checkbox("MA 200", value=True)

        with col1:
            timeframe = st.radio(
                "기간", ["1W", "1M", "3M", "1Y", "3Y", "5Y", "All"],
                index=3, horizontal=True, label_visibility="collapsed"
            )

            df = data.copy()
            is_weekly = timeframe in ["3Y", "5Y", "All"]
            if is_weekly:
                agg = {k: v for k, v in {'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}.items() if k in df.columns}
                df  = df.resample('W').agg(agg).dropna()

            close_col = df['Close'].squeeze()
            if show_ma5:   df['MA5']   = close_col.rolling(5).mean()
            if show_ema21: df['EMA21'] = close_col.ewm(span=21, adjust=False).mean()
            if show_ma50:  df['MA50']  = close_col.rolling(50).mean()
            if show_ma60:  df['MA60']  = close_col.rolling(60).mean()
            if show_ma120: df['MA120'] = close_col.rolling(120).mean()
            if show_ma200: df['MA200'] = close_col.rolling(200).mean()

            end_date = df.index[-1]
            tf_days  = {"1W":7,"1M":30,"3M":90,"1Y":365,"3Y":365*3,"5Y":365*5}
            cutoff   = (end_date - timedelta(days=tf_days[timeframe]) if timeframe in tf_days else df.index[0])

            # ★ 현재 선택된 기간 슬라이스 기준으로 Y축 초기 범위를 계산한다
            # (전체 데이터 기준 autorange 시 마이너스까지 잡히는 버그 방지)
            visible_df = df[df.index >= cutoff]
            if not visible_df.empty and 'High' in visible_df.columns and 'Low' in visible_df.columns:
                y_min = float(visible_df['Low'].squeeze().min())
                y_max = float(visible_df['High'].squeeze().max())
                padding = (y_max - y_min) * 0.05   # 위아래 5% 여백
                y_min_padded = max(0, y_min - padding)  # 0 아래로 절대 내려가지 않음
                y_max_padded = y_max + padding
            else:
                y_min_padded, y_max_padded = None, None

            # 거래량 초기 Y 범위 (0부터 최대값 + 20% 여백)
            if not visible_df.empty and 'Volume' in visible_df.columns:
                vol_max = float(visible_df['Volume'].squeeze().max())
                vol_y_max = vol_max * 1.2
            else:
                vol_y_max = None

            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                vertical_spacing=0.02,
                row_heights=[0.72, 0.28],  # 가격 72% / 거래량 28% 비중
                subplot_titles=("", "거래량 (Volume)")
            )

            # 캔들스틱: 흰 배경에서 잘 보이도록 테두리 강조
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'].squeeze(), high=df['High'].squeeze(),
                low=df['Low'].squeeze(),   close=df['Close'].squeeze(), name="Price",
                increasing_line_color='#089981', increasing_fillcolor='#089981',
                decreasing_line_color='#F23645', decreasing_fillcolor='#F23645',
                line=dict(width=1)
            ), row=1, col=1)

            # 이동평균선: 흰 배경에 맞게 색상 조정
            ma_cfg    = [('MA5','#2962FF'),('EMA21','#7B1FA2'),('MA50','#E65100'),
                         ('MA60','#B71C1C'),('MA120','#33691E'),('MA200','#880E4F')]
            show_list = [show_ma5, show_ema21, show_ma50, show_ma60, show_ma120, show_ma200]
            suffix    = " (W)" if is_weekly else ""
            for (ma_name, ma_color), shown in zip(ma_cfg, show_list):
                if shown and ma_name in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df[ma_name].squeeze(),
                        name=f"{ma_name}{suffix}",
                        line=dict(color=ma_color, width=1.5)
                    ), row=1, col=1)

            # 거래량 바: 상승/하락 색상 구분 + 반투명으로 부드럽게
            vol_colors = ['#089981' if c >= o else '#F23645'
                          for c, o in zip(df['Close'].squeeze(), df['Open'].squeeze())]
            fig.add_trace(go.Bar(
                x=df.index, y=df['Volume'].squeeze(),
                name="거래량", marker_color=vol_colors,
                marker_opacity=0.65,
                hovertemplate="%{x}<br>거래량: %{y:,.0f}<extra></extra>"
            ), row=2, col=1)

            # ── 흰색 라이트 테마 차트 레이아웃 ──
            fig.update_layout(
                template="plotly_white",
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                dragmode="pan",
                xaxis_rangeslider_visible=False,
                height=600,
                margin=dict(l=0, r=70, t=8, b=0),
                showlegend=False,
                hovermode="x unified",
                hoverdistance=50,
                # 가격 X축
                xaxis=dict(
                    showgrid=True, gridcolor="#f0f3fa", gridwidth=1,
                    zeroline=False,
                    range=[cutoff, end_date],
                    showspikes=True, spikemode="across",
                    spikecolor="#9b9ea3", spikedash="dot", spikethickness=1,
                    showticklabels=False  # 공유 축이므로 상단엔 레이블 숨김
                ),
                # ★ 가격 Y축: 음수 방지 + 초기 범위를 현재 뷰 데이터 기준으로 설정
                yaxis=dict(
                    showgrid=True, gridcolor="#f0f3fa", gridwidth=1,
                    zeroline=False,
                    range=[y_min_padded, y_max_padded],  # 뷰 슬라이스 기반 초기 범위
                    rangemode="nonnegative",              # ★ 음수 Y값 완전 차단
                    fixedrange=False,                     # 수동 Y 조작 허용
                    side="right",
                    showspikes=True, spikemode="across",
                    spikecolor="#9b9ea3", spikedash="dot", spikethickness=1,
                    type="log" if scale_type == "Log" else "linear",
                    tickformat=",.0f"
                ),
                # 거래량 X축
                xaxis2=dict(
                    showgrid=True, gridcolor="#f0f3fa",
                    zeroline=False,
                    range=[cutoff, end_date]
                ),
                # 거래량 Y축: 항상 0부터 시작
                yaxis2=dict(
                    showgrid=True, gridcolor="#f0f3fa",
                    zeroline=True, zerolinecolor="#e0e3eb",
                    rangemode="nonnegative",  # ★ 거래량도 음수 없음
                    range=[0, vol_y_max],
                    fixedrange=False,
                    side="right",
                    tickformat=".2s"  # 1.2B, 500M 등 축약 표기
                ),
                font=dict(color="#5d606b", family="Trebuchet MS", size=11)
            )

            # subplot 제목 스타일
            fig.update_annotations(font=dict(color="#9b9ea3", size=10))

            st.plotly_chart(fig, use_container_width=True, config={
                'scrollZoom': True,
                'modeBarButtonsToRemove': ['zoomIn2d','zoomOut2d','lasso2d','select2d','autoScale2d'],
                'displaylogo': False,
                'toImageButtonOptions': {'format': 'png', 'scale': 2}
            })

        # ── 펀더멘털 ──
        st.markdown("<hr style='border-color:#e0e3eb;margin:12px 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='color:#787b86;font-size:0.78em;letter-spacing:0.1em;margin-bottom:8px;'>KEY FUNDAMENTALS</div>", unsafe_allow_html=True)

        def fmt_mcap(mcap, curr):
            if not mcap: return "N/A"
            if curr == "KRW": return f"{mcap/1e12:.2f}조"
            if mcap >= 1e12:  return f"${mcap/1e12:.2f}T"
            if mcap >= 1e9:   return f"${mcap/1e9:.2f}B"
            return f"${mcap/1e6:.2f}M"

        market_cap    = info.get('marketCap')
        forward_pe    = info.get('forwardPE')
        price_to_book = info.get('priceToBook')
        roe           = info.get('returnOnEquity')
        disp_pe  = f"{forward_pe:.2f}"    if forward_pe   is not None else "N/A"
        disp_pb  = f"{price_to_book:.2f}" if price_to_book is not None else "N/A"
        disp_roe = f"{roe*100:.2f}%"      if roe          is not None else "N/A"

        v_col1, v_col2 = st.columns(2)
        with v_col1:
            st.markdown("<div style='color:#787b86;font-size:0.78em;letter-spacing:0.08em;margin-bottom:6px;'>VALUATION</div>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("시가총액",     fmt_mcap(market_cap, currency))
            c2.metric("Forward P/E", disp_pe)
            c3.metric("P/B",         disp_pb)
            c4.metric("ROE",         disp_roe)

        with v_col2:
            st.markdown(f"<div style='color:#787b86;font-size:0.78em;letter-spacing:0.08em;margin-bottom:6px;'>RELATIVE PERFORMANCE (vs {bench_name})</div>", unsafe_allow_html=True)
            e1, e2, e3, e4 = st.columns(4)

            def calc_excess_return(sdf, bdf, days):
                def _ret(df_in):
                    if df_in.empty: return 0.0
                    c = df_in['Close'].squeeze()
                    cut = c.index[-1] - timedelta(days=days)
                    past = c[c.index <= cut]
                    base = float(past.iloc[-1]) if not past.empty else float(c.iloc[0])
                    return (float(c.iloc[-1]) / base - 1) if base else 0.0
                return _ret(sdf) - _ret(bdf)

            try:
                for col, (label, days) in zip([e1,e2,e3,e4], [("1M",30),("3M",90),("6M",180),("1Y",365)]):
                    val = calc_excess_return(data_1y, bench_1y, days)
                    col.metric(label, f"{val*100:.2f}%", delta=f"{val*100:.2f}%")
            except Exception:
                for col, label in zip([e1,e2,e3,e4], ["1M","3M","6M","1Y"]):
                    col.metric(label, "N/A")

        # ── 실적 요약표 ──
        st.markdown("<hr style='border-color:#2a2e39;margin:12px 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='color:#787b86;font-size:0.78em;letter-spacing:0.1em;margin-bottom:8px;'>EARNINGS SUMMARY</div>", unsafe_allow_html=True)

        if inc_data.empty:
            st.info("이 종목의 재무제표 데이터를 불러올 수 없습니다.")
        else:
            sorted_cols = sorted(inc_data.columns)
            def get_row(df_in, names):
                for n in names:
                    if n in df_in.index: return df_in.loc[n]
                return None
            rev_row = get_row(inc_data, ['Total Revenue','Operating Revenue','Revenue','Gross Profit'])
            ni_row  = get_row(inc_data, ['Net Income','Net Income Continuous Operations'])
            eps_row = get_row(inc_data, ['Basic EPS','Diluted EPS','Reported EPS'])

            def fmt_num(val, is_eps=False):
                if val is None or (isinstance(val, float) and pd.isna(val)): return "-"
                if is_eps: return f"${val:.2f}" if currency != "KRW" else f"₩{val:,.0f}"
                if currency == "KRW": return f"{val/1e12:.1f}조" if val >= 1e12 else f"{val/1e8:.0f}억"
                if abs(val) >= 1e9: return f"${val/1e9:.1f}B"
                if abs(val) >= 1e6: return f"${val/1e6:.1f}M"
                return f"${val:,.0f}"

            def calc_yoy(cur, prev):
                if any(v is None or (isinstance(v, float) and pd.isna(v)) for v in [cur, prev]) or prev == 0:
                    return "-"
                pct = (cur - prev) / abs(prev) * 100
                color = "#26a69a" if pct > 0 else "#ef5350"
                arrow = "▲" if pct > 0 else "▼"
                return f"<span style='color:{color};font-weight:600;'>{arrow} {abs(pct):.1f}%</span>"

            rows_html = ""
            for i, col in enumerate(sorted_cols):
                rev = rev_row[col] if rev_row is not None else None
                ni  = ni_row[col]  if ni_row  is not None else None
                eps = eps_row[col] if eps_row is not None else None
                if i > 0:
                    pc = sorted_cols[i-1]
                    rv_yoy  = calc_yoy(rev, rev_row[pc] if rev_row is not None else None)
                    ni_yoy  = calc_yoy(ni,  ni_row[pc]  if ni_row  is not None else None)
                    eps_yoy = calc_yoy(eps, eps_row[pc] if eps_row is not None else None)
                else:
                    rv_yoy = ni_yoy = eps_yoy = "-"
                cells  = [f"{col.year}", fmt_num(rev), rv_yoy, fmt_num(ni), ni_yoy, fmt_num(eps, True), eps_yoy]
                aligns = ["left"] + ["right"] * 6
                rows_html += "<tr>"
                for cell, align in zip(cells, aligns):
                    rows_html += (f"<td style='padding:12px 16px;text-align:{align};"
                                  f"border-bottom:1px solid #1e222d;color:#d1d4dc;font-size:0.92em;'>{cell}</td>")
                rows_html += "</tr>"

            headers = ["연도","매출","YoY","순이익","YoY","EPS","YoY"]
            aligns  = ["left"] + ["right"] * 6
            thead   = "".join(
                f"<th style='padding:12px 16px;text-align:{a};color:#787b86;font-size:0.78em;"
                f"letter-spacing:0.08em;border-bottom:2px solid #2a2e39;'>{h}</th>"
                for h, a in zip(headers, aligns)
            )
            st.markdown(
                f"<div style='background:#1e222d;border:1px solid #2a2e39;border-radius:8px;overflow:hidden;'>"
                f"<table style='width:100%;border-collapse:collapse;'>"
                f"<thead><tr>{thead}</tr></thead><tbody>{rows_html}</tbody></table></div>",
                unsafe_allow_html=True
            )
    else:
        st.error("데이터를 불러올 수 없습니다. 다른 종목을 검색해주세요.")


# ─────────────────────────────────────────────────────────────────────────────
#  탭 1: 관심목록 화면 (완전히 분리된 독립 페이지)
# ─────────────────────────────────────────────────────────────────────────────
with main_tab_objs[1]:
    st.markdown(
        "<h3 style='color:#d1d4dc;margin-bottom:4px;'>⭐ 내 관심목록</h3>"
        "<p style='color:#787b86;font-size:0.88em;margin-top:0;'>저장된 종목의 실시간 현황을 한눈에 확인하세요.</p>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border-color:#2a2e39;margin:8px 0 16px;'>", unsafe_allow_html=True)

    watchlist = st.session_state['watchlist_data']

    if not watchlist:
        st.markdown(
            "<div style='text-align:center;padding:60px 0;color:#787b86;'>"
            "<div style='font-size:3em;margin-bottom:12px;'>☆</div>"
            "<div style='font-size:1.1em;font-weight:600;color:#d1d4dc;margin-bottom:8px;'>관심종목이 없습니다</div>"
            "<div style='font-size:0.9em;'>차트 화면에서 ⭐ 관심추가 버튼을 눌러 종목을 저장해 보세요!</div>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        # 새로고침 버튼 (캐시를 날리고 최신 가격을 다시 불러옴)
        ref_col, _, count_col = st.columns([1, 4, 1])
        with ref_col:
            if st.button("🔄 가격 새로고침", use_container_width=True):
                fetch_watchlist_prices.clear()
                st.rerun()
        with count_col:
            st.markdown(f"<div style='text-align:right;color:#787b86;padding-top:8px;font-size:0.85em;'>총 {len(watchlist)}개 종목</div>", unsafe_allow_html=True)

        # 저장된 종목들의 ticker를 뽑아서 일괄 가격 조회 (API를 한 번에 배치 처리)
        tickers_in_watchlist = tuple(ticker_map[dn] for dn in watchlist if dn in ticker_map)
        with st.spinner("관심종목 가격 조회 중..."):
            price_data = fetch_watchlist_prices(tickers_in_watchlist)

        # 3열 그리드로 카드 배치
        NUM_COLS = 3
        for row_start in range(0, len(watchlist), NUM_COLS):
            cols = st.columns(NUM_COLS)
            for col_idx, item in enumerate(watchlist[row_start: row_start + NUM_COLS]):
                if item not in ticker_map:
                    continue
                t        = ticker_map[item]
                name     = item.split('(')[0].strip()
                sym      = item.split('(')[-1].rstrip(')')
                pdata    = price_data.get(t, {})
                price    = pdata.get('price')
                change   = pdata.get('change', 0)
                pct      = pdata.get('pct', 0)

                is_up    = pct >= 0
                card_color  = "#26a69a" if is_up else "#ef5350"
                bg_tint     = "rgba(38,166,154,0.07)" if is_up else "rgba(239,83,80,0.07)"
                arrow       = "▲" if is_up else "▼"
                sign        = "+" if is_up else ""
                price_str   = f"{price:,.2f}" if price is not None else "—"

                # HTML 카드 렌더링
                cols[col_idx].markdown(
                    f"<div style='background:#1e222d;border:1px solid #2a2e39;border-radius:10px;"
                    f"padding:18px 20px;margin-bottom:10px;border-left:3px solid {card_color};'>"
                    f"<div style='color:#787b86;font-size:0.75em;letter-spacing:0.08em;margin-bottom:4px;'>{sym}</div>"
                    f"<div style='color:#d1d4dc;font-size:1em;font-weight:700;margin-bottom:10px;"
                    f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{name}</div>"
                    f"<div style='font-size:1.6em;font-weight:700;color:#d1d4dc;'>{price_str}</div>"
                    f"<div style='font-size:0.88em;color:{card_color};font-weight:600;margin-top:4px;background:{bg_tint};"
                    f"border-radius:4px;padding:2px 8px;display:inline-block;'>"
                    f"{arrow} {sign}{change:+.2f} ({sign}{pct:.2f}%)</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                # 차트 보기 버튼: 클릭 시 해당 종목 선택 + 차트 탭으로 전환
                cols[col_idx].button(
                    "📊 차트 보기", key=f"goto_{item}",
                    use_container_width=True,
                    on_click=switch_to_chart, args=(item,)
                )
                # 관심 해제 버튼
                if cols[col_idx].button("❌ 삭제", key=f"del_{item}", use_container_width=True):
                    st.session_state['watchlist_data'].remove(item)
                    save_watchlist(st.session_state['watchlist_data'])
                    fetch_watchlist_prices.clear()
                    st.rerun()
