import pandas as pd
import json
from pathlib import Path

def analyze_review_dummy(original_text):
    """더미 분석 함수 - 실제 API 호출 없이 테스트"""
    if not original_text or original_text.strip() == "" or str(original_text) == "nan":
        return {
            "original_text": original_text,
            "refined_text": "",
            "is_anonymized": False,
            "sentiment": "중립",
            "labels": []
        }
    
    # 간단한 키워드 기반 더미 분석
    text = str(original_text).lower()
    
    # 감정 분석
    positive_words = ["감사", "친절", "빠른", "좋", "만족"]
    negative_words = ["문제", "어려움", "부족", "강압적", "힘들"]
    
    sentiment = "긍정" if any(word in text for word in positive_words) else \
                "부정" if any(word in text for word in negative_words) else "중립"
    
    # 라벨 분류
    labels = []
    if "부서" in text or "담당" in text:
        labels.append("부서간 협업")
    if "소통" in text or "연락" in text:
        labels.append("직원간 소통")
    if "업무" in text or "처리" in text:
        labels.append("전문성 부족")
    if "태도" in text or "친절" in text:
        labels.append("업무 태도")
    if "감사" in text or "배려" in text:
        labels.append("상호 존중")
    
    return {
        "original_text": original_text,
        "refined_text": original_text,  # 더미에서는 그대로 유지
        "is_anonymized": False,
        "sentiment": sentiment,
        "labels": labels
    }

def process_csv_test(input_file, column_name="협업 후기", output_file=None, max_rows=50):
    """테스트용 CSV 처리 함수"""
    
    # CSV 파일 읽기 (인코딩 처리)
    try:
        df = pd.read_csv(input_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(input_file, encoding='cp949')
        except UnicodeDecodeError:
            df = pd.read_csv(input_file, encoding='euc-kr')
    
    print(f"CSV 파일 로드 완료: {len(df)} 행")
    
    # 컬럼 존재 확인
    if column_name not in df.columns:
        available_columns = list(df.columns)
        raise ValueError(f"'{column_name}' 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {available_columns}")
    
    # NaN이 아닌 값들만 필터링
    non_null_df = df[df[column_name].notna()].copy()
    print(f"'{column_name}' 컬럼에서 NaN이 아닌 값: {len(non_null_df)} 개")
    
    if max_rows:
        non_null_df = non_null_df.head(max_rows)
    
    if output_file is None:
        output_file = str(Path(input_file).stem) + "_test_processed.csv"
    
    results = []
    total_rows = len(non_null_df)
    
    print(f"총 {total_rows}개의 '{column_name}' 리뷰를 처리합니다...")
    
    for idx, (_, row) in enumerate(non_null_df.iterrows()):
        original_text = str(row[column_name])
        
        print(f"처리 중... ({idx + 1}/{total_rows}): {original_text[:50]}...")
        
        # 더미 리뷰 분석
        result = analyze_review_dummy(original_text)
        results.append(result)
    
    # 결과를 DataFrame으로 변환
    result_df = pd.DataFrame(results)
    
    # 원본 데이터와 결과를 합친 새로운 DataFrame 생성
    processed_df = non_null_df.copy()
    for col in result_df.columns:
        processed_df[f"{column_name}_{col}"] = result_df[col]
    
    # CSV 파일로 저장
    processed_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n처리 완료! 결과가 '{output_file}'에 저장되었습니다.")
    
    # 통계 출력
    sentiment_counts = result_df['sentiment'].value_counts()
    print(f"\n'{column_name}' 감정 분석 결과:")
    for sentiment, count in sentiment_counts.items():
        print(f"  {sentiment}: {count}개")
    
    # 라벨 통계
    all_labels = []
    for labels in result_df['labels']:
        all_labels.extend(labels)
    
    if all_labels:
        from collections import Counter
        label_counts = Counter(all_labels)
        print(f"\n라벨 분석 결과:")
        for label, count in label_counts.items():
            print(f"  {label}: {count}개")

def main():
    CSV_FILE = "설문조사_전처리데이터_20250620_0731.csv"
    COLUMN_NAME = "협업 후기"
    OUTPUT_FILE = "설문조사_전처리데이터_20250620_0731_test_processed.csv"
    
    try:
        process_csv_test(CSV_FILE, COLUMN_NAME, OUTPUT_FILE, max_rows=50)
    except Exception as e:
        import traceback
        print(f"오류 발생: {e}")
        print(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    main()