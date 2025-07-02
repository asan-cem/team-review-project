import pandas as pd
import ast

# 엑셀 파일 로드
df = pd.read_excel('설문조사_전처리데이터_20250620_0731_processed.xlsx')

print('=== 데이터프레임 기본 정보 ===')
print(f'- 전체 행 수: {len(df)}')
print(f'- 전체 컬럼 수: {len(df.columns)}')

print('\n=== 핵심_키워드 컬럼 분석 ===')
keyword_col = df['핵심_키워드']
print(f'- 전체 행 수: {len(keyword_col)}')
print(f'- 결측값(NaN): {keyword_col.isna().sum()}')

# 빈 문자열과 빈 리스트 확인
empty_str_count = (keyword_col == '').sum()
empty_list_count = (keyword_col == '[]').sum()
print(f'- 빈 문자열: {empty_str_count}')
print(f'- 빈 리스트 문자열: {empty_list_count}')

# 유효한 키워드가 있는 행들 찾기
valid_mask = keyword_col.notna() & (keyword_col != '') & (keyword_col != '[]')
valid_keywords = keyword_col[valid_mask]

print(f'- 유효한 키워드가 있는 행 수: {len(valid_keywords)}')

if len(valid_keywords) > 0:
    print('\n샘플 키워드 데이터:')
    for i, keyword in enumerate(valid_keywords.head(10).values):
        print(f'{i+1:2d}. {keyword}')

print('\n=== 부서/Unit 정보 ===')
dept_col = '피평가대상 부서명'
unit_col = '피평가대상 UNIT명'

if dept_col in df.columns:
    dept_counts = df[dept_col].value_counts().head(5)
    print(f'상위 5개 {dept_col}:')
    for dept, count in dept_counts.items():
        print(f'- {dept}: {count}개')

if unit_col in df.columns:
    unit_counts = df[unit_col].value_counts().head(5)
    print(f'\n상위 5개 {unit_col}:')
    for unit, count in unit_counts.items():
        print(f'- {unit}: {count}개')

print('\n=== 감정 분석 데이터 ===')
if '감정_분류' in df.columns:
    sentiment_counts = df['감정_분류'].value_counts()
    print('감정 분류 분포:')
    for sentiment, count in sentiment_counts.items():
        print(f'- {sentiment}: {count}개')

if '의료_맥락' in df.columns:
    context_col = df['의료_맥락']
    valid_context = context_col[context_col.notna() & (context_col != '') & (context_col != '[]')]
    print(f'\n의료_맥락 유효 데이터 수: {len(valid_context)}')
    if len(valid_context) > 0:
        print('샘플 의료_맥락 데이터:')
        for i, context in enumerate(valid_context.head(5).values):
            print(f'{i+1}. {context}')