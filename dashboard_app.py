import pandas as pd
import streamlit as st

# 데이터 로드 함수
@st.cache_data
def load_data():
    file_path = '설문조사_전처리데이터_20250620_0731_processed.xlsx'
    try:
        df = pd.read_excel(file_path)
        return df
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {file_path}")
        st.stop()
    except Exception as e:
        st.error(f"데이터 로딩 중 오류 발생: {e}")
        st.stop()

def main():
    st.set_page_config(layout="wide")
    st.title("협업 평가 대시보드")

    df = load_data()

    if df is None:
        return

    # --- 필터링 섹션 ---
    st.sidebar.header("필터링")

    # 설문시행연도 필터
    all_years = sorted(df['설문시행연도'].unique())
    selected_years = st.sidebar.multiselect(
        "설문시행연도",
        options=all_years,
        default=all_years
    )

    # 평가_부문/부서/Unit 필터
    all_eval_sections = sorted(df['평가_부문'].unique())
    selected_eval_sections = st.sidebar.multiselect(
        "평가 부문",
        options=all_eval_sections,
        default=all_eval_sections
    )

    all_eval_departments = sorted(df['평가_부서명'].unique())
    selected_eval_departments = st.sidebar.multiselect(
        "평가 부서",
        options=all_eval_departments,
        default=all_eval_departments
    )

    all_eval_units = sorted(df['평가_Unit명'].dropna().unique())
    selected_eval_units = st.sidebar.multiselect(
        "평가 Unit",
        options=all_eval_units,
        default=all_eval_units
    )

    # 피평가대상 부문/부서/Unit 필터
    all_target_sections = sorted(df['피평가대상 부문'].unique())
    selected_target_sections = st.sidebar.multiselect(
        "피평가대상 부문",
        options=all_target_sections,
        default=all_target_sections
    )

    all_target_departments = sorted(df['피평가대상 부서명'].unique())
    selected_target_departments = st.sidebar.multiselect(
        "피평가대상 부서",
        options=all_target_departments,
        default=all_target_departments
    )

    all_target_units = sorted(df['피평가대상 UNIT명'].dropna().unique())
    selected_target_units = st.sidebar.multiselect(
        "피평가대상 Unit",
        options=all_target_units,
        default=all_target_units
    )

    # 필터링 적용
    filtered_df = df[
        (df['설문시행연도'].isin(selected_years)) &
        (df['평가_부문'].isin(selected_eval_sections)) &
        (df['평가_부서명'].isin(selected_eval_departments)) &
        (df['평가_Unit명'].isin(selected_eval_units) | df['평가_Unit명'].isna()) & # NaN 값도 포함
        (df['피평가대상 부문'].isin(selected_target_sections)) &
        (df['피평가대상 부서명'].isin(selected_target_departments)) &
        (df['피평가대상 UNIT명'].isin(selected_target_units) | df['피평가대상 UNIT명'].isna()) # NaN 값도 포함
    ]

    if filtered_df.empty:
        st.warning("선택된 필터에 해당하는 데이터가 없습니다.")
        return

    st.subheader("필터링된 데이터 미리보기")
    st.dataframe(filtered_df.head())

    # --- 객관식 점수 분석 섹션 (추후 구현) ---
    st.header("객관식 점수 분석")
    st.info("이 섹션은 추후 구현될 예정입니다.")

    # --- 주관식 분석 섹션 (추후 구현) ---
    st.header("주관식 분석")
    st.info("이 섹션은 추후 구현될 예정입니다.")

if __name__ == "__main__":
    main()
