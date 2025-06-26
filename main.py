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
import sys  # 명령행 인자 처리
import argparse  # 명령행 인자 파싱
import os  # 파일 시스템 조작
import numpy as np  # 수치 계산
from scipy import stats  # 통계 분석
from sklearn.metrics.pairwise import cosine_similarity  # 코사인 유사도
import warnings  # 경고 메시지 제어
warnings.filterwarnings('ignore')

# Google Cloud AI 라이브러리
import vertexai  # Google Vertex AI 플랫폼
from vertexai.generative_models import GenerativeModel  # AI 모델

# 감정 분류 상수 정의
EMOTION_CATEGORIES = {
    "긍정군": ["기쁨", "감사", "신뢰", "만족"],
    "부정군": ["분노", "슬픔", "두려움", "실망"], 
    "중립군": ["평온", "무관심"]
}

MEDICAL_CONTEXT_CATEGORIES = {
    "환자_안전": ["응급상황", "투약오류", "수술협력", "안전사고", "의료사고"],
    "업무_효율": ["일정조율", "정보공유", "프로세스", "업무분담", "효율성"],
    "인간_관계": ["존중", "소통", "배려", "예의", "친절"],
    "전문성": ["지식", "기술", "경험", "역량", "전문성"]
}

# AI에게 보낼 분석 지시사항 템플릿 (고도화 버전)
PROMPT_TEMPLATE = """
[페르소나]
당신은 의료진 간 협업 피드백을 분석하는 전문 AI 분석가입니다. 8가지 세분화된 감정과 복합 감정 분석을 통해 정확하고 깊이 있는 감정 분석을 수행합니다.

[지시사항]
1. 주어진 원본 텍스트의 핵심 의미를 보존하면서, 오타와 문법을 교정하여 refined_text를 생성합니다.
2. 속거나 공격적인 표현은 전문적이고 정중한 표현으로 순화합니다.
3. **매우 중요 - 비식별 처리 규칙**: 
   **3-1. 긍정적/중립적 피드백 처리 규칙:**
   - 긍정적이거나 중립적 피드백은 실명이 포함되어 있어도 절대 비식별 처리하지 않습니다.
   - is_anonymized를 반드시 false로 설정합니다.
   
   **3-2. 부정적 피드백 처리 규칙:**
   - 부정적 피드백이면서 실명이나 매우 구체적인 개인 식별 정보가 있는 경우에만 비식별 처리합니다.
   - 일반적인 호칭("선생님", "직원분" 등)은 비식별 처리하지 않습니다.

4. **고도화된 감정 분석**:
   - primary_emotion: 주요 감정 (기쁨, 감사, 신뢰, 만족, 분노, 슬픔, 두려움, 실망, 평온, 무관심 중 1개)
   - secondary_emotion: 보조 감정 (있는 경우에만, 없으면 null)
   - emotion_intensity: 감정 강도 (1-10)
   - emotional_complexity: "단순" 또는 "복합"
   - emotion_mix: 복합 감정인 경우 각 감정의 비율 (합계 1.0)

5. **의료 협업 맥락 분석**:
   - medical_context: 환자_안전, 업무_효율, 인간_관계, 전문성 중 해당하는 모든 항목
   - context_weight: 각 맥락의 중요도 (1-5)

6. confidence_score를 1-10 스케일로 평가합니다.
7. key_terms를 추출하여 리스트로 제공합니다 (주요 키워드 3-5개).
8. 기존 분류 체계도 유지합니다.

[감정 분류 가이드]
**긍정군:**
- 기쁨: "기뻐요", "즐거워요", "행복해요"
- 감사: "감사합니다", "고마워요", "도움이 되었어요"
- 신뢰: "믿을 수 있어요", "전문적이에요", "안심이 돼요"
- 만족: "만족해요", "좋았어요", "훌륭해요"

**부정군:**
- 분노: "화나요", "짜증나요", "분해요"
- 슬픔: "슬퍼요", "우울해요", "마음이 아파요"
- 두려움: "무서워요", "걱정돼요", "불안해요"
- 실망: "실망해요", "아쉬워요", "기대에 못 미쳐요"

**중립군:**
- 평온: "괜찮아요", "보통이에요", "평범해요"
- 무관심: "상관없어요", "그냥 그래요"

[출력 형식]
- JSON 형식으로만 응답하세요.
- 아래 키들을 모두 포함해야 합니다.

예시 형식:
{{
  "refined_text": "최종 정제 및 비식별 처리된 텍스트",
  "is_anonymized": false,
  "primary_emotion": "감사",
  "secondary_emotion": "신뢰",
  "emotion_intensity": 7,
  "emotional_complexity": "복합",
  "emotion_mix": {{"감사": 0.7, "신뢰": 0.3}},
  "medical_context": ["인간_관계", "전문성"],
  "context_weight": {{"인간_관계": 4, "전문성": 3}},
  "confidence_score": 8,
  "key_terms": ["감사", "전문적", "도움"],
  "labels": ["상호 존중", "업무 태도"],
  "sentiment": "긍정",
  "sentiment_intensity": 7
}}

[기존 호환성 필드]
- sentiment: 기존 3분류 (긍정/부정/중립) 유지
- sentiment_intensity: 기존 강도 점수 유지

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
    
    def analyze_refined_text(self, refined_text: str, is_already_anonymized: bool = False) -> dict:
        """
        이미 정제된 텍스트를 AI로 분석하여 감정 분석을 수행합니다.
        텍스트 정제와 비식별 처리는 건너뛰고 감정 분석만 수행합니다.
        
        Args:
            refined_text: 이미 정제된 텍스트
            is_already_anonymized: 이미 비식별 처리 여부
            
        Returns:
            dict: 분석 결과 (감정, 개선된 텍스트, 라벨 등)
        """
        # 빈 텍스트 처리
        if not refined_text or refined_text.strip() == "":
            return {
                "original_text": refined_text,
                "refined_text": "",
                "is_anonymized": is_already_anonymized,
                "primary_emotion": "평온",
                "secondary_emotion": None,
                "emotion_intensity": 5,
                "emotional_complexity": "단순",
                "emotion_mix": {"평온": 1.0},
                "medical_context": [],
                "context_weight": {},
                "sentiment": "중립",
                "sentiment_intensity": 5,
                "confidence_score": 10,
                "key_terms": [],
                "labels": []
            }
        
        # 정제된 텍스트에 대한 감정 분석 전용 프롬프트
        refined_prompt = f"""
[페르소나]
당신은 의료진 간 협업 피드백을 분석하는 전문 AI 분석가입니다. 이미 정제된 텍스트에 대해 감정 분석만 수행합니다.

[지시사항]
주어진 텍스트는 이미 정제 및 비식별 처리가 완료된 상태입니다. 
텍스트 수정 없이 감정 분석만 수행하세요.

1. **고도화된 감정 분석**:
   - primary_emotion: 주요 감정 (기쁨, 감사, 신뢰, 만족, 분노, 슬픔, 두려움, 실망, 평온, 무관심 중 1개)
   - secondary_emotion: 보조 감정 (있는 경우에만, 없으면 null)
   - emotion_intensity: 감정 강도 (1-10)
   - emotional_complexity: "단순" 또는 "복합"
   - emotion_mix: 복합 감정인 경우 각 감정의 비율 (합계 1.0)

2. **의료 협업 맥락 분석**:
   - medical_context: 환자_안전, 업무_효율, 인간_관계, 전문성 중 해당하는 모든 항목
   - context_weight: 각 맥락의 중요도 (1-5)

3. confidence_score를 1-10 스케일로 평가합니다.
4. key_terms를 추출하여 리스트로 제공합니다 (주요 키워드 3-5개).
5. labels를 분류 체계에 따라 제공합니다.

[분류 체계]
- "부서간 협업": 서로 다른 부서/팀 간의 업무 연계와 협력 문제.
- "직원간 소통": 같은 부서/팀 내 동료 간의 소통 및 관계 문제.
- "전문성 부족": 개인의 업무 지식, 기술, 경험 부족 문제.
- "업무 태도": 책임감, 적극성 등 업무를 대하는 자세 문제.
- "상호 존중": 인격적 대우, 배려 등 관계에서의 예의 문제.

[출력 형식 - JSON만 응답]
{{
  "refined_text": "{refined_text}",
  "is_anonymized": {str(is_already_anonymized).lower()},
  "primary_emotion": "감사",
  "secondary_emotion": null,
  "emotion_intensity": 7,
  "emotional_complexity": "단순",
  "emotion_mix": {{"감사": 1.0}},
  "medical_context": ["인간_관계"],
  "context_weight": {{"인간_관계": 4}},
  "confidence_score": 8,
  "key_terms": ["감사", "도움"],
  "labels": ["상호 존중"],
  "sentiment": "긍정",
  "sentiment_intensity": 7
}}

분석할 정제된 텍스트: "{refined_text}"
"""
        
        try:
            # AI 모델에 분석 요청
            response = self.model.generate_content(refined_prompt)
            response_text = response.text.strip()
            
            # AI 응답에서 JSON 부분 추출 및 파싱
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    result = json.loads(json_text)
                    result["original_text"] = refined_text
                    return result
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
            except json.JSONDecodeError:
                print(f"AI 응답 파싱 실패: {refined_text[:50]}...")
                return {
                    "original_text": refined_text,
                    "refined_text": refined_text,
                    "is_anonymized": is_already_anonymized,
                    "primary_emotion": "평온",
                    "secondary_emotion": None,
                    "emotion_intensity": 5,
                    "emotional_complexity": "단순",
                    "emotion_mix": {"평온": 1.0},
                    "medical_context": [],
                    "context_weight": {},
                    "sentiment": "중립",
                    "sentiment_intensity": 5,
                    "confidence_score": 1,
                    "key_terms": [],
                    "labels": []
                }
                
        except Exception as e:
            print(f"AI 분석 실패: {e}")
            return {
                "original_text": refined_text,
                "refined_text": refined_text,
                "is_anonymized": is_already_anonymized,
                "primary_emotion": "평온",
                "secondary_emotion": None,
                "emotion_intensity": 5,
                "emotional_complexity": "단순",
                "emotion_mix": {"평온": 1.0},
                "medical_context": [],
                "context_weight": {},
                "sentiment": "중립",
                "sentiment_intensity": 5,
                "confidence_score": 1,
                "key_terms": [],
                "labels": []
            }

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
                "primary_emotion": "평온",
                "secondary_emotion": None,
                "emotion_intensity": 5,
                "emotional_complexity": "단순",
                "emotion_mix": {"평온": 1.0},
                "medical_context": [],
                "context_weight": {},
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
                    "primary_emotion": "평온",
                    "secondary_emotion": None,
                    "emotion_intensity": 5,
                    "emotional_complexity": "단순",
                    "emotion_mix": {"평온": 1.0},
                    "medical_context": [],
                    "context_weight": {},
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
                "primary_emotion": "평온",
                "secondary_emotion": None,
                "emotion_intensity": 5,
                "emotional_complexity": "단순",
                "emotion_mix": {"평온": 1.0},
                "medical_context": [],
                "context_weight": {},
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
                            "primary_emotion": "평온",
                            "secondary_emotion": None,
                            "emotion_intensity": 5,
                            "emotional_complexity": "단순",
                            "emotion_mix": {"평온": 1.0},
                            "medical_context": [],
                            "context_weight": {},
                            "sentiment": "중립",
                            "sentiment_intensity": 5,
                            "confidence_score": 1,
                            "key_terms": [],
                            "labels": []
                        }
            
            # 배치 결과를 전체 결과에 순서대로 추가
            results.extend(batch_results)
        
        return results
    
    def analyze_refined_batch(self, texts_and_flags: list, batch_size: int) -> list:
        """
        여러 정제된 텍스트를 배치로 처리하여 성능을 향상시킵니다.
        
        Args:
            texts_and_flags: (정제된_텍스트, 비식별_여부) 튜플 리스트
            batch_size: 배치 크기
            
        Returns:
            list: 분석 결과 리스트
        """
        results = []
        
        # 병렬 처리를 위한 ThreadPoolExecutor 사용
        with ThreadPoolExecutor(max_workers=min(5, len(texts_and_flags))) as executor:
            # 각 텍스트에 대해 비동기 작업 제출 (인덱스와 함께)
            future_to_index = {}
            for idx, (refined_text, is_anonymized) in enumerate(texts_and_flags):
                future = executor.submit(self.analyze_refined_text, refined_text, is_anonymized)
                future_to_index[future] = (idx, refined_text, is_anonymized)
            
            # 배치 크기만큼 결과 리스트 초기화
            batch_results = [None] * len(texts_and_flags)
            
            # 결과 수집 (완료 순서와 관계없이 원래 순서 유지)
            for future in as_completed(future_to_index):
                idx, refined_text, is_anonymized = future_to_index[future]
                try:
                    result = future.result()
                    batch_results[idx] = result
                except Exception as e:
                    print(f"배치 처리 오류: {e} - {refined_text[:50]}...")
                    # 오류 발생 시 기본값 반환
                    batch_results[idx] = {
                        "original_text": refined_text,
                        "refined_text": refined_text,
                        "is_anonymized": is_anonymized,
                        "primary_emotion": "평온",
                        "secondary_emotion": None,
                        "emotion_intensity": 5,
                        "emotional_complexity": "단순",
                        "emotion_mix": {"평온": 1.0},
                        "medical_context": [],
                        "context_weight": {},
                        "sentiment": "중립",
                        "sentiment_intensity": 5,
                        "confidence_score": 1,
                        "key_terms": [],
                        "labels": []
                    }
        
        return batch_results
    
    def retry_low_quality_analysis_refined(self, texts_and_flags: list, results: list, quality_results: list, max_retries: int = 2) -> tuple:
        """
        정제된 텍스트에 대한 낮은 품질의 분석 결과를 재분석합니다.
        
        Args:
            texts_and_flags: (정제된_텍스트, 비식별_여부) 튜플 리스트
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
                
                refined_text, is_anonymized = texts_and_flags[idx]
                original_quality = quality_results[idx]['quality_score']
                
                # 재분석 수행
                new_result = self.analyze_refined_text(refined_text, is_anonymized)
                new_quality = self.validate_analysis_quality(new_result, refined_text)
                
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
    
    def _create_explanation_sheets(self, writer, vector_analysis, statistical_results, advanced_metrics):
        """
        수학적/통계적 분석 결과에 대한 상세 설명 시트들을 생성합니다.
        비전공자도 이해할 수 있도록 자세한 설명을 포함합니다.
        """
        
        # 1. 분석 방법론 설명 시트
        methodology_data = [
            ["분석 항목", "분석 목적", "분석 방법", "활용 분야"],
            ["", "", "", ""],
            ["📊 벡터분석", "감정을 수학적 공간에 배치하여 패턴 파악", "8차원 벡터 공간에서 감정의 위치와 관계 계산", "감정의 다양성, 응집도, 극성 분석"],
            ["", "• 감정 간의 유사성과 차이점 정량화", "• 각 감정을 고유한 숫자 벡터로 표현", "• 조직 내 감정 분포 균형 평가"],
            ["", "• 전체적인 감정 동향 파악", "• 코사인 유사도로 감정 간 관련성 측정", "• 감정 변화 추이 모니터링"],
            ["", "", "", ""],
            ["📈 기술통계량", "데이터의 기본적인 특성 파악", "평균, 분산, 왜도, 첨도 등 계산", "데이터 분포의 중심과 퍼짐 정도 파악"],
            ["", "• 감정 강도의 전반적인 수준 확인", "• 평균: 중심 경향", "• 조직 전체의 감정 수준 진단"],
            ["", "• 데이터의 변동성과 치우침 분석", "• 분산: 퍼짐 정도", "• 극단적 감정 반응 감지"],
            ["", "", "• 왜도: 비대칭 정도", "• 감정 분포의 균형성 평가"],
            ["", "", "• 첨도: 뾰족함 정도", ""],
            ["", "", "", ""],
            ["🔍 정규성검정", "데이터가 정규분포를 따르는지 확인", "Shapiro-Wilk 검정 수행", "적절한 통계분석 방법 선택의 기준"],
            ["", "• 통계적 추론의 신뢰성 확보", "• p-값이 0.05보다 크면 정규분포", "• 모수통계 vs 비모수통계 판단"],
            ["", "• 이상값과 특이 패턴 탐지", "• p-값이 0.05보다 작으면 비정규분포", "• 데이터 품질 평가"],
            ["", "", "", ""],
            ["🔗 상관관계", "감정 유형과 강도 간의 관련성 분석", "피어슨 상관계수 계산", "감정 패턴의 일관성 평가"],
            ["", "• 긍정/부정 감정과 강도의 연관성", "• -1~1 사이의 값", "• 감정 표현의 적절성 진단"],
            ["", "• 감정 반응의 예측 가능성", "• 1에 가까울수록 강한 양의 상관", "• 조직 문화 특성 파악"],
            ["", "", "• -1에 가까울수록 강한 음의 상관", ""],
            ["", "", "", ""],
            ["📏 신뢰구간", "모집단 평균의 추정 범위 제시", "95% 신뢰구간 계산", "의사결정의 불확실성 관리"],
            ["", "• 표본 데이터로부터 전체 추정", "• t-분포 기반 구간 추정", "• 정책 수립 시 고려사항"],
            ["", "• 통계적 신뢰도 정량화", "• 95% 확률로 실제값이 포함되는 구간", "• 개선 목표 설정의 기준"],
            ["", "", "", ""],
            ["🎯 고급메트릭", "감정의 복잡성과 안정성 평가", "다양한 지수와 엔트로피 계산", "조직 감정 건강도 종합 진단"],
            ["", "• 감정 일관성: 시간에 따른 안정성", "• 섀넌 엔트로피: 정보량 측정", "• 개입 필요 영역 식별"],
            ["", "• 감정 복잡도: 단순/복합 감정 비율", "• Herfindahl 지수: 집중도 측정", "• 조직 개발 전략 수립"],
            ["", "• 의료 맥락 다양성: 업무 영역별 분포", "• 변동 계수: 상대적 변동성", "• 맞춤형 개선 방안 도출"]
        ]
        
        methodology_df = pd.DataFrame(methodology_data)
        methodology_df.to_excel(writer, sheet_name='분석방법_설명', index=False, header=False)
        
        # 2. 지표 해석 가이드 시트
        interpretation_data = [
            ["지표명", "값의 범위", "해석 기준", "우수 기준", "주의 기준", "실제 활용 예시"],
            ["", "", "", "", "", ""],
            ["🎯 감정 다양성 지수", "0.0 ~ 1.0", "감정 표현의 풍부함 정도", "0.3 이상", "0.1 이하", "다양성이 높으면 솔직한 피드백 문화"],
            ["", "", "높을수록 다양한 감정 표현", "균형잡힌 감정 분포", "획일적 감정 반응", "다양성이 낮으면 표현 억제 가능성"],
            ["", "", "", "", "", ""],
            ["⚖️ 평균 감정 극성", "-1.0 ~ 1.0", "전체적인 감정의 긍정/부정 정도", "0.2 이상", "-0.2 이하", "극성이 높으면 긍정적 조직 문화"],
            ["", "", "양수: 긍정적, 음수: 부정적", "긍정적 업무 환경", "부정적 업무 환경", "극성이 낮으면 개선 노력 필요"],
            ["", "", "", "", "", ""],
            ["🤝 감정 응집도", "0.0 ~ 1.0", "감정 반응의 일관성 정도", "0.7 이상", "0.3 이하", "응집도가 높으면 공감대 형성"],
            ["", "", "높을수록 비슷한 감정 패턴", "팀워크와 동질감", "의견 분산과 갈등", "응집도가 낮으면 소통 강화 필요"],
            ["", "", "", "", "", ""],
            ["📊 강도 안정성", "0.0 ~ 1.0", "감정 강도 변동의 안정성", "0.8 이상", "0.5 이하", "안정성이 높으면 예측 가능한 반응"],
            ["", "", "높을수록 일정한 감정 표현", "안정된 감정 상태", "변동성이 큰 감정", "안정성이 낮으면 스트레스 요인 점검"],
            ["", "", "", "", "", ""],
            ["📈 감정 강도 평균", "1.0 ~ 10.0", "감정 표현의 강렬함 정도", "6.0 ~ 8.0", "4.0 이하", "적정 수준: 적극적이면서 안정적"],
            ["", "", "높을수록 강한 감정 반응", "적극적 참여", "소극적 반응", "너무 높으면 과도한 스트레스"],
            ["", "", "", "", "", "너무 낮으면 무관심 상태"],
            ["", "", "", "", "", ""],
            ["🎲 감정 엔트로피", "0.0 ~ log₂(감정수)", "감정 분포의 균등성", "최대값의 80%", "최대값의 30%", "높으면 다양하고 균형잡힌 감정"],
            ["", "", "높을수록 고른 감정 분포", "건강한 감정 다양성", "편중된 감정 반응", "낮으면 특정 감정에 치우침"],
            ["", "", "", "", "", ""],
            ["⚡ 감정 일관성 지수", "0.0 ~ 1.0", "연속된 감정의 안정성", "0.6 이상", "0.3 이하", "일관성이 높으면 안정된 관계"],
            ["", "", "높을수록 예측 가능한 반응", "신뢰할 수 있는 환경", "예측 어려운 반응", "일관성이 낮으면 관계 개선 필요"],
            ["", "", "", "", "", ""],
            ["🔄 감정 복잡도 지수", "0.0 ~ 1.0", "복합 감정의 비율", "0.2 ~ 0.4", "0.1 이하", "적정 복잡도: 미묘한 감정 표현"],
            ["", "", "높을수록 복잡한 감정 혼재", "성숙한 감정 표현", "단순한 감정만", "과도하면 혼란스러운 상태"],
            ["", "", "", "", "", ""],
            ["🏥 의료맥락 다양성", "0.0 ~ 1.0", "업무 영역별 고른 분포", "0.7 이상", "0.4 이하", "다양성이 높으면 전방위적 개선"],
            ["", "", "높을수록 전 영역 고른 피드백", "포괄적 업무 관심", "특정 영역 편중", "다양성이 낮으면 특정 영역 집중"],
            ["", "", "", "", "", ""],
            ["💫 전체 정교성", "0.0 ~ 1.0", "종합적인 감정 분석 품질", "0.6 이상", "0.3 이하", "정교성이 높으면 신뢰할 만한 분석"],
            ["", "", "높을수록 정밀한 감정 분석", "고품질 피드백", "단순한 감정 반응", "정교성이 낮으면 더 세밀한 조사 필요"]
        ]
        
        interpretation_df = pd.DataFrame(interpretation_data)
        interpretation_df.to_excel(writer, sheet_name='지표해석_가이드', index=False, header=False)
        
        # 3. 활용 방안 안내 시트
        utilization_data = [
            ["활용 영역", "주요 지표", "판단 기준", "개선 방향", "구체적 액션"],
            ["", "", "", "", ""],
            ["🎯 조직 문화 진단", "평균 감정 극성", "0.2 이상이면 긍정적", "부정적 문화 개선", "• 소통 채널 확대"],
            ["", "감정 다양성 지수", "0.3 이상이면 건강함", "표현 자유도 증진", "• 익명 피드백 시스템"],
            ["", "감정 응집도", "0.7 이상이면 통합됨", "팀워크 강화", "• 팀빌딩 활동"],
            ["", "", "", "", ""],
            ["📊 개선 우선순위", "감정 강도 분포", "4.0 이하면 시급", "참여도 제고", "• 동기부여 프로그램"],
            ["", "부정 감정 비율", "40% 이상이면 주의", "만족도 향상", "• 고충 처리 시스템"],
            ["", "재검토 필요 항목", "20% 이상이면 점검", "피드백 품질 향상", "• 설문 방식 개선"],
            ["", "", "", "", ""],
            ["🔍 세부 영역 분석", "의료맥락 다양성", "영역별 균형 확인", "전방위적 개선", "• 영역별 맞춤 교육"],
            ["", "키워드 빈도", "주요 이슈 파악", "핵심 문제 해결", "• 워드클라우드 시각화"],
            ["", "감정 복잡도", "0.4 이상이면 복잡", "명확한 소통", "• 의사소통 교육"],
            ["", "", "", "", ""],
            ["📈 모니터링 체계", "감정 일관성", "시간별 변화 추적", "지속적 개선", "• 정기 설문 실시"],
            ["", "안정성 지수", "계절별/분기별 비교", "예방적 관리", "• 트렌드 분석 대시보드"],
            ["", "신뢰구간", "통계적 유의성 확인", "신뢰할 수 있는 의사결정", "• 표본 크기 최적화"],
            ["", "", "", "", ""],
            ["🎭 감정별 맞춤 대응", "주요 감정 분포", "'감사' 많으면 → 인정 문화", "긍정 감정 강화", "• 칭찬 제도 확대"],
            ["", "", "'실망' 많으면 → 기대 관리", "부정 감정 해소", "• 기대치 명확화"],
            ["", "", "'불안' 많으면 → 안정성 제공", "심리적 안전감", "• 변화 관리 프로그램"],
            ["", "", "", "", ""],
            ["🏆 성과 측정", "품질 점수", "8.0 이상이면 우수", "분석 신뢰도 향상", "• AI 모델 정교화"],
            ["", "전체 정교성", "0.6 이상이면 양호", "데이터 품질 관리", "• 전처리 과정 개선"],
            ["", "정규성 검정", "p>0.05면 정규분포", "적절한 분석 방법", "• 비모수 통계 고려"],
            ["", "", "", "", ""],
            ["🚀 전략적 활용", "벡터 중심점", "조직의 감정 무게중심", "조직 정체성 강화", "• 핵심 가치 재정립"],
            ["", "극성 표준편차", "감정 분산 정도", "통합된 조직 문화", "• 공통 목표 설정"],
            ["", "엔트로피 비율", "정보 활용도", "효과적 피드백 시스템", "• 맞춤형 개선 계획"]
        ]
        
        utilization_df = pd.DataFrame(utilization_data)
        utilization_df.to_excel(writer, sheet_name='활용방안_안내', index=False, header=False)
        
        # 4. 실제 결과 해석 예시 시트 (현재 분석 결과 기반)
        if vector_analysis and statistical_results and advanced_metrics:
            example_data = [
                ["📋 현재 분석 결과 해석 예시", "", "", ""],
                ["", "", "", ""],
                ["지표", "측정값", "해석", "권장 조치"],
                ["", "", "", ""],
                ["🎯 감정 다양성 지수", f"{vector_analysis.get('emotion_diversity', 0):.3f}", 
                 "낮음" if vector_analysis.get('emotion_diversity', 0) < 0.3 else "보통" if vector_analysis.get('emotion_diversity', 0) < 0.6 else "높음",
                 "표현의 자유도 향상 필요" if vector_analysis.get('emotion_diversity', 0) < 0.3 else "양호한 수준"],
                 
                ["⚖️ 평균 감정 극성", f"{vector_analysis.get('avg_polarity', 0):.3f}",
                 "부정적" if vector_analysis.get('avg_polarity', 0) < -0.2 else "중립적" if vector_analysis.get('avg_polarity', 0) < 0.2 else "긍정적",
                 "긍정 문화 조성 필요" if vector_analysis.get('avg_polarity', 0) < 0 else "긍정적 문화 유지"],
                 
                ["🤝 감정 응집도", f"{vector_analysis.get('emotion_cohesion', 0):.3f}",
                 "낮음" if vector_analysis.get('emotion_cohesion', 0) < 0.3 else "보통" if vector_analysis.get('emotion_cohesion', 0) < 0.7 else "높음",
                 "팀워크 강화 프로그램" if vector_analysis.get('emotion_cohesion', 0) < 0.5 else "현재 수준 유지"],
                 
                ["📊 감정 강도 평균", f"{statistical_results.get('descriptive_stats', {}).get('intensity', {}).get('mean', 0):.2f}",
                 "낮음" if statistical_results.get('descriptive_stats', {}).get('intensity', {}).get('mean', 0) < 4 else 
                 "적정" if statistical_results.get('descriptive_stats', {}).get('intensity', {}).get('mean', 0) < 8 else "높음",
                 "참여 유도 필요" if statistical_results.get('descriptive_stats', {}).get('intensity', {}).get('mean', 0) < 5 else "적절한 수준"],
                 
                ["⚡ 감정 일관성", f"{advanced_metrics.get('emotion_consistency_index', 0):.3f}",
                 "낮음" if advanced_metrics.get('emotion_consistency_index', 0) < 0.3 else "보통" if advanced_metrics.get('emotion_consistency_index', 0) < 0.6 else "높음",
                 "관계 안정성 향상" if advanced_metrics.get('emotion_consistency_index', 0) < 0.5 else "안정적 관계 유지"],
                 
                ["🔄 감정 복잡도", f"{advanced_metrics.get('emotion_complexity_index', 0):.3f}",
                 "단순" if advanced_metrics.get('emotion_complexity_index', 0) < 0.2 else "적정" if advanced_metrics.get('emotion_complexity_index', 0) < 0.4 else "복잡",
                 "감정 표현 다양화" if advanced_metrics.get('emotion_complexity_index', 0) < 0.2 else "현재 수준 적절"],
                 
                ["💫 전체 정교성", f"{advanced_metrics.get('overall_sophistication', 0):.3f}",
                 "낮음" if advanced_metrics.get('overall_sophistication', 0) < 0.3 else "보통" if advanced_metrics.get('overall_sophistication', 0) < 0.6 else "높음",
                 "피드백 품질 향상" if advanced_metrics.get('overall_sophistication', 0) < 0.5 else "고품질 피드백 유지"],
                 
                ["", "", "", ""],
                ["📊 종합 진단", "", "", ""],
                ["", "• 현재 조직의 감정 상태를 종합적으로 평가한 결과입니다.", "", ""],
                ["", "• 각 지표를 통해 강점과 개선점을 파악할 수 있습니다.", "", ""],
                ["", "• 정기적인 모니터링을 통해 변화 추이를 관찰하세요.", "", ""],
                ["", "• 구체적인 개선 방안은 '활용방안_안내' 시트를 참고하세요.", "", ""]
            ]
            
            example_df = pd.DataFrame(example_data)
            example_df.to_excel(writer, sheet_name='결과해석_예시', index=False, header=False)
    
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
    
    def calculate_emotion_vectors(self, results: list) -> dict:
        """
        감정 데이터를 벡터 공간으로 변환하여 수학적 분석을 수행합니다.
        
        Args:
            results: 분석 결과 리스트
            
        Returns:
            dict: 벡터 공간 분석 결과
        """
        # 감정을 숫자 벡터로 매핑
        emotion_mapping = {
            "기쁨": [1, 0, 0, 0, 0, 0, 0, 0],     # 긍정군
            "감사": [0, 1, 0, 0, 0, 0, 0, 0],
            "신뢰": [0, 0, 1, 0, 0, 0, 0, 0], 
            "만족": [0, 0, 0, 1, 0, 0, 0, 0],
            "분노": [0, 0, 0, 0, 1, 0, 0, 0],     # 부정군
            "슬픔": [0, 0, 0, 0, 0, 1, 0, 0],
            "두려움": [0, 0, 0, 0, 0, 0, 1, 0],
            "실망": [0, 0, 0, 0, 0, 0, 0, 1],
            "평온": [0, 0, 0, 0, 0, 0, 0, 0],     # 중립군 (원점)
            "무관심": [0, 0, 0, 0, 0, 0, 0, 0]
        }
        
        # 감정 벡터 생성
        emotion_vectors = []
        emotion_intensities = []
        
        for result in results:
            primary = result.get('primary_emotion', '평온')
            secondary = result.get('secondary_emotion')
            intensity = result.get('emotion_intensity', 5)
            emotion_mix = result.get('emotion_mix', {})
            
            if primary in emotion_mapping:
                # 복합 감정인 경우 가중 평균 벡터 생성
                if secondary and emotion_mix:
                    primary_weight = emotion_mix.get(primary, 1.0)
                    secondary_weight = emotion_mix.get(secondary, 0.0)
                    
                    primary_vec = np.array(emotion_mapping[primary]) * primary_weight
                    secondary_vec = np.array(emotion_mapping.get(secondary, [0]*8)) * secondary_weight
                    
                    emotion_vector = primary_vec + secondary_vec
                else:
                    emotion_vector = np.array(emotion_mapping[primary])
                
                # 강도로 벡터 크기 조정
                emotion_vector = emotion_vector * (intensity / 10.0)
                emotion_vectors.append(emotion_vector)
                emotion_intensities.append(intensity)
        
        if not emotion_vectors:
            return {}
        
        emotion_matrix = np.array(emotion_vectors)
        
        # 1. 중심 벡터 (평균 감정 벡터)
        centroid = np.mean(emotion_matrix, axis=0)
        
        # 2. 감정 다양성 (벡터 분산)
        emotion_variance = np.var(emotion_matrix, axis=0)
        emotion_diversity = np.mean(emotion_variance)
        
        # 3. 감정 극성 (긍정-부정 축)
        positive_axis = np.sum(emotion_matrix[:, :4], axis=1)  # 긍정 감정 합
        negative_axis = np.sum(emotion_matrix[:, 4:8], axis=1)  # 부정 감정 합
        polarity_scores = positive_axis - negative_axis
        avg_polarity = np.mean(polarity_scores)
        polarity_std = np.std(polarity_scores)
        
        # 4. 감정 응집도 (코사인 유사도 기반)
        if len(emotion_vectors) > 1:
            similarity_matrix = cosine_similarity(emotion_matrix)
            # 대각선 제외한 평균 유사도
            mask = ~np.eye(similarity_matrix.shape[0], dtype=bool)
            avg_similarity = np.mean(similarity_matrix[mask])
        else:
            avg_similarity = 1.0
        
        # 5. 감정 안정성 (강도 변동 계수)
        intensity_cv = np.std(emotion_intensities) / np.mean(emotion_intensities) if np.mean(emotion_intensities) > 0 else 0
        
        return {
            "centroid_vector": centroid.tolist(),
            "emotion_diversity": float(emotion_diversity),
            "avg_polarity": float(avg_polarity),
            "polarity_std": float(polarity_std),
            "emotion_cohesion": float(avg_similarity),
            "intensity_stability": float(1 - intensity_cv),  # 높을수록 안정적
            "vector_magnitude": float(np.linalg.norm(centroid)),
            "emotion_distribution": {
                "positive_ratio": float(np.mean(positive_axis > 0)),
                "negative_ratio": float(np.mean(negative_axis > 0)),
                "neutral_ratio": float(np.mean((positive_axis == 0) & (negative_axis == 0)))
            }
        }
    
    def statistical_analysis(self, results: list) -> dict:
        """
        감정 데이터에 대한 통계적 분석을 수행합니다.
        
        Args:
            results: 분석 결과 리스트
            
        Returns:
            dict: 통계 분석 결과
        """
        if not results:
            return {}
        
        # 데이터 추출
        emotions = [r.get('primary_emotion', '평온') for r in results]
        intensities = [r.get('emotion_intensity', 5) for r in results]
        confidences = [r.get('confidence_score', 5) for r in results]
        complexities = [r.get('emotional_complexity', '단순') for r in results]
        
        # 1. 기술 통계량
        intensity_stats = stats.describe(intensities)
        confidence_stats = stats.describe(confidences)
        
        # 2. 분포 정규성 검정 (Shapiro-Wilk)
        if len(intensities) >= 3:
            intensity_normality = stats.shapiro(intensities)
            confidence_normality = stats.shapiro(confidences)
        else:
            intensity_normality = (0.0, 1.0)
            confidence_normality = (0.0, 1.0)
        
        # 3. 감정과 강도 간 상관관계
        emotion_intensity_corr = self._calculate_emotion_intensity_correlation(emotions, intensities)
        
        # 4. 신뢰구간 계산 (95%)
        intensity_ci = stats.t.interval(0.95, len(intensities)-1, 
                                       loc=np.mean(intensities), 
                                       scale=stats.sem(intensities))
        confidence_ci = stats.t.interval(0.95, len(confidences)-1,
                                        loc=np.mean(confidences),
                                        scale=stats.sem(confidences))
        
        # 5. 감정 엔트로피 계산
        emotion_counts = Counter(emotions)
        total = len(emotions)
        emotion_entropy = -sum((count/total) * math.log2(count/total) 
                              for count in emotion_counts.values())
        
        # 6. 복합성 비율
        complex_ratio = emotions.count('복합') / len(complexities) if complexities else 0
        
        # 7. 이상값 탐지 (IQR 방법)
        q1_intensity = np.percentile(intensities, 25)
        q3_intensity = np.percentile(intensities, 75)
        iqr_intensity = q3_intensity - q1_intensity
        intensity_outliers = [x for x in intensities 
                             if x < q1_intensity - 1.5*iqr_intensity or x > q3_intensity + 1.5*iqr_intensity]
        
        return {
            "descriptive_stats": {
                "intensity": {
                    "mean": float(intensity_stats.mean),
                    "variance": float(intensity_stats.variance),
                    "skewness": float(intensity_stats.skewness),
                    "kurtosis": float(intensity_stats.kurtosis),
                    "min": float(intensity_stats.minmax[0]),
                    "max": float(intensity_stats.minmax[1]),
                    "std": float(np.std(intensities)),
                    "median": float(np.median(intensities)),
                    "q1": float(q1_intensity),
                    "q3": float(q3_intensity)
                },
                "confidence": {
                    "mean": float(confidence_stats.mean),
                    "variance": float(confidence_stats.variance),
                    "std": float(np.std(confidences)),
                    "median": float(np.median(confidences))
                }
            },
            "normality_tests": {
                "intensity_shapiro": {
                    "statistic": float(intensity_normality[0]),
                    "p_value": float(intensity_normality[1]),
                    "is_normal": intensity_normality[1] > 0.05
                },
                "confidence_shapiro": {
                    "statistic": float(confidence_normality[0]),
                    "p_value": float(confidence_normality[1]),
                    "is_normal": confidence_normality[1] > 0.05
                }
            },
            "correlations": emotion_intensity_corr,
            "confidence_intervals": {
                "intensity_95ci": [float(intensity_ci[0]), float(intensity_ci[1])],
                "confidence_95ci": [float(confidence_ci[0]), float(confidence_ci[1])]
            },
            "information_theory": {
                "emotion_entropy": float(emotion_entropy),
                "max_entropy": float(math.log2(len(set(emotions)))),
                "entropy_ratio": float(emotion_entropy / math.log2(len(set(emotions)))) if len(set(emotions)) > 1 else 0
            },
            "complexity_analysis": {
                "complex_ratio": float(complex_ratio),
                "simple_ratio": float(1 - complex_ratio)
            },
            "outlier_detection": {
                "intensity_outliers": len(intensity_outliers),
                "outlier_ratio": float(len(intensity_outliers) / len(intensities))
            }
        }
    
    def _calculate_emotion_intensity_correlation(self, emotions: list, intensities: list) -> dict:
        """감정 카테고리와 강도 간의 상관관계를 계산합니다."""
        # 감정을 숫자로 매핑
        emotion_scores = []
        for emotion in emotions:
            if emotion in ["기쁨", "감사", "신뢰", "만족"]:
                emotion_scores.append(1)  # 긍정
            elif emotion in ["분노", "슬픔", "두려움", "실망"]:
                emotion_scores.append(-1)  # 부정
            else:
                emotion_scores.append(0)  # 중립
        
        if len(set(emotion_scores)) > 1:
            correlation, p_value = stats.pearsonr(emotion_scores, intensities)
            return {
                "pearson_r": float(correlation),
                "p_value": float(p_value),
                "significant": p_value < 0.05
            }
        else:
            return {"pearson_r": 0.0, "p_value": 1.0, "significant": False}
    
    def advanced_emotion_metrics(self, results: list) -> dict:
        """
        고급 감정 분석 메트릭을 계산합니다.
        
        Args:
            results: 분석 결과 리스트
            
        Returns:
            dict: 고급 메트릭 결과
        """
        if not results:
            return {}
        
        # 데이터 추출
        primary_emotions = [r.get('primary_emotion', '평온') for r in results]
        secondary_emotions = [r.get('secondary_emotion') for r in results]
        emotion_mixes = [r.get('emotion_mix', {}) for r in results]
        medical_contexts = [r.get('medical_context', []) for r in results]
        
        # 1. 감정 일관성 지수 (Emotion Consistency Index)
        consistency_scores = []
        for i in range(len(results)-1):
            curr_emotion = primary_emotions[i]
            next_emotion = primary_emotions[i+1]
            
            # 같은 감정군인지 확인
            same_group = self._same_emotion_group(curr_emotion, next_emotion)
            consistency_scores.append(1.0 if same_group else 0.0)
        
        emotion_consistency = np.mean(consistency_scores) if consistency_scores else 0.0
        
        # 2. 감정 복잡도 지수 (Emotion Complexity Index)
        complexity_scores = []
        for emotion_mix in emotion_mixes:
            if emotion_mix and len(emotion_mix) > 1:
                # 섀넌 엔트로피 기반 복잡도
                values = list(emotion_mix.values())
                entropy = -sum(v * math.log2(v) for v in values if v > 0)
                complexity_scores.append(entropy)
            else:
                complexity_scores.append(0.0)
        
        avg_complexity = np.mean(complexity_scores) if complexity_scores else 0.0
        
        # 3. 의료 맥락 다양성 지수
        all_contexts = []
        for contexts in medical_contexts:
            if isinstance(contexts, list):
                all_contexts.extend(contexts)
        
        if all_contexts:
            context_counts = Counter(all_contexts)
            total_contexts = len(all_contexts)
            context_entropy = -sum((count/total_contexts) * math.log2(count/total_contexts) 
                                  for count in context_counts.values())
            max_context_entropy = math.log2(len(context_counts))
            context_diversity = context_entropy / max_context_entropy if max_context_entropy > 0 else 0
        else:
            context_diversity = 0.0
        
        # 4. 감정 변동성 지수 (Emotional Volatility Index)
        intensities = [r.get('emotion_intensity', 5) for r in results]
        if len(intensities) > 1:
            # 연속된 강도 차이의 평균
            intensity_changes = [abs(intensities[i+1] - intensities[i]) for i in range(len(intensities)-1)]
            volatility = np.mean(intensity_changes) / 10.0  # 정규화 (0-1)
        else:
            volatility = 0.0
        
        # 5. 감정 집중도 지수 (Emotion Concentration Index)
        emotion_counts = Counter(primary_emotions)
        total_emotions = len(primary_emotions)
        # Herfindahl-Hirschman Index 변형
        concentration = sum((count/total_emotions)**2 for count in emotion_counts.values())
        
        return {
            "emotion_consistency_index": float(emotion_consistency),
            "emotion_complexity_index": float(avg_complexity),
            "medical_context_diversity": float(context_diversity),
            "emotional_volatility_index": float(volatility),
            "emotion_concentration_index": float(concentration),
            "stability_score": float(1 - volatility),  # 변동성의 역수
            "balance_score": float(1 - concentration),  # 집중도의 역수
            "overall_sophistication": float((avg_complexity + context_diversity) / 2)
        }
    
    def _same_emotion_group(self, emotion1: str, emotion2: str) -> bool:
        """두 감정이 같은 그룹에 속하는지 확인합니다."""
        positive = ["기쁨", "감사", "신뢰", "만족"]
        negative = ["분노", "슬픔", "두려움", "실망"]
        neutral = ["평온", "무관심"]
        
        if emotion1 in positive and emotion2 in positive:
            return True
        elif emotion1 in negative and emotion2 in negative:
            return True
        elif emotion1 in neutral and emotion2 in neutral:
            return True
        else:
            return False
    
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
    
    def process_xlsx_with_refined_text(self, input_file: str, refined_column: str, anonymized_column: str = None, output_file: str = None, delay: float = 0.1, max_rows: int = None, use_batch: bool = True, batch_size: int = 10, enable_quality_retry: bool = True):
        """
        이미 정제된 텍스트가 있는 엑셀 파일을 분석하여 결과를 저장합니다.
        
        Args:
            input_file: 입력 엑셀 파일 경로
            refined_column: 정제된 텍스트가 포함된 컬럼명
            anonymized_column: 비식별 처리 여부 컬럼명 (선택사항)
            output_file: 결과를 저장할 파일 경로 (기본값: 입력파일명_analyzed.xlsx)
            delay: API 호출 간 대기 시간 (초) - 배치 처리 시 무시됨
            max_rows: 테스트용으로 처리할 최대 행 수
            use_batch: 배치 처리 사용 여부 (기본값: True)
            batch_size: 배치 크기 (기본값: 10)
            enable_quality_retry: 낮은 품질 항목 재분석 여부 (기본값: True)
        """
        # 엑셀 파일 읽기
        df = pd.read_excel(input_file)
        
        # 테스트용으로 일부 데이터만 처리하는 경우
        if max_rows:
            df = df.head(max_rows)
            print(f"전체 데이터에서 상단 {len(df)}개 추출")
        
        # 지정한 컬럼이 존재하는지 확인
        if refined_column not in df.columns:
            available_columns = list(df.columns)
            raise ValueError(f"'{refined_column}' 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {available_columns}")
        
        # 출력 파일명 설정
        if output_file is None:
            output_file = str(Path(input_file).stem) + "_analyzed.xlsx"
        
        # 정제된 텍스트가 있는 데이터만 필터링
        valid_data = df[df[refined_column].notna() & (df[refined_column] != "")]
        total_rows = len(valid_data)
        
        print(f"총 {len(df)}개 행 중 {total_rows}개의 유효한 '{refined_column}' 텍스트를 분석합니다...")
        
        # 텍스트와 비식별 정보 추출
        texts_and_flags = []
        for _, row in valid_data.iterrows():
            refined_text = str(row[refined_column]) if pd.notna(row[refined_column]) else ""
            is_anonymized = bool(row[anonymized_column]) if anonymized_column and anonymized_column in df.columns and pd.notna(row[anonymized_column]) else False
            texts_and_flags.append((refined_text, is_anonymized))
        
        # 배치 처리 또는 순차 처리 선택
        if use_batch:
            print(f"배치 처리 모드 (배치 크기: {batch_size})")
            print(f"예상 소요시간: 약 {math.ceil(total_rows / batch_size) * 2}분 (배치 처리 기준)")
            
            # 진행률 표시와 함께 배치 처리
            results = []
            with tqdm(total=total_rows, desc="분석 진행률", unit="건") as pbar:
                for i in range(0, len(texts_and_flags), batch_size):
                    batch_texts_flags = texts_and_flags[i:i+batch_size]
                    batch_results = self.analyze_refined_batch(batch_texts_flags, len(batch_texts_flags))
                    results.extend(batch_results)
                    pbar.update(len(batch_texts_flags))
        else:
            print(f"순차 처리 모드")
            est_sec = total_rows * delay
            est_time = str(datetime.timedelta(seconds=math.ceil(est_sec)))
            print(f"예상 소요시간: {est_time} (지연 {delay}초/건 기준)")
            
            # 순차 처리와 진행률 표시
            results = []
            with tqdm(total=total_rows, desc="분석 진행률", unit="건") as pbar:
                for refined_text, is_anonymized in texts_and_flags:
                    result = self.analyze_refined_text(refined_text, is_anonymized)
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
        for idx, (result, (refined_text, _)) in enumerate(zip(results, texts_and_flags)):
            quality_check = self.validate_analysis_quality(result, refined_text)
            quality_results.append(quality_check)
        
        # 낮은 품질 항목 재분석 (활성화된 경우에만)
        if enable_quality_retry:
            results, quality_results = self.retry_low_quality_analysis_refined(texts_and_flags, results, quality_results, max_retries=3)
        
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
        
        # 수학적/통계적 분석 수행
        print("\n수학적 분석 수행 중...")
        vector_analysis = self.calculate_emotion_vectors(results)
        
        print("통계적 분석 수행 중...")
        statistical_results = self.statistical_analysis(results)
        
        print("고급 감정 메트릭 계산 중...")
        advanced_metrics = self.advanced_emotion_metrics(results)
        
        # 분석 결과를 데이터프레임으로 변환
        result_df = pd.DataFrame(results)
        
        # 원본 데이터와 분석 결과를 합친 새로운 데이터프레임 생성
        # 유효한 데이터의 인덱스를 사용하여 매핑
        processed_df = valid_data.copy().reset_index(drop=True)
        
        # 컬럼명을 한국어로 매핑 (고도화 버전)
        korean_column_names = {
            'refined_text': '분석텍스트',
            'is_anonymized': '비식별처리여부',
            'primary_emotion': '주요감정',
            'secondary_emotion': '보조감정', 
            'emotion_intensity': '감정강도',
            'emotional_complexity': '감정복합성',
            'emotion_mix': '감정비율',
            'medical_context': '의료맥락',
            'context_weight': '맥락중요도',
            'sentiment': '감정분석',
            'sentiment_intensity': '감정강도점수',
            'confidence_score': 'AI신뢰도',
            'key_terms': '핵심키워드',
            'labels': '분류라벨',
            'quality_score': '품질점수',
            'needs_review': '재검토필요',
            'quality_issues': '품질문제'
        }
        
        for col in result_df.columns:
            korean_col_name = korean_column_names.get(col, col)
            processed_df[f"{refined_column}_{korean_col_name}"] = result_df[col]
        
        # 수학적 분석 결과를 별도 시트로 저장
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 메인 데이터
            processed_df.to_excel(writer, sheet_name='분석결과', index=False)
            
            # 벡터 분석 결과
            if vector_analysis:
                vector_df = pd.DataFrame([vector_analysis])
                vector_df.to_excel(writer, sheet_name='벡터분석', index=False)
            
            # 통계 분석 결과
            if statistical_results:
                # 기술통계량
                desc_stats = pd.DataFrame(statistical_results.get('descriptive_stats', {}))
                desc_stats.to_excel(writer, sheet_name='기술통계량', index=True)
                
                # 정규성 검정
                normality_df = pd.DataFrame(statistical_results.get('normality_tests', {}))
                normality_df.to_excel(writer, sheet_name='정규성검정', index=True)
                
                # 상관관계
                corr_df = pd.DataFrame([statistical_results.get('correlations', {})])
                corr_df.to_excel(writer, sheet_name='상관관계', index=False)
                
                # 신뢰구간
                ci_df = pd.DataFrame([statistical_results.get('confidence_intervals', {})])
                ci_df.to_excel(writer, sheet_name='신뢰구간', index=False)
            
            # 고급 메트릭
            if advanced_metrics:
                metrics_df = pd.DataFrame([advanced_metrics])
                metrics_df.to_excel(writer, sheet_name='고급메트릭', index=False)
            
            # 상세 설명 시트 추가
            self._create_explanation_sheets(writer, vector_analysis, statistical_results, advanced_metrics)
        
        print(f"\n분석 완료! 결과가 '{output_file}'에 저장되었습니다.")
        print("📊 다중 시트 엑셀 파일이 생성되었습니다:")
        print("  - 분석결과: 기본 감정 분석 데이터")
        print("  - 벡터분석: 감정 벡터 공간 분석")
        print("  - 기술통계량: 기본 통계 정보")
        print("  - 정규성검정: 분포 정규성 검정 결과")
        print("  - 상관관계: 감정-강도 상관분석")
        print("  - 신뢰구간: 95% 신뢰구간")
        print("  - 고급메트릭: 감정 복잡도, 일관성 등")
        print("  - 분석방법_설명: 수학/통계 방법론 설명")
        print("  - 지표해석_가이드: 각 지표의 의미와 기준")
        print("  - 활용방안_안내: 실무 활용 가이드")
        print("  - 결과해석_예시: 현재 결과 해석 예시")
        
        # 낮은 품질 항목 안내
        if low_quality_indices:
            print(f"\n⚠️  {len(low_quality_indices)}개 항목이 재검토가 필요합니다.")
            print("세부 사항은 'quality_issues' 컬럼을 확인하세요.")
        
        # 고도화된 감정 분석 통계 출력
        print(f"\n=== '{refined_column}' 고도화된 분석 결과 ====")
        
        # 기존 3분류 감정 통계
        sentiment_counts = result_df['sentiment'].value_counts()
        print(f"기본 감정 분류:")
        for sentiment, count in sentiment_counts.items():
            percentage = (count / len(result_df)) * 100
            print(f"  {sentiment}: {count}개 ({percentage:.1f}%)")
        
        # 8가지 세분화된 감정 통계
        if 'primary_emotion' in result_df.columns:
            primary_emotion_counts = result_df['primary_emotion'].value_counts()
            print(f"\n세분화된 주요 감정:")
            for emotion, count in primary_emotion_counts.items():
                percentage = (count / len(result_df)) * 100
                print(f"  {emotion}: {count}개 ({percentage:.1f}%)")
        
        # 복합 감정 통계
        if 'emotional_complexity' in result_df.columns:
            complexity_counts = result_df['emotional_complexity'].value_counts()
            print(f"\n감정 복합성:")
            for complexity, count in complexity_counts.items():
                percentage = (count / len(result_df)) * 100
                print(f"  {complexity}: {count}개 ({percentage:.1f}%)")
        
        # 의료 맥락 통계
        if 'medical_context' in result_df.columns:
            all_contexts = []
            for contexts in result_df['medical_context']:
                if isinstance(contexts, list):
                    all_contexts.extend(contexts)
            if all_contexts:
                from collections import Counter
                context_counts = Counter(all_contexts)
                print(f"\n의료 협업 맥락:")
                for context, count in context_counts.most_common():
                    print(f"  {context}: {count}건")
        
        # 기존 통계
        intensity_mean = result_df['emotion_intensity'].mean() if 'emotion_intensity' in result_df.columns else result_df['sentiment_intensity'].mean()
        confidence_mean = result_df['quality_score'].mean() if 'quality_score' in result_df.columns else result_df['confidence_score'].mean()
        
        print(f"\n평균 감정 강도: {intensity_mean:.1f}/10")
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
        
        # 수학적/통계적 분석 결과 요약 출력
        if vector_analysis:
            print(f"\n=== 감정 벡터 분석 결과 ====")
            print(f"감정 다양성 지수: {vector_analysis.get('emotion_diversity', 0):.3f}")
            print(f"평균 감정 극성: {vector_analysis.get('avg_polarity', 0):.3f}")
            print(f"감정 응집도: {vector_analysis.get('emotion_cohesion', 0):.3f}")
            print(f"강도 안정성: {vector_analysis.get('intensity_stability', 0):.3f}")
            
            dist = vector_analysis.get('emotion_distribution', {})
            print(f"감정 분포 - 긍정: {dist.get('positive_ratio', 0):.1%}, "
                  f"부정: {dist.get('negative_ratio', 0):.1%}, "
                  f"중립: {dist.get('neutral_ratio', 0):.1%}")
        
        if statistical_results:
            print(f"\n=== 통계적 분석 결과 ====")
            desc_stats = statistical_results.get('descriptive_stats', {})
            intensity_stats = desc_stats.get('intensity', {})
            
            print(f"감정 강도 통계:")
            print(f"  평균: {intensity_stats.get('mean', 0):.2f} ± {intensity_stats.get('std', 0):.2f}")
            print(f"  중앙값: {intensity_stats.get('median', 0):.2f}")
            print(f"  왜도: {intensity_stats.get('skewness', 0):.3f}")
            print(f"  첨도: {intensity_stats.get('kurtosis', 0):.3f}")
            
            # 정규성 검정 결과
            normality = statistical_results.get('normality_tests', {})
            intensity_norm = normality.get('intensity_shapiro', {})
            print(f"정규성 검정 (Shapiro-Wilk): p={intensity_norm.get('p_value', 0):.4f} "
                  f"({'정규분포' if intensity_norm.get('is_normal', False) else '비정규분포'})")
            
            # 상관관계
            corr = statistical_results.get('correlations', {})
            print(f"감정-강도 상관계수: r={corr.get('pearson_r', 0):.3f} "
                  f"({'유의' if corr.get('significant', False) else '비유의'})")
            
            # 신뢰구간
            ci = statistical_results.get('confidence_intervals', {})
            intensity_ci = ci.get('intensity_95ci', [0, 0])
            print(f"감정 강도 95% 신뢰구간: [{intensity_ci[0]:.2f}, {intensity_ci[1]:.2f}]")
            
            # 정보 이론
            info_theory = statistical_results.get('information_theory', {})
            print(f"감정 엔트로피: {info_theory.get('emotion_entropy', 0):.3f} "
                  f"(최대: {info_theory.get('max_entropy', 0):.3f})")
            
        if advanced_metrics:
            print(f"\n=== 고급 감정 메트릭 ====")
            print(f"감정 일관성 지수: {advanced_metrics.get('emotion_consistency_index', 0):.3f}")
            print(f"감정 복잡도 지수: {advanced_metrics.get('emotion_complexity_index', 0):.3f}")
            print(f"의료 맥락 다양성: {advanced_metrics.get('medical_context_diversity', 0):.3f}")
            print(f"감정 변동성 지수: {advanced_metrics.get('emotional_volatility_index', 0):.3f}")
            print(f"감정 집중도 지수: {advanced_metrics.get('emotion_concentration_index', 0):.3f}")
            print(f"안정성 점수: {advanced_metrics.get('stability_score', 0):.3f}")
            print(f"균형성 점수: {advanced_metrics.get('balance_score', 0):.3f}")
            print(f"전체 정교성: {advanced_metrics.get('overall_sophistication', 0):.3f}")

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
        
        # 수학적/통계적 분석 수행
        print("\n수학적 분석 수행 중...")
        vector_analysis = self.calculate_emotion_vectors(results)
        
        print("통계적 분석 수행 중...")
        statistical_results = self.statistical_analysis(results)
        
        print("고급 감정 메트릭 계산 중...")
        advanced_metrics = self.advanced_emotion_metrics(results)
        
        # 분석 결과를 데이터프레임으로 변환
        result_df = pd.DataFrame(results)
        
        # 원본 데이터와 분석 결과를 합친 새로운 데이터프레임 생성
        processed_df = df.copy()
        
        # 컬럼명을 한국어로 매핑 (고도화 버전)
        korean_column_names = {
            'refined_text': '정제텍스트',
            'is_anonymized': '비식별처리여부',
            'primary_emotion': '주요감정',
            'secondary_emotion': '보조감정', 
            'emotion_intensity': '감정강도',
            'emotional_complexity': '감정복합성',
            'emotion_mix': '감정비율',
            'medical_context': '의료맥락',
            'context_weight': '맥락중요도',
            'sentiment': '감정분석',
            'sentiment_intensity': '감정강도점수',
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
        
        # 수학적 분석 결과를 별도 시트로 저장
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 메인 데이터
            processed_df.to_excel(writer, sheet_name='분석결과', index=False)
            
            # 벡터 분석 결과
            if vector_analysis:
                vector_df = pd.DataFrame([vector_analysis])
                vector_df.to_excel(writer, sheet_name='벡터분석', index=False)
            
            # 통계 분석 결과
            if statistical_results:
                # 기술통계량
                desc_stats = pd.DataFrame(statistical_results.get('descriptive_stats', {}))
                desc_stats.to_excel(writer, sheet_name='기술통계량', index=True)
                
                # 정규성 검정
                normality_df = pd.DataFrame(statistical_results.get('normality_tests', {}))
                normality_df.to_excel(writer, sheet_name='정규성검정', index=True)
                
                # 상관관계
                corr_df = pd.DataFrame([statistical_results.get('correlations', {})])
                corr_df.to_excel(writer, sheet_name='상관관계', index=False)
                
                # 신뢰구간
                ci_df = pd.DataFrame([statistical_results.get('confidence_intervals', {})])
                ci_df.to_excel(writer, sheet_name='신뢰구간', index=False)
            
            # 고급 메트릭
            if advanced_metrics:
                metrics_df = pd.DataFrame([advanced_metrics])
                metrics_df.to_excel(writer, sheet_name='고급메트릭', index=False)
            
            # 상세 설명 시트 추가
            self._create_explanation_sheets(writer, vector_analysis, statistical_results, advanced_metrics)
        
        print(f"\n분석 완료! 결과가 '{output_file}'에 저장되었습니다.")
        print("📊 다중 시트 엑셀 파일이 생성되었습니다:")
        print("  - 분석결과: 기본 감정 분석 데이터")
        print("  - 벡터분석: 감정 벡터 공간 분석")
        print("  - 기술통계량: 기본 통계 정보")
        print("  - 정규성검정: 분포 정규성 검정 결과")
        print("  - 상관관계: 감정-강도 상관분석")
        print("  - 신뢰구간: 95% 신뢰구간")
        print("  - 고급메트릭: 감정 복잡도, 일관성 등")
        print("  - 분석방법_설명: 수학/통계 방법론 설명")
        print("  - 지표해석_가이드: 각 지표의 의미와 기준")
        print("  - 활용방안_안내: 실무 활용 가이드")
        print("  - 결과해석_예시: 현재 결과 해석 예시")
        
        # 낮은 품질 항목 안내
        if low_quality_indices:
            print(f"\n⚠️  {len(low_quality_indices)}개 항목이 재검토가 필요합니다.")
            print("세부 사항은 'quality_issues' 컬럼을 확인하세요.")
        
        # 고도화된 감정 분석 통계 출력
        print(f"\n=== '{column_name}' 고도화된 분석 결과 ====")
        
        # 기존 3분류 감정 통계
        sentiment_counts = result_df['sentiment'].value_counts()
        print(f"기본 감정 분류:")
        for sentiment, count in sentiment_counts.items():
            percentage = (count / len(result_df)) * 100
            print(f"  {sentiment}: {count}개 ({percentage:.1f}%)")
        
        # 8가지 세분화된 감정 통계
        if 'primary_emotion' in result_df.columns:
            primary_emotion_counts = result_df['primary_emotion'].value_counts()
            print(f"\n세분화된 주요 감정:")
            for emotion, count in primary_emotion_counts.items():
                percentage = (count / len(result_df)) * 100
                print(f"  {emotion}: {count}개 ({percentage:.1f}%)")
        
        # 복합 감정 통계
        if 'emotional_complexity' in result_df.columns:
            complexity_counts = result_df['emotional_complexity'].value_counts()
            print(f"\n감정 복합성:")
            for complexity, count in complexity_counts.items():
                percentage = (count / len(result_df)) * 100
                print(f"  {complexity}: {count}개 ({percentage:.1f}%)")
        
        # 의료 맥락 통계
        if 'medical_context' in result_df.columns:
            all_contexts = []
            for contexts in result_df['medical_context']:
                if isinstance(contexts, list):
                    all_contexts.extend(contexts)
            if all_contexts:
                from collections import Counter
                context_counts = Counter(all_contexts)
                print(f"\n의료 협업 맥락:")
                for context, count in context_counts.most_common():
                    print(f"  {context}: {count}건")
        
        # 기존 통계
        intensity_mean = result_df['emotion_intensity'].mean() if 'emotion_intensity' in result_df.columns else result_df['sentiment_intensity'].mean()
        confidence_mean = result_df['quality_score'].mean() if 'quality_score' in result_df.columns else result_df['confidence_score'].mean()
        
        print(f"\n평균 감정 강도: {intensity_mean:.1f}/10")
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
        
        # 수학적/통계적 분석 결과 요약 출력
        if vector_analysis:
            print(f"\n=== 감정 벡터 분석 결과 ====")
            print(f"감정 다양성 지수: {vector_analysis.get('emotion_diversity', 0):.3f}")
            print(f"평균 감정 극성: {vector_analysis.get('avg_polarity', 0):.3f}")
            print(f"감정 응집도: {vector_analysis.get('emotion_cohesion', 0):.3f}")
            print(f"강도 안정성: {vector_analysis.get('intensity_stability', 0):.3f}")
            
            dist = vector_analysis.get('emotion_distribution', {})
            print(f"감정 분포 - 긍정: {dist.get('positive_ratio', 0):.1%}, "
                  f"부정: {dist.get('negative_ratio', 0):.1%}, "
                  f"중립: {dist.get('neutral_ratio', 0):.1%}")
        
        if statistical_results:
            print(f"\n=== 통계적 분석 결과 ====")
            desc_stats = statistical_results.get('descriptive_stats', {})
            intensity_stats = desc_stats.get('intensity', {})
            
            print(f"감정 강도 통계:")
            print(f"  평균: {intensity_stats.get('mean', 0):.2f} ± {intensity_stats.get('std', 0):.2f}")
            print(f"  중앙값: {intensity_stats.get('median', 0):.2f}")
            print(f"  왜도: {intensity_stats.get('skewness', 0):.3f}")
            print(f"  첨도: {intensity_stats.get('kurtosis', 0):.3f}")
            
            # 정규성 검정 결과
            normality = statistical_results.get('normality_tests', {})
            intensity_norm = normality.get('intensity_shapiro', {})
            print(f"정규성 검정 (Shapiro-Wilk): p={intensity_norm.get('p_value', 0):.4f} "
                  f"({'정규분포' if intensity_norm.get('is_normal', False) else '비정규분포'})")
            
            # 상관관계
            corr = statistical_results.get('correlations', {})
            print(f"감정-강도 상관계수: r={corr.get('pearson_r', 0):.3f} "
                  f"({'유의' if corr.get('significant', False) else '비유의'})")
            
            # 신뢰구간
            ci = statistical_results.get('confidence_intervals', {})
            intensity_ci = ci.get('intensity_95ci', [0, 0])
            print(f"감정 강도 95% 신뢰구간: [{intensity_ci[0]:.2f}, {intensity_ci[1]:.2f}]")
            
            # 정보 이론
            info_theory = statistical_results.get('information_theory', {})
            print(f"감정 엔트로피: {info_theory.get('emotion_entropy', 0):.3f} "
                  f"(최대: {info_theory.get('max_entropy', 0):.3f})")
            
        if advanced_metrics:
            print(f"\n=== 고급 감정 메트릭 ====")
            print(f"감정 일관성 지수: {advanced_metrics.get('emotion_consistency_index', 0):.3f}")
            print(f"감정 복잡도 지수: {advanced_metrics.get('emotion_complexity_index', 0):.3f}")
            print(f"의료 맥락 다양성: {advanced_metrics.get('medical_context_diversity', 0):.3f}")
            print(f"감정 변동성 지수: {advanced_metrics.get('emotional_volatility_index', 0):.3f}")
            print(f"감정 집중도 지수: {advanced_metrics.get('emotion_concentration_index', 0):.3f}")
            print(f"안정성 점수: {advanced_metrics.get('stability_score', 0):.3f}")
            print(f"균형성 점수: {advanced_metrics.get('balance_score', 0):.3f}")
            print(f"전체 정교성: {advanced_metrics.get('overall_sophistication', 0):.3f}")

def get_user_input():
    """
    사용자로부터 파일 경로와 설정을 입력받습니다.
    """
    print("=== 고도화된 텍스트 분석 시스템 ====")
    print("- 배치 처리로 성능 향상")
    print("- 감정 강도 점수 (1-10 스케일)")
    print("- 실시간 진행률 모니터링")
    print("- 키워드 추출 및 빈도 분석")
    print("- AI 분석 품질 검증 및 신뢰도 평가")
    print()
    
    # 입력 파일 경로
    while True:
        input_file = input("분석할 엑셀 파일 경로를 입력하세요: ").strip()
        if not input_file:
            print("파일 경로를 입력해주세요.")
            continue
        if not os.path.exists(input_file):
            print(f"파일을 찾을 수 없습니다: {input_file}")
            continue
        if not input_file.lower().endswith(('.xlsx', '.xls')):
            print("엑셀 파일(.xlsx, .xls)만 지원됩니다.")
            continue
        break
    
    # 컬럼명 입력
    try:
        df = pd.read_excel(input_file)
        print(f"\n사용 가능한 컬럼: {list(df.columns)}")
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        sys.exit(1)
    
    while True:
        column_name = input("분석할 컬럼명을 입력하세요: ").strip()
        if not column_name:
            print("컬럼명을 입력해주세요.")
            continue
        if column_name not in df.columns:
            print(f"'{column_name}' 컬럼을 찾을 수 없습니다.")
            continue
        break
    
    # 출력 파일 경로 (선택사항)
    output_file = input("결과 파일 경로를 입력하세요 (엔터: 자동 생성): ").strip()
    if not output_file:
        output_file = str(Path(input_file).stem) + "_processed.xlsx"
    
    # 최대 처리 행 수 (선택사항)
    max_rows = None
    max_rows_input = input("최대 처리 행 수 입력 (엔터: 전체 처리): ").strip()
    if max_rows_input.isdigit():
        max_rows = int(max_rows_input)
    
    return input_file, column_name, output_file, max_rows

def parse_arguments():
    """
    명령행 인자를 파싱합니다.
    """
    parser = argparse.ArgumentParser(
        description="고도화된 텍스트 분석 시스템 - AI를 활용한 감정 분석 및 텍스트 정제",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  1. 대화형 모드 (권장):
     python main.py
     
  2. 명령행 인자 사용:
     python main.py -i data.xlsx -c "피드백" -o result.xlsx
     
  3. 상세 설정:
     python main.py -i data.xlsx -c "피드백" -m 1000 -b 20 --no-retry
     
  4. 프로젝트 ID 변경:
     python main.py -i data.xlsx -c "피드백" -p your-project-id

기능:
  - AI 기반 감정 분석 (긍정/부정/중립)
  - 텍스트 정제 및 비식별 처리
  - 키워드 추출 및 빈도 분석
  - 품질 검증 및 자동 재검토
  - 배치 처리로 성능 최적화
        """
    )
    
    parser.add_argument("--input", "-i", type=str, help="입력 엑셀 파일 경로")
    parser.add_argument("--column", "-c", type=str, help="분석할 컬럼명")
    parser.add_argument("--output", "-o", type=str, help="결과 파일 경로 (기본값: 입력파일명_processed.xlsx)")
    parser.add_argument("--max-rows", "-m", type=int, help="최대 처리 행 수 (기본값: 전체)")
    parser.add_argument("--project-id", "-p", type=str, default="mindmap-462708", help="Google Cloud 프로젝트 ID (기본값: mindmap-462708)")
    parser.add_argument("--batch-size", "-b", type=int, default=10, help="배치 크기 (기본값: 10)")
    parser.add_argument("--no-batch", action="store_true", help="배치 처리 비활성화 (순차 처리)")
    parser.add_argument("--no-retry", action="store_true", help="품질 재검토 비활성화")
    
    return parser.parse_args()

def main():
    """
    메인 실행 함수 - 텍스트 분석을 수행합니다.
    """
    # 명령행 인자 파싱
    args = parse_arguments()
    
    try:
        # 명령행 인자가 제공된 경우
        if args.input and args.column:
            input_file = args.input
            column_name = args.column
            output_file = args.output or str(Path(input_file).stem) + "_processed.xlsx"
            max_rows = args.max_rows
            
            # 파일 존재 확인
            if not os.path.exists(input_file):
                print(f"오류: 파일을 찾을 수 없습니다 - {input_file}")
                sys.exit(1)
            
            # 컬럼 존재 확인
            try:
                df = pd.read_excel(input_file)
                if column_name not in df.columns:
                    print(f"오류: '{column_name}' 컬럼을 찾을 수 없습니다.")
                    print(f"사용 가능한 컬럼: {list(df.columns)}")
                    sys.exit(1)
            except Exception as e:
                print(f"파일 읽기 오류: {e}")
                sys.exit(1)
        else:
            # 대화형 입력
            input_file, column_name, output_file, max_rows = get_user_input()
        
        print(f"\n설정 확인:")
        print(f"- 입력 파일: {input_file}")
        print(f"- 분석 컬럼: {column_name}")
        print(f"- 출력 파일: {output_file}")
        print(f"- 최대 처리 행: {max_rows or '전체'}")
        print(f"- 프로젝트 ID: {args.project_id}")
        print()
        
        # 분석기 생성 및 실행
        analyzer = ReviewAnalyzer(project_id=args.project_id)
        
        # 정제된 텍스트 컬럼 확인
        if "_refined_text" in column_name:
            # 이미 정제된 텍스트가 있는 경우
            anonymized_column = column_name.replace("_refined_text", "_is_anonymized")
            print(f"정제된 텍스트 분석 모드")
            print(f"정제 텍스트 컬럼: {column_name}")
            print(f"비식별 처리 컬럼: {anonymized_column}")
            
            analyzer.process_xlsx_with_refined_text(
                input_file,
                column_name,
                anonymized_column,
                output_file,
                max_rows=max_rows,
                use_batch=not args.no_batch,
                batch_size=args.batch_size,
                enable_quality_retry=not args.no_retry
            )
        else:
            # 원본 텍스트 분석 (기존 방식)
            print(f"원본 텍스트 분석 모드")
            analyzer.process_xlsx_with_column(
                input_file, 
                column_name, 
                output_file, 
                max_rows=max_rows,
                use_batch=not args.no_batch,
                batch_size=args.batch_size,
                enable_quality_retry=not args.no_retry
            )
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        sys.exit(0)
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
        sys.exit(1)

# 프로그램이 직접 실행될 때만 main() 함수 호출
if __name__ == "__main__":
    main() 