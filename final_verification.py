import pandas as pd
df = pd.read_excel('설문조사_전처리데이터_20250620_0731_processed.xlsx')

print('=== 수정된 시스템 최종 검증 ===')
print(f'총 분석된 데이터: {len(df)}개')

# 1. 원본-정제본 매칭 검증
problematic_cases = 0
for idx, row in df.iterrows():
    original = str(row['협업 후기']) if pd.notna(row['협업 후기']) else 'nan'
    refined = str(row['협업 후기_refined_text']) if pd.notna(row['협업 후기_refined_text']) else 'nan'
    
    # 원본 nan인데 정제본 존재하는 문제 케이스
    if original == 'nan' and refined != 'nan':
        problematic_cases += 1
        if problematic_cases <= 3:  # 첫 3개만 출력
            print(f'⚠️  문제 케이스 발견 - 인덱스 {idx}: 원본=nan, 정제="{refined}"')

print(f'\n원본 nan, 정제본 존재 문제 케이스: {problematic_cases}개')

# 2. 중복 refined_text 검증
refined_counts = df['협업 후기_refined_text'].value_counts()
duplicates = refined_counts[refined_counts > 1]
print(f'중복 refined_text: {len(duplicates)}개')

# 3. 정상 처리된 케이스 샘플
print('\n=== 정상 처리 샘플 ===')
normal_cases = df[(df['협업 후기'].notna()) & (df['협업 후기_refined_text'].notna())]
for idx, row in normal_cases.head(3).iterrows():
    original = str(row['협업 후기'])
    refined = str(row['협업 후기_refined_text'])
    sentiment = row['협업 후기_sentiment']
    confidence = row['협업 후기_quality_score']
    
    print(f'\n--- 샘플 {idx+1} ---')
    print(f'원본: {original}')
    print(f'정제: {refined}')
    print(f'감정: {sentiment}, 신뢰도: {confidence}')
    
    if original == refined:
        print('✅ 원본과 동일 (정제 불필요)')
    else:
        print('✅ 정상적으로 정제됨')

# 4. 품질 통계
print('\n=== 품질 개선 결과 ===')
high_quality = len(df[df['협업 후기_quality_score'] >= 7])
needs_review = len(df[df['협업 후기_needs_review'] == True])
print(f'고품질 분석 (신뢰도 7점 이상): {high_quality}개 ({high_quality/len(df)*100:.1f}%)')
print(f'재검토 필요: {needs_review}개 ({needs_review/len(df)*100:.1f}%)')

# 5. 비식별 처리 통계
anonymized = len(df[df['협업 후기_is_anonymized'] == True])
print(f'비식별 처리된 항목: {anonymized}개')

# 6. 부정 피드백 샘플 확인
print('\n=== 부정 피드백 샘플 (비식별 처리 확인) ===')
negative_cases = df[df['협업 후기_sentiment'] == '부정']
print(f'부정 피드백: {len(negative_cases)}개')
for idx, row in negative_cases.head(2).iterrows():
    print(f'\n인덱스 {idx}:')
    print(f'원본: {row["협업 후기"]}')
    print(f'정제: {row["협업 후기_refined_text"]}')
    print(f'비식별: {row["협업 후기_is_anonymized"]}')
    print(f'강도: {row["협업 후기_sentiment_intensity"]}')