#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
서울아산병원 협업 평가 대시보드 - 전체 부서 보고서 생성기

이 파일은 모든 부서에 대한 개별 보고서를 자동으로 생성합니다.
부문별로 폴더를 만들고 각 부서의 맞춤형 대시보드를 생성합니다.

📋 주요 기능:
1. 모든 부서 목록 자동 추출
2. 부문별 폴더 구조 생성
3. 부서별 맞춤 대시보드 HTML 생성
4. 배치 실행 및 진행 상황 추적

🔧 사용 방법:
- python generate_all_department_reports.py

작성자: Claude AI
버전: 1.0 (전체 부서 자동 생성판)
업데이트: 2025년 7월 14일
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import ast
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
import traceback

# ============================================================================
# 🔧 설정 및 상수 정의
# ============================================================================

# 📁 파일 경로 설정 (자동 감지)
def get_latest_text_processor_file():
    """rawdata 폴더에서 가장 최근 text_processor 결과 파일 찾기"""
    from pathlib import Path
    import glob
    
    rawdata_path = Path("rawdata")
    pattern = "2. text_processor_결과_*.xlsx"
    
    # _partial.xlsx 파일은 제외하고 검색
    files = [f for f in rawdata_path.glob(pattern) if not f.name.endswith('_partial.xlsx')]
    
    if not files:
        # 완료된 파일이 없으면 partial 파일도 포함하여 검색
        files = list(rawdata_path.glob(pattern))
    
    if files:
        # 가장 최근 파일 반환 (수정 시간 기준)
        latest_file = max(files, key=lambda x: x.stat().st_mtime)
        return str(latest_file)
    else:
        return "rawdata/2. text_processor_결과_20250710_153008.xlsx"  # 기본값

INPUT_DATA_FILE = get_latest_text_processor_file()  # 입력 데이터 파일 (자동 감지)
OUTPUT_BASE_DIR = "department_reports"  # 출력 기본 디렉토리

# 📊 데이터 컬럼 정의 (실제 데이터 구조와 일치)
EXCEL_COLUMNS = [
    'response_id', '설문시행연도', '평가_부서명', '평가_부서명_원본', '평가_Unit명', '평가_부문',
    '피평가대상 부서명', '피평가대상_부서명_원본', '피평가대상 UNIT명', '피평가대상 부문',
    '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.',
    '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.',
    '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.',
    '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.',
    '전반적으로 ○○과의 협업에 대해 만족한다.',
    '종합점수', '극단값', '결측값', '협업 내용', '협업 내용.1', '협업 후기', '정제된_텍스트', 
    '비식별_처리', '감정_분류', '감정_강도_점수', '핵심_키워드', '의료_맥락', '신뢰도_점수'
]

# 📈 점수 항목 정의 (차트에 사용되는 점수 컬럼들)
SCORE_COLUMNS = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수']

# 🎯 JSON 출력용 컬럼 (대시보드에 필요한 컬럼들만 선택)
JSON_OUTPUT_COLUMNS = [
    '설문시행연도', '평가부서', '피평가부문', '피평가부서', '피평가Unit', 
    '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수',
    '정제된_텍스트', '감정_분류', '핵심_키워드'
]

# 📝 결측값 처리 설정
FILL_NA_COLUMNS = ['피평가부문', '피평가부서', '피평가Unit', '정제된_텍스트']  # 'N/A'로 채울 컬럼들
EXCLUDE_VALUES = ['미분류', '윤리경영실']  # 제외할 값들

# 📊 대시보드 정보
DASHBOARD_SUBTITLE = "설문 데이터: 2022년 ~ 2025년 상반기(2025년 7월 14일 기준)"

# ============================================================================
# 🛠️ 유틸리티 함수들
# ============================================================================

def log_message(message, level="INFO"):
    """로그 메시지 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 레벨별 이모지 및 색상
    level_configs = {
        "INFO": ("ℹ️", "\033[96m"),
        "SUCCESS": ("✅", "\033[92m"),
        "WARNING": ("⚠️", "\033[93m"),
        "ERROR": ("❌", "\033[91m"),
        "DEBUG": ("🔍", "\033[95m")
    }
    
    emoji, color = level_configs.get(level, ("📝", "\033[0m"))
    reset_color = "\033[0m"
    
    print(f"[{timestamp}] {emoji} {level}: {message}{reset_color}")

def safe_filename(name):
    """파일명에 안전한 문자열 생성"""
    import re
    # 파일명에 사용할 수 없는 문자들을 제거하거나 대체
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', str(name))
    safe_name = safe_name.replace(' ', '_')
    return safe_name

# ============================================================================
# 📊 데이터 처리 함수들 (기존 로직 유지)
# ============================================================================

def load_excel_data():
    """엑셀 데이터 로드"""
    log_message("📁 엑셀 데이터 로드 시작")
    
    try:
        # 엑셀 파일 로드
        df = pd.read_excel(INPUT_DATA_FILE)
        log_message(f"✅ 원본 데이터 로드 완료: {len(df):,}행 × {len(df.columns)}열")
        
        # 컬럼명 설정
        if len(df.columns) == len(EXCEL_COLUMNS):
            df.columns = EXCEL_COLUMNS
            log_message("📋 컬럼명 설정 완료")
        else:
            log_message(f"⚠️ 컬럼 수 불일치: 예상 {len(EXCEL_COLUMNS)}개, 실제 {len(df.columns)}개", "WARNING")
        
        # 컬럼명 매핑 (기존 로직 유지)
        column_mapping = {
            '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.': '존중배려',
            '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.': '정보공유',
            '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.': '명확처리',
            '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.': '태도개선',
            '전반적으로 ○○과의 협업에 대해 만족한다.': '전반만족',
            '평가_부서명': '평가부서',
            '피평가대상 부서명': '피평가부서',
            '피평가대상 UNIT명': '피평가Unit',
            '피평가대상 부문': '피평가부문'
        }
        
        df = df.rename(columns=column_mapping)
        log_message("🔄 컬럼명 매핑 완료")
        
        return df
        
    except Exception as e:
        log_message(f"❌ 데이터 로드 실패: {str(e)}", "ERROR")
        log_message(f"📁 파일 경로: {INPUT_DATA_FILE}", "ERROR")
        raise

def preprocess_data_types(df):
    """데이터 타입 변환"""
    log_message("🔄 데이터 타입 변환 시작")
    
    try:
        # 점수 컬럼들을 숫자형으로 변환
        score_columns = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수']
        for col in score_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 연도 컬럼 처리
        if '설문시행연도' in df.columns:
            df['설문시행연도'] = pd.to_numeric(df['설문시행연도'], errors='coerce')
            # 연도가 1000 미만인 경우 2000을 더함 (예: 22 -> 2022)
            df.loc[df['설문시행연도'] < 1000, '설문시행연도'] += 2000
        
        log_message("✅ 데이터 타입 변환 완료")
        return df
        
    except Exception as e:
        log_message(f"❌ 데이터 타입 변환 실패: {str(e)}", "ERROR")
        raise

def clean_data(df):
    """데이터 정제"""
    log_message("🧹 데이터 정제 시작")
    
    try:
        original_count = len(df)
        
        # 결측값 처리
        for col in FILL_NA_COLUMNS:
            if col in df.columns:
                df[col] = df[col].fillna('N/A')
        
        # 제외할 값들 필터링
        for exclude_value in EXCLUDE_VALUES:
            if '피평가부서' in df.columns:
                before_count = len(df)
                df = df[df['피평가부서'] != exclude_value]
                excluded_count = before_count - len(df)
                if excluded_count > 0:
                    log_message(f"🗑️ '{exclude_value}' 제외: {excluded_count}행")
        
        # 결측값 및 이상치 정리
        if '피평가부서' in df.columns:
            df = df[df['피평가부서'].notna()]
            df = df[df['피평가부서'] != '']
        
        excluded_count = original_count - len(df)
        exclusion_rate = (excluded_count / original_count) * 100 if original_count > 0 else 0
        
        log_message(f"🗑️ 제외된 데이터(미분류 등): {excluded_count}행 ({exclusion_rate:.1f}%)")
        log_message(f"✅ 데이터 정제 완료: {original_count:,}행 → {len(df):,}행")
        
        return df
        
    except Exception as e:
        log_message(f"❌ 데이터 정제 실패: {str(e)}", "ERROR")
        raise

# ============================================================================
# 📋 부서 관리 함수들
# ============================================================================

def get_all_departments(df):
    """모든 부서 및 부문 정보 추출"""
    log_message("📋 부서 및 부문 정보 추출 시작")
    
    try:
        # 피평가부서와 피평가부문 조합으로 부서-부문 매핑 생성
        dept_division_map = df[['피평가부서', '피평가부문']].drop_duplicates()
        dept_division_map = dept_division_map[
            (dept_division_map['피평가부서'].notna()) & 
            (dept_division_map['피평가부서'] != 'N/A') &
            (dept_division_map['피평가부문'].notna()) & 
            (dept_division_map['피평가부문'] != 'N/A')
        ]
        
        # 부문별로 부서들을 그룹화
        divisions = {}
        for _, row in dept_division_map.iterrows():
            division = row['피평가부문']
            department = row['피평가부서']
            
            if division not in divisions:
                divisions[division] = []
            
            if department not in divisions[division]:
                divisions[division].append(department)
        
        # 부문명과 부서명을 알파벳 순으로 정렬
        for division in divisions:
            divisions[division].sort(key=lambda x: x)
        
        divisions = dict(sorted(divisions.items()))
        
        total_departments = sum(len(depts) for depts in divisions.values())
        log_message(f"✅ 부서 정보 추출 완료: {len(divisions)}개 부문, {total_departments}개 부서")
        
        return divisions
        
    except Exception as e:
        log_message(f"❌ 부서 정보 추출 실패: {str(e)}", "ERROR")
        raise

def filter_data_for_department(df, department_name):
    """특정 부서에 대한 데이터 필터링 및 보안 처리"""
    log_message(f"🔒 부서별 필터링 시작: {department_name}")
    
    try:
        # 해당 부서에 대한 평가 데이터만 필터링
        filtered_df = df[df['피평가부서'] == department_name].copy()
        
        # 보안을 위한 데이터 크기 제한 (최대 1000건)
        max_records = 1000
        if len(filtered_df) > max_records:
            log_message(f"⚠️ 데이터 크기 제한: {max_records}건으로 샘플링", "WARNING")
            filtered_df = filtered_df.sample(n=max_records, random_state=42)
        
        # 보안 감소율 계산
        original_dept_data = df[df['피평가부서'] == department_name]
        reduction_rate = (1 - len(filtered_df) / len(original_dept_data)) * 100 if len(original_dept_data) > 0 else 0
        
        log_message(f"✅ 부서별 필터링 완료: {len(filtered_df)}건 (보안 감소율: {reduction_rate:.1f}%)")
        
        return filtered_df
        
    except Exception as e:
        log_message(f"❌ 부서별 필터링 실패: {str(e)}", "ERROR")
        raise

def calculate_aggregated_data(df):
    """집계 데이터 계산 (보안 강화)"""
    log_message("🔒 집계 데이터 계산 시작 (보안 강화)")
    
    try:
        # 연도별 전체 통계 (요약 정보만)
        years = sorted(df['설문시행연도'].unique())
        yearly_summary = {}
        
        for year in years:
            year_data = df[df['설문시행연도'] == year]
            yearly_summary[year] = {
                'total_responses': len(year_data),
                'avg_scores': {
                    col: round(year_data[col].mean(), 1) 
                    for col in SCORE_COLUMNS 
                    if col in year_data.columns and not year_data[col].isna().all()
                }
            }
        
        log_message(f"✅ 집계 데이터 계산 완료: {len(years)}년치 데이터")
        
        return {
            'years': years,
            'yearly_summary': yearly_summary,
            'total_records': len(df)
        }
        
    except Exception as e:
        log_message(f"❌ 집계 데이터 계산 실패: {str(e)}", "ERROR")
        raise

# ============================================================================
# 🏗️ HTML 생성 함수들
# ============================================================================

def build_department_html(department_name, division_name, filtered_data_json, aggregated_data):
    """부서별 맞춤 HTML 대시보드 생성"""
    log_message(f"🔒 보안 강화 HTML 생성: {department_name}")
    
    try:
        # JSON 데이터를 하이브리드 구조로 변환
        hybrid_data = {
            'rawData': filtered_data_json,
            'aggregated': aggregated_data
        }
        
        # JavaScript용 데이터를 JSON으로 변환
        hybrid_data_json = json.dumps(hybrid_data, ensure_ascii=False, default=str)
        
        # 대시보드 제목 동적 생성
        dashboard_title = f"서울아산병원 협업 평가 대시보드 - {department_name}"
        
        return build_html_template(hybrid_data_json, dashboard_title, department_name)
        
    except Exception as e:
        log_message(f"❌ HTML 생성 실패: {str(e)}", "ERROR")
        raise

def build_html_template(hybrid_data_json, dashboard_title, department_name):
    """HTML 템플릿 생성 (기존 디자인과 기능 완전 유지)"""
    
    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>서울아산병원 협업 평가 대시보드</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; color: #343a40; font-size: 16px;}}
        .container {{ max-width: 1400px; margin: auto; padding: 20px; }}
        .header {{ background: linear-gradient(90deg, #4a69bd, #6a89cc); color: white; padding: 25px; text-align: center; border-radius: 0 0 10px 10px; }}
        
        /* 자동 번호 매기기 CSS */
        .container {{ counter-reset: section-counter; }}
        .section {{ counter-reset: subsection-counter; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 30px; }}
        .section h2::before {{ counter-increment: section-counter; content: counter(section-counter) ". "; color: #4a69bd; font-weight: bold; }}
        .section h3::before {{ counter-increment: subsection-counter; content: counter(section-counter) "." counter(subsection-counter) " "; color: #6a89cc; font-weight: bold; }}
        
        h1, h2, h3 {{ margin: 0; padding: 0; }}
        h2 {{ color: #4a69bd; border-bottom: 3px solid #6a89cc; padding-bottom: 10px; margin-top: 20px; margin-bottom: 20px; }}
        h3 {{ color: #555; margin-top: 30px; margin-bottom: 15px;}}
        
        /* 파트 구분 스타일 */
        .part-divider {{ background: linear-gradient(90deg, #e9ecef, #6c757d, #e9ecef); height: 3px; margin: 40px 0; border-radius: 2px; }}
        .part-title {{ text-align: center; color: #6c757d; font-size: 1.2em; font-weight: bold; margin: 30px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 5px solid #6a89cc; }}
        
        .filters, .trend-filters {{ display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-end; margin-bottom: 20px;}}
        .filter-group {{ display: flex; flex-direction: column; }}
        .filter-group label {{ margin-bottom: 5px; font-weight: bold; font-size: 0.9em; }}
        .filter-group select, .filter-group input {{ padding: 8px; border-radius: 5px; border: 1px solid #ced4da; min-width: 200px; }}
        .expander-container {{ border: 1px solid #ced4da; border-radius: 5px; background-color: white; min-width: 200px; max-width: 280px; position: relative; }}
        .expander-header {{ padding: 6px 8px; background-color: #f8f9fa; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-radius: 5px; user-select: none; font-size: 13px; }}
        .expander-header:hover {{ background-color: #e9ecef; }}
        .expander-arrow {{ transition: transform 0.3s ease; font-size: 11px; }}
        .expander-arrow.expanded {{ transform: rotate(180deg); }}
        .expander-content {{ padding: 4px; display: none; max-height: 200px; overflow-y: auto; position: absolute; top: 100%; left: 0; width: 100%; background-color: white; border: 1px solid #ced4da; border-top: none; border-radius: 0 0 5px 5px; z-index: 1000; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .expander-content.expanded {{ display: block; }}
        .checkbox-item {{ display: flex; align-items: center; padding: 2px 0; height: auto; min-height: unset; }}
        .checkbox-item input[type="checkbox"] {{ width: 16px; height: 16px; min-width: 16px; min-height: 16px; margin-right: 6px; box-sizing: border-box; }}
        .checkbox-item:hover {{ background-color: #f8f9fa; }}
        .checkbox-item label {{ cursor: pointer; font-weight: normal; font-size: 13px; line-height: 1.1; margin: 0; }}
        #metrics-container {{ display: flex; gap: 30px; margin-top: 20px; text-align: center; justify-content: center; }}
        .metric {{ background-color: #e9ecef; padding: 15px; border-radius: 8px; flex-grow: 1; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #4a69bd; }}
        .metric-label {{ font-size: 0.9em; color: #6c757d; }}
        #reviews-table-container, #keyword-reviews-table-container {{ max-height: 400px; overflow-y: auto; margin-top: 20px; border: 1px solid #dee2e6; border-radius: 5px; }}
        #network-reviews-table-container {{ max-height: 300px; overflow-y: auto; margin-top: 20px; border: 1px solid #dee2e6; border-radius: 5px; }}
        #reviews-table, #keyword-reviews-table, #network-reviews-table {{ width: 100%; border-collapse: collapse; }}
        #reviews-table th, #reviews-table td, #keyword-reviews-table th, #keyword-reviews-table td, #network-reviews-table th, #network-reviews-table td {{ padding: 12px; border-bottom: 1px solid #dee2e6; text-align: left; }}
        #reviews-table th, #keyword-reviews-table th, #network-reviews-table th {{ background-color: #f8f9fa; position: sticky; top: 0; }}
        #reviews-table tr:last-child td, #keyword-reviews-table tr:last-child td, #network-reviews-table tr:last-child td {{ border-bottom: none; }}
        .keyword-charts-container {{ display: flex; gap: 20px; }}
        .keyword-chart {{ flex: 1; }}
        
        /* 차트 컨테이너 스타일 개선 */
        .chart-container {{ margin: 20px 0; }}
        .subsection {{ margin: 30px 0; }}
        
        /* 협업 빈도 차트 스크롤 컨테이너 */
        #collaboration-frequency-chart-container {{ max-height: 600px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 5px; }}
        
        /* 협업 관계 현황 드롭다운 스타일 */
        .collaboration-status-dropdowns {{ margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
        .status-dropdown {{ border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; background: white; }}
        .status-dropdown h5 {{ margin: 0 0 10px 0; font-size: 1em; font-weight: bold; }}
        .status-dropdown.excellent {{ border-left: 4px solid #28a745; }}
        .status-dropdown.good {{ border-left: 4px solid #17a2b8; }}
        .status-dropdown.caution {{ border-left: 4px solid #ffc107; }}
        .status-dropdown.problem {{ border-left: 4px solid #dc3545; }}
        .status-dropdown select {{ width: 100%; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; background: white; }}
        .status-dropdown .dept-count {{ color: #6c757d; font-size: 0.9em; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1> {dashboard_title} </h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">{DASHBOARD_SUBTITLE} </p>
    </div>
    
    <!-- 안내 문구 섹션 -->
    <div style="max-width: 1400px; margin: 20px auto; padding: 0 20px;">
        <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #495057; margin: 0 0 15px 0; font-size: 1.1em;">📋 대시보드 이용 안내</h3>
            
            <div style="margin-bottom: 15px;">
                <strong style="color: #495057;">📊 평가 문항 설명:</strong>
                <ul style="margin: 8px 0 0 20px; color: #6c757d; font-size: 0.95em; line-height: 1.4;">
                    <li><strong>존중배려:</strong> ○○은 타 부서의 입장을 존중하고 배려하여 협력해주며, 협업 관련 의견을 경청해준다.</li>
                    <li><strong>정보공유:</strong> ○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.</li>
                    <li><strong>명확처리:</strong> ○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.</li>
                    <li><strong>태도개선:</strong> ○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.</li>
                    <li><strong>전반만족:</strong> 전반적으로 ○○과의 협업에 대해 만족한다.</li>
                </ul>
            </div>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 12px;">
                <strong style="color: #856404;">⚠️ 통계적 해석 주의사항:</strong>
                <span style="color: #856404; font-size: 0.95em;">응답건수(표본수)가 30건 미만인 경우 통계적 해석에 유의하시기 바랍니다.</span>
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- 부서/Unit 상세 분석 -->
        <div class="section">
            <h2>부서/Unit 상세 분석</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">부서와 Unit이 받은 점수 및 후기를 파악합니다.</p>
            
            <!-- 공통 필터 -->
            <div class="filters">
                <div class="filter-group"><label for="year-filter">연도 (전체)</label><select id="year-filter"></select></div>
                <div class="filter-group"><label for="department-filter">부서</label><select id="department-filter"></select></div>
                <div class="filter-group"><label for="unit-filter">Unit</label><select id="unit-filter"></select></div>
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="drilldown-score-header" onclick="toggleExpander('drilldown-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="drilldown-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="drilldown-score-expander">
                            <div id="drilldown-score-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 기본 지표 및 점수 트렌드 -->
            <div class="subsection">
                <h3>기본 지표 및 점수 트렌드</h3>
                <div id="metrics-container"></div>
                <div id="drilldown-chart-container" class="chart-container"></div>
                <div id="yearly-comparison-chart-container" class="chart-container"></div>
                
                <!-- 부서 내 Unit 비교 -->
                <div style="margin-top: 30px;">
                    <h4 style="color: #555; margin-bottom: 15px;">부서 내 Unit 비교</h4>
                    <p style="color: #6c757d; margin-bottom: 20px; font-size: 0.9em;">부서 내 Unit간 점수를 파악합니다.</p>
                    <div id="unit-comparison-chart-container" class="chart-container"></div>
                </div>
            </div>
            
            <!-- 감정 분석 -->
            <div class="subsection">
                <h3>협업 주관식 피드백 감정 분석</h3>
                <div id="sentiment-chart-container" class="chart-container"></div>
            </div>
            
            <!-- 키워드 분석 -->
            <div class="subsection">
                <h3>핵심 키워드 분석</h3>
                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #6a89cc; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>📊 이 차트는 무엇인가요?</strong><br>
                        협업 후기에서 자주 언급되는 단어들을 긍정/부정으로 분류하여 상위 10개를 보여줍니다.<br><br>
                        <strong>💡 활용 방법:</strong><br>
                        • <span style="color: #28a745;"><strong>긍정 키워드</strong></span>: 어떤 부분에서 만족하고 있는지 파악<br>
                        • <span style="color: #dc3545;"><strong>부정 키워드</strong></span>: 개선이 필요한 부분을 빠르게 확인<br>
                        • <strong>막대 클릭</strong>: 해당 키워드가 포함된 실제 후기 내용을 확인할 수 있습니다<br><br>
                        <em>예시: "신속한" 키워드 클릭 → "신속한 응답으로 업무가 원활했다" 등의 후기 표시</em>
                    </p>
                </div>
                <div class="keyword-charts-container">
                    <div id="positive-keywords-chart" class="keyword-chart"></div>
                    <div id="negative-keywords-chart" class="keyword-chart"></div>
                </div>
                <div id="keyword-reviews-container"></div>
            </div>
            
            <!-- 협업 후기 -->
            <div class="subsection">
                <h3>협업 후기 <span id="reviews-count-display" style="color: #666; font-size: 0.9em;"></span></h3>
                <div class="filters">
                    <div class="filter-group">
                        <label>감정 분류 필터</label>
                        <div class="expander-container">
                            <div class="expander-header" id="review-sentiment-header" onclick="toggleExpander('review-sentiment-expander')">
                                <span>감정 선택 (4개 선택됨)</span>
                                <span class="expander-arrow" id="review-sentiment-arrow">▼</span>
                            </div>
                            <div class="expander-content" id="review-sentiment-expander">
                                <div id="review-sentiment-filter"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div id="reviews-table-container"><table id="reviews-table"><thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody></tbody></table></div>
            </div>
        </div>

        <div class="part-divider"></div>
        
        <!-- 협업 네트워크 분석 -->
        <div class="section">
            <h2>협업 네트워크 분석</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">🔍 우리 팀/Unit과 협업을 하는 팀/Unit과의 관계를 종합적으로 분석합니다.</p>
            
            <!-- 공통 필터 -->
            <div class="filters">
                <div class="filter-group">
                    <label for="network-year-filter">연도 (전체)</label>
                    <select id="network-year-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="network-division-filter">부문</label>
                    <select id="network-division-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="network-department-filter">부서</label>
                    <select id="network-department-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="network-unit-filter">Unit</label>
                    <select id="network-unit-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="min-collaboration-filter">최소 협업 횟수</label>
                    <select id="min-collaboration-filter">
                        <option value="5">5회 이상</option>
                        <option value="10" selected>10회 이상</option>
                        <option value="30">30회 이상</option>
                    </select>
                </div>
            </div>
            
            <!-- 협업을 많이 하는 부서 -->
            <div class="subsection">
                <h3>협업을 많이 하는 부서</h3>
                <div style="background: #e8f4fd; padding: 15px; border-left: 4px solid #0066cc; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>📊 이 차트는 무엇인가요?</strong><br>
                        우리 부서/Unit에 협업 평가를 준 부서를 보여줍니다.<br>
                        • <span style="color: #dc3545;">주의 사항</span>: Unit을 선택하면 차트에는 팀으로 보여지지만 실제로는 해당 Unit의 결과입니다.<br><br>
                        <strong>💡 활용 방법:</strong><br>
                        • <strong>높은 협업 빈도</strong>: 지속적으로 협업하는 주요 파트너 부서 파악<br>
                        • <strong>협업 패턴 분석</strong>: 어떤 부문과 주로 협업하는지 확인
                    </p>
                </div>
                <div id="collaboration-frequency-chart-container" class="chart-container"></div>
            </div>
            
            <!-- 협업 관계 현황 -->
            <div class="subsection">
                <h3>협업 관계 현황</h3>
                <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>📊 이 차트는 무엇인가요?</strong><br>
                        협업 관계를 점수대별로 분류하여 현황을 보여줍니다.<br><br>
                        <strong>💡 점수 구간별 의미:</strong><br>
                        • <span style="color: #28a745;"><strong>우수 (75점 이상)</strong></span>: 매우 만족스러운 협업 관계<br>
                        • <span style="color: #17a2b8;"><strong>양호 (60-74점)</strong></span>: 원활한 협업 관계<br>
                        • <span style="color: #ffc107;"><strong>주의 (50-59점)</strong></span>: 개선이 필요한 협업 관계<br>
                        • <span style="color: #dc3545;"><strong>문제 (50점 미만)</strong></span>: 즉시 개선이 필요한 협업 관계
                    </p>
                </div>
                <div id="collaboration-status-chart-container" class="chart-container"></div>
                <div id="collaboration-status-dropdowns" class="collaboration-status-dropdowns"></div>
            </div>
            
            <!-- 협업 관계 변화 트렌드 -->
            <div class="subsection">
                <h3>협업 관계 변화 트렌드</h3>
                <div style="background: #e8f5e8; padding: 15px; border-left: 4px solid #28a745; margin-bottom: 20px; border-radius: 0 5px 5px 0;">
                    <p style="margin: 0; color: #495057; font-size: 0.95em;">
                        <strong>📊 이 차트는 무엇인가요?</strong><br>
                        선택한 협업 관계의 연도별 점수 변화를 추적합니다.<br><br>
                        <strong>💡 활용 방법:</strong><br>
                        • <strong>개선 추세</strong>: 점수가 상승하는 관계는 협업이 개선되고 있음<br>
                        • <strong>악화 추세</strong>: 점수가 하락하는 관계는 주의가 필요함<br>
                        • <strong>변동성 분석</strong>: 점수 변동이 큰 관계는 불안정한 협업 상태
                    </p>
                </div>
                <div id="collaboration-trend-chart-container" class="chart-container"></div>
            </div>
            
            <!-- 협업 후기 (네트워크) -->
            <div class="subsection">
                <h3>협업 후기 <span id="network-reviews-count-display" style="color: #666; font-size: 0.9em;"></span></h3>
                <div id="network-reviews-table-container"><table id="network-reviews-table"><thead><tr><th style="width: 100px;">연도</th><th style="width: 150px;">평가 부서</th><th>후기 내용</th></tr></thead><tbody></tbody></table></div>
            </div>
        </div>
    </div>
    
    <script>
        // 🔒 보안 강화된 하이브리드 데이터 구조
        const hybridData = {hybrid_data_json};
        const aggregatedData = hybridData.aggregated;
        const rawData = hybridData.rawData;
        
        // 공통 레이아웃 설정
        const layoutFont = {{ family: 'Malgun Gothic, Segoe UI, sans-serif', size: 12 }};
        
        // 전역 변수
        let allYears = [];
        let allDivisions = [];
        let allDepartments = [];
        let allUnits = [];
        let departmentUnitMap = {{}};
        
        // 초기화 함수
        function initializeDashboard() {{
            try {{
                // 데이터에서 고유값 추출
                allYears = [...new Set(rawData.map(item => item['설문시행연도']))].sort();
                allDivisions = [...new Set(rawData.map(item => item['피평가부문']))].filter(d => d && d !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
                allDepartments = [...new Set(rawData.map(item => item['피평가부서']))].filter(d => d && d !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
                allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
                
                // 부서-Unit 매핑 생성
                rawData.forEach(item => {{
                    const dept = item['피평가부서'];
                    const unit = item['피평가Unit'];
                    if (dept && dept !== 'N/A' && unit && unit !== 'N/A') {{
                        if (!departmentUnitMap[dept]) {{
                            departmentUnitMap[dept] = new Set();
                        }}
                        departmentUnitMap[dept].add(unit);
                    }}
                }});
                
                // Set을 Array로 변환 및 정렬
                Object.keys(departmentUnitMap).forEach(dept => {{
                    departmentUnitMap[dept] = [...departmentUnitMap[dept]].sort((a,b) => a.localeCompare(b, 'ko'));
                }});
                
                // 필터 초기화
                populateFilters();
                setupNetworkAnalysis();
                
                // 초기 차트 로드
                updateDashboard();
                updateUnitComparisonChart();
                updateNetworkAnalysis();
                
                console.log('✅ 대시보드 초기화 완료');
                
            }} catch (error) {{
                console.error('❌ 대시보드 초기화 오류:', error);
            }}
        }}
        
        // 필터 설정 함수
        function populateFilters() {{
            // 연도 필터
            const yearSelect = document.getElementById('year-filter');
            yearSelect.innerHTML = ['전체', ...allYears].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = '전체';
            
            // 부서 필터 (해당 부서로 고정)
            const deptSelect = document.getElementById('department-filter');
            deptSelect.innerHTML = `<option value="{department_name}">{department_name}</option>`;
            deptSelect.value = "{department_name}";
            
            // Unit 필터 초기화 및 이벤트 리스너 설정
            updateUnitFilter();
            
            // 문항 선택 필터 생성
            const scoreColumns = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수'];
            const scoreFilter = document.getElementById('drilldown-score-filter');
            scoreFilter.innerHTML = scoreColumns.map(col => 
                `<div class="checkbox-item"><input type="checkbox" id="drilldown-${{col}}" name="drilldown-score" value="${{col}}" checked><label for="drilldown-${{col}}">${{col}}</label></div>`
            ).join('');
            
            // 감정 분류 필터 생성
            const sentiments = ['긍정', '부정', '중립', null];
            const sentimentLabels = ['긍정', '부정', '중립', '분류없음'];
            const sentimentFilter = document.getElementById('review-sentiment-filter');
            sentimentFilter.innerHTML = sentiments.map((sentiment, idx) => 
                `<div class="checkbox-item"><input type="checkbox" id="sentiment-${{idx}}" name="review-sentiment" value="${{sentiment || ''}}" checked><label for="sentiment-${{idx}}">${{sentimentLabels[idx]}}</label></div>`
            ).join('');
            
            // 이벤트 리스너 설정
            yearSelect.addEventListener('change', () => {{
                updateDashboard();
                updateUnitComparisonChart();
            }});
            
            deptSelect.addEventListener('change', () => {{
                updateUnitFilter();
                updateDashboard();
                updateUnitComparisonChart();
            }});
            
            // 문항 선택 변경 시
            scoreFilter.addEventListener('change', () => {{
                updateDashboard();
                updateUnitComparisonChart();
                updateExpanderHeaderText('drilldown-score-header', 'drilldown-score', '문항 선택');
            }});
            
            // 감정 분류 필터 변경 시
            sentimentFilter.addEventListener('change', () => {{
                updateReviewsTable(getFilteredData());
                updateExpanderHeaderText('review-sentiment-header', 'review-sentiment', '감정 선택');
            }});
        }}
        
        // Unit 필터 업데이트 함수
        function updateUnitFilter() {{
            const departmentSelect = document.getElementById('department-filter');
            const unitSelect = document.getElementById('unit-filter');
            const selectedDept = departmentSelect.value;
            
            // 기존 이벤트 리스너 제거
            const newUnitSelect = unitSelect.cloneNode(false);
            unitSelect.parentNode.replaceChild(newUnitSelect, unitSelect);
            
            // Unit 드롭다운 업데이트
            const allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
            const units = (selectedDept === '전체' || !departmentUnitMap[selectedDept])
                ? allUnits
                : departmentUnitMap[selectedDept];
            
            newUnitSelect.innerHTML = ['전체', ...units].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            newUnitSelect.value = '전체';
            
            // 새 이벤트 리스너 추가
            newUnitSelect.addEventListener('change', updateDashboard);
            
            updateDashboard();
        }}
        
        // 필터링된 데이터 가져오기
        function getFilteredData() {{
            let filteredData = [...rawData];
            
            const selectedYear = document.getElementById('year-filter').value;
            const selectedDept = document.getElementById('department-filter').value;
            const selectedUnit = document.getElementById('unit-filter').value;
            
            if (selectedYear !== '전체') {{ filteredData = filteredData.filter(item => String(item['설문시행연도']) === String(selectedYear)); }}
            if (selectedDept !== '전체') {{ filteredData = filteredData.filter(item => item['피평가부서'] === selectedDept); }}
            if (selectedUnit !== '전체') {{ filteredData = filteredData.filter(item => item['피평가Unit'] === selectedUnit); }}
            
            return filteredData;
        }}
        
        // 네트워크 분석용 필터링된 데이터
        function getNetworkFilteredData() {{
            let filteredData = [...rawData];
            
            const selectedYear = document.getElementById('network-year-filter').value;
            const selectedDivision = document.getElementById('network-division-filter').value;
            const selectedDept = document.getElementById('network-department-filter').value;
            const selectedUnit = document.getElementById('network-unit-filter').value;
            
            if (selectedYear !== '전체') {{ filteredData = filteredData.filter(item => String(item['설문시행연도']) === String(selectedYear)); }}
            if (selectedDivision !== '전체') {{ filteredData = filteredData.filter(item => item['피평가부문'] === selectedDivision); }}
            if (selectedDept !== '전체') {{ filteredData = filteredData.filter(item => item['피평가부서'] === selectedDept); }}
            if (selectedUnit !== '전체') {{ filteredData = filteredData.filter(item => item['피평가Unit'] === selectedUnit); }}
            
            return filteredData;
        }}
        
        // 대시보드 업데이트 (메인 함수)
        function updateDashboard() {{
            const filteredData = getFilteredData();
            updateMetrics(filteredData);
            updateDrilldownChart(filteredData);
            updateYearlyComparisonChart(filteredData);
            updateSentimentChart(filteredData);
            updateKeywordCharts(filteredData);
            updateReviewsTable(filteredData);
        }}
        
        // 기본 지표 업데이트
        function updateMetrics(data) {{
            const metricsContainer = document.getElementById('metrics-container');
            const scoreColumns = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수'];
            
            if (data.length === 0) {{
                metricsContainer.innerHTML = '<div style="color: #888; text-align: center; width: 100%;">선택된 조건에 해당하는 데이터가 없습니다.</div>';
                return;
            }}
            
            const metrics = [];
            
            // 응답 수
            metrics.push({{
                label: '응답 수',
                value: data.length.toLocaleString() + '건',
                color: '#4a69bd'
            }});
            
            // 각 점수의 평균
            scoreColumns.forEach(col => {{
                const validScores = data.filter(item => item[col] != null && !isNaN(item[col]));
                if (validScores.length > 0) {{
                    const avg = validScores.reduce((sum, item) => sum + item[col], 0) / validScores.length;
                    metrics.push({{
                        label: col,
                        value: avg.toFixed(1) + '점',
                        color: '#6a89cc'
                    }});
                }}
            }});
            
            metricsContainer.innerHTML = metrics.map(metric => 
                `<div class="metric">
                    <div class="metric-value" style="color: ${{metric.color}}">${{metric.value}}</div>
                    <div class="metric-label">${{metric.label}}</div>
                </div>`
            ).join('');
        }}
        
        // 드릴다운 차트 (막대 차트)
        function updateDrilldownChart(data) {{
            const container = document.getElementById('drilldown-chart-container');
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);
            
            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            if (data.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const traces = [];
            const colors = ['#4a69bd', '#6a89cc', '#74b9ff', '#81ecec', '#a29bfe', '#fd79a8'];
            
            selectedScores.forEach((col, index) => {{
                const validData = data.filter(item => item[col] != null && !isNaN(item[col]));
                if (validData.length > 0) {{
                    const avg = validData.reduce((sum, item) => sum + item[col], 0) / validData.length;
                    traces.push({{
                        x: [col],
                        y: [avg.toFixed(1)],
                        name: col,
                        type: 'bar',
                        text: [avg.toFixed(1) + '점'],
                        textposition: 'outside',
                        textfont: {{ size: 14 }},
                        marker: {{ color: colors[index % colors.length] }},
                        hovertemplate: '%{{x}}: %{{y}}점<extra></extra>'
                    }});
                }}
            }});
            
            const layout = {{
                title: '<b>문항별 평균 점수</b>',
                height: 400,
                xaxis: {{ title: '문항' }},
                yaxis: {{ title: '평균 점수', range: [0, 100] }},
                font: layoutFont,
                showlegend: false,
                margin: {{ l: 60, r: 60, t: 80, b: 60 }}
            }};
            
            Plotly.react(container, traces, layout);
        }}
        
        // 연도별 비교 차트
        function updateYearlyComparisonChart(targetData) {{
            const container = document.getElementById('yearly-comparison-chart-container');
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);
            const selectedYear = document.getElementById('year-filter').value;
            const selectedDept = document.getElementById('department-filter').value;
            const selectedUnit = document.getElementById('unit-filter').value;
            
            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            if (targetData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const years = [...new Set(targetData.map(item => item['설문시행연도']))].sort();
            const traces = [];

            selectedScores.forEach(col => {{
                const y_values = years.map(year => {{
                    const yearData = targetData.filter(d => d['설문시행연도'] === year);
                    return yearData.length > 0 ? (yearData.reduce((sum, item) => sum + (item[col] || 0), 0) / yearData.length).toFixed(1) : 0;
                }});
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            
            const yearly_counts = years.map(year => targetData.filter(d => d['설문시행연도'] === year).length);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3 }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}건`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}건<br>연도: %{{x}}<extra></extra>' }});

            let titleText = '연도별 문항 점수';
            if (selectedDept !== '전체' && selectedUnit !== '전체') {{ titleText = `[${{selectedDept}} > ${{selectedUnit}}] 연도별 문항 점수`; }}
            else if (selectedDept !== '전체') {{ titleText = `[${{selectedDept}}] 연도별 문항 점수`; }}
            else if (selectedUnit !== '전체') {{ titleText = `[${{selectedUnit}}] 연도별 문항 점수`; }}
            
            const layout = {{
                title: `<b>${{titleText}}</b>`, barmode: 'group', height: 500,
                xaxis: {{ type: 'category', title: '설문 연도' }},
                yaxis: {{ title: '점수', range: [0, 100] }},
                yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'right', x: 1 }},
                font: layoutFont, hovermode: 'closest',
                margin: {{ l: 60, r: 60, t: 120, b: 60 }}
            }};
            
            Plotly.react(container, traces, layout);
        }}

        // 부서 내 Unit 비교 차트
        function updateUnitComparisonChart() {{
            const container = document.getElementById('unit-comparison-chart-container');
            const selectedYear = document.getElementById('year-filter').value;
            const selectedDept = document.getElementById('department-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);

            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            if (selectedDept === '전체') {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '부서를 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 선택된 부서의 모든 Unit 데이터 가져오기 (Unit 필터와 무관)
            let targetData = rawData.filter(item => item['피평가부서'] === selectedDept);
            if (selectedYear !== '전체') {{
                targetData = targetData.filter(item => item['설문시행연도'] === selectedYear);
            }}

            if (targetData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // Unit별 점수 계산
            const units = [...new Set(targetData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort();
            
            if (units.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '비교할 Unit이 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const traces = [];
            selectedScores.forEach((col, index) => {{
                const y_values = units.map(unit => {{
                    const unitData = targetData.filter(item => item['피평가Unit'] === unit);
                    return unitData.length > 0 ? (unitData.reduce((sum, item) => sum + (item[col] || 0), 0) / unitData.length).toFixed(1) : 0;
                }});
                
                const colors = ['#4a69bd', '#6a89cc', '#74b9ff', '#81ecec', '#a29bfe', '#fd79a8'];
                traces.push({{
                    x: units,
                    y: y_values,
                    name: col,
                    type: 'bar',
                    text: y_values,
                    textposition: 'outside',
                    textfont: {{ size: 12 }},
                    marker: {{ color: colors[index % colors.length] }},
                    hovertemplate: '%{{fullData.name}}: %{{y}}점<br>Unit: %{{x}}<extra></extra>'
                }});
            }});

            const layout = {{
                title: `<b>[${{selectedDept}}] Unit별 문항 점수 비교</b>`,
                height: 500,
                barmode: 'group',
                xaxis: {{ title: 'Unit', tickangle: -45 }},
                yaxis: {{ title: '평균 점수', range: [0, 100] }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'center', x: 0.5 }},
                font: layoutFont,
                margin: {{ l: 60, r: 60, t: 120, b: 100 }}
            }};

            Plotly.react(container, traces, layout);
        }}

        // 감정 분석 차트
        function updateSentimentChart(data) {{
            const container = document.getElementById('sentiment-chart-container');
            
            if (data.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            // 감정 분류별 집계
            const sentimentCounts = {{}};
            data.forEach(item => {{
                const sentiment = item['감정_분류'] || '분류없음';
                sentimentCounts[sentiment] = (sentimentCounts[sentiment] || 0) + 1;
            }});
            
            const sentiments = Object.keys(sentimentCounts);
            const counts = Object.values(sentimentCounts);
            const colors = sentiments.map(sentiment => {{
                switch(sentiment) {{
                    case '긍정': return '#28a745';
                    case '부정': return '#dc3545';
                    case '중립': return '#6c757d';
                    default: return '#ffc107';
                }}
            }});
            
            const trace = {{
                labels: sentiments,
                values: counts,
                type: 'pie',
                marker: {{ colors: colors }},
                textinfo: 'label+percent+value',
                texttemplate: '%{{label}}<br>%{{percent}}<br>(%{{value}}건)',
                hovertemplate: '%{{label}}: %{{value}}건 (%{{percent}})<extra></extra>'
            }};
            
            const layout = {{
                title: '<b>감정 분류별 분포</b>',
                height: 400,
                font: layoutFont,
                showlegend: false,
                margin: {{ l: 60, r: 60, t: 80, b: 60 }}
            }};
            
            Plotly.react(container, [trace], layout);
        }}
        
        // 키워드 차트
        function updateKeywordCharts(data) {{
            updatePositiveKeywords(data);
            updateNegativeKeywords(data);
        }}

        function updatePositiveKeywords(data) {{
            const container = document.getElementById('positive-keywords-chart');
            const positiveData = data.filter(item => item['감정_분류'] === '긍정' && item['핵심_키워드']);
            
            if (positiveData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '긍정 키워드 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 14, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            // 키워드 빈도 계산
            const keywordCounts = {{}};
            positiveData.forEach(item => {{
                try {{
                    const keywords = typeof item['핵심_키워드'] === 'string' ? 
                        JSON.parse(item['핵심_키워드'].replace(/'/g, '"')) : 
                        item['핵심_키워드'];
                    if (Array.isArray(keywords)) {{
                        keywords.forEach(keyword => {{
                            if (keyword && keyword.trim()) {{
                                keywordCounts[keyword] = (keywordCounts[keyword] || 0) + 1;
                            }}
                        }});
                    }}
                }} catch (e) {{
                    // JSON 파싱 실패 시 무시
                }}
            }});
            
            // 상위 10개 키워드
            const sortedKeywords = Object.entries(keywordCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);
            
            if (sortedKeywords.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '표시할 긍정 키워드가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 14, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const trace = {{
                y: sortedKeywords.map(([keyword, _]) => keyword).reverse(),
                x: sortedKeywords.map(([_, count]) => count).reverse(),
                type: 'bar',
                orientation: 'h',
                text: sortedKeywords.map(([_, count]) => `${{count}}회`).reverse(),
                textposition: 'outside',
                textfont: {{ size: 11 }},
                marker: {{ color: '#28a745' }},
                hovertemplate: '%{{y}}: %{{x}}회<extra></extra>'
            }};
            
            const layout = {{
                title: '<b>긍정 키워드 TOP 10</b>',
                height: 400,
                margin: {{ l: 100, r: 40, t: 60, b: 40 }},
                xaxis: {{ title: '언급 횟수' }},
                yaxis: {{ automargin: true }},
                font: layoutFont
            }};
            
            Plotly.react(container, [trace], layout);
            
            // 클릭 이벤트 추가
            container.on('plotly_click', function(eventData) {{
                if (eventData.points && eventData.points[0]) {{
                    const keyword = eventData.points[0].y;
                    showKeywordReviews(keyword, '긍정', data);
                }}
            }});
        }}

        function updateNegativeKeywords(data) {{
            const container = document.getElementById('negative-keywords-chart');
            const negativeData = data.filter(item => item['감정_분류'] === '부정' && item['핵심_키워드']);
            
            if (negativeData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '부정 키워드 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 14, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            // 키워드 빈도 계산
            const keywordCounts = {{}};
            negativeData.forEach(item => {{
                try {{
                    const keywords = typeof item['핵심_키워드'] === 'string' ? 
                        JSON.parse(item['핵심_키워드'].replace(/'/g, '"')) : 
                        item['핵심_키워드'];
                    if (Array.isArray(keywords)) {{
                        keywords.forEach(keyword => {{
                            if (keyword && keyword.trim()) {{
                                keywordCounts[keyword] = (keywordCounts[keyword] || 0) + 1;
                            }}
                        }});
                    }}
                }} catch (e) {{
                    // JSON 파싱 실패 시 무시
                }}
            }});
            
            // 상위 10개 키워드
            const sortedKeywords = Object.entries(keywordCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);
            
            if (sortedKeywords.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '표시할 부정 키워드가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 14, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const trace = {{
                y: sortedKeywords.map(([keyword, _]) => keyword).reverse(),
                x: sortedKeywords.map(([_, count]) => count).reverse(),
                type: 'bar',
                orientation: 'h',
                text: sortedKeywords.map(([_, count]) => `${{count}}회`).reverse(),
                textposition: 'outside',
                textfont: {{ size: 11 }},
                marker: {{ color: '#dc3545' }},
                hovertemplate: '%{{y}}: %{{x}}회<extra></extra>'
            }};
            
            const layout = {{
                title: '<b>부정 키워드 TOP 10</b>',
                height: 400,
                margin: {{ l: 100, r: 40, t: 60, b: 40 }},
                xaxis: {{ title: '언급 횟수' }},
                yaxis: {{ automargin: true }},
                font: layoutFont
            }};
            
            Plotly.react(container, [trace], layout);
            
            // 클릭 이벤트 추가
            container.on('plotly_click', function(eventData) {{
                if (eventData.points && eventData.points[0]) {{
                    const keyword = eventData.points[0].y;
                    showKeywordReviews(keyword, '부정', data);
                }}
            }});
        }}

        // 키워드 관련 후기 표시
        function showKeywordReviews(keyword, sentiment, data) {{
            const container = document.getElementById('keyword-reviews-container');
            
            // 해당 키워드가 포함된 후기 찾기
            const keywordReviews = data.filter(item => {{
                if (item['감정_분류'] !== sentiment || !item['핵심_키워드'] || !item['정제된_텍스트']) return false;
                
                try {{
                    const keywords = typeof item['핵심_키워드'] === 'string' ? 
                        JSON.parse(item['핵심_키워드'].replace(/'/g, '"')) : 
                        item['핵심_키워드'];
                    return Array.isArray(keywords) && keywords.includes(keyword);
                }} catch (e) {{
                    return false;
                }}
            }});
            
            if (keywordReviews.length === 0) {{
                container.innerHTML = `<div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; text-align: center; color: #666;">
                    "${{keyword}}" 키워드가 포함된 후기를 찾을 수 없습니다.
                </div>`;
                return;
            }}
            
            // 최대 5개까지만 표시
            const displayReviews = keywordReviews.slice(0, 5);
            const sentimentColor = sentiment === '긍정' ? '#28a745' : '#dc3545';
            
            container.innerHTML = `
                <div style="margin-top: 20px;">
                    <h4 style="color: #555; margin-bottom: 15px;">
                        <span style="color: ${{sentimentColor}};">"${{keyword}}"</span> 키워드 관련 후기 
                        <span style="color: #666; font-size: 0.9em;">(${{keywordReviews.length}}건 중 ${{displayReviews.length}}건 표시)</span>
                    </h4>
                    <div id="keyword-reviews-table-container">
                        <table id="keyword-reviews-table">
                            <thead>
                                <tr>
                                    <th style="width: 80px;">연도</th>
                                    <th>후기 내용</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${{displayReviews.map(item => 
                                    `<tr>
                                        <td>${{item['설문시행연도']}}</td>
                                        <td>${{item['정제된_텍스트']}}</td>
                                    </tr>`
                                ).join('')}}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }}
        
        // 후기 테이블 업데이트
        function updateReviewsTable(data) {{
            const tableBody = document.querySelector('#reviews-table tbody');
            const countDisplay = document.getElementById('reviews-count-display');
            
            // 감정 필터 적용
            const selectedSentiments = Array.from(document.querySelectorAll('input[name="review-sentiment"]:checked')).map(cb => cb.value || null);
            const filteredData = data.filter(item => {{
                const sentiment = item['감정_분류'] || null;
                return selectedSentiments.includes(sentiment) && item['정제된_텍스트'] && item['정제된_텍스트'] !== 'N/A';
            }});
            
            countDisplay.textContent = `(${{filteredData.length}}건)`;
            
            if (filteredData.length === 0) {{
                tableBody.innerHTML = '<tr><td colspan="2" style="text-align:center;">표시할 후기가 없습니다.</td></tr>';
                return;
            }}
            
            // 최신순 정렬 후 최대 50개만 표시
            const sortedData = filteredData
                .sort((a, b) => b['설문시행연도'] - a['설문시행연도'])
                .slice(0, 50);
            
            tableBody.innerHTML = sortedData.map(item => 
                `<tr><td>${{item['설문시행연도']}}</td><td>${{item['정제된_텍스트']}}</td></tr>`
            ).join('');
        }}

        // 네트워크 분석 설정
        function setupNetworkAnalysis() {{
            // 네트워크 분석 필터 설정
            const yearSelect = document.getElementById('network-year-filter');
            const divisionSelect = document.getElementById('network-division-filter');
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const minCollabSelect = document.getElementById('min-collaboration-filter');

            // 연도 필터
            yearSelect.innerHTML = ['전체', ...allYears].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = '전체';

            // 부문 필터
            divisionSelect.innerHTML = ['전체', ...allDivisions].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            divisionSelect.value = '전체';

            // 부서 필터
            departmentSelect.innerHTML = ['전체', ...allDepartments].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            departmentSelect.value = '전체';

            // Unit 필터
            unitSelect.innerHTML = ['전체', ...allUnits].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            unitSelect.value = '전체';

            // 이벤트 리스너
            [yearSelect, divisionSelect, departmentSelect, unitSelect, minCollabSelect].forEach(select => {{
                select.addEventListener('change', () => {{
                    updateNetworkDepartments();
                    updateNetworkAnalysis();
                }});
            }});
        }}

        function updateNetworkDepartments() {{
            const divisionSelect = document.getElementById('network-division-filter');
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const selectedDivision = divisionSelect.value;

            if (selectedDivision === '전체') {{
                departmentSelect.innerHTML = ['전체', ...allDepartments].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
                unitSelect.innerHTML = ['전체', ...allUnits].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            }} else {{
                const divisionDepartments = [...new Set(rawData
                    .filter(item => item['피평가부문'] === selectedDivision)
                    .map(item => item['피평가부서'])
                    .filter(d => d && d !== 'N/A')
                )].sort();
                
                departmentSelect.innerHTML = ['전체', ...divisionDepartments].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
                
                const divisionUnits = [...new Set(rawData
                    .filter(item => item['피평가부문'] === selectedDivision)
                    .map(item => item['피평가Unit'])
                    .filter(u => u && u !== 'N/A')
                )].sort();
                
                updateNetworkUnits();
            }}

            departmentSelect.value = '전체';
            unitSelect.value = '전체';
        }}

        function updateNetworkUnits() {{
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const selectedDept = departmentSelect.value;

            if (selectedDept === '전체') {{
                const divisionSelect = document.getElementById('network-division-filter');
                const selectedDivision = divisionSelect.value;
                
                if (selectedDivision === '전체') {{
                    unitSelect.innerHTML = ['전체', ...allUnits].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
                }} else {{
                    const divisionUnits = [...new Set(rawData
                        .filter(item => item['피평가부문'] === selectedDivision)
                        .map(item => item['피평가Unit'])
                        .filter(u => u && u !== 'N/A')
                    )].sort();
                    unitSelect.innerHTML = ['전체', ...divisionUnits].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
                }}
            }} else {{
                const deptUnits = [...new Set(rawData
                    .filter(item => item['피평가부서'] === selectedDept)
                    .map(item => item['피평가Unit'])
                    .filter(u => u && u !== 'N/A')
                )].sort();
                
                unitSelect.innerHTML = ['전체', ...deptUnits].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            }}

            unitSelect.value = '전체';
        }}

        function updateNetworkAnalysis() {{
            updateCollaborationFrequencyChart();
            updateCollaborationStatusChart();
            updateCollaborationTrendChart();
            updateNetworkReviews();
        }}

        function updateCollaborationFrequencyChart() {{
            const container = document.getElementById('collaboration-frequency-chart-container');
            const filteredData = getNetworkFilteredData();
            const minCollabCount = parseInt(document.getElementById('min-collaboration-filter').value);
            
            if (filteredData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            // 협업 빈도 계산
            const collaborationCounts = {{}};
            filteredData.forEach(item => {{
                const evaluator = item['평가부서'];
                const evaluated = item['피평가부서'];
                if (evaluator !== evaluated && evaluator && evaluated && evaluator !== 'N/A' && evaluated !== 'N/A') {{
                    const key = `${{evaluator}} → ${{evaluated}}`;
                    collaborationCounts[key] = (collaborationCounts[key] || 0) + 1;
                }}
            }});
            
            // 최소 협업 횟수 이상인 관계만 필터링
            const filteredCollaborations = Object.entries(collaborationCounts)
                .filter(([_, count]) => count >= minCollabCount)
                .sort((a, b) => b[1] - a[1]);
            
            if (filteredCollaborations.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: `최소 ${{minCollabCount}}회 이상 협업한 관계가 없습니다.`, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const trace = {{
                y: filteredCollaborations.map(([key, _]) => key).reverse(),
                x: filteredCollaborations.map(([_, count]) => count).reverse(),
                type: 'bar',
                orientation: 'h',
                text: filteredCollaborations.map(([_, count]) => `${{count}}회`).reverse(),
                textposition: 'outside',
                textfont: {{ size: 12 }},
                marker: {{ color: '#4a69bd' }},
                hovertemplate: '협업 횟수: %{{x}}회<extra></extra>'
            }};
            
            // 부서 수에 따라 동적 높이 계산 (막대당 최소 25px 보장)
            const barHeight = 25;
            const dynamicHeight = Math.max(400, filteredCollaborations.length * barHeight + 100);
            
            const layout = {{
                title: '<b>부서 리스트</b>',
                height: dynamicHeight,
                margin: {{ l: 150, r: 40, t: 80, b: 60 }},
                xaxis: {{ title: '협업 횟수' }},
                yaxis: {{ 
                    automargin: true,
                    fixedrange: true,
                    categoryorder: 'total ascending'
                }},
                font: layoutFont
            }};
            
            Plotly.react(container, [trace], layout);
        }}

        function updateCollaborationStatusChart() {{
            const container = document.getElementById('collaboration-status-chart-container');
            const filteredData = getNetworkFilteredData();
            const minCollabCount = parseInt(document.getElementById('min-collaboration-filter').value);
            
            if (filteredData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                updateStatusDropdowns({{}});
                return;
            }}
            
            // 협업 관계별 점수 계산
            const relationshipScores = {{}};
            filteredData.forEach(item => {{
                const evaluator = item['평가부서'];
                const evaluated = item['피평가부서'];
                const score = item['종합점수'];
                if (evaluator !== evaluated && evaluator && evaluated && evaluator !== 'N/A' && evaluated !== 'N/A' && score != null) {{
                    const key = `${{evaluator}} → ${{evaluated}}`;
                    if (!relationshipScores[key]) {{ relationshipScores[key] = {{ scores: [], count: 0 }}; }}
                    relationshipScores[key].scores.push(score);
                    relationshipScores[key].count++;
                }}
            }});
            
            // 점수대별 분류
            const statusCounts = {{ '우수 (75점 이상)': 0, '양호 (60-74점)': 0, '주의 (50-59점)': 0, '문제 (50점 미만)': 0 }};
            const statusDepartments = {{ '우수': [], '양호': [], '주의': [], '문제': [] }};
            
            Object.entries(relationshipScores)
                .filter(([_, data]) => data.count >= minCollabCount)
                .forEach(([relationship, data]) => {{
                    const avgScore = data.scores.reduce((sum, score) => sum + score, 0) / data.scores.length;
                    const [evaluator, evaluated] = relationship.split(' → ');
                    const relationshipInfo = {{
                        relationship: relationship,
                        avgScore: avgScore.toFixed(1),
                        count: data.count,
                        evaluator: evaluator,
                        evaluated: evaluated
                    }};
                    
                    if (avgScore >= 75) {{
                        statusCounts['우수 (75점 이상)']++;
                        statusDepartments['우수'].push(relationshipInfo);
                    }} else if (avgScore >= 60) {{
                        statusCounts['양호 (60-74점)']++;
                        statusDepartments['양호'].push(relationshipInfo);
                    }} else if (avgScore >= 50) {{
                        statusCounts['주의 (50-59점)']++;
                        statusDepartments['주의'].push(relationshipInfo);
                    }} else {{
                        statusCounts['문제 (50점 미만)']++;
                        statusDepartments['문제'].push(relationshipInfo);
                    }}
                }});
            
            const statusLabels = Object.keys(statusCounts);
            const statusValues = Object.values(statusCounts);
            const statusColors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545'];
            
            if (statusValues.every(val => val === 0)) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: `최소 ${{minCollabCount}}회 이상 협업한 관계가 없습니다.`, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                updateStatusDropdowns({{}});
                return;
            }}
            
            const trace = {{
                x: statusLabels,
                y: statusValues,
                type: 'bar',
                text: statusValues.map(val => `${{val}}개`),
                textposition: 'outside',
                textfont: {{ size: 12 }},
                marker: {{ color: statusColors }},
                hovertemplate: '%{{x}}: %{{y}}개<extra></extra>'
            }};
            
            const layout = {{
                title: '<b>협업 관계 현황</b>',
                height: 400,
                margin: {{ l: 60, r: 60, t: 80, b: 60 }},
                xaxis: {{ title: '점수대' }},
                yaxis: {{ title: '관계 수' }},
                font: layoutFont
            }};
            
            Plotly.react(container, [trace], layout);
            updateStatusDropdowns(statusDepartments);
        }}

        function updateStatusDropdowns(statusData) {{
            const container = document.getElementById('collaboration-status-dropdowns');
            const statusClasses = {{ '우수': 'excellent', '양호': 'good', '주의': 'caution', '문제': 'problem' }};
            
            container.innerHTML = '';
            
            Object.entries(statusClasses).forEach(([status, className]) => {{
                const dropdown = document.createElement('div');
                dropdown.className = `status-dropdown ${{className}}`;
                
                const headerElement = document.createElement('h5');
                headerElement.textContent = status;
                dropdown.appendChild(headerElement);
                
                const selectElement = document.createElement('select');
                selectElement.multiple = true;
                selectElement.size = 5;
                dropdown.appendChild(selectElement);
                
                const countElement = document.createElement('div');
                countElement.className = 'dept-count';
                dropdown.appendChild(countElement);
                
                container.appendChild(dropdown);
                
                if (statusData[status] && statusData[status].length > 0) {{
                    statusData[status]
                        .sort((a, b) => b.avgScore - a.avgScore)
                        .forEach(item => {{
                            const option = document.createElement('option');
                            option.value = item.relationship;
                            option.textContent = `${{item.relationship}} (${{item.avgScore}}점, ${{item.count}}회)`;
                            selectElement.appendChild(option);
                        }});
                    
                    selectElement.addEventListener('change', updateCollaborationTrendChart);
                    countElement.textContent = `${{statusData[status].length}}개 관계`;
                }} else {{
                    countElement.textContent = '0개 관계';
                    selectElement.innerHTML = '<option disabled>해당 관계가 없습니다</option>';
                }}
            }});
        }}

        function updateCollaborationTrendChart() {{
            const container = document.getElementById('collaboration-trend-chart-container');
            const filteredData = getNetworkFilteredData();
            const minCollabCount = parseInt(document.getElementById('min-collaboration-filter').value);
            
            // 선택된 관계들 가져오기
            const selectedRelationships = [];
            document.querySelectorAll('.status-dropdown select').forEach(select => {{
                Array.from(select.selectedOptions).forEach(option => {{
                    if (!option.disabled) {{
                        selectedRelationships.push(option.value);
                    }}
                }});
            }});
            
            if (selectedRelationships.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{
                        text: '협업 관계를 선택해주세요.',
                        xref: 'paper', yref: 'paper', x: 0.5, y: 0.5,
                        showarrow: false, font: {{size: 16, color: '#888'}}
                    }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const traces = [];
            const colors = ['#4a69bd', '#28a745', '#dc3545', '#ffc107', '#6a89cc', '#fd7e14'];
            
            selectedRelationships.forEach((relationship, index) => {{
                const [evaluator, evaluated] = relationship.split(' → ');
                const relationshipData = filteredData.filter(item => 
                    item['평가부서'] === evaluator && item['피평가부서'] === evaluated && item['종합점수'] != null
                );
                
                if (relationshipData.length >= minCollabCount) {{
                    // 연도별 평균 점수 계산
                    const yearlyScores = {{}};
                    relationshipData.forEach(item => {{
                        const year = item['설문시행연도'];
                        if (!yearlyScores[year]) {{ yearlyScores[year] = {{ scores: [], count: 0 }}; }}
                        yearlyScores[year].scores.push(item['종합점수']);
                        yearlyScores[year].count++;
                    }});
                    
                    const years = Object.keys(yearlyScores).sort();
                    const avgScores = years.map(year => {{
                        const scores = yearlyScores[year].scores;
                        return (scores.reduce((sum, score) => sum + score, 0) / scores.length).toFixed(1);
                    }});
                    
                    if (years.length > 0) {{
                        traces.push({{
                            x: years,
                            y: avgScores,
                            name: relationship,
                            type: 'scatter',
                            mode: 'lines+markers',
                            line: {{ color: colors[index % colors.length], width: 3 }},
                            marker: {{ size: 8 }},
                            hovertemplate: '%{{fullData.name}}<br>점수: %{{y}}점<br>연도: %{{x}}<extra></extra>'
                        }});
                    }}
                }}
            }});
            
            if (traces.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{
                        text: `선택된 관계에 대한 ${{minCollabCount}}회 이상의 연도별 데이터가 없습니다.`,
                        xref: 'paper', yref: 'paper', x: 0.5, y: 0.5,
                        showarrow: false, font: {{size: 16, color: '#888'}}
                    }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
            const layout = {{
                title: '<b>협업 관계 변화 트렌드</b>',
                height: 400,
                margin: {{ l: 60, r: 60, t: 80, b: 60 }},
                xaxis: {{ title: '연도', type: 'category' }},
                yaxis: {{ title: '점수', range: [0, 100] }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'center', x: 0.5 }},
                font: layoutFont,
                hovermode: 'closest'
            }};
            
            Plotly.react(container, traces, layout);
        }}

        function updateNetworkReviews() {{
            const tableBody = document.querySelector('#network-reviews-table tbody');
            const countDisplay = document.getElementById('network-reviews-count-display');
            const filteredData = getNetworkFilteredData();
            
            const reviewData = filteredData.filter(item => 
                item['정제된_텍스트'] && item['정제된_텍스트'] !== 'N/A'
            );
            
            countDisplay.textContent = `(${{reviewData.length}}건)`;
            
            if (reviewData.length === 0) {{
                tableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">표시할 후기가 없습니다.</td></tr>';
                return;
            }}
            
            // 최신순 정렬 후 최대 100개만 표시
            const sortedData = reviewData
                .sort((a, b) => b['설문시행연도'].localeCompare(a['설문시행연도']))
                .slice(0, 100);
            
            tableBody.innerHTML = sortedData.map(item => 
                `<tr><td>${{item['설문시행연도']}}</td><td>${{item['평가부서']}}</td><td>${{item['정제된_텍스트']}}</td></tr>`
            ).join('');
        }}
        
        // 확장/축소 토글 함수
        function toggleExpander(expanderId) {{
            const content = document.getElementById(expanderId);
            const arrow = document.getElementById(expanderId.replace('-expander', '-arrow'));
            
            if (content.classList.contains('expanded')) {{
                content.classList.remove('expanded');
                arrow.classList.remove('expanded');
            }} else {{
                content.classList.add('expanded');
                arrow.classList.add('expanded');
            }}
        }}
        
        // 확장기 헤더 텍스트 업데이트
        function updateExpanderHeaderText(headerId, checkboxName, baseText) {{
            const header = document.getElementById(headerId);
            const checkboxes = document.querySelectorAll(`input[name="${{checkboxName}}"]:checked`);
            const count = checkboxes.length;
            header.querySelector('span').textContent = `${{baseText}} (${{count}}개 선택됨)`;
        }}
        
        // 페이지 로드 완료 후 초기화
        document.addEventListener('DOMContentLoaded', initializeDashboard);
    </script>
</body>
</html>
    """

# ============================================================================
# 🏗️ 부서 보고서 생성 함수들
# ============================================================================

def create_output_directory_structure(divisions):
    """
    출력 디렉토리 구조 생성
    
    Args:
        divisions (dict): 부문별 부서 정보
    """
    log_message("📁 출력 디렉토리 구조 생성 시작")
    
    base_path = Path(OUTPUT_BASE_DIR)
    
    # 기본 디렉토리가 존재하면 삭제하고 다시 생성
    if base_path.exists():
        shutil.rmtree(base_path)
        log_message("🗑️ 기존 출력 디렉토리 삭제")
    
    base_path.mkdir(parents=True, exist_ok=True)
    
    # 부문별 디렉토리 생성
    for division_name in divisions.keys():
        division_path = base_path / safe_filename(division_name)
        division_path.mkdir(parents=True, exist_ok=True)
        log_message(f"📁 부문 디렉토리 생성: {division_name}")
    
    log_message(f"✅ 출력 디렉토리 구조 생성 완료: {len(divisions)}개 부문")

def generate_department_report(department_name, division_name, df, aggregated_data):
    """
    개별 부서 보고서 생성
    
    Args:
        department_name (str): 부서명
        division_name (str): 부문명
        df (pd.DataFrame): 전체 데이터프레임
        aggregated_data (dict): 집계된 데이터
        
    Returns:
        bool: 성공 여부
    """
    try:
        log_message(f"🏢 {department_name} 보고서 생성 시작")
        
        # 부서별 데이터 필터링
        filtered_data = filter_data_for_department(df, department_name)
        
        if len(filtered_data) == 0:
            log_message(f"⚠️ {department_name}: 데이터가 없어 보고서 생성 건너뜀", "WARNING")
            return False
        
        # JSON 변환을 위한 데이터 준비 (numpy 타입 처리 포함)
        filtered_data_json = []
        for _, row in filtered_data.iterrows():
            row_dict = {}
            for col in JSON_OUTPUT_COLUMNS:
                if col in row.index:
                    value = row[col]
                    # NaN, None, pd.NaType 처리
                    if pd.isna(value) or value is None:
                        row_dict[col] = 'N/A'
                    else:
                        # numpy 타입을 Python 기본 타입으로 변환
                        if hasattr(value, 'item'):  # numpy scalar
                            row_dict[col] = value.item()
                        elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                            row_dict[col] = str(value)
                        else:
                            row_dict[col] = value
                else:
                    row_dict[col] = 'N/A'
            filtered_data_json.append(row_dict)
        
        # HTML 생성
        html_content = build_department_html(
            department_name=department_name,
            division_name=division_name,
            filtered_data_json=filtered_data_json,
            aggregated_data=aggregated_data
        )
        
        # 파일 저장
        division_path = Path(OUTPUT_BASE_DIR) / safe_filename(division_name)
        file_name = f"서울아산병원_협업평가_대시보드_{safe_filename(department_name)}.html"
        output_path = division_path / file_name
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        log_message(f"✅ {department_name} 보고서 생성 완료: {len(filtered_data)}건 데이터")
        return True
        
    except Exception as e:
        log_message(f"❌ {department_name} 보고서 생성 실패: {str(e)}", "ERROR")
        return False

def main():
    """
    메인 실행 함수 - 모든 부서 보고서 생성
    """
    try:
        log_message("=" * 70)
        log_message("🚀 서울아산병원 협업 평가 대시보드 - 전체 부서 보고서 생성 시작")
        log_message(f"📅 실행 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}")
        log_message("=" * 70)
        
        # 1. 데이터 로드 및 전처리
        df = load_excel_data()
        df = preprocess_data_types(df)
        df = clean_data(df)
        
        # 2. 부서 및 부문 정보 추출
        divisions = get_all_departments(df)
        
        # 3. 집계 데이터 계산
        aggregated_data = calculate_aggregated_data(df)
        
        # 4. 출력 디렉토리 구조 생성
        create_output_directory_structure(divisions)
        
        # 5. 부서별 보고서 생성
        log_message("🏭 부서별 보고서 생성 시작")
        
        total_departments = sum(len(depts) for depts in divisions.values())
        success_count = 0
        failed_count = 0
        
        for division_name, departments in divisions.items():
            log_message(f"📂 {division_name} 부문 처리 시작 ({len(departments)}개 부서)")
            
            for department_name in departments:
                success = generate_department_report(
                    department_name=department_name,
                    division_name=division_name,
                    df=df,
                    aggregated_data=aggregated_data
                )
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
            
            log_message(f"✅ {division_name} 부문 처리 완료")
        
        # 6. 실행 결과 요약
        log_message("=" * 70)
        log_message("🎉 전체 부서 보고서 생성 완료!")
        log_message("=" * 70)
        log_message(f"📂 출력 디렉토리: {OUTPUT_BASE_DIR}")
        log_message(f"📊 처리된 데이터: {len(df):,}건")
        log_message(f"🏢 총 부문 수: {len(divisions)}개")
        log_message(f"✅ 성공한 부서: {success_count}개")
        if failed_count > 0:
            log_message(f"❌ 실패한 부서: {failed_count}개", "WARNING")
        log_message(f"📈 성공률: {(success_count / total_departments * 100):.1f}%")
        log_message("=" * 70)
        log_message("📋 부문별 생성 현황:")
        for division_name, departments in divisions.items():
            log_message(f"  📂 {division_name}: {len(departments)}개 부서")
        
        return success_count, failed_count
        
    except Exception as e:
        log_message(f"❌ 전체 프로세스 실패: {str(e)}", "ERROR")
        log_message(f"🔍 상세 오류: {traceback.format_exc()}", "DEBUG")
        return 0, 1

if __name__ == "__main__":
    try:
        success_count, failed_count = main()
        
        # 종료 코드 설정
        if failed_count > 0:
            sys.exit(1)  # 실패가 있으면 에러 코드로 종료
        else:
            sys.exit(0)  # 모두 성공하면 정상 종료
            
    except KeyboardInterrupt:
        log_message("⚠️ 사용자에 의해 중단되었습니다.", "WARNING")
        sys.exit(1)
    except Exception as e:
        log_message(f"❌ 예상치 못한 오류: {str(e)}", "ERROR")
        sys.exit(1)