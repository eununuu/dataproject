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

# 제목 및 앱 설명 (unsafe_allow_html=True로 올바르게 수정)
st.markdown('<h1 style="text-align: center; color: #E74C3C;">🌡️ 서울 기온 트렌드 변화 가설 검증 웹앱</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #555; font-size: 1.1rem; margin-bottom: 25px;">1980년대 전후로 대한민국(서울)의 기온 상승 속도가 가속화되었다는 가설을 데이터 기반으로 실증 분석합니다.</p>', unsafe_allow_html=True)

# 2. 데이터 로드 및 전처리
@st.cache_data
def load_and_preprocess_data():
    try:
        df = pd.read_csv('ta_20260601093156.csv', encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        
        # '날짜' 컬럼 내부의 숨겨진 공백, 탭(\t), 큰따옴표 정제
        df['날짜'] = df['날짜'].astype(str).str.replace(r'[\s"\t]+', '', regex=True)
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        df = df.dropna(subset=['날짜'])
        
        # 파생 변수 생성
        df['연도'] = df['날짜'].dt.year
        df['월'] = df['날짜'].dt.month
        
        # 기온 데이터 숫자형 변환
        for col in ['평균기온(℃)', '최저기온(℃)', '최고기온(℃)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['평균기온(℃)'])
        return df
    except Exception as e:
        st.error(f"데이터 파일 전처리 중 에러가 발생했습니다: {e}")
        return None

df_raw = load_and_preprocess_data()

if df_raw is not None:
    yearly_summary = df_raw.groupby('연도').agg({
        '평균기온(℃)': 'mean',
        '최저기온(℃)': 'mean',
        '최고기온(℃)': 'mean'
    }).reset_index()

    # 3. 사이드바 제어 패널
    st.sidebar.markdown("## ⚙️ 분석 제어 패널")
    
    split_year = st.sidebar.slider(
        "🔮 가설 분기 연도 선택", 
        min_value=int(yearly_summary['연도'].min()) + 10, 
        max_value=int(yearly_summary['연도'].max()) - 10, 
        value=1980, 
        step=5
    )
    
    target_col = st.sidebar.selectbox(
        "📊 측정 기온 변수 선택",
        ["평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]
    )
    
    df_before = yearly_summary[yearly_summary['연도'] < split_year]
    df_after = yearly_summary[yearly_summary['연도'] >= split_year]
    
    # 4. 상단 대시보드 지표
    mean_before = df_before[target_col].mean()
    mean_after = df_after[target_col].mean()
    diff_val = mean_after - mean_before
    
    st
