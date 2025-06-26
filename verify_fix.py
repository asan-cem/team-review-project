import pandas as pd

# 수정된 결과 확인
df = pd.read_excel('설문조사_전처리데이터_20250620_0731_processed.xlsx')

print('=== 수정 후 검증 결과 ===')
print(f'총 데이터: {len(df)}개')

# 원본과 정제본이 매칭되는지 확인
for idx, row in df.head(10).iterrows():
    original = str(row['협업 후기']) if pd.notna(row['협업 후기']) else 'nan'
    refined = str(row['협업 후기_refined_text']) if pd.notna(row['협업 후기_refined_text']) else 'nan'
    
    print(f'\n--- 인덱스 {idx} ---')
    print(f'원본: {original}')
    print(f'정제: {refined}')
    
    # 원본이 nan인데 정제본이 있는지 체크
    if original == 'nan' and refined != 'nan':
        print('⚠️  문제: 원본 nan, 정제본 존재')
    elif original != 'nan' and refined == 'nan':
        print('⚠️  문제: 원본 존재, 정제본 nan')
    elif original == refined:
        print('✅ 동일')
    else:
        print('✅ 정상적으로 정제됨')

# 중복 체크
print('\n=== 중복 refined_text 체크 ===')
refined_counts = df['협업 후기_refined_text'].value_counts()
duplicates = refined_counts[refined_counts > 1]
if len(duplicates) > 0:
    print(f'⚠️  중복되는 refined_text: {len(duplicates)}개')
    for text, count in duplicates.items():
        print(f'"{text}" : {count}번 반복')
else:
    print('✅ 중복 없음')