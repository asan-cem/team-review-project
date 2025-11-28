# 데이터 처리를 위한 라이브러리들
import pandas as pd  # 엑셀, CSV 파일 처리
import json  # JSON 데이터 처리
import time  # 대기 시간 처리
from pathlib import Path  # 파일 경로 처리
from tqdm import tqdm  # 진행률 표시
from concurrent.futures import ThreadPoolExecutor, as_completed  # 병렬 처리
import re  # 정규표현식
import sys  # 명령행 인자 처리
import warnings  # 경고 메시지 제어
import pickle  # 체크포인트 직렬화
import logging  # 로깅
from multiprocessing import Process, Queue  # 백그라운드 프로세싱
from collections import Counter  # 키워드 카운팅
warnings.filterwarnings('ignore')

# Google Gemini API 라이브러리
import google.generativeai as genai  # Google Gemini API

# 감정 분류 상수 정의
EMOTION_CATEGORIES = {
    "긍정군": ["기쁨", "감사", "신뢰", "만족"],
    "부정군": ["분노", "슬픔", "두려움", "실망"], 
    "중립군": ["평온", "무관심"]
}

MEDICAL_CONTEXT_CATEGORIES = {
    "의료_서비스": ["응급상황", "투약오류", "수술협력", "안전사고", "의료사고"],
    "업무_효율": ["일정조율", "정보공유", "프로세스", "업무분담", "효율성"],
    "존중_소통": ["존중", "소통", "배려", "예의", "친절"],
    "전문성": ["지식", "기술", "경험", "역량", "전문성"]
}

# AI에게 보낼 분석 지시사항 템플릿 (고도화 버전)
PROMPT_TEMPLATE = """
[페르소나]
당신은 의료진 간 협업 피드백을 분석하는 전문 AI 분석가입니다. 8가지 세분화된 감정과 복합 감정 분석을 통해 정확하고 깊이 있는 감정 분석을 수행합니다.

[지시사항]
1. **텍스트 정제 및 의미 판단**:
   - 먼저 원본 텍스트가 의미있는 내용인지 판단합니다.
   - '없습니다', '없음', '특별히 없음', '해당 없음', '없다', '없어요' 등의 표현만 있는 경우 정제된_텍스트를 빈 문자열("")로 처리합니다.
   - 불필요한 기호나 구분자만 있는 경우 (예: "---", "...", "//", "ㅡㅡ", "무" 등) 정제된_텍스트를 빈 문자열("")로 처리합니다.
   - 의미 없는 단순 반복 문자나 숫자만 있는 경우 정제된_텍스트를 빈 문자열("")로 처리합니다.
   - 의미있는 내용이 있는 경우에만 핵심 의미를 보존하면서 오타와 문법을 교정하여 정제된_텍스트를 생성합니다.

2. **표현 순화**:
   - 속어나 공격적인 표현은 전문적이고 정중한 표현으로 순화합니다.

3. **매우 중요 - 비식별 처리 규칙**: 
   **3-1. 긍정적/중립적 피드백 처리 규칙:**
   - 긍정적이거나 중립적 피드백은 실명이 포함되어 있어도 절대 비식별 처리하지 않습니다.
   - 비식별_처리를 반드시 false로 설정합니다.
   
   **3-2. 부정적 피드백 처리 규칙:**
   - 부정적 피드백이면서 실명이나 매우 구체적인 개인 식별 정보가 있는 경우에만 비식별 처리합니다.
   - 일반적인 호칭("선생님", "직원분" 등)은 비식별 처리하지 않습니다.

4. **감정 분석**:
   - 감정_분류: 긍정, 부정, 중립 중 1개 (무의미한 텍스트는 빈 문자열 "")
   - 감정_강도_점수: 1-10 (무의미한 텍스트는 빈 문자열 "")

5. **의료 협업 맥락 분석**:
   - 의료_맥락: 의료_서비스, 업무_효율, 존중_소통, 전문성 중 해당하는 모든 항목 (무의미한 텍스트는 빈 배열 [])

6. **신뢰도 평가**:
   - 신뢰도_점수를 1-10 스케일로 평가합니다 (무의미한 텍스트는 빈 문자열 "").

7. **키워드 추출**:
   - 핵심_키워드를 추출하여 리스트로 제공합니다 (무의미한 텍스트는 빈 배열 [], 의미있는 텍스트는 주요 키워드 3-5개).

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
  "정제된_텍스트": "최종 정제 및 비식별 처리된 텍스트",
  "비식별_처리": false,
  "감정_분류": "긍정",
  "감정_강도_점수": 7,
  "핵심_키워드": ["감사", "전문적", "도움"],
  "의료_맥락": ["존중_소통", "전문성"],
  "신뢰도_점수": 8
}}


[예시]
- 원본 텍스트: "김철수 팀장 일처리 너무 답답하고 소통도 안됨. 개선이 시급함"
- JSON 출력:
{{"정제된_텍스트": "담당자의 일 처리가 다소 아쉽고, 소통 방식의 개선이 필요해 보입니다.", "비식별_처리": true, "감정_분류": "부정", "감정_강도_점수": 8, "핵심_키워드": ["일처리", "소통", "개선"], "의료_맥락": ["업무_효율", "존중_소통"], "신뢰도_점수": 9}}

- 원본 텍스트: "선생님들이 업무 처리가 너무 느려서 답답합니다"
- JSON 출력:
{{"정제된_텍스트": "선생님들의 업무 처리 속도가 다소 아쉽습니다.", "비식별_처리": false, "감정_분류": "부정", "감정_강도_점수": 6, "핵심_키워드": ["업무", "처리", "속도"], "의료_맥락": ["업무_효율"], "신뢰도_점수": 7}}

- 원본 텍스트: "박영희 선생님은 항상 동료들을 먼저 챙기고 배려하는 모습이 보기 좋습니다"
- JSON 출력:
{{"정제된_텍스트": "박영희 선생님은 항상 동료들을 먼저 챙기고 배려하는 모습이 보기 좋습니다.", "비식별_처리": false, "감정_분류": "긍정", "감정_강도_점수": 8, "핵심_키워드": ["배려", "동료", "챙김"], "의료_맥락": ["존중_소통"], "신뢰도_점수": 9}}

- 원본 텍스트: "수술 중 응급상황에서 빠른 대응이 인상적이었습니다"
- JSON 출력:
{{"정제된_텍스트": "수술 중 응급상황에서 빠른 대응이 인상적이었습니다.", "비식별_처리": false, "감정_분류": "긍정", "감정_강도_점수": 8, "핵심_키워드": ["응급상황", "빠른대응", "수술"], "의료_맥락": ["의료_서비스", "전문성"], "신뢰도_점수": 9}}

- 원본 텍스트: "없습니다"
- JSON 출력:
{{"정제된_텍스트": "", "비식별_처리": false, "감정_분류": "", "감정_강도_점수": "", "핵심_키워드": [], "의료_맥락": [], "신뢰도_점수": ""}}

- 원본 텍스트: "특별히 없음"
- JSON 출력:
{{"정제된_텍스트": "", "비식별_처리": false, "감정_분류": "", "감정_강도_점수": "", "핵심_키워드": [], "의료_맥락": [], "신뢰도_점수": ""}}

- 원본 텍스트: "---"
- JSON 출력:
{{"정제된_텍스트": "", "비식별_처리": false, "감정_분류": "", "감정_강도_점수": "", "핵심_키워드": [], "의료_맥락": [], "신뢰도_점수": ""}}

원본 텍스트: "{original_text}"
"""

class CheckpointManager:
    """
    체크포인트 저장/로드를 관리하는 클래스
    """
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
    
    def save_checkpoint(self, session_id: str, data: dict):
        """체크포인트 저장"""
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{session_id}.pkl"
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(data, f)
        return checkpoint_file
    
    def load_checkpoint(self, session_id: str) -> dict:
        """체크포인트 로드"""
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{session_id}.pkl"
        if checkpoint_file.exists():
            with open(checkpoint_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def cleanup_old_checkpoints(self, keep_days: int = 7):
        """오래된 체크포인트 정리"""
        cutoff_time = time.time() - (keep_days * 24 * 3600)
        for checkpoint_file in self.checkpoint_dir.glob("checkpoint_*.pkl"):
            if checkpoint_file.stat().st_mtime < cutoff_time:
                checkpoint_file.unlink()

class ProgressMonitor:
    """
    향상된 진행률 모니터링 클래스
    """
    
    def __init__(self, total_items: int, session_id: str = None):
        self.total_items = total_items
        self.processed_items = 0
        self.start_time = time.time()
        self.session_id = session_id or f"session_{int(time.time())}"
        self.error_count = 0
        self.retry_count = 0
        
        # 성능 메트릭
        self.processing_times = []
        self.last_checkpoint_time = time.time()
    
    def update(self, increment: int = 1, processing_time: float = None):
        """진행률 업데이트"""
        self.processed_items += increment
        if processing_time:
            self.processing_times.append(processing_time)
    
    def add_error(self):
        """에러 카운트 증가"""
        self.error_count += 1
    
    def add_retry(self):
        """재시도 카운트 증가"""
        self.retry_count += 1
    
    def get_statistics(self) -> dict:
        """현재 통계 반환"""
        elapsed_time = time.time() - self.start_time
        
        if self.processed_items > 0:
            avg_time_per_item = elapsed_time / self.processed_items
            remaining_items = self.total_items - self.processed_items
            eta = remaining_items * avg_time_per_item
            items_per_second = self.processed_items / elapsed_time
        else:
            avg_time_per_item = 0
            eta = 0
            items_per_second = 0
        
        return {
            'processed': self.processed_items,
            'total': self.total_items,
            'progress_percent': (self.processed_items / self.total_items) * 100,
            'elapsed_time': elapsed_time,
            'eta_seconds': eta,
            'items_per_second': items_per_second,
            'error_count': self.error_count,
            'retry_count': self.retry_count,
            'avg_processing_time': sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        }
    
    def should_checkpoint(self, interval: int = 100) -> bool:
        """체크포인트 저장 시점 확인"""
        return self.processed_items % interval == 0 and self.processed_items > 0

class BackgroundWorker:
    """
    백그라운드 작업 관리 클래스
    """
    
    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds
        self.is_running = False
        self.heartbeat_interval = 30  # 30초마다 하트비트
    
    def run_with_timeout(self, func, *args, **kwargs):
        """타임아웃과 함께 함수 실행"""
        result_queue = Queue()
        error_queue = Queue()
        
        def worker():
            try:
                result = func(*args, **kwargs)
                result_queue.put(result)
            except Exception as e:
                error_queue.put(e)
        
        process = Process(target=worker)
        process.start()
        
        try:
            process.join(timeout=self.timeout_seconds)
            
            if process.is_alive():
                process.terminate()
                process.join()
                raise TimeoutError(f"작업이 {self.timeout_seconds}초 내에 완료되지 않음")
            
            if not error_queue.empty():
                raise error_queue.get()
            
            if not result_queue.empty():
                return result_queue.get()
            else:
                raise RuntimeError("작업 결과를 가져올 수 없음")
        
        except TimeoutError:
            raise
        except Exception as e:
            raise e

class ReviewAnalyzer:
    """
    텍스트 리뷰를 AI로 분석하는 클래스
    Google의 Gemini API를 사용하여 텍스트의 감정, 개선된 표현, 분류 라벨 등을 분석합니다.
    """
    
    def __init__(self, api_key_file: str = "Gemini API.json", enable_background: bool = True):
        """
        분석기를 초기화합니다.

        Args:
            api_key_file: Gemini API 키 JSON 파일 경로 (기본값: "Gemini API.json")
            enable_background: 백그라운드 처리 활성화 여부
        """
        # Gemini API 키 로드
        with open(api_key_file, 'r') as f:
            api_config = json.load(f)
            api_key = api_config.get('apikey') or api_config.get('api_key')
            if not api_key:
                raise KeyError("JSON 파일에 'apikey' 또는 'api_key'가 없습니다.")

        # Google Gemini API 초기화
        genai.configure(api_key=api_key)

        # 사용할 AI 모델 설정 (Gemini 2.5 Flash 모델)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
        # 새로운 기능들 초기화
        self.checkpoint_manager = CheckpointManager()
        self.background_worker = BackgroundWorker() if enable_background else None
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('analysis.log'),
                logging.StreamHandler()
            ]
        )
    
    
    def analyze_review(self, original_text: str, use_background: bool = False) -> dict:
        """
        텍스트를 AI로 분석하여 감정, 개선된 텍스트 등을 반환합니다.
        
        Args:
            original_text: 분석할 원본 텍스트
            use_background: 백그라운드 처리 사용 여부
            
        Returns:
            dict: 분석 결과 (감정, 개선된 텍스트, 라벨 등)
        """
        start_time = time.time()
        
        # 빈 텍스트 처리
        if not original_text or original_text.strip() == "":
            return {
                "original_text": original_text,
                "정제된_텍스트": "",
                "비식별_처리": False,
                "감정_분류": "",
                "감정_강도_점수": "",
                "핵심_키워드": [],
                "의료_맥락": [],
                "신뢰도_점수": ""
            }
        
        try:
            # 간소화된 직접 처리 (백그라운드 워커 제거)
            result = self._analyze_text_internal(original_text)
            
            # 처리 시간 로깅
            processing_time = time.time() - start_time
            logging.info(f"텍스트 분석 완료: {processing_time:.2f}초")
            
            return result
            
        except Exception as e:
            logging.error(f"텍스트 분석 오류: {e} - {original_text[:50]}...")
            return self._get_fallback_result(original_text)
    
    def _analyze_text_internal(self, original_text: str) -> dict:
        """
        내부 텍스트 분석 로직 (백그라운드 프로세스에서 실행)
        """
        # AI 분석 프롬프트 생성
        prompt = PROMPT_TEMPLATE.format(original_text=original_text)
        
        # API 한계 대응을 위한 재시도 로직 (균형 조정)
        max_retries = 3  # 재시도 횟수 적정
        base_wait_time = 1.0  # 기본 대기 시간 적정
        
        for attempt in range(max_retries):
            try:
                # AI 모델에 분석 요청 (타임아웃 설정)
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                
                # 성공 시 결과 파싱 및 반환
                return self._parse_ai_response(response_text, original_text)
                
            except Exception as e:
                if "429" in str(e) or "Resource exhausted" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        # 지수 백오프 with 지터: (2^attempt) * base_wait_time + random jitter
                        wait_time = (2 ** attempt) * base_wait_time + (attempt * 0.5)
                        logging.warning(f"API 한계 도달, {wait_time:.1f}초 대기 후 재시도... ({attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        # 최대 재시도 후에도 실패하면 기본값 반환
                        logging.error(f"API 한계로 인한 최종 실패: {original_text[:50]}...")
                        return self._get_fallback_result(original_text)
                else:
                    # 다른 종류의 오류는 재시도
                    if attempt < max_retries - 1:
                        wait_time = base_wait_time * (attempt + 1)
                        logging.warning(f"일반 오류 재시도: {e} - {wait_time}초 대기")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise e
        
        return self._get_fallback_result(original_text)
    
    def _parse_ai_response(self, response_text: str, original_text: str) -> dict:
        """AI 응답 파싱"""
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
            logging.warning(f"AI 응답 파싱 실패: {original_text[:50]}...")
            return self._get_fallback_result(original_text)
    
    def _get_fallback_result(self, original_text: str) -> dict:
        """기본 결과 반환"""
        return {
            "original_text": original_text,
            "정제된_텍스트": original_text,
            "비식별_처리": False,
            "감정_분류": "중립",
            "감정_강도_점수": 5,
            "핵심_키워드": [],
            "의료_맥락": [],
            "신뢰도_점수": 1
        }
    
    def _analyze_batch_with_monitoring(self, texts: list, batch_size: int, progress_monitor: ProgressMonitor) -> list:
        """
        진행률 모니터링과 함께 배치 처리
        """
        results = []
        
        # 병렬 처리를 위한 ThreadPoolExecutor 사용 (적당한 병렬 처리)
        with ThreadPoolExecutor(max_workers=min(20, len(texts))) as executor:
            # 각 텍스트에 대해 비동기 작업 제출
            future_to_index = {}
            for idx, text in enumerate(texts):
                future = executor.submit(self.analyze_review, text, False)  # 직접 처리
                future_to_index[future] = (idx, text)
            
            # 배치 크기만큼 결과 리스트 초기화
            batch_results = [None] * len(texts)
            
            # 결과 수집 (완료 순서와 관계없이 원래 순서 유지)
            for future in as_completed(future_to_index):
                idx, original_text = future_to_index[future]
                start_time = time.time()
                try:
                    result = future.result(timeout=60)  # 1분 타임아웃으로 단축
                    batch_results[idx] = result
                    processing_time = time.time() - start_time
                    progress_monitor.update(1, processing_time)
                except Exception as e:
                    logging.error(f"배치 처리 오류: {e} - {original_text[:50]}...")
                    progress_monitor.add_error()
                    # 오류 발생 시 기본값 반환
                    batch_results[idx] = self._get_fallback_result(original_text)
        
        return batch_results

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
            with ThreadPoolExecutor(max_workers=min(10, len(batch))) as executor:
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
                            "정제된_텍스트": original_text,
                            "비식별_처리": False,
                            "감정_분류": "중립",
                            "감정_강도_점수": 5,
                            "핵심_키워드": [],
                            "의료_맥락": [],
                            "신뢰도_점수": 1
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
        
        # 병렬 처리를 위한 ThreadPoolExecutor 사용 (안정적 처리)
        with ThreadPoolExecutor(max_workers=min(3, len(texts_and_flags))) as executor:
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
                        "정제된_텍스트": refined_text,
                        "비식별_처리": is_anonymized,
                        "감정_분류": "중립",
                        "감정_강도_점수": 5,
                        "핵심_키워드": [],
                        "의료_맥락": [],
                        "신뢰도_점수": 1
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
        confidence_score = result.get('신뢰도_점수', 5)
        
        # 신뢰도 점수가 문자열인 경우 (빈 문자열 등) 기본값으로 처리
        if isinstance(confidence_score, str):
            if confidence_score == "":
                overall_confidence = 5  # 빈 문자열인 경우 기본값
            else:
                try:
                    overall_confidence = float(confidence_score)
                except (ValueError, TypeError):
                    overall_confidence = 5
        else:
            overall_confidence = confidence_score
        
        # 1. 기본 필드 완성도 검사
        required_fields = ['정제된_텍스트', '감정_분류', '감정_강도_점수', '핵심_키워드']
        missing_fields = [field for field in required_fields if field not in result or not result[field]]
        
        if missing_fields:
            # 필수 필드 누락 정보는 추가하지 않음 (공란 처리)
            overall_confidence -= 3
        
        # 2. 감정 강도와 감정 분류 일치성 검사
        sentiment = result.get('감정_분류', '')
        intensity_raw = result.get('감정_강도_점수', 5)
        
        # 감정 강도가 문자열인 경우 처리
        if isinstance(intensity_raw, str):
            if intensity_raw == "":
                intensity = 5  # 빈 문자열인 경우 기본값
            else:
                try:
                    intensity = float(intensity_raw)
                except (ValueError, TypeError):
                    intensity = 5
        else:
            intensity = intensity_raw
        
        if sentiment == '긍정' and intensity < 6:
            quality_issues.append("긍정 감정인데 강도가 낮음")
            overall_confidence -= 2
        elif sentiment == '부정' and intensity > 5:
            quality_issues.append("부정 감정인데 강도가 높음")
            overall_confidence -= 2
        
        # 3. 텍스트 길이 비교
        original_len = len(str(original_text).strip()) if original_text and pd.notna(original_text) else 0
        refined_len = len(str(result.get('정제된_텍스트', '')).strip())
        
        if original_len > 10 and refined_len < original_len * 0.3:
            quality_issues.append("정제된 텍스트가 너무 짧음")
            overall_confidence -= 2
        elif refined_len > original_len * 2:
            quality_issues.append("정제된 텍스트가 너무 김")
            overall_confidence -= 1
        
        # 4. 키워드 추출 품질 검사
        key_terms = result.get('핵심_키워드', [])
        if original_len > 20 and len(key_terms) == 0:
            quality_issues.append("키워드 추출 실패")
            overall_confidence -= 2
        
        # 5. 비식별 처리 일치성 검사
        is_anonymized = result.get('비식별_처리', False)
        refined_text = result.get('정제된_텍스트', '')
        
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
    
    def process_xlsx_with_column(self, input_file: str, column_name: str, output_file: str = None, 
                                max_rows: int = None, use_batch: bool = True, batch_size: int = 10,
                                enable_quality_retry: bool = True, checkpoint_interval: int = 100,
                                resume_from_checkpoint: bool = True):
        """
        엑셀 파일의 특정 컬럼을 분석하여 결과를 저장합니다.
        
        Args:
            input_file: 분석할 엑셀 파일 경로
            column_name: 분석할 컬럼명
            output_file: 결과를 저장할 파일 경로 (자동 생성 가능)
            max_rows: 테스트용으로 처리할 최대 행 수
            use_batch: 배치 처리 사용 여부
            batch_size: 배치 크기
            enable_quality_retry: 품질 재검토 활성화 여부
            checkpoint_interval: 체크포인트 저장 간격
            resume_from_checkpoint: 체크포인트에서 재개 여부
        """
        # 세션 ID 생성 (체크포인트 식별용)
        session_id = f"{Path(input_file).stem}_{column_name}_{int(time.time())}"
        
        # 출력 파일명 자동 생성
        if output_file is None:
            output_file = "rawdata/" + str(Path(input_file).stem) + "_processed.xlsx"
        
        # 체크포인트에서 재개 확인
        checkpoint_data = None
        if resume_from_checkpoint:
            checkpoint_data = self.checkpoint_manager.load_checkpoint(session_id)
            if checkpoint_data:
                logging.info(f"체크포인트에서 재개: {checkpoint_data['processed_count']}/{checkpoint_data['total_count']} 완료")
        
        # 엑셀 파일을 읽어서 데이터프레임으로 변환
        df = pd.read_excel(input_file)
        
        # 테스트용으로 일부 데이터만 처리하는 경우
        if max_rows:
            df = df.head(max_rows)
            print(f"테스트 모드: 상위 {max_rows}개 행만 처리합니다.")
        
        # 지정된 컬럼에서 텍스트 데이터 추출 및 빈 값 체크
        texts = df[column_name].tolist()
        total_texts = len(texts)
        
        # 유효한 텍스트만 필터링 (사전 필터링 강화)
        valid_texts = []
        valid_indices = []
        
        # 무의미한 텍스트 패턴 정의
        meaningless_patterns = [
            r'^없[습다음어요]*$', r'^특별히\s*없[음다습니요]*$', r'^해당\s*없[음다습니요]*$',
            r'^[-\s]*$', r'^[.\s]*$', r'^[/\s]*$', r'^[ㅡ\s]*$', r'^무\s*$',
            r'^[\d\s]*$', r'^[a-zA-Z\s]*$', r'^[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>?/\s]*$'
        ]
        
        for i, text in enumerate(texts):
            if pd.notna(text) and str(text).strip() != '' and str(text).strip() != 'nan':
                text_clean = str(text).strip()
                
                # 무의미한 패턴 검사
                is_meaningless = any(re.match(pattern, text_clean, re.IGNORECASE) for pattern in meaningless_patterns)
                
                # 길이가 너무 짧은 경우도 필터링 (3글자 미만)
                if len(text_clean) < 3:
                    is_meaningless = True
                
                if not is_meaningless:
                    valid_texts.append(text_clean)
                    valid_indices.append(i)
        
        print(f"총 {total_texts}개 중 {len(valid_texts)}개의 유효한 텍스트를 분석합니다...")
        
        # 진행률 모니터 초기화
        progress_monitor = ProgressMonitor(len(valid_texts), session_id)
        
        # 결과 리스트 초기화
        if checkpoint_data:
            # 체크포인트에서 재개
            results = checkpoint_data['results']
            progress_monitor.processed_items = checkpoint_data['processed_count']
            print(f"체크포인트에서 재개: {checkpoint_data['processed_count']}개 아이템 완료")
        else:
            # 새로 시작
            results = [None] * total_texts
        
        if len(valid_texts) > 0 and not checkpoint_data:
            # 배치 처리 강제 활성화 (속도 최적화)
            if use_batch and len(valid_texts) > 0:
                print(f"배치 처리 모드 (배치 크기: {batch_size})")
                valid_results = []
                
                # 진행률 표시를 위한 tqdm 사용
                with tqdm(total=len(valid_texts), desc="분석 진행률", unit="건") as pbar:
                    for i in range(0, len(valid_texts), batch_size):
                        batch_texts = valid_texts[i:i+batch_size]
                        
                        # 백그라운드 처리로 배치 분석
                        batch_results = self._analyze_batch_with_monitoring(
                            batch_texts, len(batch_texts), progress_monitor
                        )
                        valid_results.extend(batch_results)
                        
                        # 디버깅 로그 추가
                        print(f"🔍 배치 완료: {len(valid_results)}개 처리됨")
                        
                        # 유효한 결과를 원래 위치에 배치 (체크포인트용)
                        temp_results = results.copy()
                        for j, result in enumerate(valid_results):
                            if j < len(valid_indices):
                                temp_results[valid_indices[j]] = result
                        
                        # 체크포인트 저장 확인 (매 배치마다 강제 저장)
                        print(f"🔍 체크포인트 확인: {len(valid_results)} % 10 = {len(valid_results) % 10}")
                        if len(valid_results) > 0 and len(valid_results) % 10 == 0:
                            checkpoint_data = {
                                'session_id': session_id,
                                'input_file': input_file,
                                'column_name': column_name,
                                'total_count': len(valid_texts),
                                'processed_count': len(valid_results),
                                'results': temp_results,
                                'valid_indices': valid_indices,
                                'timestamp': time.time()
                            }
                            self.checkpoint_manager.save_checkpoint(session_id, checkpoint_data)
                            print(f"💾 체크포인트 저장됨: {len(valid_results)}/{len(valid_texts)}")
                            logging.info(f"체크포인트 저장: {len(valid_results)}/{len(valid_texts)}")
                            # 체크포인트 저장됨
                        
                        pbar.update(len(batch_texts))
                        
                        # API 대기 시간 제거 (재시도 로직에서 자동 처리)
            else:
                print("순차 처리 모드")
                valid_results = []
                
                # 각 텍스트를 하나씩 분석
                with tqdm(total=len(valid_texts), desc="분석 진행률", unit="건") as pbar:
                    for idx, text in enumerate(valid_texts):
                        start_time = time.time()
                        result = self.analyze_review(text, use_background=True)
                        processing_time = time.time() - start_time
                        
                        valid_results.append(result)
                        progress_monitor.update(1, processing_time)
                        
                        # 체크포인트 저장 확인
                        if progress_monitor.should_checkpoint(checkpoint_interval):
                            # 지금까지의 결과를 원래 위치에 배치
                            temp_results = results.copy()
                            for i, res in enumerate(valid_results):
                                if i < len(valid_indices):
                                    temp_results[valid_indices[i]] = res
                            
                            checkpoint_data = {
                                'session_id': session_id,
                                'input_file': input_file,
                                'column_name': column_name,
                                'total_count': len(valid_texts),
                                'processed_count': len(valid_results),
                                'results': temp_results,
                                'valid_indices': valid_indices,
                                'timestamp': time.time()
                            }
                            self.checkpoint_manager.save_checkpoint(session_id, checkpoint_data)
                            logging.info(f"체크포인트 저장: {len(valid_results)}/{len(valid_texts)}")
                        
                        pbar.update(1)
            
            # 유효한 결과를 원래 위치에 배치
            for i, result in enumerate(valid_results):
                if i < len(valid_indices):
                    original_index = valid_indices[i]
                    results[original_index] = result
        
        # 빈 값에 대한 기본 결과 생성
        for i, result in enumerate(results):
            if result is None:
                results[i] = {
                    "정제된_텍스트": "",
                    "비식별_처리": False,
                    "감정_분류": "",
                    "감정_강도_점수": "",
                    "핵심_키워드": [],
                    "의료_맥락": [],
                    "신뢰도_점수": ""
                }
        
        # 품질 검증을 위한 기본 리스트 초기화
        quality_results = [None] * total_texts
        
        # original_text 필드 제거 (중복 방지) 및 한국어 컬럼명 변경
        for result in results:
            if "original_text" in result:
                del result["original_text"]
            
            # 영어 컬럼명을 한국어로 변경 (필요한 컬럼만)
            if "refined_text" in result:
                result["정제된_텍스트"] = result.pop("refined_text")
            if "is_anonymized" in result:
                result["비식별_처리"] = result.pop("is_anonymized")
            if "sentiment" in result:
                result["감정_분류"] = result.pop("sentiment")
            if "sentiment_intensity" in result:
                result["감정_강도_점수"] = result.pop("sentiment_intensity")
            if "key_terms" in result:
                result["핵심_키워드"] = result.pop("key_terms")
            if "medical_context" in result:
                result["의료_맥락"] = result.pop("medical_context")
            if "confidence_score" in result:
                result["신뢰도_점수"] = result.pop("confidence_score")
        
        # 품질 검증
        if enable_quality_retry and len(valid_texts) > 0:
            print("\n분석 품질 검증 중...")
            
            with tqdm(total=len(valid_texts), desc="품질 검증", unit="건") as pbar:
                for i, valid_index in enumerate(valid_indices):
                    result = results[valid_index]
                    original_text = texts[valid_index]
                    quality = self.validate_analysis_quality(result, original_text)
                    quality_results[valid_index] = quality
                    pbar.update(1)
            
            # 품질 재검토 (유효한 텍스트만)
            if len(valid_texts) > 0:
                # 유효한 텍스트와 결과만 추출
                valid_results_for_retry = [results[i] for i in valid_indices]
                valid_quality_for_retry = [quality_results[i] for i in valid_indices]
                
                improved_results, improved_quality = self.retry_low_quality_analysis(valid_texts, valid_results_for_retry, valid_quality_for_retry)
                
                # 개선된 결과를 원래 위치에 반영
                for i, improved_result in enumerate(improved_results):
                    original_index = valid_indices[i]
                    # original_text 제거
                    if "original_text" in improved_result:
                        del improved_result["original_text"]
                    results[original_index] = improved_result
                    quality_results[original_index] = improved_quality[i]
            
            # 품질 통계 출력 (유효한 분석 결과만)
            valid_quality_results = [q for q in quality_results if q is not None]
            if len(valid_quality_results) > 0:
                reliable_count = sum(1 for q in valid_quality_results if q['is_reliable'])
                avg_quality = sum(q['quality_score'] for q in valid_quality_results) / len(valid_quality_results)
                
                print(f"\n품질 검증 결과:")
                print(f"- 신뢰할 수 있는 분석: {reliable_count}/{len(valid_quality_results)} ({reliable_count/len(valid_quality_results)*100:.1f}%)")
                print(f"- 평균 품질 점수: {avg_quality:.2f}/10")
        
        # 분석 결과를 데이터프레임으로 변환
        result_df = pd.DataFrame(results)
        
        # 컬럼 분류 및 최적화
        final_df = self._optimize_columns_for_dashboard(df, result_df)
        
        # 엑셀 파일로 저장 (여러 시트로 구분)
        self._save_to_excel_with_sheets(final_df, output_file)
        
        print(f"\n분석 완료! 결과가 '{output_file}'에 저장되었습니다.")
        
        # 최종 통계 및 체크포인트 정리
        final_stats = progress_monitor.get_statistics()
        logging.info(f"분석 완료 - 처리 시간: {final_stats['elapsed_time']:.2f}초, 평균 속도: {final_stats['items_per_second']:.2f}건/초")
        
        # 체크포인트 파일 삭제 (완료 후)
        try:
            checkpoint_file = self.checkpoint_manager.checkpoint_dir / f"checkpoint_{session_id}.pkl"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                logging.info("체크포인트 파일 삭제 완료")
        except Exception as e:
            logging.warning(f"체크포인트 파일 삭제 실패: {e}")
        
        print(f"최종 통계: {final_stats['processed']}개 처리, 에러 {final_stats['error_count']}개, 재시도 {final_stats['retry_count']}개")
        
        # 감정 분석 통계 출력
        self._print_analysis_statistics(result_df)
    
    def _print_analysis_statistics(self, result_df):
        """분석 결과 통계를 출력합니다."""
        print("\n=== 분석 결과 통계 ===")
        
        # 감정 분석 통계 (한국어 컬럼명 사용)
        if '감정_분류' in result_df.columns:
            # 빈 값을 제외하고 통계 계산
            valid_sentiments = result_df['감정_분류'][result_df['감정_분류'] != '']
            if len(valid_sentiments) > 0:
                sentiment_counts = valid_sentiments.value_counts()
                print(f"\n감정 분류 (유효한 {len(valid_sentiments)}개 분석):")
                for sentiment, count in sentiment_counts.items():
                    percentage = (count / len(valid_sentiments)) * 100
                    print(f"  {sentiment}: {count}개 ({percentage:.1f}%)")
        
        # 강도 통계
        if '감정_강도_점수' in result_df.columns:
            # 빈 값과 문자열을 제외하고 숫자만 계산
            valid_intensities = pd.to_numeric(result_df['감정_강도_점수'], errors='coerce').dropna()
            if len(valid_intensities) > 0:
                avg_intensity = valid_intensities.mean()
                print(f"\n평균 감정 강도: {avg_intensity:.2f}/10")
        
        
        # 키워드 통계
        if '핵심_키워드' in result_df.columns:
            all_keywords = []
            for keywords in result_df['핵심_키워드']:
                if isinstance(keywords, list) and len(keywords) > 0:
                    all_keywords.extend(keywords)
            
            if all_keywords:
                keyword_counts = Counter(all_keywords)
                print("\n주요 키워드:")
                for keyword, count in keyword_counts.most_common(10):
                    print(f"  {keyword}: {count}회")
    
    def _optimize_columns_for_dashboard(self, original_df, result_df):
        """원본 데이터 완전성을 유지하면서 분석 결과를 통합합니다."""
        
        # 지정된 텍스트 분석 컬럼 (7개)
        analysis_columns = [
            '정제된_텍스트',
            '비식별_처리',
            '감정_분류',
            '감정_강도_점수',
            '핵심_키워드',
            '의료_맥락',
            '신뢰도_점수'
        ]
        
        # 원본 데이터 전체 유지 + 분석 결과 추가
        analysis_data = pd.concat([
            original_df,
            result_df[[col for col in analysis_columns if col in result_df.columns]]
        ], axis=1)
        
        return {
            'analysis': analysis_data
        }
    
    def _save_to_excel_with_sheets(self, data_dict, output_file):
        """분석 시트 하나로 엑셀 파일에 저장합니다."""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 분석 시트 (원본 데이터 + 분석 결과)
            data_dict['analysis'].to_excel(
                writer, 
                sheet_name='분석 시트', 
                index=False
            )
        
        print(f"\n=== 데이터 시트 구성 ===")
        print(f"분석 시트: {len(data_dict['analysis'].columns)}개 컬럼")
        print(f"- 원본 데이터: {len(data_dict['analysis'].columns) - 7}개 컬럼")
        print(f"- 분석 결과: 7개 컬럼")



# 글로벌 변수 선언 (KeyboardInterrupt에서 사용)
current_session_info = None

def main():
    """
    메인 실행 함수 - 텍스트 분석을 수행합니다.
    """
    try:
        # rawdata 폴더에서 최신 data_processor 결과 파일 찾기
        rawdata_path = Path("rawdata")
        pattern = "1. data_processor_결과_*.xlsx"

        # 패턴에 맞는 모든 파일 찾기
        matching_files = list(rawdata_path.glob(pattern))

        if not matching_files:
            print(f"❌ '{pattern}' 패턴에 맞는 파일을 찾을 수 없습니다.")
            print(f"rawdata 폴더를 확인하세요: {rawdata_path.absolute()}")
            sys.exit(1)

        # 가장 최근에 수정된 파일 선택 (파일명의 타임스탬프 기준)
        input_file = max(matching_files, key=lambda x: x.stat().st_mtime)

        print(f"📂 최신 파일 자동 선택: {input_file.name}")

        # 출력 파일명 생성 (타임스탬프 추출)
        input_filename = input_file.stem
        timestamp = input_filename.split('_')[-2] + '_' + input_filename.split('_')[-1]
        output_file = f"rawdata/2. text_processor_결과_{timestamp}.xlsx"
        
        column_name = "협업 후기"
        max_rows = None  # 전체 데이터 처리 (숫자로 설정하면 해당 행 수만 처리)
        api_key_file = "Gemini API.json"

        print(f"\n설정 확인:")
        print(f"- 입력 파일: {input_file.name}")
        print(f"- 분석 컬럼: {column_name}")
        print(f"- 출력 파일: {output_file}")
        print(f"- 최대 처리 행: {max_rows or '전체'}")
        print(f"- API 키 파일: {api_key_file}")
        print()

        # 분석기 생성 및 실행 (백그라운드 워커 제거로 효율성 향상)
        analyzer = ReviewAnalyzer(api_key_file=api_key_file, enable_background=False)

        # 글로벌 변수로 세션 정보 저장 (KeyboardInterrupt에서 사용)
        global current_session_info
        current_session_info = {
            'input_file': str(input_file),
            'column_name': column_name,
            'output_file': output_file
        }
        
        # 원본 텍스트 분석
        print(f"원본 텍스트 분석 모드")
        analyzer.process_xlsx_with_column(
            str(input_file),
            column_name,
            output_file,
            max_rows=max_rows,
            use_batch=True,
            batch_size=10,  # 테스트용: 작은 배치 크기
            enable_quality_retry=False,  # 속도 최적화를 위해 비활성화
            checkpoint_interval=5,  # 테스트용: 5개마다 체크포인트
            resume_from_checkpoint=True  # 체크포인트에서 재개 활성화
        )
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        print("중단된 상태까지 결과를 저장하는 중...")
        
        try:
            # 체크포인트에서 부분 결과 로드 (가장 최근 체크포인트 파일 찾기)
            checkpoint_manager = CheckpointManager()
            
            # 현재 입력 파일과 컬럼명에 해당하는 체크포인트 파일들 찾기
            file_stem = Path(current_session_info['input_file']).stem
            checkpoint_pattern = f"checkpoint_{file_stem}_{current_session_info['column_name']}_*.pkl"
            
            # 체크포인트 파일 검색
            checkpoint_files = list(checkpoint_manager.checkpoint_dir.glob(checkpoint_pattern))
            
            if not checkpoint_files:
                print(f"❌ 체크포인트 파일을 찾을 수 없습니다. 패턴: {checkpoint_pattern}")
                print(f"체크포인트 폴더: {checkpoint_manager.checkpoint_dir}")
                print("사용 가능한 체크포인트 파일:")
                for f in checkpoint_manager.checkpoint_dir.glob("*.pkl"):
                    print(f"  - {f.name}")
                checkpoint_data = None
            else:
                # 가장 최근 체크포인트 파일 선택
                latest_checkpoint = max(checkpoint_files, key=lambda x: x.stat().st_mtime)
                print(f"가장 최근 체크포인트 파일: {latest_checkpoint.name}")
                
                # 세션 ID 추출
                session_id = latest_checkpoint.stem.replace('checkpoint_', '')
                checkpoint_data = checkpoint_manager.load_checkpoint(session_id)
            
            if checkpoint_data and 'results' in checkpoint_data:
                # 원본 데이터 로드
                df = pd.read_excel(current_session_info['input_file'])
                
                # 부분 결과를 데이터프레임으로 변환
                partial_results = checkpoint_data['results']
                result_df = pd.DataFrame(partial_results)
                
                # 분석 결과 컬럼 정리
                analysis_columns = [
                    '정제된_텍스트', '비식별_처리', '감정_분류', '감정_강도_점수',
                    '핵심_키워드', '의료_맥락', '신뢰도_점수'
                ]
                
                # 빈 결과 기본값으로 채우기
                for i, result in enumerate(partial_results):
                    if result is None:
                        partial_results[i] = {
                            "정제된_텍스트": "",
                            "비식별_처리": False,
                            "감정_분류": "",
                            "감정_강도_점수": "",
                            "핵심_키워드": [],
                            "의료_맥락": [],
                            "신뢰도_점수": ""
                        }
                
                # original_text 필드 제거
                for result in partial_results:
                    if "original_text" in result:
                        del result["original_text"]
                
                # 결과 데이터프레임 생성
                result_df = pd.DataFrame(partial_results)
                
                # 원본 데이터와 결합
                final_df = pd.concat([
                    df,
                    result_df[[col for col in analysis_columns if col in result_df.columns]]
                ], axis=1)
                
                # 부분 결과 파일명 생성
                partial_output_file = current_session_info['output_file'].replace('.xlsx', '_partial.xlsx')
                
                # 엑셀 파일로 저장
                with pd.ExcelWriter(partial_output_file, engine='openpyxl') as writer:
                    final_df.to_excel(writer, sheet_name='분석 시트', index=False)
                
                processed_count = checkpoint_data.get('processed_count', 0)
                total_count = checkpoint_data.get('total_count', len(df))
                
                print(f"✅ 부분 결과 저장 완료: {partial_output_file}")
                print(f"📊 처리 현황: {processed_count}/{total_count} ({processed_count/total_count*100:.1f}%)")
                
            else:
                print("❌ 저장할 체크포인트 데이터가 없습니다.")
                
        except Exception as save_error:
            print(f"❌ 부분 결과 저장 중 오류 발생: {save_error}")
        
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"오류 발생: {e}")
        print(f"상세 오류: {traceback.format_exc()}")
        print("\n해결 방법:")
        print("1. Gemini API 키 파일 존재 여부 확인 (Gemini API.json)")
        print("2. API 키 유효성 확인")
        print("3. 엑셀 파일 존재 여부 확인")
        print("4. 필요한 패키지 설치 확인 (pandas, openpyxl, tqdm, google-generativeai)")
        sys.exit(1)

# 프로그램이 직접 실행될 때만 main() 함수 호출
if __name__ == "__main__":
    main() 