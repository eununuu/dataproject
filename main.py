import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="서울 기온 트렌드 분석기", layout="wide")
st.title("🌡️ 1980년대 전후 서울 기온 상승 트렌드 비교 웹앱")
st.markdown("""
1980년대를 기점으로 기온 상승 속도가 달라졌을 것이라는 가설을 검증하기 위한 대시보드입니다.  
제공된 서울 기온 역사 데이터를 분석하여 **1980년 이전**과 **1980년 이후**의 연평균 기온 추세선을 비교합니다.
""")

# 2. 데이터 로드 및 전처리 함수
@st.cache_data
def load_data():
    # 파일 인코딩을 'utf-8-sig'로 변경하여 에러 수정 및 BOM 제거
    df = pd.read_csv('ta_20260601093156.csv', encoding='utf-8-sig')
    
    # 컬럼명 정제 (공백 제거)
    df.columns = df.columns.str.strip()
    
    # '날짜' 컬럼의 탭 문자(\t) 및 따옴표 제거 후 데이트타임 변환
    df['날짜'] = df['날짜'].astype(str).str.replace(r'[\s"\t]+', '', regex=True)
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # 연도 컬럼 추출
    df['연도'] = df['날짜'].dt.year
    
    # 기온 데이터 숫자형 변환 및 결측치 제거
    df['평균기온(℃)'] = pd.to_numeric(df['평균기온(℃)'], errors='coerce')
    df = df.dropna(subset=['평균기온(℃)'])
    
    # 연도별 평균 기온 계산
    yearly_df = df.groupby('연도')['평균기온(℃)'].mean().reset_index()
    return yearly_df

try:
    data = load_data()
    
    # 3. 사이드바 - 분석 기준점 설정
    st.sidebar.header("📊 분석 설정")
    split_year = st.sidebar.slider("트렌드 분기 연도 선택", min_value=1950, max_value=2010, value=1980, step=5)
    
    # 데이터 분할
    df_before = data[data['연도'] < split_year]
    df_after = data[data['연도'] >= split_year]
    
    # 4. 주요 지표 (Metrics) 시각화
    mean_before = df_before['평균기온(℃)'].mean()
    mean_after = df_after['평균기온(℃)'].mean()
    temp_diff = mean_after - mean_before
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="이전 평균 기온", value=f"{mean_before:.2f} °C")
    col2.metric(label="이후 평균 기온", value=f"{mean_after:.2f} °C")
    col3.metric(label="평균 기온 상승 폭", value=f"+{temp_diff:.2f} °C", delta=f"{temp_diff:.2f} °C")
    
    st.markdown("---")
    
    # 5. 시각화 (Plotly) - 추세선 그리기
    st.subheader(f"📈 {split_year}년 전후 기온 추세선 비교")
    
    fig = go.Figure()
    
    # 전체 실제 데이터 산점도
    fig.add_trace(go.Scatter(
        x=data['연도'], y=data['평균기온(℃)'],
        mode='markers', name='연평균 기온',
        marker=dict(color='gray', opacity=0.5)
    ))
    
    # 분기 이전 추세선 계산 및 추가
    if len(df_before) > 1:
        slope_b, intercept_b = np.polyfit(df_before['연도'], df_before['평균기온(℃)'], 1)
        fig.add_trace(go.Scatter(
            x=df_before['연도'], y=slope_b * df_before['연도'] + intercept_b,
            mode='lines', name=f'{split_year}년 이전 추세선 (기여도: {slope_b*10:.3f}°C/10년)',
            line=dict(color='blue', width=3)
        ))
    else:
        slope_b = 0
        
    # 분기 이후 추세선 계산 및 추가
    if len(df_after) > 1:
        slope_a, intercept_a = np.polyfit(df_after['연도'], df_after['평균기온(℃)'], 1)
        fig.add_trace(go.Scatter(
            x=df_after['연度'] if '연度' in df_after else df_after['연도'], 
            y=slope_a * df_after['연도'] + intercept_a,
            mode='lines', name=f'{split_year}년 이후 추세선 (기여도: {slope_a*10:.3f}°C/10년)',
            line=dict(color='red', width=3)
        ))
    else:
        slope_a = 0
        
    fig.update_layout(
        xaxis_title="연도",
        yaxis_title="평균 기온 (℃)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 6. 통계적 인사이트 요약
    st.subheader("💡 가설 검증 결과 요약")
    rate_multiplier = (slope_a / slope_b) if slope_b != 0 else 0
    
    st.write(f"""
    - **{split_year}년 이전**에는 10년마다 약 **{slope_b*10:.3f}°C**씩 변화했습니다.
    - **{split_year}년 이후**에는 10년마다 약 **{slope_a*10:.3f}°C**씩 빠르게 상승하고 있습니다.
    - {split_year}년 이후의 기온 상승 속도는 이전과 비교했을 때 약 **{rate_multiplier:.1f}배** 차이가 납니다.
    """)
    
except FileNotFoundError:
    st.error("❌ 'ta_20260601093156.csv' 파일을 찾을 수 없습니다. 앱과 같은 폴더(또는 GitHub 저장소)에 파일을 위치시켜 주세요.")
except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
