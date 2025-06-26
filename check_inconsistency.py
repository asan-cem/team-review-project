import pandas as pd

# 데이터 로드
df = pd.read_excel('설문조사_전처리데이터_20250620_0731_processed.xlsx')

print('=== 협업 후기 vs refined_text 불일치 문제 분석 ===')

# 원본과 정제본 비교
comparison_data = []
for idx, row in df.iterrows():
    original = str(row['협업 후기']) if pd.notna(row['협업 후기']) else 'nan'
    refined = str(row['협업 후기_refined_text']) if pd.notna(row['협업 후기_refined_text']) else 'nan'
    
    # 내용이 다른 경우만 추출
    if original != 'nan' and refined != 'nan' and original != refined:
        comparison_data.append({
            'index': idx,
            'original': original,
            'refined': refined
        })

print(f'전체 {len(df)}개 중 원본과 정제본이 다른 케이스: {len(comparison_data)}개')

# 처음 5개 불일치 사례 출력
print('\n=== 불일치 사례 샘플 ===')
for i, case in enumerate(comparison_data[:5]):
    print(f'\n--- 사례 {i+1} (인덱스: {case["index"]}) ---')
    print(f'원본: {case["original"]}')
    print(f'정제: {case["refined"]}')
    print(f'길이 변화: {len(case["original"])} → {len(case["refined"])}')

# 원본이 nan인데 refined_text가 있는 경우 (이상한 케이스)
print('\n=== 원본 nan, 정제본 존재 케이스 (문제 케이스) ===')
nan_original = df[(df['협업 후기'].isna()) & (df['협업 후기_refined_text'].notna())]
print(f'이런 케이스: {len(nan_original)}개')
for idx, row in nan_original.head(5).iterrows():
    print(f'인덱스 {idx}: refined_text = "{str(row["협업 후기_refined_text"])}"')

# 동일한 내용이 들어가는 케이스 확인
print('\n=== 동일한 refined_text가 반복되는 케이스 ===')
refined_counts = df['협업 후기_refined_text'].value_counts()
duplicates = refined_counts[refined_counts > 1]
print(f'중복되는 refined_text: {len(duplicates)}개')
for text, count in duplicates.head(3).items():
    print(f'"{text}" : {count}번 반복')
    # 해당 텍스트를 가진 원본들 확인
    matching_rows = df[df['협업 후기_refined_text'] == text]
    for idx, row in matching_rows.head(3).iterrows():
        original = str(row['협업 후기']) if pd.notna(row['협업 후기']) else 'nan'
        print(f'  인덱스 {idx}: 원본 = "{original}"')
    print()