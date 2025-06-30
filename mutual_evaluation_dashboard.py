import pandas as pd
import streamlit as st

def load_data():
    df = pd.read_excel('설문조사_전처리데이터_20250620_0731_processed.xlsx')
    return df

def preprocess(df, min_count=30):
    grouped = df.groupby(['설문시행연도', '평가_부서명', '피평가대상 부서명']).agg(
        응답수=('종합점수', 'count'),
        평균점수=('종합점수', 'mean'),
        협업후기=('협업후기', lambda x: list(x.dropna()))
    ).reset_index()
    # 상호 평가 쌍 추출
    pairs = []
    for _, row in grouped.iterrows():
        y, a, b, cnt1 = row['설문시행연도'], row['평가_부서명'], row['피평가대상 부서명'], row['응답수']
        reverse = grouped[(grouped['설문시행연도']==y) & (grouped['평가_부서명']==b) & (grouped['피평가대상 부서명']==a)]
        if not reverse.empty and cnt1 >= min_count and reverse.iloc[0]['응답수'] >= min_count:
            pairs.append((y, a, b))
    return grouped, list(set(pairs))

def preprocess_unit(df, min_count=30):
    grouped = df.groupby(['설문시행연도', '평가_Unit명', '피평가대상 UNIT명']).agg(
        응답수=('종합점수', 'count'),
        평균점수=('종합점수', 'mean'),
        협업후기=('협업후기', lambda x: list(x.dropna()))
    ).reset_index()
    pairs = []
    for _, row in grouped.iterrows():
        y, a, b, cnt1 = row['설문시행연도'], row['평가_Unit명'], row['피평가대상 UNIT명'], row['응답수']
        reverse = grouped[(grouped['설문시행연도']==y) & (grouped['평가_Unit명']==b) & (grouped['피평가대상 UNIT명']==a)]
        if not reverse.empty and cnt1 >= min_count and reverse.iloc[0]['응답수'] >= min_count:
            pairs.append((y, a, b))
    return grouped, list(set(pairs))

def show_unit_response_table(df):
    st.subheader('Unit별 응답수 현황')
    years = sorted(df['설문시행연도'].unique())
    year = st.selectbox('Unit 응답수 연도 선택', years, key='unit_year')
    unit_col = '평가_Unit명' if '평가_Unit명' in df.columns else df.columns[-1]  # 컬럼명 유동적 대응
    unit_counts = df[df['설문시행연도'] == year][unit_col].value_counts().reset_index()
    unit_counts.columns = ['Unit명', '응답수']
    st.dataframe(unit_counts)

def show_unit_mutual_dashboard(df):
    st.header('Unit 단위 상호평가 대시보드')
    min_count = st.slider('Unit 상호평가 최소 응답수', min_value=1, max_value=100, value=30, step=1)
    grouped, mutual_pairs = preprocess_unit(df, min_count)
    if not mutual_pairs:
        st.warning('상호 평가 Unit 쌍이 없습니다.')
        return
    years = sorted(set([y for y, a, b in mutual_pairs]))
    year = st.selectbox('Unit 상호평가 연도 선택', years, key='unit_mutual_year')
    filtered_pairs = [(a, b) for y, a, b in mutual_pairs if y == year]
    pair = st.selectbox('Unit 쌍 선택', filtered_pairs, format_func=lambda x: f"{x[0]} ↔ {x[1]}", key='unit_pair')
    a, b = pair
    row1 = grouped[(grouped['설문시행연도']==year) & (grouped['평가_Unit명']==a) & (grouped['피평가대상 UNIT명']==b)].iloc[0]
    row2 = grouped[(grouped['설문시행연도']==year) & (grouped['평가_Unit명']==b) & (grouped['피평가대상 UNIT명']==a)].iloc[0]
    st.subheader(f"{year}년 {a} ↔ {b} Unit 상호 평가 결과")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{a} → {b}**")
        st.metric("평균점수", f"{row1['평균점수']:.1f}")
        st.metric("응답수", int(row1['응답수']))
        st.write("주요 협업 후기:")
        for txt in row1['협업후기'][:3]:
            st.write(f"- {txt}")
    with col2:
        st.markdown(f"**{b} → {a}**")
        st.metric("평균점수", f"{row2['평균점수']:.1f}")
        st.metric("응답수", int(row2['응답수']))
        st.write("주요 협업 후기:")
        for txt in row2['협업후기'][:3]:
            st.write(f"- {txt}")

def main():
    st.title('상호 평가 부서 쌍 대시보드')
    df = load_data()
    show_unit_response_table(df)
    grouped, mutual_pairs = preprocess(df)
    if not mutual_pairs:
        st.warning('상호 평가 쌍이 없습니다.')
        return
    years = sorted(set([y for y, a, b in mutual_pairs]))
    year = st.selectbox('연도 선택', years)
    filtered_pairs = [(a, b) for y, a, b in mutual_pairs if y == year]
    pair = st.selectbox('부서 쌍 선택', filtered_pairs, format_func=lambda x: f"{x[0]} ↔ {x[1]}")
    a, b = pair
    row1 = grouped[(grouped['설문시행연도']==year) & (grouped['평가_부서명']==a) & (grouped['피평가대상 부서명']==b)].iloc[0]
    row2 = grouped[(grouped['설문시행연도']==year) & (grouped['평가_부서명']==b) & (grouped['피평가대상 부서명']==a)].iloc[0]
    st.subheader(f"{year}년 {a} ↔ {b} 상호 평가 결과")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{a} → {b}**")
        st.metric("평균점수", f"{row1['평균점수']:.1f}")
        st.metric("응답수", int(row1['응답수']))
        st.write("주요 협업 후기:")
        for txt in row1['협업후기'][:3]:
            st.write(f"- {txt}")
    with col2:
        st.markdown(f"**{b} → {a}**")
        st.metric("평균점수", f"{row2['평균점수']:.1f}")
        st.metric("응답수", int(row2['응답수']))
        st.write("주요 협업 후기:")
        for txt in row2['협업후기'][:3]:
            st.write(f"- {txt}")
    # Unit 단위 상호평가 대시보드
    show_unit_mutual_dashboard(df)

if __name__ == '__main__':
    main() 