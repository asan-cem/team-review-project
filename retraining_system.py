"""
재학습 시스템 (Advanced Learning System)
- 수정 패턴 자동 분석
- 프롬프트 자동 최적화
- 성능 지속적 개선
"""

import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import json
import re
from datetime import datetime

class RetrainingSystem:
    """AI 재학습 시스템"""
    
    def __init__(self):
        self.correction_patterns = {}
        self.performance_metrics = {}
        self.learning_history = []
        self.optimized_prompt = None
    
    def analyze_corrections(self, original_file, corrected_file):
        """수정 전후 데이터 비교 분석"""
        
        print("🔍 수정 패턴 분석 시작...")
        
        # 원본과 수정본 로드
        df_original = pd.read_excel(original_file)
        df_corrected = pd.read_excel(corrected_file)
        
        # 수정된 항목 식별
        corrections = self._identify_corrections(df_original, df_corrected)
        
        # 패턴 분석
        patterns = self._extract_patterns(corrections)
        
        # 성능 개선 분석
        improvements = self._analyze_improvements(df_original, df_corrected)
        
        self.correction_patterns = patterns
        self.performance_metrics = improvements
        
        print(f"✅ 분석 완료: {len(corrections)}개 수정 사항 발견")
        
        return {
            'corrections': corrections,
            'patterns': patterns,
            'improvements': improvements
        }
    
    def _identify_corrections(self, df_original, df_corrected):
        """수정 항목 식별"""
        
        corrections = []
        
        for idx in df_original.index:
            if idx >= len(df_corrected):
                continue
                
            original_row = df_original.iloc[idx]
            corrected_row = df_corrected.iloc[idx]
            
            # 변경 사항 확인
            changes = {}
            
            fields_to_check = ['정제텍스트', '감정분석', '감정강도', '분류라벨', '품질점수']
            
            for field in fields_to_check:
                if field in original_row and field in corrected_row:
                    if original_row[field] != corrected_row[field]:
                        changes[field] = {
                            'before': original_row[field],
                            'after': corrected_row[field]
                        }
            
            if changes:
                correction = {
                    'index': idx,
                    'original_text': original_row['협업 후기'],
                    'changes': changes,
                    'reason': corrected_row.get('수정사유', 'Unknown')
                }
                corrections.append(correction)
        
        return corrections
    
    def _extract_patterns(self, corrections):
        """수정 패턴 추출"""
        
        patterns = {
            'sentiment_changes': defaultdict(int),
            'label_changes': defaultdict(int),
            'common_keywords': defaultdict(int),
            'quality_improvements': [],
            'text_refinements': []
        }
        
        for correction in corrections:
            changes = correction['changes']
            original_text = correction['original_text']
            
            # 감정 분석 변경 패턴
            if '감정분석' in changes:
                before = changes['감정분석']['before']
                after = changes['감정분석']['after']
                patterns['sentiment_changes'][f"{before}→{after}"] += 1
            
            # 분류 라벨 변경 패턴
            if '분류라벨' in changes:
                before = changes['분류라벨']['before']
                after = changes['분류라벨']['after']
                patterns['label_changes'][f"{before}→{after}"] += 1
            
            # 키워드 분석
            if isinstance(original_text, str):
                keywords = self._extract_keywords(original_text)
                for keyword in keywords:
                    patterns['common_keywords'][keyword] += 1
            
            # 품질 개선
            if '품질점수' in changes:
                before = changes['품질점수']['before']
                after = changes['품질점수']['after']
                improvement = after - before
                patterns['quality_improvements'].append(improvement)
            
            # 텍스트 정제 패턴
            if '정제텍스트' in changes:
                before = changes['정제텍스트']['before']
                after = changes['정제텍스트']['after']
                patterns['text_refinements'].append({
                    'before': before,
                    'after': after,
                    'original': original_text
                })
        
        return patterns
    
    def _extract_keywords(self, text):
        """텍스트에서 주요 키워드 추출"""
        
        if not isinstance(text, str):
            return []
        
        # 한국어 키워드 패턴
        keywords = []
        
        # 주요 단어 패턴
        patterns = [
            r'업무.*?처리',
            r'정보.*?공유',
            r'의사소통',
            r'협업',
            r'태도',
            r'서비스',
            r'전문성',
            r'신속',
            r'정확',
            r'친절',
            r'불친절',
            r'지연',
            r'개선',
            r'만족',
            r'불만',
            r'감사'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                keywords.append(pattern.replace('.*?', ' '))
        
        return keywords
    
    def _analyze_improvements(self, df_original, df_corrected):
        """성능 개선 분석"""
        
        improvements = {}
        
        # 품질점수 개선
        if '품질점수' in df_original.columns and '품질점수' in df_corrected.columns:
            original_quality = df_original['품질점수'].mean()
            corrected_quality = df_corrected['품질점수'].mean()
            improvements['quality_improvement'] = corrected_quality - original_quality
        
        # 재검토 필요 항목 감소
        if '재검토필요' in df_original.columns and '재검토필요' in df_corrected.columns:
            original_review_needed = df_original['재검토필요'].sum()
            corrected_review_needed = df_corrected['재검토필요'].sum()
            improvements['review_reduction'] = original_review_needed - corrected_review_needed
        
        # 감정 분석 정확도 (추정)
        improvements['estimated_accuracy'] = self._estimate_accuracy_improvement()
        
        return improvements
    
    def _estimate_accuracy_improvement(self):
        """정확도 개선 추정"""
        
        # 수정 패턴 기반 정확도 추정
        if not self.correction_patterns:
            return 0
        
        sentiment_changes = self.correction_patterns.get('sentiment_changes', {})
        total_changes = sum(sentiment_changes.values())
        
        if total_changes == 0:
            return 0
        
        # 부정→중립, 중립→긍정 등의 개선 패턴 비율 계산
        positive_changes = 0
        for change, count in sentiment_changes.items():
            if '부정→중립' in change or '중립→긍정' in change:
                positive_changes += count
        
        improvement_ratio = positive_changes / total_changes
        return improvement_ratio * 100  # 퍼센트로 변환
    
    def generate_optimized_prompt(self):
        """최적화된 프롬프트 생성"""
        
        if not self.correction_patterns:
            print("❌ 분석된 패턴이 없습니다. 먼저 analyze_corrections를 실행하세요.")
            return None
        
        print("🚀 최적화된 프롬프트 생성 중...")
        
        # 기본 프롬프트 템플릿
        base_prompt = """
[페르소나]
당신은 내부 직원 만족도 및 협업 피드백을 분석하는, 매우 꼼꼼하고 정확한 AI 데이터 분석 전문가입니다.
아래 학습된 패턴을 반드시 적용하여 정확한 분석을 수행하세요.
"""
        
        # 학습된 패턴 추가
        pattern_section = self._generate_pattern_rules()
        
        # 개선된 지시사항
        improved_instructions = self._generate_improved_instructions()
        
        # 품질 기준 강화
        quality_standards = self._generate_quality_standards()
        
        optimized_prompt = f"""
{base_prompt}

{pattern_section}

{improved_instructions}

{quality_standards}

[출력 형식]
반드시 다음 JSON 형식으로 출력하세요:
{{
    "refined_text": "정제된 텍스트",
    "sentiment": "긍정/부정/중립",
    "sentiment_intensity": 1-10,
    "classification": "분류라벨",
    "confidence_score": 1-10,
    "requires_review": true/false,
    "anonymized": true/false
}}
"""
        
        self.optimized_prompt = optimized_prompt
        
        # 학습 이력 저장
        self._save_learning_history()
        
        print("✅ 최적화된 프롬프트 생성 완료!")
        
        return optimized_prompt
    
    def _generate_pattern_rules(self):
        """패턴 기반 규칙 생성"""
        
        rules = ["[학습된 패턴 규칙]"]
        
        # 감정 분석 패턴
        sentiment_patterns = self.correction_patterns.get('sentiment_changes', {})
        if sentiment_patterns:
            rules.append("\\n**감정 분석 개선 규칙:**")
            
            most_common = sorted(sentiment_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for pattern, count in most_common:
                if '부정→중립' in pattern:
                    rules.append("- 업무 개선 제안이나 건설적 피드백은 '중립'으로 분류")
                elif '부정→긍정' in pattern:
                    rules.append("- 협력적이고 긍정적인 표현은 '긍정'으로 분류")
                elif '중립→부정' in pattern:
                    rules.append("- 명확한 불만이나 비판은 '부정'으로 분류")
        
        # 분류 라벨 패턴
        label_patterns = self.correction_patterns.get('label_changes', {})
        if label_patterns:
            rules.append("\\n**분류 라벨 개선 규칙:**")
            
            most_common = sorted(label_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for pattern, count in most_common:
                rules.append(f"- {pattern.replace('→', ' → ')}: {count}건 수정됨")
        
        # 키워드 기반 규칙
        common_keywords = self.correction_patterns.get('common_keywords', {})
        if common_keywords:
            rules.append("\\n**키워드 기반 분류 규칙:**")
            
            top_keywords = sorted(common_keywords.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for keyword, count in top_keywords:
                if '업무' in keyword:
                    rules.append(f"- '{keyword}' 포함 시 → 전문성 부족 또는 업무 태도")
                elif '정보' in keyword:
                    rules.append(f"- '{keyword}' 포함 시 → 직원간 소통")
                elif '협업' in keyword:
                    rules.append(f"- '{keyword}' 포함 시 → 부서간 협업")
        
        return "\\n".join(rules)
    
    def _generate_improved_instructions(self):
        """개선된 지시사항 생성"""
        
        instructions = """
[개선된 분석 지시사항]

1. **정제텍스트 생성 규칙:**
   - 원본 의미를 100% 보존하면서 표현만 개선
   - 비속어나 부적절한 표현은 전문적 표현으로 변경
   - 오타 및 문법 오류 수정
   - 불완전한 문장은 완성된 문장으로 보완

2. **감정분석 정확도 향상:**
   - 업무 개선 제안 = 중립 (부정 아님)
   - 사실적 기술 = 중립
   - 명확한 칭찬/감사 = 긍정
   - 명확한 불만/비판 = 부정

3. **분류라벨 정확성 향상:**
   - 정보 전달/공유 문제 → 직원간 소통
   - 업무 처리 속도/정확성 → 전문성 부족
   - 서비스 태도/친절도 → 업무 태도
   - 부서간 조율/협력 → 부서간 협업
   - 예의/배려/존중 → 상호 존중

4. **품질점수 기준 강화:**
   - 명확하고 구체적인 내용: 8-10점
   - 일반적이지만 의미있는 내용: 6-7점
   - 모호하거나 불분명한 내용: 4-5점
   - 의미 파악 어려운 내용: 1-3점
"""
        
        return instructions
    
    def _generate_quality_standards(self):
        """품질 기준 생성"""
        
        avg_improvement = np.mean(self.correction_patterns.get('quality_improvements', [0]))
        
        standards = f"""
[품질 보증 기준]

목표 성능:
- 품질점수 7점 이상: 90% 이상
- 재검토 필요 항목: 5% 이하
- 감정분석 정확도: 95% 이상

품질 검증 체크리스트:
□ 정제텍스트가 원본 의미를 정확히 반영하는가?
□ 감정분석이 텍스트 톤과 일치하는가?
□ 분류라벨이 내용의 핵심을 반영하는가?
□ 품질점수가 분석 신뢰도를 정확히 나타내는가?

자동 재검토 조건:
- 품질점수 6점 이하
- 감정강도와 감정분석 불일치
- 키워드와 분류라벨 불일치

목표 개선율: {avg_improvement:.1f}점 향상
"""
        
        return standards
    
    def _save_learning_history(self):
        """학습 이력 저장"""
        
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'patterns_analyzed': len(self.correction_patterns),
            'performance_metrics': self.performance_metrics,
            'prompt_version': f"v{len(self.learning_history) + 1}"
        }
        
        self.learning_history.append(history_entry)
        
        # JSON 파일로 저장
        with open('learning_history.json', 'w', encoding='utf-8') as f:
            json.dump(self.learning_history, f, ensure_ascii=False, indent=2)
    
    def evaluate_performance(self, test_file):
        """성능 평가"""
        
        print("📊 성능 평가 시작...")
        
        df_test = pd.read_excel(test_file)
        
        metrics = {
            'total_items': len(df_test),
            'high_quality_ratio': len(df_test[df_test['품질점수'] >= 7]) / len(df_test),
            'review_needed_ratio': df_test['재검토필요'].sum() / len(df_test),
            'average_quality': df_test['품질점수'].mean(),
            'sentiment_distribution': df_test['감정분석'].value_counts().to_dict()
        }
        
        print("📈 성능 평가 결과:")
        print(f"  • 전체 항목: {metrics['total_items']}개")
        print(f"  • 고품질 비율: {metrics['high_quality_ratio']:.1%}")
        print(f"  • 재검토 필요 비율: {metrics['review_needed_ratio']:.1%}")
        print(f"  • 평균 품질점수: {metrics['average_quality']:.1f}점")
        
        return metrics
    
    def continuous_learning_cycle(self, original_file, corrected_file, new_data_file):
        """지속적 학습 사이클"""
        
        print("🔄 지속적 학습 사이클 시작...")
        
        # 1단계: 수정 패턴 분석
        analysis = self.analyze_corrections(original_file, corrected_file)
        
        # 2단계: 최적화된 프롬프트 생성
        optimized_prompt = self.generate_optimized_prompt()
        
        # 3단계: 새로운 데이터에 적용 (시뮬레이션)
        print("3단계: 최적화된 모델로 새 데이터 분석 (시뮬레이션)")
        
        # 4단계: 성능 평가
        if corrected_file:
            performance = self.evaluate_performance(corrected_file)
        
        # 5단계: 결과 리포트
        self._generate_learning_report(analysis, performance if 'performance' in locals() else None)
        
        return {
            'analysis': analysis,
            'optimized_prompt': optimized_prompt,
            'performance': performance if 'performance' in locals() else None
        }
    
    def _generate_learning_report(self, analysis, performance):
        """학습 리포트 생성"""
        
        report = f"""
# 🎓 AI 재학습 결과 리포트

## 📊 학습 개요
- **분석 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **수정 사항**: {len(analysis['corrections'])}건
- **학습된 패턴**: {len(analysis['patterns'])}개 유형

## 🔍 주요 개선 사항
"""
        
        # 감정 분석 개선
        sentiment_changes = analysis['patterns'].get('sentiment_changes', {})
        if sentiment_changes:
            report += "\\n### 감정 분석 개선\\n"
            for change, count in sorted(sentiment_changes.items(), key=lambda x: x[1], reverse=True)[:3]:
                report += f"- {change}: {count}건\\n"
        
        # 분류 개선
        label_changes = analysis['patterns'].get('label_changes', {})
        if label_changes:
            report += "\\n### 분류 라벨 개선\\n"
            for change, count in sorted(label_changes.items(), key=lambda x: x[1], reverse=True)[:3]:
                report += f"- {change}: {count}건\\n"
        
        # 성능 지표
        if performance:
            report += f"""
## 📈 성능 지표
- **고품질 비율**: {performance['high_quality_ratio']:.1%}
- **재검토 필요**: {performance['review_needed_ratio']:.1%}
- **평균 품질점수**: {performance['average_quality']:.1f}점
"""
        
        # 파일 저장
        with open('learning_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("📄 학습 리포트가 'learning_report.md'에 저장되었습니다.")

def demo_retraining_system():
    """재학습 시스템 데모"""
    
    print("🎯 AI 재학습 시스템 데모")
    print("=" * 50)
    
    # 재학습 시스템 초기화
    retraining = RetrainingSystem()
    
    # 시뮬레이션 데이터로 테스트
    print("📚 학습 데이터 시뮬레이션...")
    
    # 모의 수정 패턴 생성
    retraining.correction_patterns = {
        'sentiment_changes': {
            '부정→중립': 15,
            '중립→긍정': 8,
            '부정→긍정': 3
        },
        'label_changes': {
            '업무 태도→직원간 소통': 12,
            '전문성 부족→업무 태도': 7,
            '부서간 협업→상호 존중': 5
        },
        'quality_improvements': [2.1, 1.8, 2.5, 1.2, 3.0],
        'common_keywords': {
            '업무 처리': 20,
            '정보 공유': 15,
            '의사소통': 12,
            '협업': 10,
            '태도': 8
        }
    }
    
    # 최적화된 프롬프트 생성
    optimized_prompt = retraining.generate_optimized_prompt()
    
    if optimized_prompt:
        print("\\n✅ 재학습 완료!")
        print("📊 학습 결과:")
        print(f"  • 감정 분석 패턴: {len(retraining.correction_patterns['sentiment_changes'])}개")
        print(f"  • 분류 개선 패턴: {len(retraining.correction_patterns['label_changes'])}개")
        print(f"  • 평균 품질 개선: {np.mean(retraining.correction_patterns['quality_improvements']):.1f}점")
        
        return retraining
    else:
        print("❌ 재학습 실패")
        return None

if __name__ == "__main__":
    demo_retraining_system()