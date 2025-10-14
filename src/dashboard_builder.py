#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드 빌더 (간소화 버전)

4개의 대시보드 스크립트를 하나로 통합한 간단한 시스템
초보자도 쉽게 이해하고 수정할 수 있도록 설계됨

사용법:
    python dashboard_builder.py integrated     # 기간 통합
    python dashboard_builder.py split          # 상하반기 분할
    python dashboard_builder.py departments    # 부서별 리포트
    python dashboard_builder.py standalone     # 독립형 (인터넷 불필요)

작성일: 2025-01-14
버전: 1.0
"""

import pandas as pd
import plotly.graph_objects as go
import re
import ast
import json
import sys
import importlib.util
from pathlib import Path
from datetime import datetime


# ============================================================================
# 상수 정의 (원본 대시보드 호환)
# ============================================================================

# 원본 Excel 컬럼명
EXCEL_COLUMNS = [
    'response_id', '설문시행연도', '평가_부서명', '평가_부서명_원본', '평가_Unit명', '평가_부문',
    '피평가대상 부서명', '피평가대상_부서명_원본', '피평가대상 UNIT명', '피평가대상 부문',
    '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.',
    '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.',
    '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.',
    '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.',
    '전반적으로 ○○과의 협업에 대해 만족한다.',
    '종합점수', '극단값', '결측값', '협업 유형', '협업 후기', '정제된_텍스트',
    '비식별_처리', '감정_분류', '감정_강도_점수', '핵심_키워드', '의료_맥락', '신뢰도_점수'
]

# 점수 컬럼 (차트에 사용)
SCORE_COLUMNS = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수']

# JSON 출력용 컬럼
JSON_OUTPUT_COLUMNS = [
    '설문시행연도', '평가부서', '피평가부문', '피평가부서', '피평가Unit',
    '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수',
    '정제된_텍스트', '감정_분류', '핵심_키워드'
]

# 결측값 처리 설정
FILL_NA_COLUMNS = ['피평가부문', '피평가부서', '피평가Unit', '정제된_텍스트']
EXCLUDE_DEPARTMENTS = ['미분류', '윤리경영실']
EXCLUDE_TEAMS = ['내분비외과']


# ============================================================================
# 유틸리티 함수 (원본 호환)
# ============================================================================

def log_message(message, level="INFO"):
    """로그 메시지 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    icon = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "📝")
    print(f"[{timestamp}] {icon} {level}: {message}")


def safe_literal_eval(s):
    """
    문자열을 안전하게 파이썬 리터럴(리스트)로 변환

    Args:
        s: 변환할 문자열 (예: "['키워드1', '키워드2']")

    Returns:
        list: 변환된 리스트 또는 빈 리스트
    """
    if isinstance(s, str) and s.startswith('[') and s.endswith(']'):
        try:
            return ast.literal_eval(s)
        except (ValueError, SyntaxError):
            return []
    return []


# ============================================================================
# Phase 1.1: 데이터 로딩 함수
# ============================================================================

def load_data(file_path):
    """
    Excel 파일 로드 및 기본 검증 (원본 호환)

    Args:
        file_path (str): Excel 파일 경로

    Returns:
        pd.DataFrame: 로드된 데이터프레임

    Raises:
        FileNotFoundError: 파일이 없을 때
        ValueError: 필수 컬럼이 없을 때
    """
    try:
        log_message("📁 엑셀 데이터 로드 시작")

        # 파일 존재 확인
        if not Path(file_path).exists():
            raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {file_path}")

        # 엑셀 파일 로드
        df = pd.read_excel(file_path)
        log_message(f"✅ 원본 데이터 로드 완료: {len(df):,}행 × {len(df.columns)}열")

        # 컬럼 수 검증
        if len(df.columns) != len(EXCEL_COLUMNS):
            log_message(f"⚠️ 컬럼 수 불일치: 예상 {len(EXCEL_COLUMNS)}개, 실제 {len(df.columns)}개", "WARNING")

        # 컬럼명 설정
        df.columns = EXCEL_COLUMNS
        log_message("📋 컬럼명 설정 완료")

        # 대시보드 호환성을 위한 컬럼명 매핑
        column_mapping = {
            '설문시행연도': '설문시행연도',
            '평가_부서명': '평가부서',
            '평가_부문': '평가부문',
            '피평가대상 부서명': '피평가부서',
            '피평가대상 부문': '피평가부문',
            '피평가대상 UNIT명': '피평가Unit',
            '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.': '존중배려',
            '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.': '정보공유',
            '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.': '명확처리',
            '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.': '태도개선',
            '전반적으로 ○○과의 협업에 대해 만족한다.': '전반만족',
            '종합점수': '종합점수',
            '협업 후기': '협업후기'
        }

        # 컬럼명 변경
        df = df.rename(columns=column_mapping)
        log_message("🔄 컬럼명 매핑 완료")

        return df

    except FileNotFoundError as e:
        log_message(str(e), "ERROR")
        raise
    except Exception as e:
        log_message(f"데이터 로드 중 오류 발생: {str(e)}", "ERROR")
        raise


def preprocess_data_types(df, split_2025_period=False):
    """
    데이터 타입 변환 및 기본 전처리 (원본 호환)

    Args:
        df (pd.DataFrame): 원본 데이터프레임
        split_2025_period (bool): 2025년 데이터를 상하반기로 분할할지 여부

    Returns:
        pd.DataFrame: 타입 변환된 데이터프레임
    """
    log_message("🔄 데이터 타입 변환 시작")

    # 설문시행연도를 문자열로 변환
    df['설문시행연도'] = df['설문시행연도'].astype(str)

    # 점수 컬럼들을 숫자형으로 변환
    for col in SCORE_COLUMNS:
        if col in df.columns:
            original_count = df[col].notna().sum()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            converted_count = df[col].notna().sum()
            if original_count != converted_count:
                log_message(f"⚠️ {col}: {original_count - converted_count}개 값이 숫자 변환 실패", "WARNING")

    # 핵심 키워드 컬럼 전처리 (문자열 → 리스트)
    if '핵심_키워드' in df.columns:
        df['핵심_키워드'] = df['핵심_키워드'].apply(safe_literal_eval)
        log_message("🔍 핵심 키워드 파싱 완료")

    # 기간_표시 컬럼 생성 (상하반기 분할 옵션)
    if split_2025_period and 'response_id' in df.columns:
        def parse_period_from_response_id(response_id):
            """
            response_id에서 연도와 반기를 추출하여 기간 표시 생성
            - 2022년~2024년: '2022년', '2023년', '2024년' (반기 구분 없이)
            - 2025년: '2025년 상반기', '2025년 하반기' (반기 구분)
            """
            try:
                parts = str(response_id).split('_')
                if len(parts) >= 2:
                    year = parts[0]
                    period = parts[1]

                    # 2025년만 상반기/하반기로 구분
                    if year == "2025":
                        period_name = "상반기" if period == "1" else "하반기"
                        return f"{year}년 {period_name}"
                    else:
                        # 2022~2024년은 반기 구분 없이 연도만 표시
                        return f"{year}년"
                return str(response_id)
            except:
                return str(response_id)

        df['기간_표시'] = df['response_id'].apply(parse_period_from_response_id)
        log_message("📅 기간 표시 컬럼 생성 완료 (2025년만 상반기/하반기 구분)")
    else:
        df['기간_표시'] = df['설문시행연도']

    log_message("✅ 데이터 타입 변환 완료")
    return df


def clean_data(df):
    """
    데이터 정제 및 품질 관리 (원본 호환)

    Args:
        df (pd.DataFrame): 전처리된 데이터프레임

    Returns:
        pd.DataFrame: 정제된 데이터프레임
    """
    log_message("🧹 데이터 정제 시작")
    original_count = len(df)

    # 1. 부문 기준 제외할 값들 필터링
    for exclude_dept in EXCLUDE_DEPARTMENTS:
        condition = (df['평가부문'] != exclude_dept) & (df['피평가부문'] != exclude_dept)
        df = df[condition]

    division_excluded_count = original_count - len(df)
    if division_excluded_count > 0:
        log_message(f"🗑️ 부문 기준 제외된 데이터: {division_excluded_count}행")

    # 2. 부서 기준 제외할 값들 필터링
    current_count = len(df)
    for exclude_team in EXCLUDE_TEAMS:
        condition = (df['평가부서'] != exclude_team) & (df['피평가부서'] != exclude_team)
        df = df[condition]

    team_excluded_count = current_count - len(df)
    if team_excluded_count > 0:
        log_message(f"🗑️ 부서 기준 제외된 데이터: {team_excluded_count}행")

    # 3. 종합점수 결측값 제거
    df = df.dropna(subset=['종합점수'])

    # 4. 결측값 처리 (지정된 컬럼들을 'N/A'로 채움)
    for col in FILL_NA_COLUMNS:
        if col in df.columns:
            na_count = df[col].isna().sum()
            if na_count > 0:
                df[col] = df[col].fillna('N/A')
                log_message(f"📝 {col}: {na_count}개 결측값을 'N/A'로 처리")

    final_count = len(df)
    log_message(f"✅ 데이터 정제 완료: {original_count:,}행 → {final_count:,}행")
    return df


# ============================================================================
# Phase 1.2: 기간 파싱 함수
# ============================================================================

def parse_period(response_id, mode='integrated'):
    """
    response_id에서 기간 정보 추출

    Args:
        response_id (str): "2025_1_123" 형식의 응답 ID
        mode (str): 'integrated' (연도만) 또는 'split' (상하반기 구분)

    Returns:
        str: 파싱된 기간 문자열 (예: "2025년", "2025년 상반기")

    Examples:
        >>> parse_period("2024_1_123", "integrated")
        "2024년"
        >>> parse_period("2025_1_456", "split")
        "2025년 상반기"
        >>> parse_period("2025_2_789", "split")
        "2025년 하반기"
    """
    try:
        # response_id를 underscore로 분리
        parts = str(response_id).split('_')

        if len(parts) < 2:
            return '미분류'

        year = parts[0]
        period = parts[1]

        # split 모드이고 2025년인 경우만 상하반기 구분
        if mode == 'split' and year == '2025':
            half = '상반기' if period == '1' else '하반기'
            return f"{year}년 {half}"
        else:
            return f"{year}년"

    except Exception:
        return '미분류'


# ============================================================================
# Phase 1.3: 데이터 전처리 함수
# ============================================================================

def process_data(df, mode='integrated'):
    """
    데이터 전처리 (부서명 정제, 기간 파싱, 텍스트 정제)

    Args:
        df (pd.DataFrame): 원본 데이터프레임
        mode (str): 기간 표시 모드 ('integrated' 또는 'split')

    Returns:
        pd.DataFrame: 전처리된 데이터프레임
    """
    print(f"⚙️ 데이터 처리 (모드: {mode})")
    df = df.copy()

    # 1. 설문시행연도를 문자열로 변환
    df['설문시행연도'] = df['설문시행연도'].astype(str)

    # 2. 부서명 정제 (공백 제거, 결측값 처리)
    dept_cols = ['평가_부서명', '피평가대상 부서명']
    for col in dept_cols:
        if col in df.columns:
            df[col] = df[col].str.strip().fillna('미분류')

    # 3. 기간 파싱 (response_id에서 기간 추출)
    df['기간'] = df['response_id'].apply(lambda x: parse_period(x, mode))
    print(f"   기간 파싱 완료: {df['기간'].nunique()}개 고유 기간")

    # 4. 텍스트 컬럼 정제 (결측값 처리)
    text_cols = ['협업후기', '정제된_텍스트']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').str.strip()

    # 5. 점수 컬럼을 숫자형으로 변환
    score_cols = ['종합점수', '감정_강도_점수', '신뢰도_점수']
    for col in score_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 6. 종합점수 결측값 제거 (가장 중요한 지표)
    before_count = len(df)
    df = df.dropna(subset=['종합점수'])
    removed_count = before_count - len(df)
    if removed_count > 0:
        print(f"   종합점수 결측값 제거: {removed_count}행")

    print(f"✅ 처리 완료: {len(df):,}행")
    return df


# ============================================================================
# Phase 1.4: 집계 함수
# ============================================================================

def aggregate_by_period(df):
    """
    기간별 집계

    Args:
        df (pd.DataFrame): 전처리된 데이터프레임

    Returns:
        pd.DataFrame: 기간별 집계 결과
    """
    # 기간별 집계 (평균, 표준편차, 개수)
    result = df.groupby('기간').agg({
        '협업후기': 'count',  # 응답 수
        '감정_강도_점수': ['mean', 'std'],
        '신뢰도_점수': 'mean'
    }).reset_index()

    # 컬럼명 평탄화
    result.columns = ['기간', '응답수', '감정_평균', '감정_표준편차', '신뢰도_평균']

    return result


def aggregate_by_department(df):
    """
    부서별 집계

    Args:
        df (pd.DataFrame): 전처리된 데이터프레임

    Returns:
        pd.DataFrame: 부서별 집계 결과
    """
    dept_stats = []

    # 부서별로 순회하면서 통계 계산
    for dept in df['피평가대상 부서명'].unique():
        dept_df = df[df['피평가대상 부서명'] == dept]

        # 부서별 통계 계산
        stats = {
            '부서명': dept,
            '총_응답수': len(dept_df),
            '긍정_비율': (dept_df['감정_분류'] == '긍정').mean() * 100,
            '평균_감정강도': dept_df['감정_강도_점수'].mean(),
            '평균_신뢰도': dept_df['신뢰도_점수'].mean(),
            '평균_종합점수': dept_df['종합점수'].mean()
        }
        dept_stats.append(stats)

    # DataFrame으로 변환
    result = pd.DataFrame(dept_stats)

    # 총 응답수 기준으로 정렬
    result = result.sort_values('총_응답수', ascending=False)

    return result


# ============================================================================
# 원본 대시보드 집계 함수 (완전판)
# ============================================================================

def calculate_aggregated_data(df):
    """
    섹션 1-4용 집계 데이터 미리 계산 (원본 호환)
    원본 개별 응답 데이터 대신 계산된 통계만 저장

    Args:
        df (pd.DataFrame): 전체 데이터프레임

    Returns:
        dict: 집계된 통계 데이터
    """
    log_message("📊 집계 데이터 계산 시작")

    aggregated = {
        "hospital_yearly": {},
        "division_yearly": {},
        "division_comparison": {},
        "team_ranking": {},
        "metadata": {
            "calculation_date": datetime.now().isoformat(),
            "total_responses": len(df),
            "security_level": "AGGREGATED_ONLY"
        }
    }

    # 1. [전체] 연도별 문항 점수
    for year in df['설문시행연도'].unique():
        if pd.notna(year):
            year_data = df[df['설문시행연도'] == year]
            aggregated["hospital_yearly"][str(year)] = {
                col: float(year_data[col].mean()) if col in year_data.columns else 0.0
                for col in SCORE_COLUMNS
            }
            aggregated["hospital_yearly"][str(year)]["응답수"] = len(year_data)

    # 2. 부문별 종합 점수 (연도별 부문 비교)
    for year in df['설문시행연도'].unique():
        if pd.notna(year):
            year_str = str(year)
            year_data = df[df['설문시행연도'] == year]

            aggregated["division_comparison"][year_str] = {}

            # 모든 부문별 평균 계산
            for division in df['피평가부문'].unique():
                if pd.notna(division) and division != 'N/A':
                    div_year_data = year_data[year_data['피평가부문'] == division]
                    if len(div_year_data) > 0:
                        aggregated["division_comparison"][year_str][division] = {
                            col: float(div_year_data[col].mean()) if col in div_year_data.columns else 0.0
                            for col in SCORE_COLUMNS
                        }
                        aggregated["division_comparison"][year_str][division]["응답수"] = len(div_year_data)

    # 3. 소속 부문 결과 ([부문별] 연도별 문항 점수)
    for division in df['피평가부문'].unique():
        if pd.notna(division) and division != 'N/A':
            div_data = df[df['피평가부문'] == division]
            aggregated["division_yearly"][division] = {}
            for year in div_data['설문시행연도'].unique():
                if pd.notna(year):
                    year_data = div_data[div_data['설문시행연도'] == year]
                    aggregated["division_yearly"][division][str(year)] = {
                        col: float(year_data[col].mean()) if col in year_data.columns else 0.0
                        for col in SCORE_COLUMNS
                    }
                    aggregated["division_yearly"][division][str(year)]["응답수"] = len(year_data)

    # 4. 부문별 팀 점수 순위
    for division in df['피평가부문'].unique():
        if pd.notna(division) and division != 'N/A':
            div_data = df[df['피평가부문'] == division]
            for year in div_data['설문시행연도'].unique():
                if pd.notna(year):
                    year_str = str(year)
                    year_data = div_data[div_data['설문시행연도'] == year]
                    dept_scores = []

                    for dept in year_data['피평가부서'].unique():
                        if pd.notna(dept):
                            dept_data = year_data[year_data['피평가부서'] == dept]
                            avg_score = dept_data['종합점수'].mean() if len(dept_data) > 0 else 0.0
                            dept_scores.append({
                                "department": dept,
                                "division": division,
                                "score": round(float(avg_score), 1),
                                "count": len(dept_data)
                            })

                    # 점수 순으로 정렬하고 순위 부여
                    dept_scores.sort(key=lambda x: x["score"], reverse=True)
                    for i, dept in enumerate(dept_scores):
                        dept["rank"] = i + 1

                    # 부문별로 구분하여 저장
                    if year_str not in aggregated["team_ranking"]:
                        aggregated["team_ranking"][year_str] = {}
                    aggregated["team_ranking"][year_str][division] = dept_scores

    log_message(f"✅ 집계 데이터 계산 완료: {len(aggregated['hospital_yearly'])}년치 데이터")
    return aggregated


def prepare_json_data(df):
    """
    대시보드용 JSON 데이터 준비 (상세 분석용 원시 데이터)

    Args:
        df (pd.DataFrame): 정제된 데이터프레임

    Returns:
        str: JSON 형태의 데이터
    """
    log_message("📄 JSON 데이터 준비 시작")

    # 필요한 컬럼만 선택
    available_columns = [col for col in JSON_OUTPUT_COLUMNS if col in df.columns]
    missing_columns = [col for col in JSON_OUTPUT_COLUMNS if col not in df.columns]

    if missing_columns:
        log_message(f"⚠️ 누락된 컬럼: {missing_columns}", "WARNING")

    # 데이터 복사 및 JSON 변환
    df_for_json = df[available_columns].copy()

    # JSON 변환 (한글 유지)
    data_json = df_for_json.to_json(orient='records', force_ascii=False)

    log_message(f"✅ JSON 데이터 준비 완료: {len(df_for_json):,}건")
    return data_json


# ============================================================================
# Phase 2: 차트 생성 함수
# ============================================================================

def create_sentiment_chart(df, title="감정 분포"):
    """
    감정 분포 파이 차트 생성

    Args:
        df (pd.DataFrame): 전처리된 데이터프레임
        title (str): 차트 제목

    Returns:
        str: Plotly HTML (CDN 방식)
    """
    # 감정 분류 집계
    counts = df['감정_분류'].value_counts()

    # 색상 매핑 (긍정: 초록, 부정: 빨강, 중립: 회색)
    colors = {
        '긍정': '#27ae60',  # 초록
        '부정': '#e74c3c',  # 빨강
        '중립': '#95a5a6'   # 회색
    }
    chart_colors = [colors.get(label, '#95a5a6') for label in counts.index]

    # 파이 차트 생성
    fig = go.Figure(data=[go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.3,  # 도넛 차트
        marker=dict(colors=chart_colors),
        textinfo='label+percent',
        textposition='auto'
    )])

    # 레이아웃 설정
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        height=400,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
    )

    # HTML로 변환 (CDN 방식)
    return fig.to_html(include_plotlyjs='cdn', full_html=False)


def create_trend_chart(period_df, title="기간별 감정 트렌드"):
    """
    기간별 트렌드 라인 차트 생성

    Args:
        period_df (pd.DataFrame): aggregate_by_period() 결과
        title (str): 차트 제목

    Returns:
        str: Plotly HTML (CDN 방식)
    """
    # 기간 순서 정렬 (문자열 정렬이지만 "YYYY년" 형식이므로 자연스럽게 정렬됨)
    period_df = period_df.sort_values('기간')

    # 라인 차트 생성
    fig = go.Figure()

    # 감정 평균 라인
    fig.add_trace(go.Scatter(
        x=period_df['기간'],
        y=period_df['감정_평균'],
        mode='lines+markers',
        name='감정 평균',
        line=dict(color='#3498db', width=3),
        marker=dict(size=10, symbol='circle'),
        hovertemplate='<b>%{x}</b><br>감정 평균: %{y:.2f}<extra></extra>'
    ))

    # 레이아웃 설정
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        xaxis_title="기간",
        yaxis_title="감정 강도 점수",
        height=400,
        hovermode='x unified',
        showlegend=True
    )

    # HTML로 변환 (CDN 방식)
    return fig.to_html(include_plotlyjs='cdn', full_html=False)


def create_department_chart(dept_stats, title="부서별 긍정 비율", top_n=20):
    """
    부서별 긍정 비율 가로 막대 차트 생성

    Args:
        dept_stats (pd.DataFrame): aggregate_by_department() 결과
        title (str): 차트 제목
        top_n (int): 표시할 상위 부서 수

    Returns:
        str: Plotly HTML (CDN 방식)
    """
    # 긍정 비율 기준으로 정렬하고 상위 N개만 선택
    dept_stats = dept_stats.sort_values('긍정_비율', ascending=True).tail(top_n)

    # 가로 막대 차트 생성
    fig = go.Figure(data=[go.Bar(
        x=dept_stats['긍정_비율'],
        y=dept_stats['부서명'],
        orientation='h',  # 가로 방향
        marker=dict(
            color=dept_stats['긍정_비율'],
            colorscale='RdYlGn',  # 빨강-노랑-초록 그라데이션
            showscale=True,
            colorbar=dict(title="긍정 비율 (%)")
        ),
        hovertemplate='<b>%{y}</b><br>긍정 비율: %{x:.1f}%<extra></extra>'
    )])

    # 레이아웃 설정
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        xaxis_title="긍정 비율 (%)",
        yaxis_title="부서명",
        height=max(400, len(dept_stats) * 25),  # 동적 높이 (부서 수에 따라)
        showlegend=False
    )

    # HTML로 변환 (CDN 방식)
    return fig.to_html(include_plotlyjs='cdn', full_html=False)


# ============================================================================
# Phase 3: HTML 생성 함수
# ============================================================================

def build_html(charts, stats, title="대시보드"):
    """
    HTML 문서 생성

    Args:
        charts (list): Plotly HTML 차트 리스트
        stats (dict): 통계 딕셔너리 {'total': 1000, 'positive_pct': 75.5, ...}
        title (str): 대시보드 제목

    Returns:
        str: 완성된 HTML 문자열
    """
    from datetime import datetime

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header p {{
            opacity: 0.9;
            font-size: 0.95em;
        }}

        .content {{
            padding: 40px;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        }}

        .stat-card strong {{
            display: block;
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .section-title {{
            font-size: 1.8em;
            color: #2c3e50;
            margin: 40px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .chart {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
            border-top: 1px solid #ecf0f1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <p>생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</p>
        </div>

        <div class="content">
            <h2 class="section-title">📈 요약 통계</h2>
            <div class="summary">
                <div class="stat-card">
                    <strong>총 응답 수</strong>
                    <div class="value">{stats.get('total', 0):,}</div>
                </div>
                <div class="stat-card">
                    <strong>긍정 비율</strong>
                    <div class="value">{stats.get('positive_pct', 0):.1f}%</div>
                </div>
                <div class="stat-card">
                    <strong>평균 감정 강도</strong>
                    <div class="value">{stats.get('avg_intensity', 0):.2f}</div>
                </div>
            </div>

            <h2 class="section-title">📊 시각화</h2>
            {''.join([f'<div class="chart">{chart}</div>' for chart in charts])}
        </div>

        <div class="footer">
            <p>🤖 Dashboard Builder v1.0 | 의료진 협업 피드백 분석 시스템</p>
        </div>
    </div>
</body>
</html>
    """

    return html


# ============================================================================
# Phase 3.3: 메인 로직
# ============================================================================

def build_dashboard(config_name):
    """
    대시보드 생성 메인 함수

    Args:
        config_name (str): 설정 이름 ('full', 'integrated', 'split', 'departments', 'standalone')

    Returns:
        Path: 생성된 HTML 파일 경로
    """
    from .config import DASHBOARD_CONFIGS, COMMON_CONFIG, PLOTLY_JS_PATH

    # 설정 가져오기
    if config_name not in DASHBOARD_CONFIGS:
        raise ValueError(f"알 수 없는 설정: {config_name}")

    config = {**COMMON_CONFIG, **DASHBOARD_CONFIGS[config_name]}

    print(f"\n{'='*60}")
    print(f"🚀 대시보드 생성: {config['name']}")
    print(f"{'='*60}\n")

    # === 원본 완전판 모드: 원본 스크립트 사용 ===
    if config.get('use_original', False):
        print("📦 원본 스크립트 모듈 로딩...")

        # 원본 스크립트 import (config에서 지정한 경로 사용)
        original_script_path = Path(__file__).parent.parent / config['original_script']

        if not original_script_path.exists():
            raise FileNotFoundError(f"원본 스크립트를 찾을 수 없습니다: {original_script_path}")

        print(f"   경로: {config['original_script']}")

        spec = importlib.util.spec_from_file_location("original_dashboard", str(original_script_path))
        original_module = importlib.util.module_from_spec(spec)
        sys.modules["original_dashboard"] = original_module
        spec.loader.exec_module(original_module)

        print("✅ 원본 모듈 로드 완료\n")

        # split 모드는 원본 스크립트의 전체 로직 사용 (상하반기 분할 포함)
        if config['mode'] == 'split':
            print("📂 원본 스크립트의 전체 처리 로직 사용 (상하반기 분할 적용)...")

            # 원본 스크립트의 함수들 사용
            df = original_module.load_excel_data()
            df = original_module.preprocess_data_types(df)
            df = original_module.clean_data(df)

            # 원본 스크립트의 집계 및 JSON 준비 함수 사용
            aggregated_data = original_module.calculate_aggregated_data(df)
            raw_data_json = original_module.prepare_json_data(df)
        else:
            # 기타 모드는 우리의 함수 사용
            print("📂 데이터 로드 및 전처리...")
            df = load_data(config['input_file'])
            df = preprocess_data_types(df)
            df = clean_data(df)

            # 2. 집계 데이터 계산
            print("📊 집계 데이터 계산...")
            aggregated_data = calculate_aggregated_data(df)

            # 3. 원시 데이터 JSON 준비
            print("📄 JSON 데이터 준비...")
            raw_data_json = prepare_json_data(df)

        # 4. 원본 build_html 함수 사용 (모드별로 적절한 mode 전달)
        print(f"🔨 원본 HTML 생성 (모든 섹션 포함, mode={config['mode']})...")
        html = original_module.build_html(aggregated_data, raw_data_json, mode=config['mode'])

        # 5. 파일 저장
        output_path = Path(config['output_file'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding='utf-8')

        file_size = output_path.stat().st_size / (1024 * 1024)  # MB로 표시
        print(f"\n✅ 완료: {output_path}")
        print(f"   파일 크기: {file_size:.1f} MB")
        print(f"   설명: {config.get('description', '')}\n")

        return output_path

    # === 간소화 모드: 기존 로직 ===
    # 1. 데이터 로드
    df = load_data(config['input_file'])

    # 2. 데이터 처리
    df = process_data(df, mode=config.get('mode', 'integrated'))

    # 3. 통계 계산
    stats = {
        'total': len(df),
        'positive_pct': (df['감정_분류'] == '긍정').mean() * 100,
        'avg_intensity': df['감정_강도_점수'].mean()
    }

    # 4. 차트 생성
    charts = []
    chart_types = config.get('charts', ['sentiment', 'trend'])

    if 'sentiment' in chart_types:
        print("📊 감정 분포 차트 생성...")
        charts.append(create_sentiment_chart(df))

    if 'trend' in chart_types:
        print("📈 기간별 트렌드 차트 생성...")
        period_df = aggregate_by_period(df)
        charts.append(create_trend_chart(period_df))

    if 'departments' in chart_types:
        print("🏢 부서별 비교 차트 생성...")
        dept_df = aggregate_by_department(df)
        charts.append(create_department_chart(dept_df))

    # 5. HTML 생성
    print("🔨 HTML 문서 생성...")
    html = build_html(charts, stats, title=config['name'])

    # 6. Standalone 모드 처리 (필요시)
    if config.get('plotly_mode') == 'standalone':
        print("🔄 Standalone 모드로 변환...")
        html = convert_to_standalone(html, PLOTLY_JS_PATH)

    # 7. 파일 저장
    output_path = Path(config['output_file'])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')

    file_size = output_path.stat().st_size / 1024
    print(f"\n✅ 완료: {output_path}")
    print(f"   파일 크기: {file_size:.1f} KB")
    print(f"   설명: {config.get('description', '')}\n")

    return output_path


def convert_to_standalone(html, plotly_js_path):
    """
    CDN 기반 HTML을 Standalone으로 변환

    Args:
        html (str): 원본 HTML
        plotly_js_path (str): Plotly JS 파일 경로

    Returns:
        str: 변환된 HTML
    """
    import re

    # Plotly JS 읽기
    js_path = Path(plotly_js_path)
    if not js_path.exists():
        print(f"⚠️ Plotly JS 파일 없음: {plotly_js_path}")
        print("   CDN 모드로 유지합니다.")
        return html

    with open(js_path, 'r', encoding='utf-8') as f:
        plotly_js = f.read()

    # CDN 링크를 임베드된 JS로 대체
    cdn_patterns = [
        r'<script src="https://cdn\.plot\.ly/plotly-latest\.min\.js"></script>',
        r'<script src="https://cdn\.plot\.ly/plotly-[\d.]+\.min\.js"></script>',
    ]

    embedded_script = f'<script>{plotly_js}</script>'

    for pattern in cdn_patterns:
        html = re.sub(pattern, embedded_script, html, flags=re.IGNORECASE)

    return html


# ============================================================================
# Phase 4: CLI 실행 스크립트
# ============================================================================

if __name__ == "__main__":
    import sys

    # 모듈로 실행될 때는 상대 import, 직접 실행될 때는 절대 import
    try:
        from .config import DASHBOARD_CONFIGS
    except ImportError:
        # 직접 실행되는 경우
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.config import DASHBOARD_CONFIGS

    # CLI 인자 처리
    if len(sys.argv) < 2:
        print("=" * 60)
        print("📊 대시보드 빌더")
        print("=" * 60)
        print("\n사용법: python -m src.dashboard_builder [모드]\n")
        print("또는: python dashboard_builder.py [모드]\n")
        print("사용 가능한 모드:")
        for key, config in DASHBOARD_CONFIGS.items():
            print(f"  • {key:15} - {config['description']}")
        print("\n예시:")
        print("  python dashboard_builder.py full")
        print("  python dashboard_builder.py integrated")
        print()
        sys.exit(0)

    mode = sys.argv[1]

    # 대시보드 생성
    try:
        build_dashboard(mode)
        print("✨ 모든 작업이 완료되었습니다!\n")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
