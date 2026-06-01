import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

# 1. 페이지 초기 설정
st.set_page_config(
    page_title="서울 기후변화 가설 검증기",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 테마 및 스타일링
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 800; color: #E74C3C; text-align: center; margin-bottom: 5px; }
    .sub-title { font-size: 1.1rem; color: #555; text-align: center; margin-bottom: 25px; }
    .reportview-container { background: #FAF9F6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_style_html=True)

st.markdown('<div class="main-title">🌡️ 서울 기온 트렌드 변화 가설 검증 웹앱</div>', unsafe_style_html=True)
st.markdown('<div class="sub-title">1980년대 전후로 대한민국(서울)의 기온 상승 속도가 가속화되었다는 가설을 데이터 기반으로 실증 분석합니다.</div>', unsafe_style_html=True)

# 2. 데이터 로드 및 고도화된 전처리
@st.cache_data
def load_and_preprocess_data():
    try:
        # 공백 제거 및 인코딩 처리 확보
        df = pd.read_csv('ta_20260601093156.csv', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        
        # '날짜' 컬럼 내부의 숨겨진 공백, 탭(\t), 큰따옴표 정제
        df['날짜'] = df['날짜'].astype(str).str.replace(r'[\s"\t]+', '', regex=True)
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        df = df.dropna(subset=['날짜'])
        
        # 파생 변수 생성
        df['연도'] = df['날짜'].dt.year
        df['월'] = df['날짜'].dt.month
        
        # 기온 데이터 강제 숫자 변환 및 결측값 제거
        for col in ['평균기온(℃)', '최저기온(℃)', '최고기온(℃)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['평균기온(℃)'])
        return df
    except Exception as e:
        st.error(f"데이터 파일 전처리 중 예기치 못한 에러가 발생했습니다: {e}")
        return None

df_raw = load_and_preprocess_data()

if df_raw is not None:
    # 연도별 핵심 요약 통계량 산출
    yearly_summary = df_raw.groupby('연도').agg({
        '평균기온(℃)': 'mean',
        '최저기온(℃)': 'mean',
        '최고기온(℃)': 'mean'
    }).reset_index()

    # 3. 사이드바 제어 패널 설정
    st.sidebar.markdown("## ⚙️ 분석 제어 패널")
    st.sidebar.info("이곳에서 가설의 경계선이 되는 연도를 바꾸고 기온 지표를 변경해 보세요.")
    
    # 가설 분기 연도 제어
    split_year = st.sidebar.slider(
        "🔮 가설 분기 연도(Split Year) 선택", 
        min_value=int(yearly_summary['연도'].min()) + 10, 
        max_value=int(yearly_summary['연도'].max()) - 10, 
        value=1980, 
        step=5
    )
    
    # 분석 대상 변수 선택
    target_col = st.sidebar.selectbox(
        "📊 측정 기온 변수 선택",
        ["평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]
    )
    
    # 데이터 분할 실행
    df_before = yearly_summary[yearly_summary['연도'] < split_year]
    df_after = yearly_
