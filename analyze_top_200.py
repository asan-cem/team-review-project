import pandas as pd
import json
import time
from pathlib import Path
import vertexai
from vertexai.generative_models import GenerativeModel
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
}}

참고: 감정강도는 다음 세부 기준을 따름
1-2: 매우 약한 감정 (미미한 긍정/부정, 형식적 표현)
3-4: 약한 감정 (살짝 긍정/부정, 일반적인 만족/불만족)
5-6: 보통 감정 (분명한 감정 표현, 구체적 이유 있음)
7-8: 강한 감정 (매우 긍정/부정, 강조 표현 포함)
9-10: 극도로 강한 감정 (극찬/극도 불만, 감정적 표현 풍부)

원본 텍스트: "{original_text}"
"""

class Top200Analyzer:
    def __init__(self, project_id: str, location: str = "us-central1"):
        """상위 200건 분석기 초기화"""
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash")
        
    
    
    def analyze_review(self, original_text: str) -> dict:
        """단일 리뷰 분석"""
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
        
        # 전처리
        processed_text = str(original_text).strip()
        
        prompt = ADVANCED_PROMPT_TEMPLATE.format(original_text=processed_text)
        
        try:
            print(f"    🤖 AI 분석 중: {processed_text[:30]}...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON 파싱
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    result = json.loads(json_text)
                    
                    # 결과 간단 표시
                    sentiment = result.get('primary_sentiment', '알 수 없음')
                    detailed = result.get('detailed_sentiment', '알 수 없음')
                    print(f"    ✅ 완료: {sentiment} ({detailed})")
                    
                    return result
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
                    
            except json.JSONDecodeError:
                print(f"    ❌ JSON 파싱 실패")
                return self._create_fallback_result(processed_text)
                
        except Exception as e:
            print(f"    ❌ API 호출 실패: {e}")
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
    print("🔍 협업 후기 상위 200건 분석 시작")
    print("=" * 50)
    
    try:
        # 1. 원본 Excel 파일 읽기
        print("📁 원본 파일 로딩...")
        df = pd.read_excel('설문조사_전처리데이터_20250620_0731.xlsx', engine='openpyxl')
        
        # 2. 협업 후기가 있는 상위 200건 추출
        print("📊 협업 후기 데이터 추출...")
        feedback_df = df[df['협업 후기'].notna()].head(200).copy()
        print(f"✅ 추출 완료: {len(feedback_df)}건")
        
        # 3. AI 분석 시작
        print(f"\n🤖 AI 분석 시작 (총 {len(feedback_df)}건)")
        analyzer = Top200Analyzer(project_id="mindmap-462708")
        
        results = []
        for i, (idx, row) in enumerate(feedback_df.iterrows(), 1):
            print(f"\n[{i}/{len(feedback_df)}] 분석 중...")
            original_text = str(row['협업 후기'])
            
            result = analyzer.analyze_review(original_text)
            results.append(result)
            
            # API 호출 제한
            time.sleep(0.1)
        
        # 4. 결과를 원본 DataFrame에 추가
        print(f"\n📋 분석 결과를 원본 시트에 추가...")
        
        # 분석 결과 컬럼들 추가
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