#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연도별 통계 분석 스크립트

다음 데이터를 Excel 파일로 추출:
1. 연도별 문항별 점수 (평균, 표준편차, 표본수)
2. 부문별 종합점수 (연도별, 표본수 포함)
3. 부문별 부서 종합점수 (연도별, 표본수 포함)

출력: 상호평가_요약_연도별.xlsx (60KB)
기간: 2022년, 2023년, 2024년, 2025년 (4개 연도)

사용법:
    python "4. 연도별_통계분석.py"

작성일: 2025-01-15
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# src 폴더를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.dashboard_builder import (
    load_data,
    preprocess_data_types,
    clean_data,
    SCORE_COLUMNS
)


def extract_yearly_question_scores(df):
    """
    연도별 문항별 점수 추출

    Args:
        df (pd.DataFrame): 정제된 데이터프레임

    Returns:
        pd.DataFrame: 연도별 문항별 점수 (평균, 표준편차, 표본수)
    """
    print("📊 1. 연도별 문항별 점수 추출 중...")

    results = []

    for year in sorted(df['설문시행연도'].unique()):
        if pd.notna(year):
            year_data = df[df['설문시행연도'] == year]

            row = {'연도': year}

            # 각 문항별 통계 계산
            for col in SCORE_COLUMNS:
                if col in year_data.columns:
                    scores = year_data[col].dropna()
                    row[f'{col}_평균'] = scores.mean()
                    row[f'{col}_표준편차'] = scores.std()
                    row[f'{col}_표본수'] = len(scores)

            # 전체 표본수
            row['전체_표본수'] = len(year_data)

            results.append(row)

    result_df = pd.DataFrame(results)
    print(f"   ✅ {len(result_df)}개 연도 처리 완료")

    return result_df


def extract_division_scores(df):
    """
    부문별 종합점수 추출 (연도별)

    Args:
        df (pd.DataFrame): 정제된 데이터프레임

    Returns:
        pd.DataFrame: 부문별 종합점수 (연도별, 표본수 포함)
    """
    print("📊 2. 부문별 종합점수 추출 중...")

    results = []

    for year in sorted(df['설문시행연도'].unique()):
        if pd.notna(year):
            year_data = df[df['설문시행연도'] == year]

            for division in sorted(year_data['피평가부문'].unique()):
                if pd.notna(division) and division != 'N/A':
                    div_year_data = year_data[year_data['피평가부문'] == division]

                    if len(div_year_data) > 0:
                        row = {
                            '연도': year,
                            '부문': division,
                            '표본수': len(div_year_data)
                        }

                        # 각 문항별 평균 점수
                        for col in SCORE_COLUMNS:
                            if col in div_year_data.columns:
                                scores = div_year_data[col].dropna()
                                row[f'{col}_평균'] = scores.mean()
                                row[f'{col}_표준편차'] = scores.std()

                        results.append(row)

    result_df = pd.DataFrame(results)
    print(f"   ✅ {len(result_df)}개 부문-연도 조합 처리 완료")

    return result_df


def extract_department_scores_by_division(df):
    """
    부문별 부서 종합점수 추출 (연도별)

    Args:
        df (pd.DataFrame): 정제된 데이터프레임

    Returns:
        pd.DataFrame: 부문별 부서 종합점수 (연도별, 표본수 포함)
    """
    print("📊 3. 부문별 부서 종합점수 추출 중...")

    results = []

    for year in sorted(df['설문시행연도'].unique()):
        if pd.notna(year):
            year_data = df[df['설문시행연도'] == year]

            for division in sorted(year_data['피평가부문'].unique()):
                if pd.notna(division) and division != 'N/A':
                    div_year_data = year_data[year_data['피평가부문'] == division]

                    for dept in sorted(div_year_data['피평가부서'].unique()):
                        if pd.notna(dept) and dept != 'N/A':
                            dept_data = div_year_data[div_year_data['피평가부서'] == dept]

                            if len(dept_data) > 0:
                                row = {
                                    '연도': year,
                                    '부문': division,
                                    '부서': dept,
                                    '표본수': len(dept_data)
                                }

                                # 각 문항별 평균 점수
                                for col in SCORE_COLUMNS:
                                    if col in dept_data.columns:
                                        scores = dept_data[col].dropna()
                                        row[f'{col}_평균'] = scores.mean()
                                        row[f'{col}_표준편차'] = scores.std()

                                results.append(row)

    result_df = pd.DataFrame(results)
    print(f"   ✅ {len(result_df)}개 부문-부서-연도 조합 처리 완료")

    return result_df


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("📊 연도별 통계 분석 (2022~2025년)")
    print("=" * 60)
    print()

    try:
        # 1. 데이터 로드 및 전처리
        print("📁 데이터 로드 중...")
        input_file = 'rawdata/2. text_processor_결과_20251013_093925.xlsx'
        df = load_data(input_file)

        print("🔄 데이터 전처리 중...")
        df = preprocess_data_types(df)
        df = clean_data(df)

        print(f"✅ 전처리 완료: {len(df):,}행\n")

        # 2. 데이터 추출
        yearly_questions = extract_yearly_question_scores(df)
        division_scores = extract_division_scores(df)
        department_scores = extract_department_scores_by_division(df)

        # 3. Excel 저장
        print("\n💾 Excel 파일 저장 중...")
        output_file = '상호평가_요약_연도별.xlsx'
        output_path = (Path(output_file)).absolute()

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: 연도별 문항별 점수
            yearly_questions.to_excel(
                writer,
                sheet_name='연도별_문항별_점수',
                index=False
            )

            # Sheet 2: 부문별 종합점수
            division_scores.to_excel(
                writer,
                sheet_name='부문별_종합점수',
                index=False
            )

            # Sheet 3: 부문별 부서 종합점수
            department_scores.to_excel(
                writer,
                sheet_name='부문별_부서_종합점수',
                index=False
            )

        print(f"✅ Excel 파일 저장 완료")
        print()
        print("📂 생성된 파일:")
        print(f"   {output_path}")
        print()
        print("📋 포함된 시트:")
        print(f"   1. 연도별_문항별_점수: {len(yearly_questions)}행")
        print(f"   2. 부문별_종합점수: {len(division_scores)}행")
        print(f"   3. 부문별_부서_종합점수: {len(department_scores)}행")
        print()
        print("✨ 연도별 통계 분석 완료!")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
