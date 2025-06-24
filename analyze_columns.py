import pandas as pd

# Excel 파일 읽기
df = pd.read_excel('설문조사_전처리데이터_20250620_0731.xlsx', engine='openpyxl')

print('=== 텍스트 데이터가 있는 컬럼들 ===')

# 협업 내용.1 컬럼 분석
col1 = '협업 내용.1'
non_null_count1 = df[col1].notna().sum()
print(f'📝 {col1}:')
print(f'   데이터 건수: {non_null_count1:,}건')
if non_null_count1 > 0:
    sample_data1 = df[col1].dropna().head(3)
    print('   샘플 데이터:')
    for i, text in enumerate(sample_data1, 1):
        print(f'   {i}. {str(text)[:80]}...')

print()

# 협업 후기 컬럼 분석  
col2 = '협업 후기'
non_null_count2 = df[col2].notna().sum()
print(f'📝 {col2}:')
print(f'   데이터 건수: {non_null_count2:,}건')
if non_null_count2 > 0:
    sample_data2 = df[col2].dropna().head(3)
    print('   샘플 데이터:')
    for i, text in enumerate(sample_data2, 1):
        print(f'   {i}. {str(text)[:80]}...')

print()

# 두 컬럼 교집합/합집합 분석
both_exist = df[(df[col1].notna()) & (df[col2].notna())]
either_exist = df[(df[col1].notna()) | (df[col2].notna())]

print(f'=== 데이터 분포 분석 ===')
print(f'두 컬럼 모두 데이터가 있는 건수: {len(both_exist):,}건')
print(f'어느 하나라도 데이터가 있는 건수: {len(either_exist):,}건')
print(f'협업 내용.1만 있는 건수: {non_null_count1 - len(both_exist):,}건')
print(f'협업 후기만 있는 건수: {non_null_count2 - len(both_exist):,}건')

# 샘플 데이터 생성 (두 컬럼 모두 포함)
print(f'\n=== 두 컬럼 모두 있는 샘플 데이터 ===')
if len(both_exist) > 0:
    sample_both = both_exist.head(5)
    for i, (idx, row) in enumerate(sample_both.iterrows(), 1):
        print(f'{i}. 협업 내용.1: {str(row[col1])[:60]}...')
        print(f'   협업 후기: {str(row[col2])[:60]}...')
        print()