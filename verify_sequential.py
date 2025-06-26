import pandas as pd

# 원본 파일과 처리된 파일 비교
original_df = pd.read_excel('설문조사_전처리데이터_20250620_0731.xlsx')
processed_df = pd.read_excel('설문조사_전처리데이터_20250620_0731_processed.xlsx')

print('=== 순차 추출 후 데이터 일치성 검증 ===')
print(f'원본 파일 크기: {len(original_df)}개')
print(f'처리된 파일 크기: {len(processed_df)}개')

# 상위 20개 비교
print('\n=== 상위 20개 데이터 비교 ===')
for i in range(min(20, len(processed_df))):
    original_text = str(original_df.iloc[i]['협업 후기']) if pd.notna(original_df.iloc[i]['협업 후기']) else 'None'
    processed_original = str(processed_df.iloc[i]['협업 후기']) if pd.notna(processed_df.iloc[i]['협업 후기']) else 'None'
    refined_text = str(processed_df.iloc[i]['협업 후기_refined_text']) if pd.notna(processed_df.iloc[i]['협업 후기_refined_text']) else 'None'
    
    print(f'\n--- 인덱스 {i} ---')
    print(f'원본파일: {original_text}')
    print(f'처리파일 원본: {processed_original}')
    print(f'처리파일 정제: {refined_text}')
    
    # 원본 파일과 처리된 파일의 원본 컬럼 비교
    if original_text != processed_original:
        print('❌ 원본 파일과 처리된 파일의 원본 데이터 불일치!')
    else:
        print('✅ 원본 데이터 일치')
    
    # 처리된 파일 내에서 원본과 정제본 비교
    if processed_original == 'None' and refined_text == 'None':
        print('✅ 빈 데이터 정상 처리')
    elif processed_original != 'None' and refined_text == 'None':
        print('❌ 원본 있는데 정제본 없음')
    elif processed_original == 'None' and refined_text != 'None':
        print('❌ 원본 없는데 정제본 있음')
    elif processed_original == refined_text:
        print('✅ 정제 불필요 (원본과 동일)')
    else:
        print('✅ 정상 정제됨')

# 통계
print('\n=== 전체 통계 ===')
match_count = 0
mismatch_count = 0
for i in range(len(processed_df)):
    if i < len(original_df):
        original_text = str(original_df.iloc[i]['협업 후기']) if pd.notna(original_df.iloc[i]['협업 후기']) else 'None'
        processed_original = str(processed_df.iloc[i]['협업 후기']) if pd.notna(processed_df.iloc[i]['협업 후기']) else 'None'
        
        if original_text == processed_original:
            match_count += 1
        else:
            mismatch_count += 1

print(f'데이터 일치: {match_count}개')
print(f'데이터 불일치: {mismatch_count}개')
print(f'일치율: {match_count/len(processed_df)*100:.1f}%')