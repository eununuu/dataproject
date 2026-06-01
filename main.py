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
    
    st.markdown(f"### 📍 {split_year}년 기준 데이터 요약 지표")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label=f"⏳ {split_year}년 이전 평균", value=f"{mean_before:.2f} °C")
    with m2:
        st.metric(label=f"🚀 {split_year}년 이후 평균", value=f"{mean_after:.2f} °C")
    with m3:
        st.metric(label="🌡️ 두 기간의 기온 편차", value=f"{diff_val:+.2f} °C", delta=f"{diff_val:.2f} °C 변경")
    
    st.markdown("---")
    
    # 5. 탭 레이아웃
    tab1, tab2, tab3 = st.tabs(["📈 시각화 및 추세 비교", "🔬 통계적 검증 (R² / p-value)", "📅 월별 기후 분포 현황"])
    
    with tab1:
        st.subheader("💡 기간별 선형 회귀 추세선 비교")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=yearly_summary['연도'], y=yearly_summary[target_col],
            mode='markers+lines', name='연도별 관측치',
            marker=dict(color='rgba(127, 140, 141, 0.6)', size=6),
            line=dict(color='rgba(189, 195, 199, 0.3)', width=1)
        ))
        
        if len(df_before) > 1:
            slope_b, intercept_b = np.polyfit(df_before['연도'], df_before[target_col], 1)
            fig.add_trace(go.Scatter(
                x=df_before['연도'], y=slope_b * df_before['연도'] + intercept_b,
                mode='lines', name=f'{split_year}년 이전 (10년당 {slope_b*10:+.3f}°C)',
                line=dict(color='#2980B9', width=4)
            ))
            
        if len(df_after) > 1:
            slope_a, intercept_a = np.polyfit(df_after['연도'], df_after[target_col], 1)
            fig.add_trace(go.Scatter(
                x=df_after['연도'], y=slope_a * df_after['연도'] + intercept_a,
                mode='lines', name=f'{split_year}년 이후 (10년당 {slope_a*10:+.3f}°C)',
                line=dict(color='#E74C3C', width=4)
            ))
            
        fig.update_layout(
            xaxis_title="연도(Year)", yaxis_title=target_col,
            hovermode="x unified", height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.01)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.subheader("🔬 가설 검증을 위한 선형 회귀 통계 데이터 요약")
        slope_b, intercept_b, r_val_b, p_val_b, std_err_b = stats.linregress(df_before['연도'], df_before[target_col])
        slope_a, intercept_a, r_val_a, p_val_a, std_err_a = stats.linregress(df_after['연도'], df_after[target_col])
            
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### 🔵 {split_year}년 이전 기술 통계")
            st.write(f"- **10년 환산 변화량:** `{slope_b*10:+.3f} °C`")
            st.write(f"- **결정계수 (R-squared):** `{r_val_b**2:.4f}`")
            st.write(f"- **p-value:** `{p_val_b:.4e}`")
                
        with c2:
            st.markdown(f"#### 🔴 {split_year}년 이후 기술 통계")
            st.write(f"- **10년 환산 변화량:** `{slope_a*10:+.3f} °C`")
            st.write(f"- **결정계수 (R-squared):** `{r_val_a**2:.4f}`")
            st.write(f"- **p-value:** `{p_val_a:.4e}`")
        
        st.markdown("---")
        acceleration = (slope_a / slope_b) if slope_b != 0 else 0
        if slope_a > slope_b and p_val_a < 0.05:
            st.success(f"**🔥 가설 채택:** {split_year}년 이후 기온 상승 속도가 전보다 약 {acceleration:.2f}배 빨라졌으며, 통계적으로 유의미합니다.")
        else:
            st.warning("⚠️ 상승 속도의 차이가 통계적 유의 수준(p < 0.05)에 미치지 못할 수 있습니다.")
            
    with tab3:
        st.subheader("📅 두 기간의 월별 기온 분포 차이")
        df_raw['기간분류'] = np.where(df_raw['연도'] < split_year, f"1. {split_year}년 이전", f"2. {split_year}년 이후")
        fig_box = px.box(
            df_raw, x="월", y=target_col, color="기간분류",
            color_discrete_map={f"1. {split_year}년 이전": "#2980B9", f"2. {split_year}년 이후": "#E74C3C"}
        )
        fig_box.update_layout(xaxis=dict(tickmode='array', tickvals=list(range(1, 13))), boxmode="group")
        st.plotly_chart(fig_box, use_container_width=True)

else:
    st.error("데이터 로드 실패.")
