import pandas as pd
import json
import time
import re
from pathlib import Path
import vertexai
from vertexai.generative_models import GenerativeModel
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import warnings
warnings.filterwarnings('ignore')

# 고도화된 프롬프트 템플릿
ADVANCED_PROMPT_TEMPLATE = """
[페르소나]
당신은 의료기관 내부 직원 만족도 및 협업 피드백을 분석하는 고급 AI 데이터 분석 전문가입니다. 의료 용어, 업무 용어, 약어에 대한 깊은 이해를 바탕으로 정확한 분석을 수행합니다.

[지시사항]
1. 주어진 원본 텍스트의 핵심 의미를 보존하면서, 오타와 문법을 교정하여 refined_text를 생성합니다.
2. 속거나 공격적인 표현은 전문적이고 정중한 표현으로 순화합니다.
3. **비식별 처리 규칙** (부정적 피드백이면서 아래 조건에 해당할 경우에만):
   - 실명이 명시된 경우 (예: "김민희 직원", "혈액은행 김현성 직원")
   - 소수 인원으로 특정 가능한 구체적 호칭 (예: "팀장", "과장", "대리", "여자 직원")
   - 부서명+직책이 결합된 경우 (예: "혈액은행 김현성", "마케팅팀 과장")
   **절대 규칙**: 긍정적이거나 중립적 피드백은 어떤 경우에도 is_anonymized를 false로 설정
4. "없음" 등 무의미한 텍스트는 refined_text를 빈 문자열로 처리합니다.

[감정 분석 - 2단계 분류]
**1단계 (주감정)**: "긍정", "부정", "중립" 중 하나
**2단계 (세부감정)**: 주감정에 따른 세부 분류
- 긍정: "만족", "감사", "칭찬", "격려", "기대"
- 부정: "불만", "실망", "분노", "우려", "비판"  
- 중립: "제안", "정보", "질문", "관찰", "기타"

[핵심 키워드 추출]
텍스트에서 가장 중요한 키워드 3-5개를 추출하세요. 의료 용어, 부서명, 업무 관련 용어를 우선적으로 포함하세요.

[분류 체계]
다음 중 해당하는 모든 라벨을 포함:
- "부서간 협업": 서로 다른 부서/팀 간의 업무 연계와 협력 문제
- "직원간 소통": 같은 부서/팀 내 동료 간의 소통 및 관계 문제  
- "전문성 부족": 개인의 업무 지식, 기술, 경험 부족 문제
- "업무 태도": 책임감, 적극성 등 업무를 대하는 자세 문제
- "상호 존중": 인격적 대우, 배려 등 관계에서의 예의 문제
- "시스템/프로세스": 업무 시스템, 절차, 환경 관련 문제
- "교육/훈련": 직원 교육, 역량 개발 관련 사항
- "리더십": 관리자, 팀장 등의 리더십 관련 사항

[출력 형식]
{{
  "refined_text": "정제된 텍스트",
  "is_anonymized": false,
  "primary_sentiment": "긍정/부정/중립",
  "detailed_sentiment": "세부감정",
  "sentiment_intensity": 감정강도점수(1-10),
  "keywords": ["키워드1", "키워드2", "키워드3"],
  "labels": ["라벨1", "라벨2"],
  "medical_terms": ["의료용어1", "의료용어2"] 
}}

원본 텍스트: "{original_text}"
"""

class AdvancedReviewAnalyzer:
    def __init__(self, project_id: str, location: str = "us-central1"):
        """고도화된 리뷰 분석기 초기화"""
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash")
        
        # 의료/업무 용어 사전
        self.medical_terms = {
            'OCS', 'EMR', 'PACS', 'HIS', 'LIS', 'RIS', 'EHR', 'ICU', 'ER', 'OR',
            '응급실', '중환자실', '수술실', '외래', '병동', '간호사', '의사', '약사',
            '검사실', '방사선과', '병리과', '재활의학과', '정형외과', '내과', '외과',
            '산부인과', '소아과', '정신과', '피부과', '안과', '이비인후과', '비뇨기과',
            '혈액은행', '임상병리', '진단검사', 'CT', 'MRI', 'X-ray', '초음파',
            '채혈', '투약', '처방', '진료', '입원', '퇴원', '수술', '마취'
        }
        
        self.batch_results = []
        
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if pd.isna(text) or str(text).strip() == "":
            return ""
            
        text = str(text)
        # 특수문자 정리 (의료용어 보존)
        text = re.sub(r'[^\w\s가-힣.,!?()/-]', ' ', text)
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_medical_terms(self, text: str) -> list:
        """의료/업무 용어 추출"""
        found_terms = []
        text_upper = text.upper()
        for term in self.medical_terms:
            if term in text_upper or term in text:
                found_terms.append(term)
        return found_terms
    
    def analyze_review(self, original_text: str) -> dict:
        """단일 리뷰 분석 (고도화)"""
        if not original_text or str(original_text).strip() == "":
            return {
                "original_text": original_text,
                "refined_text": "",
                "is_anonymized": False,
                "primary_sentiment": "중립",
                "detailed_sentiment": "기타",
                "sentiment_intensity": 5,
                "keywords": [],
                "labels": [],
                "medical_terms": []
            }
        
        # 전처리
        processed_text = self.preprocess_text(original_text)
        medical_terms = self.extract_medical_terms(processed_text)
        
        prompt = ADVANCED_PROMPT_TEMPLATE.format(original_text=processed_text)
        
        try:
            print(f"    🤖 AI 분석 중...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            print(f"    ✅ AI 응답 받음 ({len(response_text)}자)")
            
            # JSON 파싱
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    result = json.loads(json_text)
                    result["original_text"] = original_text
                    result["medical_terms"] = medical_terms
                    
                    # 결과 요약 표시
                    sentiment = result.get('primary_sentiment', '알 수 없음')
                    detailed = result.get('detailed_sentiment', '알 수 없음')
                    print(f"    📈 분석 결과: {sentiment} ({detailed})")
                    
                    return result
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
                    
            except json.JSONDecodeError:
                print(f"    ❌ JSON 파싱 실패: {processed_text[:50]}...")
                return self._create_fallback_result(original_text, processed_text, medical_terms)
                
        except Exception as e:
            print(f"    ❌ API 호출 실패: {e}")
            return self._create_fallback_result(original_text, processed_text, medical_terms)
    
    def _create_fallback_result(self, original_text: str, processed_text: str, medical_terms: list) -> dict:
        """API 실패 시 기본 결과 생성"""
        return {
            "original_text": original_text,
            "refined_text": processed_text,
            "is_anonymized": False,
            "primary_sentiment": "중립",
            "detailed_sentiment": "기타",
            "sentiment_intensity": 5,
            "keywords": [],
            "labels": [],
            "medical_terms": medical_terms
        }
    
    def process_batch(self, df_batch: pd.DataFrame, column_name: str, batch_num: int, delay: float = 0.1) -> pd.DataFrame:
        """배치 단위 처리"""
        print(f"\n=== 배치 {batch_num} 처리 시작 ({len(df_batch)}건) ===")
        start_time = time.time()
        
        results = []
        processed_count = 0
        
        for idx, row in df_batch.iterrows():
            original_text = str(row[column_name]) if pd.notna(row[column_name]) else ""
            
            # 더 자주 진행률 표시 (10건마다)
            if processed_count % 10 == 0:
                elapsed = time.time() - start_time
                if processed_count > 0:
                    avg_time_per_item = elapsed / processed_count
                    remaining_items = len(df_batch) - processed_count
                    estimated_remaining = avg_time_per_item * remaining_items
                    print(f"  📊 진행률: {processed_count + 1}/{len(df_batch)} ({(processed_count/len(df_batch)*100):.1f}%) | "
                          f"소요시간: {elapsed:.1f}초 | 예상 잔여시간: {estimated_remaining:.1f}초")
                else:
                    print(f"  📊 진행률: {processed_count + 1}/{len(df_batch)} (시작)")
            
            # 텍스트 처리 상태 표시
            if original_text.strip():
                print(f"  🔄 처리 중 #{processed_count + 1}: {original_text[:50]}...")
            else:
                print(f"  ⏭️  빈 텍스트 #{processed_count + 1}: 건너뜀")
            
            result = self.analyze_review(original_text)
            if "original_text" in result:
                del result["original_text"]
            results.append(result)
            
            processed_count += 1
            
            if delay > 0:
                time.sleep(delay)
        
        # 결과를 DataFrame으로 변환
        result_df = pd.DataFrame(results)
        
        # 원본 데이터와 결합
        processed_batch = df_batch.copy()
        for col in result_df.columns:
            processed_batch[f"{column_name}_{col}"] = result_df[col]
        
        # 배치 통계 출력
        self._print_batch_stats(result_df, batch_num)
        
        return processed_batch
    
    def _print_batch_stats(self, result_df: pd.DataFrame, batch_num: int):
        """배치 처리 통계 출력"""
        print(f"\n--- 배치 {batch_num} 처리 결과 ---")
        
        # 감정 분석 결과
        if 'primary_sentiment' in result_df.columns:
            sentiment_counts = result_df['primary_sentiment'].value_counts()
            print("주 감정 분포:")
            for sentiment, count in sentiment_counts.items():
                print(f"  {sentiment}: {count}건 ({count/len(result_df)*100:.1f}%)")
        
        # 세부 감정 분석
        if 'detailed_sentiment' in result_df.columns:
            detailed_counts = result_df['detailed_sentiment'].value_counts().head(5)
            print("세부 감정 TOP 5:")
            for sentiment, count in detailed_counts.items():
                print(f"  {sentiment}: {count}건")
        
        # 주요 라벨
        if 'labels' in result_df.columns:
            all_labels = []
            for labels in result_df['labels']:
                if isinstance(labels, list):
                    all_labels.extend(labels)
            if all_labels:
                label_counts = Counter(all_labels).most_common(5)
                print("주요 라벨 TOP 5:")
                for label, count in label_counts:
                    print(f"  {label}: {count}건")
        
        # 비식별 처리 비율
        if 'is_anonymized' in result_df.columns:
            anon_rate = result_df['is_anonymized'].sum() / len(result_df) * 100
            print(f"비식별 처리율: {anon_rate:.1f}%")
        
        print(f"--- 배치 {batch_num} 완료 ---\n")
    
    def generate_advanced_insights(self, df: pd.DataFrame, column_name: str) -> dict:
        """고급 인사이트 생성"""
        insights = {}
        
        # 감정 강도 분석
        if f'{column_name}_sentiment_intensity' in df.columns:
            intensity_stats = df[f'{column_name}_sentiment_intensity'].describe()
            insights['intensity_analysis'] = {
                'mean': intensity_stats['mean'],
                'median': intensity_stats['50%'],
                'high_intensity_count': (df[f'{column_name}_sentiment_intensity'] >= 8).sum(),
                'low_intensity_count': (df[f'{column_name}_sentiment_intensity'] <= 3).sum()
            }
        
        # 키워드 분석
        if f'{column_name}_keywords' in df.columns:
            all_keywords = []
            for keywords in df[f'{column_name}_keywords']:
                if isinstance(keywords, list):
                    all_keywords.extend(keywords)
            keyword_freq = Counter(all_keywords).most_common(20)
            insights['top_keywords'] = keyword_freq
        
        # 의료용어 사용 빈도
        if f'{column_name}_medical_terms' in df.columns:
            all_medical = []
            for terms in df[f'{column_name}_medical_terms']:
                if isinstance(terms, list):
                    all_medical.extend(terms)
            medical_freq = Counter(all_medical).most_common(10)
            insights['medical_terms_usage'] = medical_freq
        
        return insights
    
    def process_csv_advanced(self, input_file: str, column_name: str, batch_size: int = 5000, 
                           output_file: str = None, delay: float = 0.1):
        """고도화된 CSV/Excel 처리 (배치 단위)"""
        
        # 파일 확장자에 따라 읽기 방법 결정
        file_ext = Path(input_file).suffix.lower()
        
        if file_ext == '.xlsx' or file_ext == '.xls':
            # Excel 파일 읽기
            try:
                df = pd.read_excel(input_file, engine='openpyxl')
            except Exception as e:
                print(f"Excel 파일 읽기 실패: {e}")
                raise
        else:
            # CSV 파일 읽기
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(input_file, encoding='cp949')
                except UnicodeDecodeError:
                    df = pd.read_csv(input_file, encoding='euc-kr')
        
        if column_name not in df.columns:
            available_columns = list(df.columns)
            raise ValueError(f"'{column_name}' 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {available_columns}")
        
        total_rows = len(df)
        num_batches = (total_rows + batch_size - 1) // batch_size
        
        print(f"총 {total_rows}건을 {num_batches}개 배치로 나누어 처리합니다 (배치 크기: {batch_size})")
        
        if output_file is None:
            output_file = str(Path(input_file).stem) + "_advanced_processed.csv"
        
        processed_batches = []
        
        # 배치별 처리
        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, total_rows)
            batch_df = df.iloc[start_idx:end_idx].copy()
            
            processed_batch = self.process_batch(batch_df, column_name, i + 1, delay)
            processed_batches.append(processed_batch)
            
            # 중간 저장 (배치마다)
            batch_output = f"{Path(output_file).stem}_batch_{i+1}.csv"
            processed_batch.to_csv(batch_output, index=False, encoding='utf-8-sig')
            print(f"배치 {i+1} 결과가 '{batch_output}'에 저장되었습니다.")
            
            # 첫 번째 배치 후 사용자 확인
            if i == 0:
                print(f"\n{'='*50}")
                print("첫 번째 배치 처리가 완료되었습니다.")
                print("결과를 확인한 후 나머지 배치 처리 여부를 결정하세요.")
                print(f"{'='*50}")
                return processed_batch, f"첫 번째 배치만 처리 완료. 파일: {batch_output}"
        
        # 전체 결과 합치기
        final_df = pd.concat(processed_batches, ignore_index=True)
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        # 고급 인사이트 생성
        insights = self.generate_advanced_insights(final_df, column_name)
        
        # 인사이트 저장
        insights_file = f"{Path(output_file).stem}_insights.json"
        with open(insights_file, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)
        
        print(f"전체 처리 완료! 최종 결과: '{output_file}', 인사이트: '{insights_file}'")
        return final_df, insights

def main():
    """메인 실행 함수"""
    PROJECT_ID = "mindmap-462708"
    EXCEL_FILE = "설문조사_전처리데이터_20250620_0731.xlsx"
    COLUMN_NAME = "협업 후기"
    BATCH_SIZE = 5000
    OUTPUT_FILE = "설문조사_전처리데이터_20250620_0731_advanced_processed.csv"
    
    try:
        analyzer = AdvancedReviewAnalyzer(project_id=PROJECT_ID)
        
        # 첫 5천건 처리 (지연시간 단축)
        result, message = analyzer.process_csv_advanced(
            EXCEL_FILE, 
            COLUMN_NAME, 
            batch_size=BATCH_SIZE,
            output_file=OUTPUT_FILE,
            delay=0.05  # 지연시간을 0.1초에서 0.05초로 단축
        )
        
        print(f"\n처리 완료: {message}")
        
    except Exception as e:
        import traceback
        print(f"오류 발생: {e}")
        print(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    main()