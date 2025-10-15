#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
종합점수 결측값 정확한 카운트 확인
"""

import pandas as pd

# 원본 파일 로드
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
df['설문시행연도'] = df['설문시행연도'].astype(str)

print("=" * 80)
print("🔍 원본 데이터에서 종합점수 결측값 확인")
print("=" * 80)
print()

# 1. 원본 그대로 확인
print("1️⃣ 원본 데이터 (필터링 전)")
print("-" * 80)
missing_original = df['종합점수'].isna()
print(f"종합점수 결측값: {missing_original.sum()}행")

missing_by_year_original = df[missing_original]['설문시행연도'].value_counts().sort_index()
print("\n연도별 종합점수 결측값:")
total = 0
for year, count in missing_by_year_original.items():
    print(f"  {year}년: {count}행")
    total += count
print(f"  총계: {total}행")
print()

# 2. 부문/부서 필터링 후 확인
print("2️⃣ 부문/부서 필터링 후")
print("-" * 80)

EXCLUDE_DEPARTMENTS = ['미분류', '윤리경영실']
EXCLUDE_TEAMS = ['내분비외과']

df_filtered = df.copy()

# 부문 필터링
for exclude_dept in EXCLUDE_DEPARTMENTS:
    condition = (df_filtered['평가_부문'] != exclude_dept) & (df_filtered['피평가대상 부문'] != exclude_dept)
    df_filtered = df_filtered[condition]

# 부서 필터링
for exclude_team in EXCLUDE_TEAMS:
    condition = (df_filtered['평가_부서명'] != exclude_team) & (df_filtered['피평가대상 부서명'] != exclude_team)
    df_filtered = df_filtered[condition]

missing_filtered = df_filtered['종합점수'].isna()
print(f"종합점수 결측값: {missing_filtered.sum()}행")

missing_by_year_filtered = df_filtered[missing_filtered]['설문시행연도'].value_counts().sort_index()
print("\n연도별 종합점수 결측값:")
total = 0
for year, count in missing_by_year_filtered.items():
    print(f"  {year}년: {count}행")
    total += count
print(f"  총계: {total}행")
print()

# 3. 숫자 변환 후 확인
print("3️⃣ 숫자 변환 후 (pd.to_numeric)")
print("-" * 80)

df_filtered['종합점수_숫자'] = pd.to_numeric(df_filtered['종합점수'], errors='coerce')
missing_numeric = df_filtered['종합점수_숫자'].isna()
print(f"종합점수 결측값 (숫자 변환 후): {missing_numeric.sum()}행")

missing_by_year_numeric = df_filtered[missing_numeric]['설문시행연도'].value_counts().sort_index()
print("\n연도별 종합점수 결측값:")
total = 0
for year, count in missing_by_year_numeric.items():
    print(f"  {year}년: {count}행")
    total += count
print(f"  총계: {total}행")
print()

# 4. 차이 확인
print("4️⃣ 원본 vs 숫자변환 차이")
print("-" * 80)
print(f"원본 결측값: {missing_filtered.sum()}행")
print(f"숫자변환 후 결측값: {missing_numeric.sum()}행")
print(f"차이: {missing_numeric.sum() - missing_filtered.sum()}행")
print()

# 숫자 변환에서 추가로 결측이 된 데이터 확인
if missing_numeric.sum() > missing_filtered.sum():
    print("숫자 변환 시 추가로 결측이 된 데이터:")
    extra_missing = df_filtered[~missing_filtered & missing_numeric]
    print(extra_missing[['설문시행연도', '종합점수']].head(20))
