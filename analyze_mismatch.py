import pandas as pd

# 현재 결과 파일 분석
df = pd.read_excel('설문조사_전처리데이터_20250620_0731_processed.xlsx')

print('=== 데이터 불일치 문제 상세 분석 ===')
print(f'전체 데이터: {len(df)}개')

mismatch_cases = []
for idx, row in df.head(20).iterrows():
    original = str(row['협업 후기']) if pd.notna(row['협업 후기']) else 'None'
    refined = str(row['협업 후기_refined_text']) if pd.notna(row['협업 후기_refined_text']) else 'None'
    
    print(f'\n=== 인덱스 {idx} ===')
    print(f'원본: {original}')
    print(f'정제: {refined}')
    
    if original != refined and original != 'None' and refined != 'None':
        mismatch_cases.append(idx)
        print(f'❌ 불일치 #{len(mismatch_cases)}')
    elif original == 'None' and refined != 'None':
        print('❌ 원본 없음, 정제본 존재')
    elif original != 'None' and refined == 'None':
        print('❌ 원본 존재, 정제본 없음')
    else:
        print('✅ 정상')

print(f'\n총 불일치 건수: {len(mismatch_cases)}개')
print(f'불일치 인덱스: {mismatch_cases}')

# 원본 파일도 확인
original_df = pd.read_excel('설문조사_전처리데이터_20250620_0731.xlsx')
print(f'\n원본 파일 크기: {len(original_df)}개')
print(f'원본 파일 상위 5개 협업 후기:')
for i in range(5):
    if i < len(original_df):
        value = str(original_df.iloc[i]['협업 후기']) if pd.notna(original_df.iloc[i]['협업 후기']) else 'None'
        print(f'  {i}: {value}')