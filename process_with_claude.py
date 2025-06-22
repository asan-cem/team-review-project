import pandas as pd
import json
import time
from pathlib import Path
import requests
import os

PROMPT_TEMPLATE = """
[페르소나]
당신은 내부 직원 만족도 및 협업 피드백을 분석하는, 매우 꼼꼼하고 정확한 AI 데이터 분석 전문가입니다. 당신의 임무는 주어진 원본 텍스트를 바탕으로, 아래 지시사항에 따라 구조화된 JSON 데이터를 생성하는 것입니다.

[지시사항]
1. 주어진 원본 텍스트의 핵심 의미를 보존하면서, 오타와 문법을 교정하여 refined_text를 생성합니다.
2. 속거나 공격적인 표현은 전문적이고 정중한 표현으로 순화합니다.
3. **매우 중요**: 피드백이 '부정적' 뉘앙스이면서 동시에 아래 조건에 해당할 경우에만 비식별 처리하고 is_anonymized를 true로 설정합니다:
   - 실명이 명시된 경우 (예: "김민희 직원", "혈액은행 김현성 직원")
   - 소수 인원으로 특정 가능한 구체적 호칭 (예: "팀장", "과장", "대리", "여자 직원", "유엠")
   - 부서명+직책이 결합된 경우 (예: "혈액은행 김현성", "마케팅팀 과장")
   **절대 규칙**: 긍정적이거나 중립적 피드백은 어떤 경우에도 is_anonymized를 false로 설정하고 비식별 처리하지 않습니다. 일반적인 호칭("선생님", "직원분", "담당자", "관리자")도 비식별 처리하지 않습니다.
4. "없음" 등 무의미한 텍스트는 refined_text를 빈 문자열로 처리합니다.
5. 전체적인 맥락을 파악하여 sentiment를 "긍정", "부정", "중립" 중 하나로 분류합니다.
6. 아래 [분류 체계]를 기준으로, 내용과 일치하는 모든 라벨을 labels 리스트에 포함시킵니다.

[분류 체계]
- "부서간 협업": 서로 다른 부서/팀 간의 업무 연계와 협력 문제.
- "직원간 소통": 같은 부서/팀 내 동료 간의 소통 및 관계 문제.
- "전문성 부족": 개인의 업무 지식, 기술, 경험 부족 문제.
- "업무 태도": 책임감, 적극성 등 업무를 대하는 자세 문제.
- "상호 존중": 인격적 대우, 배려 등 관계에서의 예의 문제.

[출력 형식]
- 반드시 아래 명시된 키를 가진 JSON 객체 형식으로만 응답해야 합니다.
- JSON 앞뒤로 어떠한 설명이나 Markdown 코드 블록도 붙이지 마세요.

예시 형식:
{{"refined_text": "최종 정제 및 비식별 처리된 텍스트", "is_anonymized": false, "sentiment": "긍정", "labels": ["라벨1", "라벨2"]}}

[예시]
- 원본 텍스트: "김철수 팀장 일처리 너무 답답하고 소통도 안됨. 개선이 시급함"
- JSON 출력:
{{"refined_text": "담당자의 일 처리가 다소 아쉽고, 소통 방식의 개선이 필요해 보입니다.", "is_anonymized": true, "sentiment": "부정", "labels": ["전문성 부족", "직원간 소통"]}}

- 원본 텍스트: "선생님들이 업무 처리가 너무 느려서 답답습니다"
- JSON 출력:
{{"refined_text": "선생님들의 업무 처리 속도가 다소 아쉽습니다.", "is_anonymized": false, "sentiment": "부정", "labels": ["전문성 부족"]}}

- 원본 텍스트: "박영희 선생님은 항상 동료들을 먼저 챙기고 배려하는 모습이 보기 좋습니다"
- JSON 출력:
{{"refined_text": "박영희 선생님은 항상 동료들을 먼저 챙기고 배려하는 모습이 보기 좋습니다.", "is_anonymized": false, "sentiment": "긍정", "labels": ["상호 존중", "업무 태도"]}}

- 원본 텍스트: "여자 직원분이 불친절해서 기분이 나빴습니다"
- JSON 출력:
{{"refined_text": "담당 직원분의 서비스 태도가 아쉬웠습니다.", "is_anonymized": true, "sentiment": "부정", "labels": ["상호 존중"]}}

- 원본 텍스트: "여자 직원분이 도움을 많이 주셨어요"
- JSON 출력:
{{"refined_text": "여자 직원분이 도움을 많이 주셨어요.", "is_anonymized": false, "sentiment": "긍정", "labels": ["업무 태도"]}}

원본 텍스트: "{original_text}"
"""

class ClaudeReviewAnalyzer:
    def __init__(self, api_key: str):
        """
        Claude API를 사용한 리뷰 분석기 초기화
        
        Args:
            api_key: Anthropic API 키
        """
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    
    def analyze_review(self, original_text: str) -> dict:
        """
        단일 리뷰 텍스트를 분석하여 JSON 형태로 반환
        
        Args:
            original_text: 원본 리뷰 텍스트
            
        Returns:
            dict: 분석 결과 딕셔너리
        """
        if not original_text or original_text.strip() == "":
            return {
                "original_text": original_text,
                "refined_text": "",
                "is_anonymized": False,
                "sentiment": "중립",
                "labels": []
            }
        
        prompt = PROMPT_TEMPLATE.format(original_text=original_text)
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1000,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                print(f"API 호출 실패 (상태코드: {response.status_code}): {response.text}")
                return {
                    "original_text": original_text,
                    "refined_text": original_text,
                    "is_anonymized": False,
                    "sentiment": "중립",
                    "labels": []
                }
            
            response_data = response.json()
            response_text = response_data["content"][0]["text"].strip()
            
            # JSON 파싱 시도
            try:
                # 응답에서 JSON 부분만 추출
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    result = json.loads(json_text)
                    result["original_text"] = original_text
                    return result
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
            except json.JSONDecodeError:
                print(f"JSON 파싱 실패: {original_text[:50]}...")
                return {
                    "original_text": original_text,
                    "refined_text": original_text,
                    "is_anonymized": False,
                    "sentiment": "중립",
                    "labels": []
                }
                
        except Exception as e:
            print(f"API 호출 실패: {e}")
            return {
                "original_text": original_text,
                "refined_text": original_text,
                "is_anonymized": False,
                "sentiment": "중립",
                "labels": []
            }
    
    def process_csv(self, input_file: str, output_file: str = None, delay: float = 1.0, max_rows: int = None):
        """
        CSV 파일의 모든 리뷰를 처리하여 결과를 저장
        
        Args:
            input_file: 입력 CSV 파일 경로
            output_file: 출력 CSV 파일 경로 (기본값: input_file에 _claude_processed 추가)
            delay: API 호출 간 지연 시간 (초)
            max_rows: 처리할 최대 행 수 (테스트용)
        """
        # CSV 파일 읽기
        df = pd.read_csv(input_file)
        
        if max_rows:
            df = df.head(max_rows)
        
        if output_file is None:
            output_file = str(Path(input_file).stem) + "_claude_processed.csv"
        
        results = []
        total_rows = len(df)
        
        print(f"총 {total_rows}개의 리뷰를 Claude Sonnet으로 처리합니다...")
        
        for idx, row in df.iterrows():
            original_text = str(row['original_review']) if 'original_review' in row else str(row.iloc[0])
            
            print(f"처리 중... ({idx + 1}/{total_rows})")
            
            # 리뷰 분석
            result = self.analyze_review(original_text)
            results.append(result)
            
            # API 호출 제한을 위한 지연
            if delay > 0:
                time.sleep(delay)
        
        # 결과를 DataFrame으로 변환하여 저장
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"처리 완료! 결과가 '{output_file}'에 저장되었습니다.")
        
        # 통계 출력
        sentiment_counts = result_df['sentiment'].value_counts()
        print("\n감정 분석 결과:")
        for sentiment, count in sentiment_counts.items():
            print(f"  {sentiment}: {count}개")

def main():
    # API 키 설정 - 환경변수에서 읽어오거나 직접 입력
    API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    
    if not API_KEY:
        print("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        print("다음 중 하나의 방법으로 API 키를 설정하세요:")
        print("1. 환경변수 설정: export ANTHROPIC_API_KEY='your-api-key'")
        print("2. 또는 아래 코드에서 직접 설정")
        print()
        API_KEY = input("Anthropic API 키를 입력하세요: ").strip()
        
        if not API_KEY:
            print("API 키가 필요합니다.")
            return
    
    # 설정값들
    INPUT_FILE = "reviews_original.csv"
    OUTPUT_FILE = "reviews_claude_processed.csv"
    
    try:
        # 리뷰 분석기 생성
        analyzer = ClaudeReviewAnalyzer(api_key=API_KEY)
        
        # CSV 파일 처리
        analyzer.process_csv(INPUT_FILE, OUTPUT_FILE)
        
    except Exception as e:
        import traceback
        print(f"오류 발생: {e}")
        print(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    main()