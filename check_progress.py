import pandas as pd
import json
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def check_excel_data():
    """Excel 파일의 현재 상태 확인"""
    print("=== 원본 데이터 분석 ===")
    
    # Excel 파일 읽기
    df = pd.read_excel('설문조사_전처리데이터_20250620_0731.xlsx', engine='openpyxl')
    
    print(f"📊 전체 데이터: {len(df):,}건")
    print(f"📝 '협업 후기' 컬럼 비어있지 않은 데이터: {df['협업 후기'].notna().sum():,}건")
    
    # 협업 후기 데이터만 추출
    feedback_data = df['협업 후기'].dropna()
    
    print(f"\n=== 협업 후기 데이터 샘플 (첫 5건) ===")
    for i, text in enumerate(feedback_data.head(5), 1):
        print(f"{i}. {str(text)[:100]}...")
    
    # 텍스트 길이 분포
    text_lengths = feedback_data.str.len()
    print(f"\n=== 텍스트 길이 통계 ===")
    print(f"평균 길이: {text_lengths.mean():.1f}자")
    print(f"최소 길이: {text_lengths.min()}자")
    print(f"최대 길이: {text_lengths.max()}자")
    print(f"중간값: {text_lengths.median():.1f}자")
    
    # 자주 등장하는 단어들 (간단한 분석)
    all_text = ' '.join(feedback_data.astype(str))
    words = all_text.split()
    word_counts = Counter(words)
    
    print(f"\n=== 자주 등장하는 단어 TOP 10 ===")
    for word, count in word_counts.most_common(10):
        print(f"{word}: {count}회")
    
    # 첫 5000건 확인
    first_5000 = df.head(5000)
    first_5000_feedback = first_5000['협업 후기'].dropna()
    
    print(f"\n=== 첫 5000건 중 협업 후기 데이터 ===")
    print(f"첫 5000건 중 피드백이 있는 건수: {len(first_5000_feedback):,}건")
    print(f"비율: {len(first_5000_feedback)/5000*100:.1f}%")
    
    return df, feedback_data

def analyze_sample_patterns(feedback_data, sample_size=100):
    """샘플 데이터의 패턴 분석"""
    print(f"\n=== 샘플 {sample_size}건 패턴 분석 ===")
    
    sample = feedback_data.head(sample_size)
    
    # 간단한 감정 분류 (키워드 기반)
    positive_keywords = ['감사', '만족', '좋', '훌륭', '친절', '빠르', '도움']
    negative_keywords = ['불만', '아쉬', '어려움', '늦', '불친절', '문제', '개선']
    neutral_keywords = ['없음', '해당없음', '무', '특별히']
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for text in sample:
        text_str = str(text).lower()
        
        if any(keyword in text_str for keyword in positive_keywords):
            positive_count += 1
        elif any(keyword in text_str for keyword in negative_keywords):
            negative_count += 1
        elif any(keyword in text_str for keyword in neutral_keywords):
            neutral_count += 1
        else:
            # 길이로 판단
            if len(text_str) < 10:
                neutral_count += 1
    
    print(f"긍정적 피드백 (추정): {positive_count}건 ({positive_count/sample_size*100:.1f}%)")
    print(f"부정적 피드백 (추정): {negative_count}건 ({negative_count/sample_size*100:.1f}%)")
    print(f"중립적 피드백 (추정): {neutral_count}건 ({neutral_count/sample_size*100:.1f}%)")
    print(f"기타: {sample_size - positive_count - negative_count - neutral_count}건")

def check_medical_terms(feedback_data, sample_size=100):
    """의료 용어 사용 빈도 확인"""
    print(f"\n=== 의료 용어 사용 빈도 (샘플 {sample_size}건) ===")
    
    medical_terms = [
        'ICU', 'ER', 'OR', 'CT', 'MRI', 'EMR', 'PACS', 'HIS', 'LIS',
        '응급실', '중환자실', '수술실', '외래', '병동', '간호사', '의사', '약사',
        '검사', '처방', '진료', '입원', '퇴원', '수술', '마취', '투약',
        '혈액', '방사선', '병리', '재활', '정형외과', '내과', '외과'
    ]
    
    sample = feedback_data.head(sample_size)
    term_counts = {}
    
    for term in medical_terms:
        count = sum(1 for text in sample if term in str(text))
        if count > 0:
            term_counts[term] = count
    
    # 빈도순 정렬
    sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
    
    print("발견된 의료 용어:")
    for term, count in sorted_terms[:15]:  # 상위 15개만 표시
        print(f"  {term}: {count}회 ({count/sample_size*100:.1f}%)")

def main():
    print("🔍 협업 후기 데이터 현황 분석")
    print("=" * 50)
    
    try:
        # 데이터 로드 및 기본 분석
        df, feedback_data = check_excel_data()
        
        # 패턴 분석
        analyze_sample_patterns(feedback_data, 200)
        
        # 의료 용어 분석
        check_medical_terms(feedback_data, 500)
        
        print(f"\n{'='*50}")
        print("✅ 분석 완료!")
        print("💡 AI 처리 시스템이 이 데이터들을 더 정확하고 체계적으로 분석할 예정입니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()