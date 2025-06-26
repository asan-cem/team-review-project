# 데이터 처리를 위한 라이브러리들
import pandas as pd  # 엑셀, CSV 파일 처리
import json  # JSON 데이터 처리
import time  # 대기 시간 처리
from pathlib import Path  # 파일 경로 처리
import math  # 수학 계산
import datetime  # 시간 처리
from tqdm import tqdm  # 진행률 표시
from concurrent.futures import ThreadPoolExecutor, as_completed  # 병렬 처리
from collections import Counter  # 단어 빈도 계산
import re  # 정규표현식

# Google Cloud AI 라이브러리
import vertexai  # Google Vertex AI 플랫폼
from vertexai.generative_models import GenerativeModel  # AI 모델

# AI에게 보낼 분석 지시사항 템플릿
PROMPT_TEMPLATE = """
[페르소나]
당신은 내부 직원 만족도 및 협업 피드백을 분석하는, 매우 꼼꼼하고 정확한 AI 데이터 분석 전문가입니다. 당신의 임무는 주어진 원본 텍스트를 바탕으로, 아래 지시사항에 따라 구조화된 JSON 데이터를 생성하는 것입니다.

[지시사항]
1. 주어진 원본 텍스트의 핵심 의미를 보존하면서, 오타와 문법을 교정하여 refined_text를 생성합니다.
2. 속거나 공격적인 표현은 전문적이고 정중한 표현으로 순화합니다.
3. **매우 중요 - 비식별 처리 규칙**: 
   **3-1. 긍정적/중립적 피드백 처리 규칙:**
   - 긍정적이거나 중립적 피드백(sentiment가 "긍정" 또는 "중립")은 실명이 포함되어 있어도 절대 비식별 처리하지 않습니다.
   - is_anonymized를 반드시 false로 설정합니다.
   - 원본 텍스트를 그대로 유지합니다.
   
   **3-2. 부정적 피드백 처리 규칙 (매우 엄격한 기준):**
   - 피드백이 '부정적' 뉘앙스(sentiment가 "부정")이면서 **반드시** 아래 조건에 정확히 해당할 경우에만 비식별 처리하고 is_anonymized를 true로 설정합니다:
   
   **비식별 처리 대상 (정확히 이런 경우에만):**
   - 한국식 실명이 명확히 명시된 경우 (예: "김민희", "이정은", "박철수", "혈액은행 김현성 직원", "이정은 선생님")
   - 매우 구체적인 특정 가능한 호칭 (예: "팀장", "과장", "대리", "여자 직원", "남자 직원", "유엠", "신입")
   - 부서명+직책이 결합된 경우 (예: "혈액은행 김현성", "마케팅팀 과장")
   - 부서명+실명이 결합된 경우 (예: "검사실 이정은", "간호팀 박영희")
   
   **3-3. 비식별 처리 절대 금지 대상:**
   - 실명이나 특정 호칭이 없는 단순 부정적 표현 (예: "혈관이 없어서 실패하면 실패하다고 인계주고 가십니다", "업무 처리가 늦어요", "불친절해요")
   - 일반적인 호칭만 사용된 경우 ("선생님", "직원분", "담당자", "관리자", "간호사", "의사")
   - 직무나 상황에 대한 일반적인 불만 표현
   - 실명이나 특정 개인을 지칭하지 않는 모든 표현
   
   **중요**: 실명이나 매우 구체적인 개인 식별 정보가 없다면 절대로 비식별 처리하지 마세요. is_anonymized는 false로 설정하세요.
4. "없음" 등 무의미한 텍스트는 refined_text를 빈 문자열로 처리합니다.
5. 전체적인 맥락을 파악하여 sentiment를 "긍정", "부정", "중립" 중 하나로 분류합니다.
6. sentiment_intensity를 1-10 스케일로 평가합니다 (1: 매우 약함, 10: 매우 강함).
7. confidence_score를 1-10 스케일로 평가합니다 (1: 분석 결과에 대한 확신 없음, 10: 매우 확신).
8. key_terms를 추출하여 리스트로 제공합니다 (주요 키워드 3-5개).
9. 아래 [분류 체계]를 기준으로, 내용과 일치하는 모든 라벨을 labels 리스트에 포함시킵니다.

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
{{"refined_text": "최종 정제 및 비식별 처리된 텍스트", "is_anonymized": false, "sentiment": "긍정", "sentiment_intensity": 7, "confidence_score": 8, "key_terms": ["키워드1", "키워드2"], "labels": ["라벨1", "라벨2"]}}

[예시]
- 원본 텍스트: "김철수 팀장 일처리 너무 답답하고 소통도 안됨. 개선이 시급함"
- JSON 출력:
{{"refined_text": "담당자의 일 처리가 다소 아쉽고, 소통 방식의 개선이 필요해 보입니다.", "is_anonymized": true, "sentiment": "부정", "sentiment_intensity": 8, "confidence_score": 9, "key_terms": ["일처리", "소통", "개선"], "labels": ["전문성 부족", "직원간 소통"]}}

- 원본 텍스트: "선생님들이 업무 처리가 너무 느려서 답답합니다"
- JSON 출력:
{{"refined_text": "선생님들의 업무 처리 속도가 다소 아쉽습니다.", "is_anonymized": false, "sentiment": "부정", "sentiment_intensity": 6, "labels": ["전문성 부족"]}}

- 원본 텍스트: "박영희 선생님은 항상 동료들을 먼저 챙기고 배려하는 모습이 보기 좋습니다"
- JSON 출력:
{{"refined_text": "박영희 선생님은 항상 동료들을 먼저 챙기고 배려하는 모습이 보기 좋습니다.", "is_anonymized": false, "sentiment": "긍정", "sentiment_intensity": 8, "labels": ["상호 존중", "업무 태도"]}}

- 원본 텍스트: "여자 직원분이 불친절해서 기분이 나빴습니다"
- JSON 출력:
{{"refined_text": "담당 직원분의 서비스 태도가 아쉬웠습니다.", "is_anonymized": true, "sentiment": "부정", "sentiment_intensity": 7, "labels": ["상호 존중"]}}

- 원본 텍스트: "여자 직원분이 도움을 많이 주셨어요"
- JSON 출력:
{{"refined_text": "여자 직원분이 도움을 많이 주셨어요.", "is_anonymized": false, "sentiment": "긍정", "sentiment_intensity": 6, "labels": ["업무 태도"]}}

- 원본 텍스트: "이정은 선생님이 불친절하고 업무 처리가 느려요"
- JSON 출력:
{{"refined_text": "담당 직원분의 서비스 태도와 업무 처리 속도가 아쉬웠습니다.", "is_anonymized": true, "sentiment": "부정", "sentiment_intensity": 7, "labels": ["상호 존중", "전문성 부족"]}}

- 원본 텍스트: "이정은 선생님 덕분에 업무가 수월했습니다"
- JSON 출력:
{{"refined_text": "이정은 선생님 덕분에 업무가 수월했습니다.", "is_anonymized": false, "sentiment": "긍정", "sentiment_intensity": 7, "labels": ["업무 태도"]}}

- 원본 텍스트: "김철수 과장님 정말 성의없게 일하시네요"
- JSON 출력:
{{"refined_text": "담당자의 업무 처리 방식이 좀 더 신중했으면 좋겠습니다.", "is_anonymized": true, "sentiment": "부정", "sentiment_intensity": 8, "labels": ["업무 태도"]}}

- 원본 텍스트: "간호팀 박영희님이 항상 친절하세요"
- JSON 출력:
{{"refined_text": "간호팀 박영희님이 항상 친절하세요.", "is_anonymized": false, "sentiment": "긍정", "sentiment_intensity": 7, "labels": ["상호 존중"]}}

- 원본 텍스트: "혈관이 없어서 실패하면 실패하다고 인계주고 가십니다.. ㅠㅠ"
- JSON 출력:
{{"refined_text": "혈관 확보가 어려워 실패할 경우, 상황을 인계하고 가시는 경우가 있어 아쉽습니다.", "is_anonymized": false, "sentiment": "부정", "sentiment_intensity": 6, "labels": ["업무 태도", "직원간 소통"]}}

- 원본 텍스트: "업무 처리가 너무 늦고 답답해요"
- JSON 출력:
{{"refined_text": "업무 처리 속도가 다소 아쉽습니다.", "is_anonymized": false, "sentiment": "부정", "sentiment_intensity": 6, "labels": ["전문성 부족"]}}

- 원본 텍스트: "불친절하고 말도 안 들어줘요"
- JSON 출력:
{{"refined_text": "서비스 태도와 소통 방식이 개선되었으면 좋겠습니다.", "is_anonymized": false, "sentiment": "부정", "sentiment_intensity": 7, "labels": ["상호 존중", "직원간 소통"]}}

원본 텍스트: "{original_text}"
"""

class ReviewAnalyzer:
    """
    텍스트 리뷰를 AI로 분석하는 클래스
    Google의 Vertex AI를 사용하여 텍스트의 감정, 개선된 표현, 분류 라벨 등을 분석합니다.
    """
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        분석기를 초기화합니다.
        
        Args:
            project_id: Google Cloud 프로젝트 ID (필수)
            location: AI 모델이 실행될 지역 (기본값: us-central1)
        """
        # Google Cloud AI 플랫폼 초기화
        vertexai.init(project=project_id, location=location)
        
        # 사용할 AI 모델 설정 (Gemini 2.0 Flash 모델)
        self.model = GenerativeModel("gemini-2.0-flash")
    
    def analyze_review(self, original_text: str) -> dict:
        """
        텍스트를 AI로 분석하여 감정, 개선된 텍스트 등을 반환합니다.
        
        Args:
            original_text: 분석할 원본 텍스트
            
        Returns:
            dict: 분석 결과 (감정, 개선된 텍스트, 라벨 등)
        """
        # 빈 텍스트 처리
        if not original_text or original_text.strip() == "":
            return {
                "original_text": original_text,
                "refined_text": "",
                "is_anonymized": False,
                "sentiment": "중립",
                "sentiment_intensity": 5,
                "confidence_score": 10,
                "key_terms": [],
                "labels": []
            }
        
        # AI 분석 프롬프트 생성
        prompt = PROMPT_TEMPLATE.format(original_text=original_text)
        
        try:
            # AI 모델에 분석 요청
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # AI 응답에서 JSON 부분 추출 및 파싱
            try:
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
                print(f"AI 응답 파싱 실패: {original_text[:50]}...")
                return {
                    "original_text": original_text,
                    "refined_text": original_text,
                    "is_anonymized": False,
                    "sentiment": "중립",
                    "sentiment_intensity": 5,
                    "confidence_score": 1,
                    "key_terms": [],
                    "labels": []
                }
                
        except Exception as e:
            print(f"AI 분석 실패: {e}")
            return {
                "original_text": original_text,
                "refined_text": original_text,
                "is_anonymized": False,
                "sentiment": "중립",
                "sentiment_intensity": 5,
                "confidence_score": 1,
                "key_terms": [],
                "labels": []
            }
    
    def process_csv(self, input_file: str, output_file: str = None, delay: float = 0.1, max_rows: int = None):
        """
        CSV 파일의 텍스트 데이터를 분석하여 결과를 저장합니다.
        
        Args:
            input_file: 분석할 CSV 파일 경로
            output_file: 결과를 저장할 파일 경로 (자동 생성 가능)
            delay: AI 호출 간 대기 시간 (초)
            max_rows: 테스트용으로 처리할 최대 행 수
        """
        # CSV 파일을 읽어서 데이터프레임으로 변환
        df = pd.read_csv(input_file)
        
        # 테스트용으로 일부 데이터만 처리하는 경우
        if max_rows:
            df = df.head(max_rows)
        
        # 출력 파일명 자동 생성
        if output_file is None:
            output_file = str(Path(input_file).stem) + "_processed.csv"
        
        results = []  # 분석 결과를 저장할 리스트
        total_rows = len(df)
        
        print(f"총 {total_rows}개의 리뷰를 분석합니다...")
        
        # 각 행의 텍스트 데이터를 하나씩 분석
        for idx, row in df.iterrows():
            # 텍스트 데이터 추출 (컬럼명에 따라 자동 선택)
            original_text = str(row['original_review']) if 'original_review' in row else str(row.iloc[0])
            
            print(f"분석 중... ({idx + 1}/{total_rows})")
            
            # AI로 텍스트 분석 수행
            result = self.analyze_review(original_text)
            results.append(result)
            
            # AI 서비스 과부하 방지를 위한 대기
            if delay > 0:
                time.sleep(delay)
        
        # 분석 결과를 CSV 파일로 저장
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"분석 완료! 결과가 '{output_file}'에 저장되었습니다.")
        
        # 감정 분석 통계 출력
        sentiment_counts = result_df['sentiment'].value_counts()
        print("\n감정 분석 결과:")
        for sentiment, count in sentiment_counts.items():
            print(f"  {sentiment}: {count}개")


    def analyze_batch(self, texts: list, batch_size: int = 10) -> list:
        """
        여러 텍스트를 배치로 처리하여 성능을 향상시킵니다.
        
        Args:
            texts: 분석할 텍스트 리스트
            batch_size: 한 번에 처리할 텍스트 수
            
        Returns:
            list: 분석 결과 리스트
        """
        results = []
        
        # 배치 단위로 처리 (순서 보장)
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_results = []
            
            # 병렬 처리를 위한 ThreadPoolExecutor 사용
            with ThreadPoolExecutor(max_workers=min(5, len(batch))) as executor:
                # 각 텍스트에 대해 비동기 작업 제출 (인덱스와 함께)
                future_to_index = {}
                for idx, text in enumerate(batch):
                    future = executor.submit(self.analyze_review, text)
                    future_to_index[future] = (idx, text)
                
                # 배치 크기만큼 결과 리스트 초기화
                batch_results = [None] * len(batch)
                
                # 결과 수집 (완료 순서와 관계없이 원래 순서 유지)
                for future in as_completed(future_to_index):
                    idx, original_text = future_to_index[future]
                    try:
                        result = future.result()
                        batch_results[idx] = result
                    except Exception as e:
                        print(f"배치 처리 오류: {e} - {original_text[:50]}...")
                        # 오류 발생 시 기본값 반환
                        batch_results[idx] = {
                            "original_text": original_text,
                            "refined_text": original_text,
                            "is_anonymized": False,
                            "sentiment": "중립",
                            "sentiment_intensity": 5,
                            "confidence_score": 1,
                            "key_terms": [],
                            "labels": []
                        }
            
            # 배치 결과를 전체 결과에 순서대로 추가
            results.extend(batch_results)
        
        return results
    
    def extract_keywords(self, texts: list, min_length: int = 2, exclude_words: set = None) -> dict:
        """
        텍스트에서 키워드를 추출하고 빈도를 분석합니다.
        
        Args:
            texts: 분석할 텍스트 리스트
            min_length: 최소 키워드 길이
            exclude_words: 제외할 단어 집합
            
        Returns:
            dict: 키워드 빈도 딕셔너리
        """
        if exclude_words is None:
            # 일반적인 불용어 설정
            exclude_words = {
                '이', '가', '은', '는', '이다', '있다', '하다', '되다', '아니다',
                '그', '그녀', '그들', '우리', '저희', '너희', '자신', '누군가',
                '무엇', '언제', '어디', '어떻게', '왜', '매우', '조금', '조금',
                '너무', '정말', '매우', '좋다', '나쁘다', '나', '저', '전', '후',
                '여기', '거기', '저기', '지금', '오늘', '어제', '내일', '이번',
                '선생님', '직원분', '담당자', '관리자', '간호사', '의사'
            }
        
        all_keywords = []
        
        # 모든 텍스트에서 키워드 추출
        for text in texts:
            if not text or pd.isna(text):
                continue
                
            # 한글, 영어, 숫자만 유지
            clean_text = re.sub(r'[^\w\s\uac00-\ud7a3]', ' ', str(text))
            
            # 단어 분리
            words = clean_text.split()
            
            for word in words:
                word = word.strip()
                # 길이 및 빈 문자열 검사
                if len(word) >= min_length and word not in exclude_words:
                    all_keywords.append(word)
        
        # 빈도 계산
        keyword_freq = Counter(all_keywords)
        
        return dict(keyword_freq.most_common(50))  # 상위 50개 반환
    
    def validate_analysis_quality(self, result: dict, original_text: str) -> dict:
        """
        AI 분석 결과의 품질을 검증하고 신뢰도를 평가합니다.
        
        Args:
            result: AI 분석 결과
            original_text: 원본 텍스트
            
        Returns:
            dict: 품질 검증 결과
        """
        quality_issues = []
        overall_confidence = result.get('confidence_score', 5)
        
        # 1. 기본 필드 완성도 검사
        required_fields = ['refined_text', 'sentiment', 'sentiment_intensity', 'labels']
        missing_fields = [field for field in required_fields if field not in result or not result[field]]
        
        if missing_fields:
            # 필수 필드 누락 정보는 추가하지 않음 (공란 처리)
            overall_confidence -= 3
        
        # 2. 감정 강도와 감정 분류 일치성 검사
        sentiment = result.get('sentiment', '')
        intensity = result.get('sentiment_intensity', 5)
        
        if sentiment == '긍정' and intensity < 6:
            quality_issues.append("긍정 감정인데 강도가 낮음")
            overall_confidence -= 2
        elif sentiment == '부정' and intensity > 5:
            quality_issues.append("부정 감정인데 강도가 높음")
            overall_confidence -= 2
        
        # 3. 텍스트 길이 비교
        original_len = len(original_text.strip()) if original_text else 0
        refined_len = len(result.get('refined_text', '').strip())
        
        if original_len > 10 and refined_len < original_len * 0.3:
            quality_issues.append("정제된 텍스트가 너무 짧음")
            overall_confidence -= 2
        elif refined_len > original_len * 2:
            quality_issues.append("정제된 텍스트가 너무 김")
            overall_confidence -= 1
        
        # 4. 키워드 추출 품질 검사
        key_terms = result.get('key_terms', [])
        if len(original_text.strip()) > 20 and len(key_terms) == 0:
            quality_issues.append("키워드 추출 실패")
            overall_confidence -= 2
        
        # 5. 비식별 처리 일치성 검사
        is_anonymized = result.get('is_anonymized', False)
        refined_text = result.get('refined_text', '')
        
        # 실명 패턴 검사 (간단한 한글 이름 패턴)
        name_pattern = r'[\uac00-\ud7a3]{2,3}\s*선생님|[\uac00-\ud7a3]{2,3}\s*과장|[\uac00-\ud7a3]{2,3}\s*팀장|[\uac00-\ud7a3]{2,3}\s*대리'
        
        if is_anonymized and re.search(name_pattern, refined_text):
            quality_issues.append("비식별 처리 불완전 - 실명 잔존")
            overall_confidence -= 3
        
        # 최종 신뢰도 조정
        overall_confidence = max(1, min(10, overall_confidence))
        
        return {
            'quality_score': overall_confidence,
            'issues': quality_issues,
            'needs_review': overall_confidence < 6 or len(quality_issues) > 2,
            'is_reliable': overall_confidence >= 7 and len(quality_issues) <= 1
        }
    
    def retry_low_quality_analysis(self, texts: list, results: list, quality_results: list, max_retries: int = 2) -> tuple:
        """
        낮은 품질의 분석 결과를 재분석합니다.
        
        Args:
            texts: 원본 텍스트 리스트
            results: 분석 결과 리스트
            quality_results: 품질 검증 결과 리스트
            max_retries: 최대 재시도 횟수
            
        Returns:
            tuple: (개선된 결과 리스트, 개선된 품질 결과 리스트)
        """
        improved_results = results.copy()
        improved_quality = quality_results.copy()
        
        # 재검토가 필요한 항목들 찾기
        retry_indices = [i for i, q in enumerate(quality_results) if q['needs_review']]
        
        if not retry_indices:
            print("재검토가 필요한 항목이 없습니다.")
            return improved_results, improved_quality
        
        print(f"\n{len(retry_indices)}개 항목을 재분석합니다...")
        
        retry_count = 0
        total_improved = 0
        
        with tqdm(total=len(retry_indices), desc="재분석 진행률", unit="건") as pbar:
            for idx in retry_indices:
                if retry_count >= max_retries:
                    break
                
                original_text = texts[idx]
                original_quality = quality_results[idx]['quality_score']
                
                # 재분석 수행
                new_result = self.analyze_review(original_text)
                new_quality = self.validate_analysis_quality(new_result, original_text)
                
                # 개선된 경우에만 결과 반영
                if new_quality['quality_score'] > original_quality:
                    # original_text 제거
                    if "original_text" in new_result:
                        del new_result["original_text"]
                    
                    improved_results[idx] = new_result
                    improved_quality[idx] = new_quality
                    total_improved += 1
                
                retry_count += 1
                pbar.update(1)
                
                # API 제한을 위한 짧은 대기
                time.sleep(0.5)
        
        print(f"재분석 완료: {total_improved}개 항목이 개선되었습니다.")
        
        return improved_results, improved_quality
    
    def process_xlsx_with_column(self, input_file: str, column_name: str, output_file: str = None, delay: float = 0.1, max_rows: int = None, use_batch: bool = True, batch_size: int = 10, enable_quality_retry: bool = True):
        """
        엑셀 파일의 특정 컬럼에 있는 텍스트 데이터를 분석하여 결과를 저장합니다.
        
        Args:
            input_file: 입력 엑셀 파일 경로
            column_name: 분석할 텍스트가 포함된 컬럼명
            output_file: 결과를 저장할 파일 경로 (기본값: 입력파일명_processed.xlsx)
            delay: API 호출 간 대기 시간 (초) - 배치 처리 시 무시됨
            max_rows: 테스트용으로 처리할 최대 행 수
            use_batch: 배치 처리 사용 여부 (기본값: True)
            batch_size: 배치 크기 (기본값: 10)
            enable_quality_retry: 낮은 품질 항목 재분석 여부 (기본값: True)
        """
        # 엑셀 파일 읽기
        df = pd.read_excel(input_file)
        
        # 테스트용으로 일부 데이터만 처리하는 경우 (상단부터 순차 추출)
        if max_rows:
            df = df.head(max_rows)
            print(f"전체 데이터에서 상단 {len(df)}개 추출")
        
        # 지정한 컬럼이 존재하는지 확인
        if column_name not in df.columns:
            available_columns = list(df.columns)
            raise ValueError(f"'{column_name}' 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {available_columns}")
        
        # 출력 파일명 설정
        if output_file is None:
            output_file = str(Path(input_file).stem) + "_processed.xlsx"
        
        total_rows = len(df)
        print(f"총 {total_rows}개의 '{column_name}' 텍스트를 분석합니다...")
        
        # 텍스트 데이터 추출
        texts = []
        for _, row in df.iterrows():
            original_text = str(row[column_name]) if pd.notna(row[column_name]) else ""
            texts.append(original_text)
        
        # 배치 처리 또는 순차 처리 선택
        if use_batch:
            print(f"배치 처리 모드 (배치 크기: {batch_size})")
            print(f"예상 소요시간: 약 {math.ceil(total_rows / batch_size) * 2}분 (배치 처리 기준)")
            
            # 진행률 표시와 함께 배치 처리
            results = []
            with tqdm(total=total_rows, desc="분석 진행률", unit="건") as pbar:
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i+batch_size]
                    batch_results = self.analyze_batch(batch_texts, len(batch_texts))
                    results.extend(batch_results)
                    pbar.update(len(batch_texts))
        else:
            print(f"순차 처리 모드")
            est_sec = total_rows * delay
            est_time = str(datetime.timedelta(seconds=math.ceil(est_sec)))
            print(f"예상 소요시간: {est_time} (지연 {delay}초/건 기준)")
            
            # 순차 처리와 진행률 표시
            results = []
            with tqdm(total=total_rows, desc="분석 진행률", unit="건") as pbar:
                for text in texts:
                    result = self.analyze_review(text)
                    # 원본 텍스트는 결과에서 제거
                    if "original_text" in result:
                        del result["original_text"]
                    results.append(result)
                    pbar.update(1)
                    
                    # API 호출 제한을 위한 대기
                    if delay > 0:
                        time.sleep(delay)
        
        # 결과에서 원본 텍스트 제거 및 정리
        for result in results:
            if "original_text" in result:
                del result["original_text"]
        
        # 품질 검증 수행
        quality_results = []
        print("\n품질 검증 수행 중...")
        for idx, (result, original_text) in enumerate(zip(results, texts)):
            quality_check = self.validate_analysis_quality(result, original_text)
            quality_results.append(quality_check)
        
        # 낮은 품질 항목 재분석 (활성화된 경우에만)
        if enable_quality_retry:
            results, quality_results = self.retry_low_quality_analysis(texts, results, quality_results, max_retries=3)
        
        # 최종 낮은 품질 항목 찾기
        low_quality_indices = [i for i, q in enumerate(quality_results) if q['needs_review']]
        
        # 품질 검증 결과를 결과에 추가
        for i, result in enumerate(results):
            result['quality_score'] = quality_results[i]['quality_score']
            result['needs_review'] = quality_results[i]['needs_review']
            result['quality_issues'] = '; '.join(quality_results[i]['issues']) if quality_results[i]['issues'] else ''
        
        # 키워드 분석
        print("\n키워드 분석 수행 중...")
        all_refined_texts = [r.get('refined_text', '') for r in results]
        keyword_freq = self.extract_keywords(all_refined_texts)
        
        # 분석 결과를 데이터프레임으로 변환
        result_df = pd.DataFrame(results)
        
        # 원본 데이터와 분석 결과를 합친 새로운 데이터프레임 생성
        processed_df = df.copy()
        
        # 컬럼명을 한국어로 매핑
        korean_column_names = {
            'refined_text': '정제텍스트',
            'is_anonymized': '비식별처리여부',
            'sentiment': '감정분석',
            'sentiment_intensity': '감정강도',
            'confidence_score': 'AI신뢰도',
            'key_terms': '핵심키워드',
            'labels': '분류라벨',
            'quality_score': '품질점수',
            'needs_review': '재검토필요',
            'quality_issues': '품질문제'
        }
        
        for col in result_df.columns:
            korean_col_name = korean_column_names.get(col, col)
            processed_df[f"{column_name}_{korean_col_name}"] = result_df[col]
        
        # 엑셀 파일로 저장
        processed_df.to_excel(output_file, index=False)
        
        print(f"\n분석 완료! 결과가 '{output_file}'에 저장되었습니다.")
        
        # 낮은 품질 항목 안내
        if low_quality_indices:
            print(f"\n⚠️  {len(low_quality_indices)}개 항목이 재검토가 필요합니다.")
            print("세부 사항은 'quality_issues' 컬럼을 확인하세요.")
        
        # 감정 분석 통계 출력
        sentiment_counts = result_df['sentiment'].value_counts()
        intensity_mean = result_df['sentiment_intensity'].mean()
        confidence_mean = result_df['quality_score'].mean()
        
        print(f"\n=== '{column_name}' 분석 결과 ====")
        print(f"감정 분류:")
        for sentiment, count in sentiment_counts.items():
            percentage = (count / len(result_df)) * 100
            print(f"  {sentiment}: {count}개 ({percentage:.1f}%)")
        print(f"평균 감정 강도: {intensity_mean:.1f}/10")
        print(f"평균 신뢰도: {confidence_mean:.1f}/10")
        
        # 추가 통계
        if 'is_anonymized' in result_df.columns:
            anonymized_count = result_df['is_anonymized'].sum()
            print(f"비식별 처리된 항목: {anonymized_count}개")
        
        # 품질 통계
        needs_review_count = sum(1 for q in quality_results if q['needs_review'])
        reliable_count = sum(1 for q in quality_results if q['is_reliable'])
        print(f"재검토 필요 항목: {needs_review_count}개")
        print(f"신뢰도 높은 항목: {reliable_count}개")
        
        # 주요 키워드 출력
        print(f"\n=== 주요 키워드 TOP 10 ====")
        for keyword, freq in list(keyword_freq.items())[:10]:
            print(f"  {keyword}: {freq}번")

def main():
    """
    메인 실행 함수 - 텍스트 분석을 수행합니다.
    """
    # 설정값들
    PROJECT_ID = "mindmap-462708"  # Google Cloud 프로젝트 ID
    XLSX_FILE = "설문조사_전처리데이터_20250620_0731.xlsx"  # 분석할 엑셀 파일
    COLUMN_NAME = "협업 후기"  # 분석할 컬럼명
    OUTPUT_FILE = "설문조사_전처리데이터_20250620_0731_processed.xlsx"  # 결과 파일
    
    try:
        print("=== 고도화된 텍스트 분석 시스템 ====")
        print("- 배치 처리로 성능 향상")
        print("- 감정 강도 점수 (1-10 스케일)")
        print("- 실시간 진행률 모니터링")
        print("- 키워드 추출 및 빈도 분석")
        print("- AI 분석 품질 검증 및 신뢰도 평가")
        print()
        
        # 분석기 생성 및 실행
        analyzer = ReviewAnalyzer(project_id=PROJECT_ID)
        analyzer.process_xlsx_with_column(
            XLSX_FILE, 
            COLUMN_NAME, 
            OUTPUT_FILE, 
            max_rows=10000,  # 상위 10000개 데이터 처리
            use_batch=True,  # 배치 처리 사용
            batch_size=10,   # 배치 크기 (10000개 처리를 위해 속도 최적화)
            enable_quality_retry=True  # 자동 재검토 기능 활성화
        )
        
    except Exception as e:
        import traceback
        print(f"오류 발생: {e}")
        print(f"상세 오류: {traceback.format_exc()}")
        print("\n해결 방법:")
        print("1. Google Cloud 프로젝트 ID 확인")
        print("2. Vertex AI API 활성화 확인")
        print("3. 인증 설정 확인 (gcloud auth application-default login)")
        print("4. 엑셀 파일 존재 여부 확인")
        print("5. 필요한 패키지 설치 확인 (pandas, openpyxl, tqdm)")

# 프로그램이 직접 실행될 때만 main() 함수 호출
if __name__ == "__main__":
    main() 