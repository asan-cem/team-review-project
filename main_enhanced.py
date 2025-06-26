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

# 고도화된 AI 감정 분석 지시사항 템플릿
ENHANCED_PROMPT_TEMPLATE = """
[페르소나]
당신은 서울아산병원 내부 직원 협업 피드백을 분석하는 고도화된 AI 감정 분석 전문가입니다. 의료진간 협업 맥락을 깊이 이해하고, 8가지 세분화된 감정과 복합 감정, 그리고 감정의 원인까지 분석하는 것이 당신의 임무입니다.

[고도화된 감정 분석 지시사항]

1. **텍스트 정제 및 비식별 처리**: 기존 규칙과 동일하게 적용

2. **8가지 세분화 감정 분석**:
   - **긍정군**: "기쁨", "감사", "신뢰", "만족"
   - **부정군**: "분노", "슬픔", "두려움", "실망"
   - **중립군**: "평온", "무관심"

3. **의료 협업 맥락 분석**:
   - **환자_안전**: 환자 치료, 안전, 응급상황 관련
   - **업무_효율**: 일정, 프로세스, 업무 흐름 관련
   - **인간_관계**: 존중, 소통, 배려, 팀워크 관련
   - **전문성**: 의료 지식, 기술, 경험, 역량 관련

4. **복합 감정 분석**:
   - primary_emotion: 주요 감정 (가장 강한 감정)
   - secondary_emotion: 보조 감정 (복합 감정인 경우)
   - emotional_complexity: "단순" 또는 "복합"
   - emotion_mix: 감정 비율 (복합인 경우만)

5. **감정 원인 분석** (부정 감정인 경우):
   - **소통_문제**: 의사소통 부족, 정보 전달 오류
   - **시간_압박**: 일정 지연, 업무 과부하
   - **기술_부족**: 전문성 부족, 경험 부족
   - **태도_문제**: 불친절, 비협조적 태도
   - **시스템_문제**: 프로세스 비효율, 도구 부족

6. **개선 방안 자동 제안** (부정 감정인 경우):
   - 감정 원인에 따른 구체적 개선 방안 제시

[의료진 협업 특화 감정 키워드]
- **기쁨**: "좋아요", "훌륭해요", "멋져요", "기뻐요"
- **감사**: "감사", "고마워", "도움", "수고"
- **신뢰**: "믿어", "의지", "전문적", "안심", "신뢰"
- **만족**: "만족", "충분", "괜찮아", "좋았어"
- **분노**: "화나", "짜증", "답답", "불만", "열받아"
- **슬픔**: "속상", "슬퍼", "안타까워", "우울"
- **두려움**: "걱정", "불안", "무서워", "염려"
- **실망**: "아쉬워", "실망", "기대이하", "부족"

[출력 형식]
반드시 아래 JSON 구조로만 응답하세요:

{
  "refined_text": "정제된 텍스트",
  "is_anonymized": false,
  "primary_emotion": "감사",
  "secondary_emotion": "신뢰",
  "emotional_complexity": "복합",
  "emotion_mix": {"감사": 0.7, "신뢰": 0.3},
  "sentiment_intensity": 8,
  "confidence_score": 9,
  "medical_context": "인간_관계",
  "root_cause": "없음",
  "improvement_suggestion": "없음",
  "key_terms": ["키워드1", "키워드2"],
  "labels": ["라벨1", "라벨2"]
}

[분석 예시]

**예시 1: 복합 긍정 감정**
원본: "김선생님 덕분에 환자 케어도 잘 되고 정말 감사해요. 믿고 일할 수 있어서 든든합니다."
출력:
{
  "refined_text": "김선생님 덕분에 환자 케어도 잘 되고 정말 감사해요. 믿고 일할 수 있어서 든든합니다.",
  "is_anonymized": false,
  "primary_emotion": "감사",
  "secondary_emotion": "신뢰",
  "emotional_complexity": "복합",
  "emotion_mix": {"감사": 0.6, "신뢰": 0.4},
  "sentiment_intensity": 8,
  "confidence_score": 9,
  "medical_context": "인간_관계",
  "root_cause": "없음",
  "improvement_suggestion": "없음",
  "key_terms": ["환자케어", "감사", "믿고일할수있어"],
  "labels": ["업무 태도", "상호 존중"]
}

**예시 2: 복합 부정 감정**
원본: "이정은 간호사가 환자 처치할 때 너무 서둘러서 실수할까 걱정돼요. 좀 더 신중했으면 좋겠어요."
출력:
{
  "refined_text": "담당 간호사가 환자 처치할 때 다소 서둘러서 실수할까 우려됩니다. 좀 더 신중한 접근이 필요해 보입니다.",
  "is_anonymized": true,
  "primary_emotion": "두려움",
  "secondary_emotion": "실망",
  "emotional_complexity": "복합",
  "emotion_mix": {"두려움": 0.7, "실망": 0.3},
  "sentiment_intensity": 6,
  "confidence_score": 8,
  "medical_context": "환자_안전",
  "root_cause": "기술_부족",
  "improvement_suggestion": "환자 처치 시 충분한 시간 확보 및 신중한 접근 교육 필요",
  "key_terms": ["환자처치", "서둘러", "실수우려"],
  "labels": ["전문성 부족"]
}

**예시 3: 단순 감정**
원본: "업무 처리가 늦어서 답답해요"
출력:
{
  "refined_text": "업무 처리 속도가 다소 아쉽습니다.",
  "is_anonymized": false,
  "primary_emotion": "분노",
  "secondary_emotion": "없음",
  "emotional_complexity": "단순",
  "emotion_mix": {"분노": 1.0},
  "sentiment_intensity": 6,
  "confidence_score": 8,
  "medical_context": "업무_효율",
  "root_cause": "시간_압박",
  "improvement_suggestion": "업무 프로세스 점검 및 효율성 개선 방안 모색",
  "key_terms": ["업무처리", "늦어서", "답답"],
  "labels": ["전문성 부족"]
}

이제 주어진 협업 후기 텍스트를 위 형식에 따라 고도화된 감정 분석을 수행하세요.
"""

class EnhancedReviewAnalyzer:
    def __init__(self, project_id="mindmap-462708"):
        """고도화된 리뷰 분석기 초기화"""
        self.project_id = project_id
        self.location = "us-central1"
        
        # Vertex AI 초기화
        vertexai.init(project=project_id, location=self.location)
        self.model = GenerativeModel("gemini-2.0-flash")
        
        # 통계 변수들
        self.stats = {
            'total_processed': 0,
            'high_quality': 0,
            'needs_review': 0,
            'emotion_distribution': Counter(),
            'context_distribution': Counter(),
            'complexity_distribution': Counter()
        }
    
    def _clean_json_response(self, response_text):
        """JSON 응답에서 마크다운 코드 블록 제거 및 정리"""
        # 마크다운 코드 블록 제거
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        # 앞뒤 공백 제거
        response_text = response_text.strip()
        
        return response_text
    
    def analyze_single_text_enhanced(self, text):
        """단일 텍스트에 대한 고도화된 AI 분석 수행"""
        if pd.isna(text) or str(text).strip() == "":
            return self._create_empty_result_enhanced()
        
        try:
            # AI 모델에 고도화된 프롬프트로 분석 요청
            full_prompt = f"{ENHANCED_PROMPT_TEMPLATE}\n\n분석할 텍스트: \"{text}\""
            response = self.model.generate_content(full_prompt)
            
            # JSON 응답 정리 및 파싱
            response_text = self._clean_json_response(response.text)
            
            # JSON 파싱 시도
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 재시도
                print(f"JSON 파싱 실패, 재시도...")
                time.sleep(2)
                response = self.model.generate_content(full_prompt)
                response_text = self._clean_json_response(response.text)
                result = json.loads(response_text)
            
            # 고도화된 결과 검증 및 품질 평가
            quality_score, quality_issues = self._evaluate_quality_enhanced(result, text)
            needs_review = quality_score < 6 or len(quality_issues) > 2
            
            # 통계 업데이트
            self._update_stats_enhanced(result, quality_score, needs_review)
            
            # 최종 결과 구성
            final_result = {
                'refined_text': result.get('refined_text', ''),
                'is_anonymized': result.get('is_anonymized', False),
                'primary_emotion': result.get('primary_emotion', '알 수 없음'),
                'secondary_emotion': result.get('secondary_emotion', '없음'),
                'emotional_complexity': result.get('emotional_complexity', '단순'),
                'emotion_mix': result.get('emotion_mix', {}),
                'sentiment_intensity': result.get('sentiment_intensity', 5),
                'confidence_score': result.get('confidence_score', 5),
                'medical_context': result.get('medical_context', '기타'),
                'root_cause': result.get('root_cause', '없음'),
                'improvement_suggestion': result.get('improvement_suggestion', '없음'),
                'key_terms': result.get('key_terms', []),
                'labels': result.get('labels', []),
                'quality_score': quality_score,
                'needs_review': needs_review,
                'quality_issues': ', '.join(quality_issues) if quality_issues else ''
            }
            
            return final_result
            
        except Exception as e:
            print(f"분석 오류 발생: {e}")
            return self._create_error_result_enhanced(str(e))
    
    def _create_empty_result_enhanced(self):
        """빈 텍스트에 대한 고도화된 기본 결과 생성"""
        return {
            'refined_text': '',
            'is_anonymized': False,
            'primary_emotion': '알 수 없음',
            'secondary_emotion': '없음',
            'emotional_complexity': '단순',
            'emotion_mix': {},
            'sentiment_intensity': 1,
            'confidence_score': 1,
            'medical_context': '기타',
            'root_cause': '없음',
            'improvement_suggestion': '없음',
            'key_terms': [],
            'labels': [],
            'quality_score': 1,
            'needs_review': True,
            'quality_issues': '빈 텍스트'
        }
    
    def _create_error_result_enhanced(self, error_msg):
        """오류 발생 시 고도화된 기본 결과 생성"""
        return {
            'refined_text': '',
            'is_anonymized': False,
            'primary_emotion': '알 수 없음',
            'secondary_emotion': '없음',
            'emotional_complexity': '단순',
            'emotion_mix': {},
            'sentiment_intensity': 1,
            'confidence_score': 1,
            'medical_context': '기타',
            'root_cause': '분석 오류',
            'improvement_suggestion': '재분석 필요',
            'key_terms': [],
            'labels': [],
            'quality_score': 1,
            'needs_review': True,
            'quality_issues': f'분석 오류: {error_msg}'
        }
    
    def _evaluate_quality_enhanced(self, result, original_text):
        """고도화된 분석 결과의 품질 평가"""
        quality_score = result.get('confidence_score', 5)
        quality_issues = []
        
        # 1. 필수 필드 검증
        required_fields = ['refined_text', 'primary_emotion', 'sentiment_intensity', 'medical_context']
        for field in required_fields:
            if field not in result or result[field] == '':
                quality_issues.append(f'{field} 누락')
                quality_score -= 2
        
        # 2. 감정 일관성 검증
        primary_emotion = result.get('primary_emotion', '')
        intensity = result.get('sentiment_intensity', 5)
        
        # 긍정 감정인데 강도가 낮은 경우
        if primary_emotion in ['기쁨', '감사', '신뢰', '만족'] and intensity < 4:
            quality_issues.append('긍정 감정-강도 불일치')
            quality_score -= 1
        
        # 부정 감정인데 강도가 너무 낮은 경우
        if primary_emotion in ['분노', '슬픔', '두려움', '실망'] and intensity < 3:
            quality_issues.append('부정 감정-강도 불일치')
            quality_score -= 1
        
        # 3. 복합 감정 검증
        complexity = result.get('emotional_complexity', '단순')
        emotion_mix = result.get('emotion_mix', {})
        
        if complexity == '복합' and len(emotion_mix) < 2:
            quality_issues.append('복합 감정 구성 불완전')
            quality_score -= 1
        
        # 4. 의료 맥락 적절성 검증
        medical_context = result.get('medical_context', '')
        valid_contexts = ['환자_안전', '업무_효율', '인간_관계', '전문성', '기타']
        if medical_context not in valid_contexts:
            quality_issues.append('잘못된 의료 맥락')
            quality_score -= 1
        
        # 5. 텍스트 길이 검증
        refined_text = result.get('refined_text', '')
        if len(original_text.strip()) > 10 and len(refined_text.strip()) < 5:
            quality_issues.append('정제된 텍스트가 너무 짧음')
            quality_score -= 1
        
        # 최종 점수 범위 조정
        quality_score = max(1, min(10, quality_score))
        
        return quality_score, quality_issues
    
    def _update_stats_enhanced(self, result, quality_score, needs_review):
        """고도화된 통계 정보 업데이트"""
        self.stats['total_processed'] += 1
        
        if quality_score >= 7:
            self.stats['high_quality'] += 1
        
        if needs_review:
            self.stats['needs_review'] += 1
        
        # 감정 분포 업데이트
        primary_emotion = result.get('primary_emotion', '알 수 없음')
        self.stats['emotion_distribution'][primary_emotion] += 1
        
        # 의료 맥락 분포 업데이트
        medical_context = result.get('medical_context', '기타')
        self.stats['context_distribution'][medical_context] += 1
        
        # 복합성 분포 업데이트
        complexity = result.get('emotional_complexity', '단순')
        self.stats['complexity_distribution'][complexity] += 1
    
    def process_batch_enhanced(self, texts, batch_size=5):
        """고도화된 배치 처리"""
        results = []
        
        # 배치 단위로 처리
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_results = []
            
            # ThreadPoolExecutor를 사용한 병렬 처리
            with ThreadPoolExecutor(max_workers=min(batch_size, 10)) as executor:
                # 각 텍스트에 대해 분석 작업 제출
                futures = {executor.submit(self.analyze_single_text_enhanced, text): idx 
                          for idx, text in enumerate(batch)}
                
                # 결과 수집 (순서 보장)
                batch_results = [None] * len(batch)
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        result = future.result()
                        batch_results[idx] = result
                    except Exception as e:
                        print(f"배치 처리 오류 (인덱스 {idx}): {e}")
                        batch_results[idx] = self._create_error_result_enhanced(str(e))
            
            results.extend(batch_results)
            
            # 진행상황 출력
            processed = min(i + batch_size, len(texts))
            print(f"진행률: {processed}/{len(texts)} ({processed/len(texts)*100:.1f}%)")
            
            # API 호출 제한을 위한 대기
            if i + batch_size < len(texts):
                time.sleep(10)
        
        return results
    
    def print_enhanced_stats(self):
        """고도화된 통계 정보 출력"""
        total = self.stats['total_processed']
        if total == 0:
            print("처리된 데이터가 없습니다.")
            return
        
        print(f"\n{'='*60}")
        print(f"🧠 고도화된 감정 분석 결과 통계")
        print(f"{'='*60}")
        
        print(f"📊 총 처리량: {total:,}개")
        print(f"✅ 고품질 분석: {self.stats['high_quality']:,}개 ({self.stats['high_quality']/total*100:.1f}%)")
        print(f"⚠️  재검토 필요: {self.stats['needs_review']:,}개 ({self.stats['needs_review']/total*100:.1f}%)")
        
        print(f"\n🎭 8가지 감정 분포:")
        for emotion, count in self.stats['emotion_distribution'].most_common():
            percentage = count/total*100
            print(f"  {emotion}: {count:,}개 ({percentage:.1f}%)")
        
        print(f"\n🏥 의료 맥락 분포:")
        for context, count in self.stats['context_distribution'].most_common():
            percentage = count/total*100
            print(f"  {context}: {count:,}개 ({percentage:.1f}%)")
        
        print(f"\n🔀 감정 복합성 분포:")
        for complexity, count in self.stats['complexity_distribution'].most_common():
            percentage = count/total*100
            print(f"  {complexity}: {count:,}개 ({percentage:.1f}%)")


def main_enhanced():
    """고도화된 메인 실행 함수"""
    
    # 설정값들
    INPUT_FILE = "설문조사_전처리데이터_20250620_0731.xlsx"
    COLUMN_NAME = "협업 후기"
    OUTPUT_FILE = "설문조사_전처리데이터_20250620_0731_enhanced.xlsx"
    MAX_ROWS = 5  # 테스트용, 전체 처리시 None으로 변경
    BATCH_SIZE = 1
    
    print("🧠 고도화된 협업 후기 감정 분석 시스템 시작")
    print(f"📂 입력 파일: {INPUT_FILE}")
    print(f"📊 분석 컬럼: {COLUMN_NAME}")
    print(f"📈 최대 처리량: {MAX_ROWS if MAX_ROWS else '전체'}")
    
    try:
        # 1. 데이터 로드
        print(f"\n📖 데이터 로딩 중...")
        df = pd.read_excel(INPUT_FILE)
        
        if COLUMN_NAME not in df.columns:
            raise ValueError(f"컬럼 '{COLUMN_NAME}'이 파일에 존재하지 않습니다.")
        
        # 처리할 데이터 범위 설정
        if MAX_ROWS:
            df = df.head(MAX_ROWS)
        
        print(f"✅ 총 {len(df):,}개 데이터 로드 완료")
        
        # 2. 고도화된 분석기 초기화
        print(f"\n🤖 고도화된 AI 분석기 초기화 중...")
        analyzer = EnhancedReviewAnalyzer()
        
        # 3. 텍스트 추출 및 전처리
        texts = df[COLUMN_NAME].fillna('').astype(str).tolist()
        print(f"📝 분석 대상 텍스트: {len(texts):,}개")
        
        # 4. 고도화된 배치 분석 실행
        print(f"\n🔍 고도화된 AI 분석 시작 (배치 크기: {BATCH_SIZE})")
        start_time = time.time()
        
        results = analyzer.process_batch_enhanced(texts, batch_size=BATCH_SIZE)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️  총 처리 시간: {processing_time:.1f}초")
        print(f"⚡ 평균 처리 속도: {len(texts)/processing_time:.1f}개/초")
        
        # 5. 결과를 DataFrame에 추가
        print(f"\n📊 결과 데이터 구성 중...")
        
        # 새로운 컬럼들 정의
        new_columns = {
            '협업 후기_정제텍스트_고도화': [r['refined_text'] for r in results],
            '협업 후기_비식별처리여부_고도화': [r['is_anonymized'] for r in results],
            '협업 후기_주요감정': [r['primary_emotion'] for r in results],
            '협업 후기_보조감정': [r['secondary_emotion'] for r in results],
            '협업 후기_감정복합성': [r['emotional_complexity'] for r in results],
            '협업 후기_감정비율': [str(r['emotion_mix']) for r in results],
            '협업 후기_감정강도_고도화': [r['sentiment_intensity'] for r in results],
            '협업 후기_AI신뢰도_고도화': [r['confidence_score'] for r in results],
            '협업 후기_의료맥락': [r['medical_context'] for r in results],
            '협업 후기_감정원인': [r['root_cause'] for r in results],
            '협업 후기_개선방안': [r['improvement_suggestion'] for r in results],
            '협업 후기_핵심키워드_고도화': [', '.join(r['key_terms']) for r in results],
            '협업 후기_분류라벨_고도화': [', '.join(r['labels']) for r in results],
            '협업 후기_품질점수_고도화': [r['quality_score'] for r in results],
            '협업 후기_재검토필요_고도화': [r['needs_review'] for r in results],
            '협업 후기_품질문제_고도화': [r['quality_issues'] for r in results]
        }
        
        # DataFrame에 새 컬럼들 추가
        for col_name, col_data in new_columns.items():
            df[col_name] = col_data
        
        # 6. 결과 저장
        print(f"\n💾 결과 저장 중: {OUTPUT_FILE}")
        df.to_excel(OUTPUT_FILE, index=False)
        print(f"✅ 저장 완료!")
        
        # 7. 통계 출력
        analyzer.print_enhanced_stats()
        
        print(f"\n🎯 고도화된 분석 완료!")
        print(f"📁 결과 파일: {OUTPUT_FILE}")
        print(f"📊 새로 추가된 컬럼: {len(new_columns)}개")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main_enhanced()