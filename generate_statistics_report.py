#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
협업평가 데이터 통계 보고서 생성

보고서 마지막 장에 첨부할 상세 통계 표 생성:
1. 연도별 표본 현황 (원본, 집계, 제외)
2. 제외 사유별 상세 통계
3. 부문별 표본 현황
4. 연도별 데이터 품질 지표

출력: 협업평가_통계보고서.xlsx

작성일: 2025-01-15
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_and_prepare_data():
    """원본 데이터 로드 및 기본 준비"""

    input_file = 'rawdata/2. text_processor_결과_20251013_093925.xlsx'
    print(f"📁 파일 로드: {input_file}\n")

    df = pd.read_excel(input_file)

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

    df.columns = EXCEL_COLUMNS

    column_mapping = {
        '설문시행연도': '설문시행연도',
        '평가_부서명': '평가부서',
        '평가_부문': '평가부문',
        '피평가대상 부서명': '피평가부서',
        '피평가대상 부문': '피평가부문',
        '피평가대상 UNIT명': '피평가Unit',
    }

    df = df.rename(columns=column_mapping)
    df['설문시행연도'] = df['설문시행연도'].astype(str)

    return df


def generate_yearly_summary(df_original, df_filtered, df_final):
    """연도별 표본 현황 요약표"""

    print("📊 1. 연도별 표본 현황 생성 중...")

    years = sorted(df_original['설문시행연도'].unique())

    summary = []
    for year in years:
        original_count = len(df_original[df_original['설문시행연도'] == year])
        filtered_count = len(df_filtered[df_filtered['설문시행연도'] == year])
        final_count = len(df_final[df_final['설문시행연도'] == year])

        excluded_total = original_count - final_count
        excluded_division = original_count - filtered_count
        excluded_score = filtered_count - final_count

        summary.append({
            '연도': f"{year}년",
            '원본_표본수': original_count,
            '집계_표본수': final_count,
            '제외_표본수': excluded_total,
            '제외_비율(%)': round(excluded_total / original_count * 100, 2),
            '부문제외': excluded_division,
            '점수결측': excluded_score,
            '데이터품질(%)': round(final_count / original_count * 100, 2)
        })

    # 전체 합계
    summary.append({
        '연도': '전체',
        '원본_표본수': len(df_original),
        '집계_표본수': len(df_final),
        '제외_표본수': len(df_original) - len(df_final),
        '제외_비율(%)': round((len(df_original) - len(df_final)) / len(df_original) * 100, 2),
        '부문제외': len(df_original) - len(df_filtered),
        '점수결측': len(df_filtered) - len(df_final),
        '데이터품질(%)': round(len(df_final) / len(df_original) * 100, 2)
    })

    df_summary = pd.DataFrame(summary)
    print(f"   ✅ {len(df_summary)}개 행 생성\n")

    return df_summary


def generate_exclusion_details(df_original):
    """제외 사유별 상세 통계"""

    print("📊 2. 제외 사유별 상세 통계 생성 중...")

    EXCLUDE_DEPARTMENTS = ['미분류', '윤리경영실']
    EXCLUDE_TEAMS = ['내분비외과']

    years = sorted(df_original['설문시행연도'].unique())

    details = []

    # 1. 미분류 부문
    for year in years:
        year_data = df_original[df_original['설문시행연도'] == year]
        excluded = year_data[
            (year_data['평가부문'] == '미분류') |
            (year_data['피평가부문'] == '미분류')
        ]

        if len(excluded) > 0:
            details.append({
                '연도': f"{year}년",
                '제외사유': '부문: 미분류',
                '제외건수': len(excluded),
                '비고': '분석 대상 부문 아님'
            })

    # 2. 윤리경영실
    for year in years:
        year_data = df_original[df_original['설문시행연도'] == year]
        excluded = year_data[
            (year_data['평가부문'] == '윤리경영실') |
            (year_data['피평가부문'] == '윤리경영실')
        ]

        if len(excluded) > 0:
            details.append({
                '연도': f"{year}년",
                '제외사유': '부문: 윤리경영실',
                '제외건수': len(excluded),
                '비고': '분석 대상 부문 아님'
            })

    # 3. 내분비외과
    for year in years:
        year_data = df_original[df_original['설문시행연도'] == year]
        excluded = year_data[
            (year_data['평가부서'] == '내분비외과') |
            (year_data['피평가부서'] == '내분비외과')
        ]

        if len(excluded) > 0:
            details.append({
                '연도': f"{year}년",
                '제외사유': '부서: 내분비외과',
                '제외건수': len(excluded),
                '비고': '분석 대상 부서 아님'
            })

    # 4. 종합점수 결측
    for year in years:
        year_data = df_original[df_original['설문시행연도'] == year]
        # 부문/부서 필터 먼저 적용
        filtered = year_data.copy()
        for dept in EXCLUDE_DEPARTMENTS:
            filtered = filtered[
                (filtered['평가부문'] != dept) &
                (filtered['피평가부문'] != dept)
            ]
        for team in EXCLUDE_TEAMS:
            filtered = filtered[
                (filtered['평가부서'] != team) &
                (filtered['피평가부서'] != team)
            ]

        excluded = filtered[filtered['종합점수'].isna()]

        if len(excluded) > 0:
            details.append({
                '연도': f"{year}년",
                '제외사유': '종합점수 결측',
                '제외건수': len(excluded),
                '비고': '분석 필수 항목 누락'
            })

    df_details = pd.DataFrame(details)
    print(f"   ✅ {len(df_details)}개 행 생성\n")

    return df_details


def generate_division_summary(df_final):
    """부문별 표본 현황"""

    print("📊 3. 부문별 표본 현황 생성 중...")

    years = sorted(df_final['설문시행연도'].unique())
    divisions = sorted(df_final['피평가부문'].unique())

    summary = []

    for division in divisions:
        if division == 'N/A':
            continue

        row = {'부문': division}

        for year in years:
            count = len(df_final[
                (df_final['설문시행연도'] == year) &
                (df_final['피평가부문'] == division)
            ])
            row[f"{year}년"] = count

        row['전체'] = len(df_final[df_final['피평가부문'] == division])
        summary.append(row)

    # 전체 합계
    total_row = {'부문': '전체'}
    for year in years:
        total_row[f"{year}년"] = len(df_final[df_final['설문시행연도'] == year])
    total_row['전체'] = len(df_final)
    summary.append(total_row)

    df_summary = pd.DataFrame(summary)
    print(f"   ✅ {len(df_summary)}개 부문 생성\n")

    return df_summary


def generate_department_summary(df_final):
    """부서별 표본 현황 (부문별로 그룹화)"""

    print("📊 4. 부서별 표본 현황 생성 중...")

    years = sorted(df_final['설문시행연도'].unique())

    summary = []

    for division in sorted(df_final['피평가부문'].unique()):
        if division == 'N/A':
            continue

        div_data = df_final[df_final['피평가부문'] == division]
        departments = sorted(div_data['피평가부서'].unique())

        for dept in departments:
            if dept == 'N/A':
                continue

            row = {
                '부문': division,
                '부서': dept
            }

            for year in years:
                count = len(df_final[
                    (df_final['설문시행연도'] == year) &
                    (df_final['피평가부문'] == division) &
                    (df_final['피평가부서'] == dept)
                ])
                row[f"{year}년"] = count

            row['전체'] = len(df_final[
                (df_final['피평가부문'] == division) &
                (df_final['피평가부서'] == dept)
            ])

            summary.append(row)

    df_summary = pd.DataFrame(summary)
    print(f"   ✅ {len(df_summary)}개 부서 생성\n")

    return df_summary


def generate_quality_indicators(df_original, df_final):
    """연도별 데이터 품질 지표"""

    print("📊 5. 데이터 품질 지표 생성 중...")

    years = sorted(df_original['설문시행연도'].unique())

    indicators = []

    for year in years:
        original = df_original[df_original['설문시행연도'] == year]
        final = df_final[df_final['설문시행연도'] == year]

        # 점수 컬럼 확인
        score_cols = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수']
        available_scores = [col for col in score_cols if col in original.columns]

        # 종합점수 결측 비율
        missing_score_ratio = (original['종합점수'].isna().sum() / len(original) * 100) if len(original) > 0 else 0

        # 응답 완성도 (모든 점수 항목이 있는 비율)
        complete_responses = 0
        if len(original) > 0:
            complete_mask = True
            for col in available_scores:
                if col in original.columns:
                    complete_mask &= original[col].notna()
            complete_responses = complete_mask.sum() / len(original) * 100

        indicators.append({
            '연도': f"{year}년",
            '원본표본수': len(original),
            '최종표본수': len(final),
            '데이터유효율(%)': round(len(final) / len(original) * 100, 2) if len(original) > 0 else 0,
            '종합점수결측률(%)': round(missing_score_ratio, 2),
            '응답완성도(%)': round(complete_responses, 2),
            '부문제외건수': len(original) - len(final[final['설문시행연도'] == year]),
        })

    df_indicators = pd.DataFrame(indicators)
    print(f"   ✅ {len(df_indicators)}개 연도 생성\n")

    return df_indicators


def main():
    """메인 실행 함수"""

    print("=" * 80)
    print("📊 협업평가 통계 보고서 생성")
    print("=" * 80)
    print()

    # 데이터 로드
    df_original = load_and_prepare_data()

    # 필터링 적용
    print("🔄 데이터 필터링 적용 중...\n")

    EXCLUDE_DEPARTMENTS = ['미분류', '윤리경영실']
    EXCLUDE_TEAMS = ['내분비외과']

    # STEP 1: 부문 필터
    df_filtered = df_original.copy()
    for dept in EXCLUDE_DEPARTMENTS:
        df_filtered = df_filtered[
            (df_filtered['평가부문'] != dept) &
            (df_filtered['피평가부문'] != dept)
        ]

    # STEP 2: 부서 필터
    for team in EXCLUDE_TEAMS:
        df_filtered = df_filtered[
            (df_filtered['평가부서'] != team) &
            (df_filtered['피평가부서'] != team)
        ]

    # STEP 3: 종합점수 결측 제거
    df_final = df_filtered[df_filtered['종합점수'].notna()].copy()

    print(f"원본: {len(df_original):,}행")
    print(f"필터링 후: {len(df_filtered):,}행")
    print(f"최종: {len(df_final):,}행\n")

    # 각종 통계표 생성
    yearly_summary = generate_yearly_summary(df_original, df_filtered, df_final)
    exclusion_details = generate_exclusion_details(df_original)
    division_summary = generate_division_summary(df_final)
    department_summary = generate_department_summary(df_final)
    quality_indicators = generate_quality_indicators(df_original, df_final)

    # Excel 저장
    print("💾 Excel 파일 저장 중...")
    output_file = '협업평가_통계보고서.xlsx'

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: 연도별 표본 현황
        yearly_summary.to_excel(
            writer,
            sheet_name='1.연도별_표본현황',
            index=False
        )

        # Sheet 2: 제외 사유별 상세
        exclusion_details.to_excel(
            writer,
            sheet_name='2.제외사유_상세',
            index=False
        )

        # Sheet 3: 부문별 표본 현황
        division_summary.to_excel(
            writer,
            sheet_name='3.부문별_표본현황',
            index=False
        )

        # Sheet 4: 부서별 표본 현황
        department_summary.to_excel(
            writer,
            sheet_name='4.부서별_표본현황',
            index=False
        )

        # Sheet 5: 데이터 품질 지표
        quality_indicators.to_excel(
            writer,
            sheet_name='5.데이터품질_지표',
            index=False
        )

    print(f"✅ Excel 파일 저장 완료: {output_file}\n")

    # 요약 출력
    print("=" * 80)
    print("📋 생성된 보고서 내용")
    print("=" * 80)
    print()
    print("📑 Sheet 1: 연도별 표본 현황")
    print("   - 원본/집계/제외 표본수")
    print("   - 제외 비율 및 사유별 분류")
    print("   - 데이터 품질 비율")
    print()
    print("📑 Sheet 2: 제외 사유별 상세")
    print("   - 연도별 제외 사유 및 건수")
    print("   - 미분류, 윤리경영실, 내분비외과, 종합점수 결측")
    print()
    print("📑 Sheet 3: 부문별 표본 현황")
    print("   - 부문별 연도별 표본수")
    print("   - 부문별 전체 합계")
    print()
    print("📑 Sheet 4: 부서별 표본 현황")
    print("   - 부문별로 그룹화된 부서 현황")
    print("   - 부서별 연도별 표본수")
    print()
    print("📑 Sheet 5: 데이터 품질 지표")
    print("   - 데이터 유효율")
    print("   - 종합점수 결측률")
    print("   - 응답 완성도")
    print()
    print("✨ 보고서 생성 완료!")
    print()


if __name__ == "__main__":
    main()
