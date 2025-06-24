import pandas as pd
import json
import time
from pathlib import Path
import vertexai
from vertexai.generative_models import GenerativeModel
import warnings
warnings.filterwarnings('ignore')

# 간소화된 프롬프트 템플릿
QUICK_PROMPT_TEMPLATE = """
[분석 지시사항]
다음 협업 후기를 분석하여 JSON 형태로 결과를 제공하세요.

[감정 분석]
- primary_sentiment: "긍정", "부정", "중립" 중 하나
- detailed_sentiment: 긍정(감사,만족,칭찬), 부정(불만,실망,비판), 중립(제안,정보,기타)
- sentiment_intensity: 1-10 점수 (1-2:매우약함, 3-4:약함, 5-6:보통, 7-8:강함, 9-10:매우강함)

[키워드 및 분류]
- keywords: 핵심 키워드 3개
- labels: 해당하는 분류 ("부서간 협업", "직원간 소통", "업무 태도", "시스템/프로세스" 등)

[출력 형식]
{{
  "refined_text": "정제된 텍스트",
  "is_anonymized": false,
  "primary_sentiment": "긍정/부정/중립",
  "detailed_sentiment": "세부감정",
  "sentiment_intensity": 감정강도점수(1-10),
  "keywords": ["키워드1", "키워드2", "키워드3"],
  "labels": ["라벨1", "라벨2"]
}}

원본 텍스트: "{original_text}"
"""

class QuickAnalyzer:
    def __init__(self, project_id: str, location: str = "us-central1"):
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash")
    
    def analyze_review(self, original_text: str) -> dict:
        """빠른 리뷰 분석"""
        if not original_text or str(original_text).strip() == "":
            return {
                "refined_text": "",
                "is_anonymized": False,
                "primary_sentiment": "중립",
                "detailed_sentiment": "기타",
                "sentiment_intensity": 5,
                "keywords": [],
                "labels": []
            }
        
        processed_text = str(original_text).strip()
        prompt = QUICK_PROMPT_TEMPLATE.format(original_text=processed_text)
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON 파싱
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    result = json.loads(json_text)
                    return result
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
                    
            except json.JSONDecodeError:
                return self._create_fallback_result(processed_text)
                
        except Exception as e:
            return self._create_fallback_result(processed_text)
    
    def _create_fallback_result(self, processed_text: str) -> dict:
        """API 실패 시 기본 결과 생성"""
        return {
            "refined_text": processed_text,
            "is_anonymized": False,
            "primary_sentiment": "중립",
            "detailed_sentiment": "기타",
            "sentiment_intensity": 5,
            "keywords": [],
            "labels": []
        }

def main():
    print("⚡ 빠른 협업 후기 200건 분석 시작")
    print("=" * 50)
    
    try:
        # 1. 원본 파일 로딩
        print("📁 원본 파일 로딩...")
        df = pd.read_excel('설문조사_전처리데이터_20250620_0731.xlsx', engine='openpyxl')
        
        # 2. 협업 후기 데이터 추출 (상위 200건)
        print("📊 협업 후기 데이터 추출...")
        feedback_mask = df['협업 후기'].notna() & (df['협업 후기'].str.len() > 0)
        feedback_df = df[feedback_mask].head(200).copy()
        print(f"✅ 추출 완료: {len(feedback_df)}건")
        
        # 3. AI 분석기 초기화
        print("🤖 AI 분석기 초기화...")
        analyzer = QuickAnalyzer(project_id="angelic-hold-456808-d2")
        
        print(f"🤖 AI 분석 시작 (총 {len(feedback_df)}건)")
        
        results = []
        for i, (idx, row) in enumerate(feedback_df.iterrows(), 1):
            if i % 10 == 0:
                print(f"[{i}/{len(feedback_df)}] 진행률: {i/len(feedback_df)*100:.1f}%")
            
            original_text = str(row['협업 후기'])
            result = analyzer.analyze_review(original_text)
            results.append(result)
            
            # API 호출 제한 완화
            time.sleep(0.05)
        
        # 4. 결과를 원본 DataFrame에 추가
        print(f"\n📋 분석 결과를 원본 시트에 추가...")
        
        feedback_df['협업후기_정제텍스트'] = [r['refined_text'] for r in results]
        feedback_df['협업후기_비식별처리'] = [r['is_anonymized'] for r in results]
        feedback_df['협업후기_주감정'] = [r['primary_sentiment'] for r in results]
        feedback_df['협업후기_세부감정'] = [r['detailed_sentiment'] for r in results]
        feedback_df['협업후기_감정강도'] = [r['sentiment_intensity'] for r in results]
        feedback_df['협업후기_키워드'] = [', '.join(r['keywords']) for r in results]
        feedback_df['협업후기_분류라벨'] = [', '.join(r['labels']) for r in results]
        
        # 5. 결과 파일 저장
        output_file = "협업후기_분석결과_상위200건.xlsx"
        feedback_df.to_excel(output_file, index=False, engine='openpyxl')
        
        print(f"✅ 분석 완료! 결과 파일: {output_file}")
        
        # 6. 간단한 통계 출력
        print(f"\n📈 분석 결과 요약:")
        sentiment_counts = pd.Series([r['primary_sentiment'] for r in results]).value_counts()
        for sentiment, count in sentiment_counts.items():
            print(f"  {sentiment}: {count}건 ({count/len(results)*100:.1f}%)")
        
        return feedback_df, results
        
    except Exception as e:
        import traceback
        print(f"❌ 오류 발생: {e}")
        print(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    main()