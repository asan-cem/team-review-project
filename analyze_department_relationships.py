#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
부서간 관계 품질 분석기
A, B 부서간의 평가 점수, 응답수, 감정분석 등을 종합하여 관계 품질을 평가합니다.

📋 주요 기능:
1. 부서간 상호평가 데이터 분석
2. 정량적/정성적 지표 계산
3. 관계 품질 등급 분류 (S/A/B/C/D)
4. 개선 포인트 제안

📊 분석 지표:
- 정량적: 점수, 응답수, 협업 규모, 데이터 신뢰성
- 정성적: 감정 분석, 텍스트 품질

작성자: Claude AI
버전: 1.0
생성일: 2025년 7월 16일
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 🔧 설정 및 상수 정의
# ============================================================================

INPUT_DATA_FILE = "rawdata/2. text_processor_결과_20250715_160846.xlsx"
OUTPUT_FILE = "부서쌍별_관계분석_결과.xlsx"

# 분석 기준 설정
MIN_RESPONSES = 5      # 최소 응답수
MIN_MUTUAL_RESPONSES = 3  # 최소 상호평가 응답수

# 등급 기준점 (텍스트 지표 제거 후 조정)
GRADE_THRESHOLDS = {
    'S': {'score': 85, 'balance': 95, 'responses': 20, 'emotion': 1.6, 'continuity': 0.75},
    'A': {'score': 80, 'balance': 90, 'responses': 15, 'emotion': 1.4, 'continuity': 0.5},
    'B': {'score': 75, 'balance': 80, 'responses': 10, 'emotion': 1.0, 'continuity': 0.25},
    'C': {'score': 65, 'balance': 60, 'responses': 5, 'emotion': 0.6, 'continuity': 0},
}

# 시계열 분석 기준
TREND_THRESHOLDS = {
    '긴급': {'score_decline': -10, 'consecutive_years': 2},
    '주의': {'score_decline': -5, 'recent_years': 1},
    '개선': {'score_improve': 5, 'consecutive_years': 2},
    '모범': {'min_score': 80, 'stable_years': 4}
}

# ============================================================================
# 🛠️ 데이터 로드 및 전처리
# ============================================================================

def load_and_preprocess_data():
    """
    데이터를 로드하고 분석에 필요한 전처리를 수행합니다.
    """
    print("🚀 부서간 관계 분석을 시작합니다...")
    
    try:
        df = pd.read_excel(INPUT_DATA_FILE)
        print(f"✅ 데이터 로드 완료: {len(df):,}건")
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {INPUT_DATA_FILE}")
        return None
    
    # 컬럼명 정리
    score_columns = [
        '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.',
        '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.',
        '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.',
        '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.',
        '전반적으로 ○○과의 협업에 대해 만족한다.'
    ]
    
    # 짧은 컬럼명으로 매핑
    column_mapping = {
        score_columns[0]: '존중배려',
        score_columns[1]: '정보공유', 
        score_columns[2]: '명확처리',
        score_columns[3]: '태도개선',
        score_columns[4]: '전반만족'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 필수 컬럼 확인
    required_columns = ['설문시행연도', '평가_부서명', '피평가대상 부서명', '종합점수']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ 필수 컬럼이 없습니다: {missing_columns}")
        return None
    
    # 데이터 전처리
    df['설문시행연도'] = df['설문시행연도'].astype(str)
    df = df.dropna(subset=['평가_부서명', '피평가대상 부서명', '종합점수'])
    
    # 감정 분류 결측값 처리
    if '감정_분류' in df.columns:
        df['감정_분류'] = df['감정_분류'].fillna('중립')
    
    print(f"📊 전처리 완료: {len(df):,}건")
    print(f"📅 분석 기간: {df['설문시행연도'].min()} ~ {df['설문시행연도'].max()}")
    
    return df

# ============================================================================
# 📊 정량적 지표 계산
# ============================================================================

def calculate_quantitative_metrics(df, dept_a, dept_b):
    """
    두 부서간의 정량적 지표를 계산합니다.
    """
    # A→B 평가 데이터
    a_to_b = df[(df['평가_부서명'] == dept_a) & (df['피평가대상 부서명'] == dept_b)]
    # B→A 평가 데이터  
    b_to_a = df[(df['평가_부서명'] == dept_b) & (df['피평가대상 부서명'] == dept_a)]
    
    # 기본 통계
    a_to_b_responses = len(a_to_b)
    b_to_a_responses = len(b_to_a)
    total_responses = a_to_b_responses + b_to_a_responses
    
    if total_responses == 0:
        return None
    
    # 점수 관련 지표
    a_to_b_score = a_to_b['종합점수'].mean() if a_to_b_responses > 0 else 0
    b_to_a_score = b_to_a['종합점수'].mean() if b_to_a_responses > 0 else 0
    
    mutual_avg_score = (a_to_b_score + b_to_a_score) / 2 if min(a_to_b_responses, b_to_a_responses) > 0 else max(a_to_b_score, b_to_a_score)
    score_balance = 100 - abs(a_to_b_score - b_to_a_score) if min(a_to_b_responses, b_to_a_responses) > 0 else 50
    
    # 응답 관련 지표
    response_balance = min(a_to_b_responses, b_to_a_responses) / max(a_to_b_responses, b_to_a_responses) * 100 if max(a_to_b_responses, b_to_a_responses) > 0 else 0
    
    # 협업 지속성 (연도별 분포)
    years_active = len(set(list(a_to_b['설문시행연도']) + list(b_to_a['설문시행연도'])))
    total_years = len(df['설문시행연도'].unique())
    continuity = years_active / total_years
    
    # 세부항목 일관성 (분산계수)
    score_cols = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족']
    available_score_cols = [col for col in score_cols if col in df.columns]
    
    consistency_score = 0
    if available_score_cols and total_responses > 0:
        all_scores = pd.concat([a_to_b[available_score_cols], b_to_a[available_score_cols]])
        if len(all_scores) > 0:
            means = all_scores.mean()
            stds = all_scores.std()
            cv = stds / means  # 변동계수
            consistency_score = max(0, 100 - cv.mean() * 10)  # 일관성 점수로 변환
    
    # 신뢰성 지표
    reliability_score = 100
    if '극단값' in df.columns:
        # 극단값 컬럼을 숫자형으로 변환 (True/False -> 1/0)
        a_to_b_extreme = pd.to_numeric(a_to_b['극단값'], errors='coerce').fillna(0)
        b_to_a_extreme = pd.to_numeric(b_to_a['극단값'], errors='coerce').fillna(0)
        extreme_ratio = (a_to_b_extreme.sum() + b_to_a_extreme.sum()) / total_responses if total_responses > 0 else 0
        reliability_score *= (1 - extreme_ratio)
    
    if '신뢰도_점수' in df.columns:
        trust_scores = pd.concat([a_to_b['신뢰도_점수'], b_to_a['신뢰도_점수']]).dropna()
        if len(trust_scores) > 0:
            avg_trust = pd.to_numeric(trust_scores, errors='coerce').mean()
            if not pd.isna(avg_trust):
                reliability_score *= avg_trust / 100
    
    return {
        'a_to_b_score': round(a_to_b_score, 2),
        'b_to_a_score': round(b_to_a_score, 2),
        'mutual_avg_score': round(mutual_avg_score, 2),
        'score_balance': round(score_balance, 1),
        'a_to_b_responses': a_to_b_responses,
        'b_to_a_responses': b_to_a_responses,
        'total_responses': total_responses,
        'response_balance': round(response_balance, 1),
        'years_active': years_active,
        'continuity': round(continuity, 3),
        'consistency_score': round(consistency_score, 1),
        'reliability_score': round(reliability_score, 1)
    }

# ============================================================================
# 😊 정성적 지표 계산  
# ============================================================================

def calculate_qualitative_metrics(df, dept_a, dept_b):
    """
    두 부서간의 정성적 지표를 계산합니다.
    """
    # A→B, B→A 평가 데이터
    a_to_b = df[(df['평가_부서명'] == dept_a) & (df['피평가대상 부서명'] == dept_b)]
    b_to_a = df[(df['평가_부서명'] == dept_b) & (df['피평가대상 부서명'] == dept_a)]
    
    combined_data = pd.concat([a_to_b, b_to_a])
    
    if len(combined_data) == 0:
        return None
    
    # 감정 분석 지표
    emotion_metrics = {'emotion_score': 0, 'emotion_intensity': 0, 'emotion_consistency': 0}
    
    if '감정_분류' in df.columns:
        emotions = combined_data['감정_분류'].value_counts()
        total = len(combined_data)
        
        positive_ratio = emotions.get('긍정', 0) / total
        neutral_ratio = emotions.get('중립', 0) / total  
        negative_ratio = emotions.get('부정', 0) / total
        
        # 감정 점수 (0~2 스케일)
        emotion_score = (positive_ratio * 2 + neutral_ratio * 1 + negative_ratio * 0)
        
        # 감정 강도
        emotion_intensity = 0
        if '감정_강도_점수' in df.columns:
            intensity_scores = combined_data['감정_강도_점수'].dropna()
            if len(intensity_scores) > 0:
                emotion_intensity = intensity_scores.mean() / 100
        
        # 감정 일관성 (엔트로피 기반)
        emotion_consistency = 0
        if total > 1:
            probabilities = [positive_ratio, neutral_ratio, negative_ratio]
            probabilities = [p for p in probabilities if p > 0]
            if len(probabilities) > 1:
                entropy = -sum(p * np.log2(p) for p in probabilities)
                max_entropy = np.log2(3)  # 3가지 감정의 최대 엔트로피
                emotion_consistency = max(0, 100 * (1 - entropy / max_entropy))
            else:
                emotion_consistency = 100  # 하나의 감정만 있으면 완전 일관성
        
        emotion_metrics = {
            'emotion_score': round(emotion_score, 3),
            'emotion_intensity': round(emotion_intensity, 3),
            'emotion_consistency': round(emotion_consistency, 1),
            'positive_ratio': round(positive_ratio * 100, 1),
            'negative_ratio': round(negative_ratio * 100, 1)
        }
    
    # 텍스트 관련 지표는 분석에서 제외
    # - 텍스트_풍부도: 데이터 품질 편차 큼
    # - 키워드_다양성: 표준화 어려움
    # - 의료_맥락: 데이터 형식 불일치
    
    return emotion_metrics

# ============================================================================
# 📈 시계열 분석 함수들
# ============================================================================

def calculate_yearly_metrics(df, dept_a, dept_b, year):
    """
    특정 연도의 부서간 관계 지표를 계산합니다.
    """
    year_data = df[df['설문시행연도'] == year]
    
    quant_metrics = calculate_quantitative_metrics(year_data, dept_a, dept_b)
    qual_metrics = calculate_qualitative_metrics(year_data, dept_a, dept_b)
    
    if not quant_metrics or not qual_metrics:
        return None
    
    return {
        'year': year,
        'mutual_avg_score': quant_metrics['mutual_avg_score'],
        'score_balance': quant_metrics['score_balance'],
        'total_responses': quant_metrics['total_responses'],
        'emotion_score': qual_metrics['emotion_score'],
        'positive_ratio': qual_metrics['positive_ratio'],
        'negative_ratio': qual_metrics['negative_ratio']
    }

def analyze_relationship_trends(df, dept_a, dept_b):
    """
    2022~2025년 부서간 관계 변화 추이를 분석합니다.
    """
    years = ['2022', '2023', '2024', '2025']
    yearly_data = {}
    
    # 연도별 지표 수집
    for year in years:
        metrics = calculate_yearly_metrics(df, dept_a, dept_b, year)
        if metrics:
            yearly_data[year] = metrics
    
    if len(yearly_data) < 2:
        return None  # 최소 2년 데이터 필요
    
    # 트렌드 지표 계산
    scores = [yearly_data[year]['mutual_avg_score'] for year in sorted(yearly_data.keys())]
    emotions = [yearly_data[year]['emotion_score'] for year in sorted(yearly_data.keys())]
    responses = [yearly_data[year]['total_responses'] for year in sorted(yearly_data.keys())]
    
    # 선형 회귀 기울기 계산 (트렌드)
    def calculate_slope(values):
        if len(values) < 2:
            return 0
        x = list(range(len(values)))
        n = len(values)
        slope = (n * sum(x[i] * values[i] for i in range(n)) - sum(x) * sum(values)) / (n * sum(x[i]**2 for i in range(n)) - sum(x)**2)
        return slope
    
    score_trend = calculate_slope(scores)
    emotion_trend = calculate_slope(emotions)
    response_trend = calculate_slope(responses)
    
    # 최근 vs 초기 비교
    recent_years = [year for year in ['2024', '2025'] if year in yearly_data]
    early_years = [year for year in ['2022', '2023'] if year in yearly_data]
    
    recent_avg_score = np.mean([yearly_data[year]['mutual_avg_score'] for year in recent_years]) if recent_years else 0
    early_avg_score = np.mean([yearly_data[year]['mutual_avg_score'] for year in early_years]) if early_years else 0
    
    recent_improvement = recent_avg_score - early_avg_score if early_years and recent_years else 0
    
    # 변동성 계산
    score_volatility = np.std(scores) if len(scores) > 1 else 0
    
    # 연속성 분석
    data_years = len(yearly_data)
    data_continuity = data_years / 4  # 4년 중 몇 년의 데이터가 있는지
    
    return {
        'yearly_data': yearly_data,
        'score_trend': round(score_trend, 3),
        'emotion_trend': round(emotion_trend, 3),
        'response_trend': round(response_trend, 3),
        'recent_improvement': round(recent_improvement, 2),
        'score_volatility': round(score_volatility, 2),
        'data_years': data_years,
        'data_continuity': round(data_continuity, 3)
    }

def classify_trend_pattern(trend_analysis):
    """
    관계 변화 패턴을 분류합니다.
    """
    if not trend_analysis:
        return 'insufficient_data', "데이터 부족"
    
    score_trend = trend_analysis['score_trend']
    recent_improvement = trend_analysis['recent_improvement']
    volatility = trend_analysis['score_volatility']
    data_years = trend_analysis['data_years']
    
    # 패턴 분류 로직
    if data_years < 2:
        return 'insufficient_data', "분석 기간 부족"
    
    # 강한 개선 추세
    if score_trend > 2 and recent_improvement > 5:
        return 'improving', f"지속적 개선 (기울기: {score_trend:.1f}, 최근개선: {recent_improvement:.1f}점)"
    
    # 강한 악화 추세  
    if score_trend < -2 and recent_improvement < -5:
        return 'declining', f"지속적 악화 (기울기: {score_trend:.1f}, 최근하락: {recent_improvement:.1f}점)"
    
    # 회복 패턴
    if score_trend > 1 and recent_improvement > 3:
        return 'recovering', f"회복 중 (최근개선: {recent_improvement:.1f}점)"
    
    # 안정 패턴
    if abs(score_trend) <= 1 and volatility < 5:
        return 'stable', f"안정적 (변동성: {volatility:.1f})"
    
    # 급변 패턴
    if volatility > 10:
        return 'volatile', f"변동성 높음 (표준편차: {volatility:.1f})"
    
    # 기본 (보통)
    return 'neutral', f"보통 수준 (기울기: {score_trend:.1f})"

def generate_trend_alert(trend_analysis, yearly_data):
    """
    조기 경보 시스템: 관계 악화 위험을 감지합니다.
    """
    if not trend_analysis or not yearly_data:
        return 'normal', "데이터 부족"
    
    recent_improvement = trend_analysis['recent_improvement']
    score_trend = trend_analysis['score_trend']
    
    # 최근 2년 연속 하락 체크
    years = sorted(yearly_data.keys())
    if len(years) >= 3:
        last_3_scores = [yearly_data[year]['mutual_avg_score'] for year in years[-3:]]
        consecutive_decline = all(last_3_scores[i] > last_3_scores[i+1] for i in range(len(last_3_scores)-1))
        
        if consecutive_decline and (last_3_scores[0] - last_3_scores[-1]) >= 10:
            return 'urgent', f"🚨 긴급: 3년 연속 하락 ({last_3_scores[0]:.1f}→{last_3_scores[-1]:.1f}점)"
    
    # 최근 급격한 하락
    if recent_improvement <= -10:
        return 'urgent', f"🚨 긴급: 최근 급격한 하락 ({recent_improvement:.1f}점)"
    
    # 주의 필요
    if recent_improvement <= -5 or score_trend <= -2:
        return 'warning', f"⚠️ 주의: 관계 악화 징후 (개선도: {recent_improvement:.1f}점)"
    
    # 개선 중
    if recent_improvement >= 5 and score_trend >= 1:
        return 'improving', f"📈 개선: 지속적 관계 향상 (개선도: {recent_improvement:.1f}점)"
    
    # 모범 사례
    recent_scores = [yearly_data[year]['mutual_avg_score'] for year in sorted(yearly_data.keys())[-2:]]
    if all(score >= 80 for score in recent_scores) and len(yearly_data) >= 3:
        return 'excellent', f"⭐ 모범: 지속적 우수 관계 (최근 평균: {np.mean(recent_scores):.1f}점)"
    
    return 'normal', "✅ 정상 범위"

# ============================================================================
# 🏆 관계 품질 등급 분류
# ============================================================================

def classify_relationship_grade(quant_metrics, qual_metrics):
    """
    정량적/정성적 지표를 종합하여 관계 품질 등급을 분류합니다.
    """
    if not quant_metrics or not qual_metrics:
        return 'F', "데이터 부족"
    
    # 기본 조건 확인
    if quant_metrics['total_responses'] < MIN_RESPONSES:
        return 'F', f"응답수 부족 ({quant_metrics['total_responses']}건)"
    
    if min(quant_metrics['a_to_b_responses'], quant_metrics['b_to_a_responses']) < MIN_MUTUAL_RESPONSES:
        return 'F', f"상호평가 부족 (A→B: {quant_metrics['a_to_b_responses']}, B→A: {quant_metrics['b_to_a_responses']})"
    
    # 등급별 기준 확인
    for grade in ['S', 'A', 'B', 'C']:
        criteria = GRADE_THRESHOLDS[grade]
        
        conditions = [
            quant_metrics['mutual_avg_score'] >= criteria['score'],
            quant_metrics['score_balance'] >= criteria['balance'],
            quant_metrics['total_responses'] >= criteria['responses'],
            qual_metrics['emotion_score'] >= criteria['emotion'],
            quant_metrics['continuity'] >= criteria['continuity']
        ]
        
        if all(conditions):
            reasons = [
                f"평균점수 {quant_metrics['mutual_avg_score']:.1f}점",
                f"점수균형 {quant_metrics['score_balance']:.1f}%",
                f"응답수 {quant_metrics['total_responses']}건",
                f"감정점수 {qual_metrics['emotion_score']:.2f}",
                f"지속성 {quant_metrics['continuity']:.2f}"
            ]
            return grade, " | ".join(reasons)
    
    return 'D', f"기준 미달 (점수: {quant_metrics['mutual_avg_score']:.1f}, 감정: {qual_metrics['emotion_score']:.2f})"

# ============================================================================
# 📝 개선 포인트 제안
# ============================================================================

def suggest_improvements(quant_metrics, qual_metrics, grade):
    """
    관계 품질 분석 결과를 바탕으로 개선 포인트를 제안합니다.
    """
    suggestions = []
    
    if grade in ['D', 'F']:
        if quant_metrics['mutual_avg_score'] < 70:
            suggestions.append("⚠️ 협업 프로세스 전반 점검 필요")
        
        if qual_metrics['negative_ratio'] > 30:
            suggestions.append("😟 부정 감정 해소를 위한 소통 강화 필요")
        
        if quant_metrics['score_balance'] < 60:
            suggestions.append("⚖️ 일방적 관계 - 상호 이해 증진 필요")
    
    elif grade in ['B', 'C']:
        if quant_metrics['response_balance'] < 70:
            suggestions.append("📊 양방향 소통 균형 개선")
        
        if qual_metrics['emotion_consistency'] < 60:
            suggestions.append("🎯 일관된 협업 경험 제공")
        
        if quant_metrics['continuity'] < 0.5:
            suggestions.append("📅 지속적 협업 관계 구축")
    
    else:  # A, S grade
        if quant_metrics['total_responses'] < 30:
            suggestions.append("📈 협업 확대 기회 탐색")
        
        if qual_metrics['emotion_score'] < 1.8:
            suggestions.append("💬 더 긍정적인 협업 경험 확산")
    
    if not suggestions:
        suggestions.append("✅ 현재 관계 품질 우수 - 현 수준 유지")
    
    return " | ".join(suggestions)

# ============================================================================
# 🔄 메인 분석 함수
# ============================================================================

def analyze_all_department_relationships():
    """
    모든 부서간 관계를 분석하고 결과를 저장합니다.
    """
    # 데이터 로드
    df = load_and_preprocess_data()
    if df is None:
        return
    
    print("\n📊 부서간 관계 분석 중...")
    
    # 상호평가 쌍 찾기
    dept_pairs = set()
    all_depts = set(df['평가_부서명'].unique()) | set(df['피평가대상 부서명'].unique())
    
    for dept_a in all_depts:
        for dept_b in all_depts:
            if dept_a != dept_b:
                # 양방향 평가가 모두 존재하는지 확인
                a_to_b_exists = len(df[(df['평가_부서명'] == dept_a) & (df['피평가대상 부서명'] == dept_b)]) > 0
                b_to_a_exists = len(df[(df['평가_부서명'] == dept_b) & (df['피평가대상 부서명'] == dept_a)]) > 0
                
                if a_to_b_exists and b_to_a_exists:
                    # 중복 방지를 위해 알파벳 순으로 정렬
                    pair = tuple(sorted([dept_a, dept_b]))
                    dept_pairs.add(pair)
    
    print(f"🔍 분석 대상 부서 쌍: {len(dept_pairs)}개")
    
    # 분석 결과 저장
    results = []
    
    for i, (dept_a, dept_b) in enumerate(dept_pairs, 1):
        if i % 50 == 0:
            print(f"   진행률: {i}/{len(dept_pairs)} ({i/len(dept_pairs)*100:.1f}%)")
        
        # 정량적 지표 계산
        quant_metrics = calculate_quantitative_metrics(df, dept_a, dept_b)
        if not quant_metrics:
            continue
            
        # 정성적 지표 계산
        qual_metrics = calculate_qualitative_metrics(df, dept_a, dept_b)
        if not qual_metrics:
            continue
        
        # 등급 분류
        grade, reason = classify_relationship_grade(quant_metrics, qual_metrics)
        
        # 개선 포인트 제안
        improvements = suggest_improvements(quant_metrics, qual_metrics, grade)
        
        # 결과 종합
        result = {
            '부서_A': dept_a,
            '부서_B': dept_b,
            '관계_등급': grade,
            '등급_사유': reason,
            'A→B_점수': quant_metrics['a_to_b_score'],
            'B→A_점수': quant_metrics['b_to_a_score'],
            '상호_평균점수': quant_metrics['mutual_avg_score'],
            '점수_균형도': quant_metrics['score_balance'],
            'A→B_응답수': quant_metrics['a_to_b_responses'],
            'B→A_응답수': quant_metrics['b_to_a_responses'],
            '총_응답수': quant_metrics['total_responses'],
            '응답_균형도': quant_metrics['response_balance'],
            '협업_지속성': quant_metrics['continuity'],
            '점수_일관성': quant_metrics['consistency_score'],
            '데이터_신뢰도': quant_metrics['reliability_score'],
            '감정_점수': qual_metrics['emotion_score'],
            '감정_강도': qual_metrics['emotion_intensity'],
            '감정_일관성': qual_metrics['emotion_consistency'],
            '긍정_비율': qual_metrics['positive_ratio'],
            '부정_비율': qual_metrics['negative_ratio'],
            '개선_포인트': improvements
        }
        
        results.append(result)
    
    # 결과 저장
    if results:
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values(['관계_등급', '상호_평균점수'], ascending=[True, False])
        
        # 엑셀 파일로 저장
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            # 전체 결과
            results_df.to_excel(writer, sheet_name='전체_관계분석', index=False)
            
            # 등급별 분류
            for grade in ['S', 'A', 'B', 'C', 'D', 'F']:
                grade_data = results_df[results_df['관계_등급'] == grade]
                if not grade_data.empty:
                    grade_data.to_excel(writer, sheet_name=f'{grade}등급_관계', index=False)
        
        print(f"\n🎉 분석 완료! 결과가 '{OUTPUT_FILE}' 파일로 저장되었습니다.")
        
        # 결과 요약
        print(f"\n📈 관계 품질 분석 결과:")
        grade_counts = results_df['관계_등급'].value_counts()
        for grade in ['S', 'A', 'B', 'C', 'D', 'F']:
            count = grade_counts.get(grade, 0)
            print(f"   - {grade}등급: {count}개 관계 ({count/len(results_df)*100:.1f}%)")
        
        # 우수/문제 관계 하이라이트
        excellent = len(results_df[results_df['관계_등급'].isin(['S', 'A'])])
        problematic = len(results_df[results_df['관계_등급'].isin(['D', 'F'])])
        
        print(f"\n🌟 우수한 관계: {excellent}개 ({excellent/len(results_df)*100:.1f}%)")
        print(f"⚠️ 개선 필요 관계: {problematic}개 ({problematic/len(results_df)*100:.1f}%)")
        
    else:
        print("\n⚠️ 분석할 상호평가 데이터가 없습니다.")

def analyze_temporal_relationships():
    """
    시계열 관계 변화 분석을 수행합니다.
    """
    # 데이터 로드
    df = load_and_preprocess_data()
    if df is None:
        return
    
    print("\n📈 시계열 관계 변화 분석 중...")
    
    # 상호평가 쌍 찾기 (기존과 동일)
    dept_pairs = set()
    all_depts = set(df['평가_부서명'].unique()) | set(df['피평가대상 부서명'].unique())
    
    for dept_a in all_depts:
        for dept_b in all_depts:
            if dept_a != dept_b:
                a_to_b_exists = len(df[(df['평가_부서명'] == dept_a) & (df['피평가대상 부서명'] == dept_b)]) > 0
                b_to_a_exists = len(df[(df['평가_부서명'] == dept_b) & (df['피평가대상 부서명'] == dept_a)]) > 0
                
                if a_to_b_exists and b_to_a_exists:
                    pair = tuple(sorted([dept_a, dept_b]))
                    dept_pairs.add(pair)
    
    print(f"🔍 시계열 분석 대상 부서 쌍: {len(dept_pairs)}개")
    
    # 시계열 분석 결과 저장
    temporal_results = []
    alert_results = []
    
    for i, (dept_a, dept_b) in enumerate(dept_pairs, 1):
        if i % 100 == 0:
            print(f"   진행률: {i}/{len(dept_pairs)} ({i/len(dept_pairs)*100:.1f}%)")
        
        # 시계열 트렌드 분석
        trend_analysis = analyze_relationship_trends(df, dept_a, dept_b)
        if not trend_analysis:
            continue
        
        # 패턴 분류
        pattern_type, pattern_desc = classify_trend_pattern(trend_analysis)
        
        # 조기 경보
        alert_level, alert_msg = generate_trend_alert(trend_analysis, trend_analysis['yearly_data'])
        
        # 연도별 상세 데이터 준비
        yearly_scores = []
        yearly_emotions = []
        yearly_responses = []
        
        for year in ['2022', '2023', '2024', '2025']:
            if year in trend_analysis['yearly_data']:
                data = trend_analysis['yearly_data'][year]
                yearly_scores.append(f"{year}:{data['mutual_avg_score']:.1f}")
                yearly_emotions.append(f"{year}:{data['emotion_score']:.2f}")
                yearly_responses.append(f"{year}:{data['total_responses']}")
            else:
                yearly_scores.append(f"{year}:N/A")
                yearly_emotions.append(f"{year}:N/A")
                yearly_responses.append(f"{year}:N/A")
        
        # 시계열 결과
        temporal_result = {
            '부서_A': dept_a,
            '부서_B': dept_b,
            '변화_패턴': pattern_type,
            '패턴_설명': pattern_desc,
            '점수_기울기': trend_analysis['score_trend'],
            '최근_개선도': trend_analysis['recent_improvement'],
            '점수_변동성': trend_analysis['score_volatility'],
            '데이터_연속성': trend_analysis['data_continuity'],
            '연도별_점수': ' | '.join(yearly_scores),
            '연도별_감정': ' | '.join(yearly_emotions),
            '연도별_응답수': ' | '.join(yearly_responses),
            '경보_수준': alert_level,
            '경보_메시지': alert_msg
        }
        
        temporal_results.append(temporal_result)
        
        # 경보가 필요한 관계는 별도 수집
        if alert_level in ['urgent', 'warning']:
            alert_results.append(temporal_result)
    
    # 결과 저장
    if temporal_results:
        # 기존 결과 파일에 시계열 시트 추가
        temporal_df = pd.DataFrame(temporal_results)
        temporal_df = temporal_df.sort_values(['경보_수준', '점수_기울기'], ascending=[True, True])
        
        # 패턴별 분류
        pattern_summary = temporal_df['변화_패턴'].value_counts()
        alert_summary = temporal_df['경보_수준'].value_counts()
        
        # 엑셀 파일 업데이트
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            # 시계열 분석 전체 결과
            temporal_df.to_excel(writer, sheet_name='시계열_관계변화', index=False)
            
            # 패턴별 분류
            improving_data = temporal_df[temporal_df['변화_패턴'].isin(['improving', 'recovering'])]
            if not improving_data.empty:
                improving_data.to_excel(writer, sheet_name='개선_추세_관계', index=False)
            
            declining_data = temporal_df[temporal_df['변화_패턴'].isin(['declining'])]
            if not declining_data.empty:
                declining_data.to_excel(writer, sheet_name='악화_추세_관계', index=False)
            
            # 경보 대상
            if alert_results:
                alert_df = pd.DataFrame(alert_results)
                alert_df.to_excel(writer, sheet_name='조기_경보_대상', index=False)
        
        print(f"\n🎉 시계열 분석 완료! 결과가 '{OUTPUT_FILE}' 파일에 추가되었습니다.")
        
        # 결과 요약
        print(f"\n📈 시계열 분석 결과:")
        print(f"   - 분석 대상: {len(temporal_results)}개 관계")
        
        print(f"\n🔄 변화 패턴 분포:")
        for pattern, count in pattern_summary.items():
            pattern_names = {
                'improving': '지속적 개선',
                'declining': '지속적 악화', 
                'recovering': '회복 중',
                'stable': '안정적',
                'volatile': '변동성 높음',
                'neutral': '보통 수준',
                'insufficient_data': '데이터 부족'
            }
            print(f"   - {pattern_names.get(pattern, pattern)}: {count}개 ({count/len(temporal_results)*100:.1f}%)")
        
        print(f"\n🚨 조기 경보 현황:")
        for alert, count in alert_summary.items():
            alert_names = {
                'urgent': '🚨 긴급',
                'warning': '⚠️ 주의',
                'improving': '📈 개선',
                'excellent': '⭐ 모범',
                'normal': '✅ 정상'
            }
            print(f"   - {alert_names.get(alert, alert)}: {count}개 ({count/len(temporal_results)*100:.1f}%)")
        
        # 주요 발견사항
        urgent_count = len(temporal_df[temporal_df['경보_수준'] == 'urgent'])
        improving_count = len(temporal_df[temporal_df['변화_패턴'].isin(['improving', 'recovering'])])
        
        print(f"\n💡 주요 발견사항:")
        print(f"   - 긴급 개입 필요: {urgent_count}개 관계")
        print(f"   - 개선 추세: {improving_count}개 관계")
        
    else:
        print("\n⚠️ 시계열 분석할 데이터가 없습니다.")

if __name__ == "__main__":
    print("=" * 80)
    print("🏥 서울아산병원 부서간 관계 분석 시스템")
    print("=" * 80)
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "temporal":
        # 시계열 분석만 실행
        analyze_temporal_relationships()
    else:
        # 1. 기본 관계 분석
        analyze_all_department_relationships()
        
        print("\n" + "=" * 80)
        
        # 2. 시계열 관계 변화 분석
        analyze_temporal_relationships()