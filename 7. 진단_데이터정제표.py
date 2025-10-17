#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 정제 과정 진단 스크립트

원본 Excel 파일과 정제 후 데이터의 차이를 단계별로 분석합니다.

작성일: 2025-01-15
"""

import pandas as pd
from pathlib import Path


def get_latest_text_processor_file():
    """
    rawdata 폴더에서 가장 최신의 text_processor_결과 파일을 찾아 반환합니다.

    Returns:
        str: 가장 최신 파일의 경로
    """
    rawdata_path = Path("rawdata")
    pattern = "2. text_processor_결과_*.xlsx"

    # _partial.xlsx 파일은 제외하고 검색
    files = [f for f in rawdata_path.glob(pattern) if not f.name.endswith('_partial.xlsx')]

    if not files:
        print(f"⚠️  '{pattern}' 패턴의 파일을 찾을 수 없습니다.")
        return "rawdata/2. text_processor_결과_20251013_093925.xlsx"  # 기본값

    # 파일명에서 타임스탬프를 추출하여 최신 파일 선택
    if len(files) > 1:
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        print(f"📁 최신 데이터 파일 자동 선택: {latest_file.name}")
        return str(latest_file)
    else:
        return str(files[0])


def extract_period_from_response_id(response_id):
    """
    response_id에서 연도와 반기를 추출하여 기간 표시 생성

    Args:
        response_id: response_id 값 (예: '2025_1_123', '2024_1_456')

    Returns:
        str: 기간 표시 (예: '2025년 상반기', '2024년')
    """
    try:
        parts = str(response_id).split('_')
        if len(parts) >= 2:
            year = parts[0]
            period = parts[1]

            # 2025년만 상반기/하반기로 구분
            if year == "2025":
                period_name = "상반기" if period == "1" else "하반기"
                return f"{year}년 {period_name}"
            else:
                # 나머지 연도는 연도만 표시
                return f"{year}년"
        return str(response_id)
    except:
        return str(response_id)


def analyze_data_cleaning_steps(split_mode=False):
    """
    데이터 정제 단계별 분석

    Args:
        split_mode (bool): True이면 2025년을 상하반기로 분리, False이면 연도별 통합
    """

    mode_text = "2025년 상하반기 분리" if split_mode else "연도별 통합"
    print("=" * 80)
    print(f"📊 데이터 정제 과정 진단 ({mode_text})")
    print("=" * 80)
    print()

    # 원본 파일 로드
    input_file = get_latest_text_processor_file()
    print(f"📁 파일 로드: {input_file}\n")

    df_original = pd.read_excel(input_file)

    # 컬럼명 정의 (원본과 동일)
    EXCEL_COLUMNS = [
        'response_id', '설문시행연도', '평가_부서명', '평가_부서명_원본', '평가_Unit명', '평가_부문',
        '피평가대상 부서명', '피평가대상_부서명_원본', '피평가대상 UNIT명', '피평가대상 부문',
        '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.',
        '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.',
        '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.',
        '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.',
        '전반적으로 ○○과의 협업에 대해 만족한다.',
        '종합점수', '극단값', '결측값', '협업 유형', '협업 후기', '정제된_텍스트',
        '비식별_처리', '감정_분류', '감정_강도_점수', '핵심_키워드', '의료_맥락', '신뢰도_점수'
    ]

    df_original.columns = EXCEL_COLUMNS

    # 컬럼명 매핑
    column_mapping = {
        '설문시행연도': '설문시행연도',
        '평가_부서명': '평가부서',
        '평가_부문': '평가부문',
        '피평가대상 부서명': '피평가부서',
        '피평가대상 부문': '피평가부문',
        '피평가대상 UNIT명': '피평가Unit',
        '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.': '존중배려',
        '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.': '정보공유',
        '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.': '명확처리',
        '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.': '태도개선',
        '전반적으로 ○○과의 협업에 대해 만족한다.': '전반만족',
        '종합점수': '종합점수',
        '협업 후기': '협업후기'
    }

    df_original = df_original.rename(columns=column_mapping)
    df_original['설문시행연도'] = df_original['설문시행연도'].astype(str)

    # 기간_표시 컬럼 추가
    if 'response_id' in df_original.columns:
        df_original['기간_표시'] = df_original['response_id'].apply(extract_period_from_response_id)
    else:
        df_original['기간_표시'] = df_original['설문시행연도'] + '년'

    # split_mode에 따라 집계 기준 결정
    group_column = '기간_표시' if split_mode else '설문시행연도'

    print("🔍 STEP 0: 원본 데이터")
    print("-" * 80)
    print(f"총 행수: {len(df_original):,}행\n")

    year_counts_original = df_original[group_column].value_counts().sort_index()
    period_label = "기간별" if split_mode else "연도별"
    print(f"{period_label} 행수:")
    for period, count in year_counts_original.items():
        print(f"  {period}: {count:,}행")
    print()

    # STEP 1: 부문 기준 제외
    print("🔍 STEP 1: 부문 기준 필터링 (미분류, 윤리경영실 제외)")
    print("-" * 80)

    EXCLUDE_DEPARTMENTS = ['미분류', '윤리경영실']
    df_step1 = df_original.copy()

    for exclude_dept in EXCLUDE_DEPARTMENTS:
        before = len(df_step1)
        condition = (df_step1['평가부문'] != exclude_dept) & (df_step1['피평가부문'] != exclude_dept)
        df_step1 = df_step1[condition]
        removed = before - len(df_step1)
        if removed > 0:
            print(f"  '{exclude_dept}' 제외: {removed:,}행 제거")

            # 기간별로 어떻게 제거되었는지 확인
            removed_data = df_original[~df_original.index.isin(df_step1.index)]
            removed_by_period = removed_data[
                (removed_data['평가부문'] == exclude_dept) |
                (removed_data['피평가부문'] == exclude_dept)
            ][group_column].value_counts().sort_index()

            if len(removed_by_period) > 0:
                for period, count in removed_by_period.items():
                    print(f"    - {period}: {count:,}행")

    print(f"\n총 남은 행수: {len(df_step1):,}행")

    year_counts_step1 = df_step1[group_column].value_counts().sort_index()
    print(f"\n{period_label} 행수:")
    for period, count in year_counts_step1.items():
        original_count = year_counts_original.get(period, 0)
        diff = original_count - count
        print(f"  {period}: {count:,}행 (원본 대비 -{diff:,}행)")
    print()

    # STEP 2: 부서 기준 제외
    print("🔍 STEP 2: 부서 기준 필터링 (내분비외과 제외)")
    print("-" * 80)

    EXCLUDE_TEAMS = ['내분비외과']
    df_step2 = df_step1.copy()

    for exclude_team in EXCLUDE_TEAMS:
        before = len(df_step2)
        condition = (df_step2['평가부서'] != exclude_team) & (df_step2['피평가부서'] != exclude_team)
        df_step2 = df_step2[condition]
        removed = before - len(df_step2)
        if removed > 0:
            print(f"  '{exclude_team}' 제외: {removed:,}행 제거")

            # 기간별로 어떻게 제거되었는지 확인
            removed_data = df_step1[~df_step1.index.isin(df_step2.index)]
            removed_by_period = removed_data[
                (removed_data['평가부서'] == exclude_team) |
                (removed_data['피평가부서'] == exclude_team)
            ][group_column].value_counts().sort_index()

            if len(removed_by_period) > 0:
                for period, count in removed_by_period.items():
                    print(f"    - {period}: {count:,}행")

    print(f"\n총 남은 행수: {len(df_step2):,}행")

    year_counts_step2 = df_step2[group_column].value_counts().sort_index()
    print(f"\n{period_label} 행수:")
    for period, count in year_counts_step2.items():
        original_count = year_counts_original.get(period, 0)
        diff = original_count - count
        print(f"  {period}: {count:,}행 (원본 대비 -{diff:,}행)")
    print()

    # STEP 3: 종합점수 결측값 제거
    print("🔍 STEP 3: 종합점수 결측값 제거")
    print("-" * 80)

    df_step3 = df_step2.copy()
    df_step3['종합점수'] = pd.to_numeric(df_step3['종합점수'], errors='coerce')

    before = len(df_step3)
    df_step3 = df_step3.dropna(subset=['종합점수'])
    removed = before - len(df_step3)

    print(f"  종합점수 결측값: {removed:,}행 제거")

    # 기간별로 어떻게 제거되었는지 확인
    removed_data = df_step2[~df_step2.index.isin(df_step3.index)]
    removed_by_period = removed_data[group_column].value_counts().sort_index()

    if len(removed_by_period) > 0:
        for period, count in removed_by_period.items():
            print(f"    - {period}: {count:,}행")

    print(f"\n총 남은 행수: {len(df_step3):,}행")

    year_counts_step3 = df_step3[group_column].value_counts().sort_index()
    print(f"\n{period_label} 행수:")
    for period, count in year_counts_step3.items():
        original_count = year_counts_original.get(period, 0)
        diff = original_count - count
        print(f"  {period}: {count:,}행 (원본 대비 -{diff:,}행)")
    print()

    # 최종 요약
    print("=" * 80)
    print("📋 최종 요약")
    print("=" * 80)
    print()

    period_column_name = '기간' if split_mode else '연도'
    summary_df = pd.DataFrame({
        period_column_name: sorted(year_counts_original.index),
        '원본': [year_counts_original.get(period, 0) for period in sorted(year_counts_original.index)],
        'STEP1_부문필터': [year_counts_step1.get(period, 0) for period in sorted(year_counts_original.index)],
        'STEP2_부서필터': [year_counts_step2.get(period, 0) for period in sorted(year_counts_original.index)],
        'STEP3_종합점수': [year_counts_step3.get(period, 0) for period in sorted(year_counts_original.index)]
    })

    summary_df['총_제거'] = summary_df['원본'] - summary_df['STEP3_종합점수']
    summary_df['제거율(%)'] = (summary_df['총_제거'] / summary_df['원본'] * 100).round(2)

    print(summary_df.to_string(index=False))
    print()

    # 상세 필터링 조건 저장
    print("💾 상세 분석 결과를 Excel로 저장합니다...")

    mode_suffix = '_반기별' if split_mode else '_연도별'
    output_file = f'진단_데이터정제표{mode_suffix}.xlsx'

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 요약
        summary_df.to_excel(writer, sheet_name='요약', index=False)

        # 부문 제외 상세
        excluded_divisions_cols = ['기간_표시', '설문시행연도', '평가부문', '피평가부문', '평가부서', '피평가부서'] if split_mode else ['설문시행연도', '평가부문', '피평가부문', '평가부서', '피평가부서']
        excluded_divisions = df_original[
            (df_original['평가부문'].isin(EXCLUDE_DEPARTMENTS)) |
            (df_original['피평가부문'].isin(EXCLUDE_DEPARTMENTS))
        ][[col for col in excluded_divisions_cols if col in df_original.columns]].copy()
        if len(excluded_divisions) > 0:
            excluded_divisions.to_excel(writer, sheet_name='제외_부문_상세', index=False)

        # 부서 제외 상세
        excluded_teams_cols = ['기간_표시', '설문시행연도', '평가부문', '피평가부문', '평가부서', '피평가부서'] if split_mode else ['설문시행연도', '평가부문', '피평가부문', '평가부서', '피평가부서']
        excluded_teams = df_step1[
            (df_step1['평가부서'].isin(EXCLUDE_TEAMS)) |
            (df_step1['피평가부서'].isin(EXCLUDE_TEAMS))
        ][[col for col in excluded_teams_cols if col in df_step1.columns]].copy()
        if len(excluded_teams) > 0:
            excluded_teams.to_excel(writer, sheet_name='제외_부서_상세', index=False)

        # 종합점수 결측값 상세
        missing_scores_cols = ['기간_표시', '설문시행연도', '평가부문', '피평가부문', '평가부서', '피평가부서', '종합점수'] if split_mode else ['설문시행연도', '평가부문', '피평가부문', '평가부서', '피평가부서', '종합점수']
        missing_scores = df_step2[pd.isna(pd.to_numeric(df_step2['종합점수'], errors='coerce'))][
            [col for col in missing_scores_cols if col in df_step2.columns]
        ].copy()
        if len(missing_scores) > 0:
            missing_scores.to_excel(writer, sheet_name='종합점수_결측_상세', index=False)

    print(f"✅ 저장 완료: {output_file}")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='데이터 정제 과정 진단')
    parser.add_argument('--split', action='store_true', help='2025년을 상하반기로 분리')

    args = parser.parse_args()

    analyze_data_cleaning_steps(split_mode=args.split)
