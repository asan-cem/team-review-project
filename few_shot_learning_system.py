"""
Few-Shot Learning 시스템
- 수동 수정 사례를 AI 프롬프트에 즉시 반영
- 다음 분석부터 개선된 성능 적용
"""

import pandas as pd
from main import ReviewAnalyzer

class FewShotLearningSystem:
    """Few-Shot Learning을 통한 AI 성능 개선"""
    
    def __init__(self):
        self.correction_examples = []
        self.improved_prompt = None
    
    def add_correction_example(self, original_text, corrected_analysis):
        """수정 사례 추가"""
        example = {
            'original_text': original_text,
            'ai_analysis': corrected_analysis['ai_result'],
            'corrected_analysis': corrected_analysis['manual_correction'],
            'correction_reason': corrected_analysis['reason']
        }
        self.correction_examples.append(example)
    
    def load_corrections_from_excel(self, corrected_file):
        """Excel에서 수정 사례 로드"""
        
        print("📚 수정 사례 학습 중...")
        
        # 수정된 파일 로드
        df_corrected = pd.read_excel(corrected_file)
        
        # 수정된 항목만 필터링 (수정사유 컬럼이 있는 경우)
        if '수정사유' in df_corrected.columns:
            corrected_items = df_corrected[df_corrected['수정사유'].notna()]
        else:
            # 품질점수가 높아진 항목 추정
            corrected_items = df_corrected[df_corrected['품질점수'] >= 7]
        
        print(f"수정 사례 {len(corrected_items)}개 발견")
        
        # 각 수정 사례를 분석하여 패턴 추출
        for _, row in corrected_items.iterrows():
            example = {
                'original': row['협업 후기'],
                'refined_text': row['정제텍스트'],
                'sentiment': row['감정분석'],
                'intensity': row['감정강도'],
                'label': row['분류라벨'],
                'quality': row['품질점수']
            }
            self.correction_examples.append(example)
        
        return len(corrected_items)
    
    def generate_improved_prompt(self):
        """개선된 프롬프트 생성"""
        
        if not self.correction_examples:
            print("❌ 학습할 수정 사례가 없습니다.")
            return None
        
        # 기존 프롬프트에 Few-Shot 예시 추가
        few_shot_examples = self._create_few_shot_examples()
        
        improved_prompt = f"""
[페르소나]
당신은 내부 직원 만족도 및 협업 피드백을 분석하는, 매우 꼼꼼하고 정확한 AI 데이터 분석 전문가입니다. 
아래 수정 사례들을 참고하여 더욱 정확한 분석을 수행하세요.

{few_shot_examples}

[지시사항]
위 수정 사례들의 패턴을 학습하여 다음 규칙을 적용하세요:

1. 주어진 원본 텍스트의 핵심 의미를 보존하면서, 오타와 문법을 교정하여 refined_text를 생성합니다.
2. 속거나 공격적인 표현은 전문적이고 정중한 표현으로 순화합니다.

3. **개선된 비식별 처리 규칙**:
   - 긍정적/중립적 피드백: 실명 포함되어도 비식별 처리 안함
   - 부정적 피드백: 매우 구체적인 개인 식별 정보만 비식별 처리
   - 건설적 제안이나 업무 개선 의견은 '중립'으로 분류

4. **개선된 감정 분석**:
   - 업무 개선 제안 → '중립'
   - 단순한 사실 기술 → '중립'  
   - 협력적 표현 → '긍정'
   - 명확한 불만이나 비판 → '부정'

5. **개선된 분류 기준**:
   - 정보 공유 문제 → '직원간 소통'
   - 업무 처리 속도 → '전문성 부족'
   - 태도나 서비스 → '업무 태도'
   - 부서간 조율 → '부서간 협업'
   - 예의나 배려 → '상호 존중'

6. 품질점수는 다음 기준으로 평가:
   - 명확하고 구체적인 내용: 8-10점
   - 일반적인 내용: 6-7점
   - 모호하거나 불분명한 내용: 3-5점

7. 분석 결과를 JSON 형태로 출력하세요.
"""
        
        self.improved_prompt = improved_prompt
        return improved_prompt
    
    def _create_few_shot_examples(self):
        """Few-Shot 예시 생성"""
        
        examples_text = "\n[수정 사례 학습]\n"
        
        # 대표적인 수정 사례들을 선별
        selected_examples = self.correction_examples[:5]  # 상위 5개 사례
        
        for i, example in enumerate(selected_examples, 1):
            examples_text += f"""
예시 {i}:
원본: "{example['original']}"
정제텍스트: "{example['refined_text']}"
감정분석: {example['sentiment']}
감정강도: {example['intensity']}
분류라벨: {example['label']}
품질점수: {example['quality']}
"""
        
        # 패턴 분석 추가
        sentiment_patterns = self._analyze_sentiment_patterns()
        label_patterns = self._analyze_label_patterns()
        
        examples_text += f"\n[학습된 패턴]\n{sentiment_patterns}\n{label_patterns}"
        
        return examples_text
    
    def _analyze_sentiment_patterns(self):
        """감정 분석 패턴 추출"""
        
        patterns = []
        
        # 중립으로 재분류된 패턴
        neutral_keywords = ['개선', '필요', '요청', '제안', '상황', '처리']
        patterns.append(f"건설적 표현 ({', '.join(neutral_keywords)}) → 중립")
        
        # 긍정 패턴
        positive_keywords = ['감사', '만족', '좋아', '친절', '신속']
        patterns.append(f"긍정적 표현 ({', '.join(positive_keywords)}) → 긍정")
        
        return "감정분석 패턴: " + " | ".join(patterns)
    
    def _analyze_label_patterns(self):
        """분류 라벨 패턴 추출"""
        
        patterns = []
        patterns.append("정보 공유 관련 → 직원간 소통")
        patterns.append("업무 처리 속도 → 전문성 부족")
        patterns.append("태도/서비스 → 업무 태도")
        
        return "분류 패턴: " + " | ".join(patterns)
    
    def apply_improved_analysis(self, new_data_file, output_file):
        """개선된 프롬프트로 새로운 분석 수행"""
        
        if not self.improved_prompt:
            print("❌ 개선된 프롬프트가 생성되지 않았습니다.")
            return False
        
        print("🚀 개선된 AI로 분석 시작...")
        
        # 새로운 ReviewAnalyzer 인스턴스 생성 (개선된 프롬프트 적용)
        analyzer = ImprovedReviewAnalyzer(
            project_id="gen-lang-client-0492208227",
            location="us-central1",
            improved_prompt=self.improved_prompt
        )
        
        # 분석 실행
        try:
            analyzer.process_xlsx_with_column(
                new_data_file,
                '협업 후기',
                output_file,
                max_rows=100,  # 테스트용 소규모
                use_batch=True,
                batch_size=10
            )
            
            print("✅ 개선된 분석 완료!")
            return True
            
        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            return False

class ImprovedReviewAnalyzer(ReviewAnalyzer):
    """개선된 프롬프트를 사용하는 분석기"""
    
    def __init__(self, project_id, location, improved_prompt):
        super().__init__(project_id, location)
        self.prompt_template = improved_prompt

def demo_few_shot_learning():
    """Few-Shot Learning 데모"""
    
    print("🎯 Few-Shot Learning 시스템 데모")
    print("=" * 50)
    
    # 1. Few-Shot 시스템 초기화
    few_shot = FewShotLearningSystem()
    
    # 2. 수동 수정 사례 추가 (시뮬레이션)
    correction_examples = [
        {
            'original': '혈관이 없어서 실패하면 실패하다고 인계주고 가십니다',
            'refined_text': '채혈 시 혈관 확보 실패 상황에 대한 명확한 인계 필요',
            'sentiment': '중립',
            'intensity': 4,
            'label': '직원간 소통',
            'quality': 8
        },
        {
            'original': '업무 처리가 늦어요',
            'refined_text': '업무 처리 속도 개선이 필요함',
            'sentiment': '중립',
            'intensity': 4,
            'label': '전문성 부족',
            'quality': 7
        },
        {
            'original': '항상 친절하게 도와주셔서 감사합니다',
            'refined_text': '항상 친절하게 도와주셔서 감사합니다',
            'sentiment': '긍정',
            'intensity': 7,
            'label': '상호 존중',
            'quality': 9
        }
    ]
    
    # 수정 사례 추가
    for example in correction_examples:
        few_shot.correction_examples.append(example)
    
    # 3. 개선된 프롬프트 생성
    improved_prompt = few_shot.generate_improved_prompt()
    
    if improved_prompt:
        print("✅ 개선된 프롬프트 생성 완료!")
        print(f"📊 학습된 사례 수: {len(few_shot.correction_examples)}개")
        
        # 프롬프트 일부 출력
        print("\n📝 개선된 프롬프트 (일부):")
        print(improved_prompt[:500] + "...")
        
        return few_shot
    else:
        print("❌ 프롬프트 생성 실패")
        return None

if __name__ == "__main__":
    demo_few_shot_learning()