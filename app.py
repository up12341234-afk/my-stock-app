import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(page_title="나의 주식 분석기", layout="wide")

st.title("📈 개인용 주식 데이터 시각화 도구")

# 사이드바에서 설정
ticker = st.sidebar.text_input("티커 입력 (예: AAPL, TSLA, 005930.KS)", value="AAPL")
period = st.sidebar.selectbox("기간 선택", ["1mo", "3mo", "6mo", "1y", "2y", "5y"])

# 데이터 가져오기
data = yf.download(ticker, period=period)

if not data.empty:
    # 이동평균선 계산
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA60'] = data['Close'].rolling(window=60).mean()

    # 차트 생성 (주가 + 거래량 2단 구성)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1, subplot_titles=(f'{ticker} 주가', '거래량'),
                        row_width=[0.2, 0.7])

    # 1. 캔들스틱 차트
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                 low=data['Low'], close=data['Close'], name="Price"), row=1, col=1)
    
    # 2. 이동평균선 추가
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA20", line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['MA60'], name="MA60", line=dict(color='blue')), row=1, col=1)

    # 3. 거래량 차트
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name="Volume", marker_color='gray'), row=2, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False, height=700)
    st.plotly_chart(fig, use_container_width=True)

    # 데이터 표 출력
    st.subheader("최근 데이터 내역")
    st.dataframe(data.tail(10))
else:
    st.error("데이터를 불러올 수 없습니다. 티커를 확인해주세요.")
