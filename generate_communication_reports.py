#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
서울아산병원 협업 평가 대시보드 - 커뮤니케이션실 부서별 보고서 생성기

이 파일은 커뮤니케이션실 산하 모든 부서에 대한 개별 보고서를 자동으로 생성합니다.
기존 '고객만족팀' 보고서의 UI/UX와 모든 기능을 그대로 유지합니다.

📋 주요 기능:
1. 커뮤니케이션실 산하 부서 목록 자동 추출
2. 부서별 맞춤 대시보드 HTML 생성
3. 배치 실행 및 진행 상황 추적

🔧 사용 방법:
- python generate_communication_reports.py

작성자: Claude AI
버전: 1.0 (커뮤니케이션실 부서별 자동 생성판)
업데이트: 2025년 7월 14일
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import ast
import sys
from pathlib import Path
from datetime import datetime
import traceback

# ============================================================================
# 🔧 설정 및 상수 정의 (이 부분을 수정하여 설정 변경)
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
TARGET_DIVISION = "커뮤니케이션실" # 보고서를 생성할 대상 부문

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

# 📝 결측값 처리 설정
FILL_NA_COLUMNS = ['피평가부문', '피평가부서', '피평가Unit', '정제된_텍스트']  # 'N/A'로 채울 컬럼들
EXCLUDE_VALUES = ['미분류', '윤리경영실']  # 제외할 값들

# 📊 대시보드 정보
DASHBOARD_SUBTITLE = "설문 데이터: 2022년 ~ 2025년 상반기(2025년 7월 14일 기준)"

# ============================================================================
# 🛠️ 유틸리티 함수들
# ============================================================================

def log_message(message, level="INFO"):
    """
    실행 과정을 추적하기 위한 로그 메시지 출력
    
    Args:
        message (str): 출력할 메시지
        level (str): 로그 레벨 ("INFO", "WARNING", "ERROR")
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    icon = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "📝")
    print(f"[{timestamp}] {icon} {level}: {message}")

def check_file_exists(file_path):
    """
    파일이 존재하는지 확인
    
    Args:
        file_path (str): 확인할 파일 경로
        
    Returns:
        bool: 파일 존재 여부
    """
    return Path(file_path).exists()

# ============================================================================
# 📊 개선된 데이터 로드 및 전처리 함수들
# ============================================================================

def safe_literal_eval(s):
    """
    문자열을 안전하게 파이썬 리터럴(리스트)로 변환
    """
    if isinstance(s, str) and s.startswith('[') and s.endswith(']'):
        try:
            return ast.literal_eval(s)
        except (ValueError, SyntaxError):
            log_message(f"키워드 파싱 실패: {s}", "WARNING")
            return []
    return []

def load_excel_data(file_path=INPUT_DATA_FILE):
    """
    엑셀 파일에서 데이터를 로드하고 기본 검증 수행
    """
    try:
        log_message("📁 엑셀 데이터 로드 시작")
        if not check_file_exists(file_path):
            raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {file_path}")
        
        df = pd.read_excel(file_path)
        log_message(f"✅ 원본 데이터 로드 완료: {len(df):,}행 × {len(df.columns)}열")
        
        if len(df.columns) != len(EXCEL_COLUMNS):
            log_message(f"⚠️ 컬럼 수 불일치: 예상 {len(EXCEL_COLUMNS)}개, 실제 {len(df.columns)}개", "WARNING")
        
        df.columns = EXCEL_COLUMNS
        log_message("📋 컬럼명 설정 완료")
        
        column_mapping = {
            '설문시행연도': '설문시행연도', '평가_부서명': '평가부서', '평가_부문': '평가부문',  
            '피평가대상 부서명': '피평가부서', '피평가대상 부문': '피평가부문', '피평가대상 UNIT명': '피평가Unit',
            '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.': '존중배려',
            '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.': '정보공유',
            '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.': '명확처리',
            '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.': '태도개선',
            '전반적으로 ○○과의 협업에 대해 만족한다.': '전반만족',
            '종합점수': '종합점수', '협업 후기': '협업후기'
        }
        df = df.rename(columns=column_mapping)
        log_message("🔄 컬럼명 매핑 완료")
        return df
        
    except FileNotFoundError as e:
        log_message(str(e), "ERROR")
        raise
    except Exception as e:
        log_message(f"데이터 로드 중 오류 발생: {str(e)}", "ERROR")
        raise

def preprocess_data_types(df):
    """
    데이터 타입 변환 및 기본 전처리
    """
    log_message("🔄 데이터 타입 변환 시작")
    df['설문시행연도'] = df['설문시행연도'].astype(str)
    
    for col in SCORE_COLUMNS:
        if col in df.columns:
            original_count = df[col].notna().sum()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            converted_count = df[col].notna().sum()
            if original_count != converted_count:
                log_message(f"⚠️ {col}: {original_count - converted_count}개 값이 숫자 변환 실패", "WARNING")
    
    if '핵심_키워드' in df.columns:
        df['핵심_키워드'] = df['핵심_키워드'].apply(safe_literal_eval)
        log_message("🔍 핵심 키워드 파싱 완료")
    
    log_message("✅ 데이터 타입 변환 완료")
    return df

def clean_data(df):
    """
    데이터 정제 및 품질 개선
    """
    log_message("🧹 데이터 정제 시작")
    original_count = len(df)
    
    for exclude_value in EXCLUDE_VALUES:
        condition = (df['평가부문'] != exclude_value) & (df['피평가부문'] != exclude_value)
        df = df[condition]
    
    excluded_count = original_count - len(df)
    if excluded_count > 0:
        log_message(f"🗑️ 제외된 데이터(미분류 등): {excluded_count}행 ({excluded_count/original_count*100:.1f}%)")
    
    df = df.dropna(subset=['종합점수'])
    final_count = len(df)
    
    for col in FILL_NA_COLUMNS:
        if col in df.columns:
            na_count = df[col].isna().sum()
            if na_count > 0:
                df[col] = df[col].fillna('N/A')
                log_message(f"📝 {col}: {na_count}개 결측값을 'N/A'로 처리")
    
    log_message(f"✅ 데이터 정제 완료: {original_count:,}행 → {final_count:,}행")
    return df

# ============================================================================
# 🔒 보안 강화 함수들 (하이브리드 데이터 접근 방식)
# ============================================================================

def calculate_aggregated_data(df, division_name):
    """
    섹션 1-4용 집계 데이터 미리 계산 (보안 강화)
    """
    log_message(f"🔒 '{division_name}' 부문 집계 데이터 계산 시작")
    
    division_departments = sorted(list(df[df['피평가부문'] == division_name]['피평가부서'].unique()))

    aggregated = {
        "hospital_yearly": {}, "division_yearly": {}, "division_comparison": {}, "team_ranking": {},
        "metadata": {
            "calculation_date": datetime.now().isoformat(), "total_responses": len(df),
            "target_division": division_name, "division_departments": division_departments
        }
    }
    
    # 1. [전체] 연도별 문항 점수
    for year in df['설문시행연도'].unique():
        if pd.notna(year):
            year_data = df[df['설문시행연도'] == year]
            aggregated["hospital_yearly"][str(year)] = {
                col: float(year_data[col].mean()) if col in year_data.columns else 0.0 for col in SCORE_COLUMNS
            }
            aggregated["hospital_yearly"][str(year)]["응답수"] = len(year_data)
    
    # 2. [부문별] 연도별 문항 점수
    div_data = df[df['피평가부문'] == division_name]
    aggregated["division_yearly"][division_name] = {}
    for year in div_data['설문시행연도'].unique():
        if pd.notna(year):
            year_data = div_data[div_data['설문시행연도'] == year]
            aggregated["division_yearly"][division_name][str(year)] = {
                col: float(year_data[col].mean()) if col in year_data.columns else 0.0 for col in SCORE_COLUMNS
            }
            aggregated["division_yearly"][division_name][str(year)]["응답수"] = len(year_data)
    
    # 3. 연도별 부문 비교
    for year in df['설문시행연도'].unique():
        if pd.notna(year):
            year_str, year_data = str(year), df[df['설문시행연도'] == year]
            aggregated["division_comparison"][year_str] = {}
            for division in df['피평가부문'].unique():
                if pd.notna(division) and division != 'N/A':
                    div_year_data = year_data[year_data['피평가부문'] == division]
                    if len(div_year_data) > 0:
                        aggregated["division_comparison"][year_str][division] = {
                            col: float(div_year_data[col].mean()) if col in div_year_data.columns else 0.0 for col in SCORE_COLUMNS
                        }
                        aggregated["division_comparison"][year_str][division]["응답수"] = len(div_year_data)
    
    # 4. 부문별 팀 점수 순위
    for year in div_data['설문시행연도'].unique():
        if pd.notna(year):
            year_str, year_data = str(year), div_data[div_data['설문시행연도'] == year]
            dept_scores = []
            for dept in year_data['피평가부서'].unique():
                if pd.notna(dept):
                    dept_data = year_data[year_data['피평가부서'] == dept]
                    avg_score = dept_data['종합점수'].mean() if len(dept_data) > 0 else 0.0
                    dept_scores.append({"department": dept, "score": round(float(avg_score), 1), "count": len(dept_data)})
            
            dept_scores.sort(key=lambda x: x["score"], reverse=True)
            for i, dept in enumerate(dept_scores): dept["rank"] = i + 1
            aggregated["team_ranking"][year_str] = dept_scores
    
    log_message(f"✅ 집계 데이터 계산 완료: {len(aggregated['hospital_yearly'])}년치 데이터")
    return aggregated

def prepare_department_filtered_data(df, target_department):
    """
    섹션 5-6용 부서별 필터링된 데이터 준비
    """
    log_message(f"🔒 부서별 필터링 시작: {target_department}")
    dept_data = df[df['피평가부서'] == target_department].copy()
    safe_columns = [
        '설문시행연도', '평가부서', '피평가부문', '피평가부서', '피평가Unit',
        '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수',
        '정제된_텍스트', '감정_분류', '핵심_키워드'
    ]
    available_columns = [col for col in safe_columns if col in dept_data.columns]
    filtered_data = dept_data[available_columns].copy()
    filtered_json = filtered_data.to_json(orient='records', force_ascii=False)
    log_message(f"✅ 부서별 필터링 완료: {len(filtered_data):,}건")
    return filtered_json

def build_secure_html(aggregated_data, filtered_rawdata, target_department):
    """
    보안 강화된 HTML 생성 (하이브리드 데이터 구조)
    """
    log_message(f"🔒 보안 강화 HTML 생성: {target_department}")
    security_metadata = {
        "target_department": target_department,
        "data_scope": f"{target_department} 관련 데이터만 포함",
        "security_level": "HIGH",
        "aggregated_sections": ["전체 연도별", "부문별 연도별", "부문 비교", "팀 순위"],
        "filtered_sections": ["부서 상세분석", "네트워크 분석"]
    }
    
    import json
    hybrid_data = {
        "aggregated": aggregated_data,
        "rawData": json.loads(filtered_rawdata) if isinstance(filtered_rawdata, str) else filtered_rawdata,
        "security": security_metadata
    }
    
    return build_html_with_hybrid_data(hybrid_data, target_department)

def build_html_with_hybrid_data(hybrid_data, target_department):
    """보안 강화된 하이브리드 데이터 구조로 HTML 생성"""
    import json
    hybrid_data_json = json.dumps(hybrid_data, ensure_ascii=False, default=str)
    dashboard_title = f"서울아산병원 협업 평가 대시보드 - {target_department}"

    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>{dashboard_title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; color: #343a40; font-size: 16px;}}
        .container {{ max-width: 1400px; margin: auto; padding: 20px; }}
        .header {{ background: linear-gradient(90deg, #4a69bd, #6a89cc); color: white; padding: 25px; text-align: center; border-radius: 0 0 10px 10px; }}
        .container {{ counter-reset: section-counter; }}
        .section {{ counter-reset: subsection-counter; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 30px; }}
        .section h2::before {{ counter-increment: section-counter; content: counter(section-counter) ". "; color: #4a69bd; font-weight: bold; }}
        .section h3::before {{ counter-increment: subsection-counter; content: counter(section-counter) "." counter(subsection-counter) " "; color: #6a89cc; font-weight: bold; }}
        h1, h2, h3 {{ margin: 0; padding: 0; }}
        h2 {{ color: #4a69bd; border-bottom: 3px solid #6a89cc; padding-bottom: 10px; margin-top: 20px; margin-bottom: 20px; }}
        h3 {{ color: #555; margin-top: 30px; margin-bottom: 15px;}}
        .part-divider {{ background: linear-gradient(90deg, #e9ecef, #6c757d, #e9ecef); height: 3px; margin: 40px 0; border-radius: 2px; }}
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
        #reviews-table-container, #keyword-reviews-table-container, #network-reviews-table-container {{ max-height: 400px; overflow-y: auto; margin-top: 20px; border: 1px solid #dee2e6; border-radius: 5px; }}
        #reviews-table, #keyword-reviews-table, #network-reviews-table {{ width: 100%; border-collapse: collapse; }}
        #reviews-table th, #reviews-table td, #keyword-reviews-table th, #keyword-reviews-table td, #network-reviews-table th, #network-reviews-table td {{ padding: 12px; border-bottom: 1px solid #dee2e6; text-align: left; }}
        #reviews-table th, #keyword-reviews-table th, #network-reviews-table th {{ background-color: #f8f9fa; position: sticky; top: 0; }}
        .keyword-charts-container {{ display: flex; gap: 20px; }}
        .keyword-chart {{ flex: 1; }}
        .chart-container {{ margin: 20px 0; }}
        .subsection {{ margin: 30px 0; }}
        #collaboration-frequency-chart-container {{ max-height: 600px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 5px; }}
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
        <h1>{dashboard_title}</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">{DASHBOARD_SUBTITLE}</p>
    </div>
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
        <div class="section">
            <h2>[전체] 연도별 문항 점수</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">우리 병원의 점수 트렌드를 파악합니다.</p>
            <div class="filters">
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="hospital-score-header" onclick="toggleExpander('hospital-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="hospital-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="hospital-score-expander"><div id="hospital-score-filter"></div></div>
                    </div>
                </div>
            </div>
            <div id="hospital-yearly-chart-container" class="chart-container"></div>
        </div>
        <div class="part-divider"></div>
        <div class="section">
            <h2>[부문별] 연도별 문항 점수</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">부문별 점수 트렌드를 파악합니다.</p>
            <div class="filters">
                <div class="filter-group"><label for="division-chart-filter">��문 선택</label><select id="division-chart-filter"></select></div>
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="division-score-header" onclick="toggleExpander('division-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="division-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="division-score-expander"><div id="division-score-filter"></div></div>
                    </div>
                </div>
            </div>
            <div id="division-yearly-chart-container" class="chart-container"></div>
        </div>
        <div class="section">
            <h2>연도별 부문 비교</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">특정 연도의 부문간 점수를 비교합니다.</p>
            <div class="filters">
                <div class="filter-group"><label for="comparison-year-filter">연도 선택</label><select id="comparison-year-filter"></select></div>
                <div class="filter-group">
                    <label>부문 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="comparison-division-header" onclick="toggleExpander('comparison-division-expander')">
                            <span>부문 선택 (0개 선택됨)</span>
                            <span class="expander-arrow" id="comparison-division-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="comparison-division-expander"><div id="comparison-division-filter"></div></div>
                    </div>
                </div>
            </div>
            <div id="comparison-chart-container" class="chart-container"></div>
        </div>
        <div class="part-divider"></div>
        <div class="section">
            <h2>부문별 팀 점수 순위</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">부문 내 부서간 점수를 파악합니다.</p>
            <div class="filters">
                <div class="filter-group"><label for="team-ranking-year-filter">연도 선택</label><select id="team-ranking-year-filter"></select></div>
                <div class="filter-group"><label for="team-ranking-division-filter">부문 선택</label><select id="team-ranking-division-filter"></select></div>
            </div>
            <div id="team-ranking-chart-container" class="chart-container"></div>
        </div>
        <div class="part-divider"></div>
        <div class="section">
            <h2>부서/Unit 상세 분석</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">부서와 Unit이 받은 점수 및 후기를 파악합니다.</p>
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
                        <div class="expander-content" id="drilldown-score-expander"><div id="drilldown-score-filter"></div></div>
                    </div>
                </div>
            </div>
            <div class="subsection">
                <h3>기본 지표 및 점수 트렌드</h3>
                <div id="metrics-container"></div>
                <div id="drilldown-chart-container" class="chart-container"></div>
                <div id="yearly-comparison-chart-container" class="chart-container"></div>
                <div style="margin-top: 30px;">
                    <h4 style="color: #555; margin-bottom: 15px;">부서 내 Unit 비교</h4>
                    <p style="color: #6c757d; margin-bottom: 20px; font-size: 0.9em;">부서 내 Unit간 점수를 파악합니다.</p>
                    <div id="unit-comparison-chart-container" class="chart-container"></div>
                </div>
            </div>
            <div class="subsection">
                <h3>협업 주관식 피드백 감정 분석</h3>
                <div id="sentiment-chart-container" class="chart-container"></div>
            </div>
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
                        <em>예시: "신속한" 키��드 클릭 → "신속한 응답으로 업무가 원활했다" 등의 후기 표시</em>
                    </p>
                </div>
                <div class="keyword-charts-container">
                    <div id="positive-keywords-chart" class="keyword-chart"></div>
                    <div id="negative-keywords-chart" class="keyword-chart"></div>
                </div>
                <div id="keyword-reviews-container"></div>
            </div>
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
                            <div class="expander-content" id="review-sentiment-expander"><div id="review-sentiment-filter"></div></div>
                        </div>
                    </div>
                </div>
                <div id="reviews-table-container"><table id="reviews-table"><thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody></tbody></table></div>
            </div>
        </div>
        <div class="part-divider"></div>
        <div class="section">
            <h2>협업 네트워크 분석</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">🔍 우리 팀/Unit과 협업을 하는 팀/Unit과의 관계를 종합적으로 분석합니다.</p>
            <div class="filters">
                <div class="filter-group"><label for="network-year-filter">연도 (전체)</label><select id="network-year-filter"></select></div>
                <div class="filter-group"><label for="network-division-filter">부문</label><select id="network-division-filter"></select></div>
                <div class="filter-group"><label for="network-department-filter">부서</label><select id="network-department-filter"></select></div>
                <div class="filter-group"><label for="network-unit-filter">Unit</label><select id="network-unit-filter"></select></div>
                <div class="filter-group">
                    <label for="min-collaboration-filter">최소 협업 횟수</label>
                    <select id="min-collaboration-filter">
                        <option value="5">5회 이상</option><option value="10" selected>10회 이상</option><option value="30">30회 이상</option>
                    </select>
                </div>
            </div>
            <div class="subsection">
                <h3>협업을 많이 하는 부서</h3>
                <div id="collaboration-frequency-chart-container" class="chart-container"></div>
            </div>
            <div class="subsection">
                <h3>협업 관계 현황</h3>
                <div id="collaboration-status-chart-container" class="chart-container"></div>
                <div class="collaboration-status-dropdowns">
                    <div class="status-dropdown excellent">
                        <h5>🏆 우수 (75점 이상)</h5>
                        <div class="expander-container">
                            <div class="expander-header" id="excellent-dept-header" onclick="toggleExpander('excellent-dept-expander')"><span>부서 선택 (0개 선택됨)</span><span class="expander-arrow" id="excellent-dept-arrow">▼</span></div>
                            <div class="expander-content" id="excellent-dept-expander"><div id="excellent-dept-filter"></div></div>
                        </div>
                        <div class="dept-count" id="excellent-count">0개 관계</div>
                    </div>
                    <div class="status-dropdown good">
                        <h5>✅ 양호 (60-74점)</h5>
                        <div class="expander-container">
                            <div class="expander-header" id="good-dept-header" onclick="toggleExpander('good-dept-expander')"><span>부서 선택 (0개 선택됨)</span><span class="expander-arrow" id="good-dept-arrow">▼</span></div>
                            <div class="expander-content" id="good-dept-expander"><div id="good-dept-filter"></div></div>
                        </div>
                        <div class="dept-count" id="good-count">0개 관계</div>
                    </div>
                    <div class="status-dropdown caution">
                        <h5>⚠️ 주의 (50-59점)</h5>
                        <div class="expander-container">
                            <div class="expander-header" id="caution-dept-header" onclick="toggleExpander('caution-dept-expander')"><span>부서 선택 (0개 선택됨)</span><span class="expander-arrow" id="caution-dept-arrow">▼</span></div>
                            <div class="expander-content" id="caution-dept-expander"><div id="caution-dept-filter"></div></div>
                        </div>
                        <div class="dept-count" id="caution-count">0개 관계</div>
                    </div>
                    <div class="status-dropdown problem">
                        <h5>🚨 문제 (50점 미만)</h5>
                        <div class="expander-container">
                            <div class="expander-header" id="problem-dept-header" onclick="toggleExpander('problem-dept-expander')"><span>부서 선택 (0개 선택됨)</span><span class="expander-arrow" id="problem-dept-arrow">▼</span></div>
                            <div class="expander-content" id="problem-dept-expander"><div id="problem-dept-filter"></div></div>
                        </div>
                        <div class="dept-count" id="problem-count">0개 관계</div>
                    </div>
                </div>
            </div>
            <div class="subsection">
                <h3>협업 관계 변화 트렌드</h3>
                <div id="collaboration-trend-chart-container" class="chart-container"></div>
            </div>
            <div class="subsection">
                <h3>협업 후기 <span id="network-reviews-count-display" style="color: #666; font-size: 0.9em;"></span></h3>
                <div class="filters">
                    <div class="filter-group">
                        <label>감정 분류 필터</label>
                        <select id="network-sentiment-filter">
                            <option value="전체">전체 (긍정+부정+중립)</option><option value="긍정">긍정</option><option value="부정">부정</option><option value="중립">중립</option>
                        </select>
                    </div>
                </div>
                <div id="network-reviews-table-container"><table id="network-reviews-table"><thead><tr><th style="width: 80px;">연도</th><th style="width: 120px;">협업 부서</th><th>후기 내용</th></tr></thead><tbody></tbody></table></div>
            </div>
        </div>
    </div>
    <script>
        const hybridData = {hybrid_data_json};
        const rawData = hybridData.rawData;
        const aggregatedData = hybridData.aggregated;
        const securityInfo = hybridData.security;
        const targetDepartment = securityInfo.target_department;
        const targetDivision = aggregatedData.metadata.target_division;
        const divisionDepartments = aggregatedData.metadata.division_departments;
        
        const scoreCols = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수'];
        const allYears = [...new Set(rawData.map(item => item['설문시행연도']))].sort();
        const allDivisions = Object.keys(aggregatedData.division_comparison).length > 0 
            ? [...new Set(Object.values(aggregatedData.division_comparison).flatMap(yearData => Object.keys(yearData)))].sort((a, b) => a.localeCompare(b, 'ko'))
            : [targetDivision];
        const layoutFont = {{ size: 14 }};
        
        console.log('🔒 보안 정보:', securityInfo);

        const departmentUnitMap = rawData.reduce((acc, item) => {{
            const dept = item['피평가부서'];
            const unit = item['피평가Unit'];
            if (dept && dept !== 'N/A' && unit && unit !== 'N/A') {{
                if (!acc[dept]) {{ acc[dept] = new Set(); }}
                acc[dept].add(unit);
            }}
            return acc;
        }}, {{}});
        for (const dept in departmentUnitMap) {{
            departmentUnitMap[dept] = [...departmentUnitMap[dept]].sort((a, b) => String(a).localeCompare(String(b), 'ko'));
        }}

        function populateFilters() {{
            const yearSelect = document.getElementById('year-filter');
            const years = [...new Set(rawData.map(item => item['설문시행연도']))].sort((a, b) => String(a).localeCompare(String(b), 'ko'));
            yearSelect.innerHTML = ['전체', ...years].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.addEventListener('change', updateDashboard);
            
            const deptSelect = document.getElementById('department-filter');
            deptSelect.innerHTML = `<option value="${{targetDepartment}}">${{targetDepartment}}</option>`;
            deptSelect.value = targetDepartment;
            deptSelect.addEventListener('change', updateUnitFilter);
            
            updateUnitFilter();
        }}

        function updateUnitFilter() {{
            const deptSelect = document.getElementById('department-filter');
            const unitSelect = document.getElementById('unit-filter');
            const selectedDept = deptSelect.value;

            const allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
            const units = (selectedDept === '전체' || !departmentUnitMap[selectedDept]) ? allUnits : departmentUnitMap[selectedDept];
            unitSelect.innerHTML = ['전체', ...units].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            unitSelect.value = '전체';
            unitSelect.addEventListener('change', updateDashboard);
        }}

        function setupDivisionChart() {{
            const select = document.getElementById('division-chart-filter');
            select.innerHTML = `<option value="${{targetDivision}}">${{targetDivision}}</option>`;
            select.value = targetDivision;
            select.addEventListener('change', updateDivisionYearlyChart);
            createCheckboxFilter('division-score-filter', scoreCols, 'division-score', updateDivisionYearlyChart);
            updateDivisionYearlyChart();
        }}
        
        function setupComparisonChart() {{
            const yearSelect = document.getElementById('comparison-year-filter');
            yearSelect.innerHTML = allYears.map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = allYears[allYears.length - 1];
            yearSelect.addEventListener('change', updateYearlyDivisionComparisonChart);
            createCheckboxFilter('comparison-division-filter', allDivisions, 'comparison-division', updateYearlyDivisionComparisonChart, true);
        }}

        function getFilteredData() {{
            let filteredData = [...rawData];
            const filters = {{ 'year-filter': '설문시행연도', 'department-filter': '피평가부서', 'unit-filter': '피평가Unit' }};
            for (const [elementId, dataCol] of Object.entries(filters)) {{
                const selectedValue = document.getElementById(elementId).value;
                if (selectedValue !== '전체') {{ filteredData = filteredData.filter(item => item[dataCol] == selectedValue); }}
            }}
            return filteredData;
        }}

        function updateDashboard() {{
            const filteredData = getFilteredData();
            updateMetrics(filteredData);
            updateDrilldownChart(filteredData);
            updateSentimentChart(filteredData);
            updateReviewsTable(filteredData);
            updateKeywordAnalysis(filteredData);
            updateYearlyComparisonChart();
            updateUnitComparisonChart();
        }}
        
        function calculateAverages(data) {{
            const averages = {{}};
            scoreCols.forEach(col => {{
                const total = data.reduce((sum, item) => sum + (item[col] || 0), 0);
                averages[col] = data.length > 0 ? (total / data.length) : 0;
            }});
            return averages;
        }}

        function updateMetrics(data) {{
            const container = document.getElementById('metrics-container');
            if (data.length === 0) {{ container.innerHTML = "<p style='text-align:center;'>선택된 조건에 해당하는 데이터가 없습니다.</p>"; return; }}
            const averages = calculateAverages(data);
            container.innerHTML = `<div class="metric"><div class="metric-value">${{data.length}}</div><div class="metric-label">응답 수</div></div><div class="metric"><div class="metric-value">${{averages['종합점수'].toFixed(1)}}</div><div class="metric-label">종합점수</div></div>`;
        }}
        
        function updateDrilldownChart(data) {{
            const container = document.getElementById('drilldown-chart-container');
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);
            if (data.length === 0 || selectedScores.length === 0) {{ 
                const message = data.length > 0 ? '표시할 문항을 선택해주세요.' : '';
                Plotly.react(container, [], {{ height: 400, annotations: [{{ text: message, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }});
                return;
            }}
            const averages = calculateAverages(data);
            const chartData = [{{ x: selectedScores, y: selectedScores.map(col => averages[col].toFixed(1)), type: 'bar', text: selectedScores.map(col => averages[col].toFixed(1)), textposition: 'outside', textfont: {{ size: 14 }}, marker: {{ color: '#6a89cc' }}, hovertemplate: '%{{x}}: %{{y}}<extra></extra>' }}];
            const selectedYear = document.getElementById('year-filter').value;
            const selectedDept = document.getElementById('department-filter').value;
            const selectedUnit = document.getElementById('unit-filter').value;
            let titleParts = [];
            if (selectedDept !== '전체') {{ titleParts.push(selectedDept); }}
            if (selectedUnit !== '전체') {{ titleParts.push(selectedUnit); }}
            const titlePrefix = titleParts.length > 0 ? titleParts.join(' > ') : '부서, Unit';
            const yearSuffix = selectedYear === '전체' ? ' (전체 연도)' : ` (${{selectedYear}})`;
            const title = `<b>${{titlePrefix}} 문항 점수${{yearSuffix}}</b>`;
            const layout = {{ title: title, yaxis: {{ title: '점수', range: [0, 100] }}, font: layoutFont, hovermode: 'closest', margin: {{ l: 60, r: 60, t: 80, b: 60 }} }};
            Plotly.react(container, chartData, layout);
        }}
        
        function updateHospitalYearlyChart() {{
            const container = document.getElementById('hospital-yearly-chart-container');
            const selectedScores = Array.from(document.querySelectorAll('input[name="hospital-score"]:checked')).map(cb => cb.value);
            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{ height: 500, annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }});
                return;
            }}
            const hospitalData = aggregatedData.hospital_yearly;
            const years = Object.keys(hospitalData).sort();
            const traces = [];
            selectedScores.forEach(col => {{
                const y_values = years.map(year => hospitalData[year][col] ? hospitalData[year][col].toFixed(1) : '0.0');
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            const yearly_counts = years.map(year => hospitalData[year]['응답수'] || 0);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3 }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}건`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}건<br>연도: %{{x}}<extra></extra>' }});
            const layout = {{ title: '<b>[전체] 연도별 문항 점수</b>', barmode: 'group', height: 500, xaxis: {{ type: 'category', title: '설문 연도' }}, yaxis: {{ title: '점수', range: [0, 100] }}, yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }}, legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'right', x: 1 }}, font: layoutFont, hovermode: 'closest', margin: {{ l: 60, r: 60, t: 120, b: 60 }} }};
            Plotly.react(container, traces, layout);
        }}

        function updateDivisionYearlyChart() {{
            const container = document.getElementById('division-yearly-chart-container');
            const selectedDivision = document.getElementById('division-chart-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="division-score"]:checked')).map(cb => cb.value);
            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{ height: 500, annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }});
                return;
            }}
            const divisionData = aggregatedData.division_yearly[selectedDivision] || {{}};
            const years = Object.keys(divisionData).sort();
            const traces = [];
            selectedScores.forEach(col => {{
                const y_values = years.map(year => divisionData[year] && divisionData[year][col] ? divisionData[year][col].toFixed(1) : '0.0');
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            const yearly_counts = years.map(year => divisionData[year] ? divisionData[year]['응답수'] || 0 : 0);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3 }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}건`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}건<br>연도: %{{x}}<extra></extra>' }});
            const layout = {{ title: `<b>[${{selectedDivision}}] 연도별 문항 점수</b>`, barmode: 'group', height: 500, xaxis: {{ type: 'category', title: '설문 연도' }}, yaxis: {{ title: '점수', range: [0, 100] }}, yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }}, legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'right', x: 1 }}, font: layoutFont, hovermode: 'closest', margin: {{ l: 60, r: 60, t: 120, b: 60 }} }};
            Plotly.react(container, traces, layout);
        }}

        function updateYearlyDivisionComparisonChart() {{
            const container = document.getElementById('comparison-chart-container');
            const selectedYear = document.getElementById('comparison-year-filter').value;
            const selectedDivisions = Array.from(document.querySelectorAll('input[name="comparison-division"]:checked')).map(cb => cb.value);
            if (selectedDivisions.length === 0) {{
                Plotly.react(container, [], {{ height: 500, annotations: [{{ text: '비교할 부문을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }});
                return;
            }}
            const comparisonData = aggregatedData.division_comparison[selectedYear] || {{}};
            const divisions = selectedDivisions.filter(div => comparisonData[div]).sort((a,b) => a.localeCompare(b, 'ko'));
            const avgScores = divisions.map(div => comparisonData[div]['종합점수'] ? comparisonData[div]['종합점수'].toFixed(1) : '0.0');
            const trace = [{{ x: divisions, y: avgScores, type: 'bar', text: avgScores, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{x}}: %{{y}}<extra></extra>' }}];
            const layout = {{ title: `<b>${{selectedYear}} 부문별 점수 비교</b>`, yaxis: {{ title: '점수', range: [0, 100] }}, font: layoutFont, height: 500, barmode: 'group', hovermode: 'closest', margin: {{ l: 60, r: 60, t: 80, b: 60 }} }};
            Plotly.react(container, trace, layout);
        }}

        function updateSentimentChart(data) {{
            const container = document.getElementById('sentiment-chart-container');
            if (data.length === 0) {{
                Plotly.react(container, [], {{ height: 400, annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }});
                return;
            }}
            const validSentimentData = data.filter(item => {{ const sentiment = item['감정_분류']; return sentiment && sentiment !== 'N/A' && sentiment !== '알 수 없음'; }});
            if (validSentimentData.length === 0) {{
                Plotly.react(container, [], {{ height: 400, annotations: [{{ text: '감정 분류 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }});
                return;
            }}
            const sentimentCounts = {{}};
            validSentimentData.forEach(item => {{ const sentiment = item['감정_분류']; sentimentCounts[sentiment] = (sentimentCounts[sentiment] || 0) + 1; }});
            const desiredOrder = ['긍정', '부정', '중립'];
            const sentiments = desiredOrder.filter(sentiment => sentimentCounts[sentiment] > 0);
            const counts = sentiments.map(sentiment => sentimentCounts[sentiment]);
            const total = counts.reduce((sum, count) => sum + count, 0);
            const percentages = counts.map(count => ((count / total) * 100).toFixed(1));
            const colorMap = {{ '긍정': '#2E8B57', '부정': '#DC143C', '중립': '#4682B4', '알 수 없음': '#808080' }};
            const colors = sentiments.map(sentiment => colorMap[sentiment] || '#808080');
            const trace = {{ x: sentiments, y: counts, type: 'bar', text: counts.map((count, idx) => `${{count}}건 (${{percentages[idx]}}%)`), textposition: 'outside', textfont: {{ size: 12 }}, marker: {{ color: colors }}, hovertemplate: '%{{x}}: %{{y}}건 (%{{text}})<extra></extra>' }};
            const layout = {{ title: '<b>감정 분류별 응답 분포</b>', height: 400, xaxis: {{ title: '감정 분류' }}, yaxis: {{ title: '응답 수', rangemode: 'tozero', range: [0, Math.max(...counts) * 1.15] }}, font: layoutFont, hovermode: 'closest', showlegend: false, margin: {{ l: 60, r: 60, t: 80, b: 60 }} }};
            Plotly.react(container, [trace], layout);
        }}

        function updateReviewsTable(data = null) {{
            const tbody = document.querySelector("#reviews-table tbody");
            if (data === null) {{ data = getFilteredData(); }}
            const selectedSentiments = Array.from(document.querySelectorAll('input[name="review-sentiment"]:checked')).map(cb => cb.value);
            let filteredData = data;
            if (selectedSentiments.length > 0 && !selectedSentiments.includes('전체')) {{
                filteredData = data.filter(item => selectedSentiments.includes(item['감정_분류']));
            }}
            const reviews = filteredData.map(item => ({{ year: item['설문시행연도'], review: item['정제된_텍스트'], sentiment: item['감정_분류'] || '알 수 없음' }})).filter(r => r.review && r.review !== 'N/A').sort((a, b) => b.year - a.year).slice(0, 50);
            const countDisplay = document.getElementById('reviews-count-display');
            if (countDisplay) {{ countDisplay.textContent = `(${{reviews.length}}건)`; }}
            tbody.innerHTML = (reviews.length > 0) ? reviews.map(r => `<tr><td>${{r.year}}</td><td>${{r.review}} <span style="color: #666; font-size: 0.9em;">[${{r.sentiment}}]</span></td></tr>`).join('') : '<tr><td colspan="2">해당 조건의 후기가 없습니다.</td></tr>';
        }}

        function updateKeywordAnalysis(data) {{
            const positiveCounts = {{}}; const negativeCounts = {{}};
            data.forEach(item => {{
                const keywords = item['핵심_키워드'];
                if (keywords && Array.isArray(keywords) && keywords.length > 0) {{
                    const sentiment = item['감정_분류'];
                    keywords.forEach(kw => {{
                        if (sentiment === '긍정') {{ positiveCounts[kw] = (positiveCounts[kw] || 0) + 1; }}
                        else if (sentiment === '부정') {{ negativeCounts[kw] = (negativeCounts[kw] || 0) + 1; }}
                    }});
                }}
            }});
            const topPositive = Object.entries(positiveCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
            const topNegative = Object.entries(negativeCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
            plotKeywordChart(document.getElementById('positive-keywords-chart'), '긍정 키워드 Top 10', topPositive, '긍정');
            plotKeywordChart(document.getElementById('negative-keywords-chart'), '부정 키워드 Top 10', topNegative, '부정');
            displayKeywordReviews(null, null, true);
        }}

        function plotKeywordChart(container, title, data, sentiment) {{
            if (data.length === 0) {{ Plotly.react(container, [], {{ title: `<b>${{title}}</b>`, height: 400, annotations: [{{ text: '데이터 없음', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false }}] }}); return; }}
            const trace = {{ y: data.map(d => d[0]).reverse(), x: data.map(d => d[1]).reverse(), type: 'bar', orientation: 'h', marker: {{ color: sentiment === '긍정' ? '#28a745' : '#dc3545' }}, hovertemplate: '언급 횟수: %{{x}}<extra></extra>' }};
            const layout = {{ title: `<b>${{title}}</b>`, height: 400, margin: {{ l: 120, r: 40, t: 80, b: 60 }}, xaxis: {{ title: '언급 횟수' }}, yaxis: {{ automargin: true }} }};
            Plotly.react(container, [trace], layout);
            container.removeAllListeners('plotly_click');
            container.on('plotly_click', (eventData) => {{ const keyword = eventData.points[0].y; displayKeywordReviews(keyword, sentiment); }});
        }}

        function displayKeywordReviews(keyword, sentiment, isInitial = false) {{
            const container = document.getElementById('keyword-reviews-container');
            if (isInitial) {{ container.innerHTML = `<h4>관련 리뷰</h4><p>위 그래프의 막대를 클릭하면 관련 리뷰를 확인할 수 있습니다.</p><div id="keyword-reviews-table-container"><table id="keyword-reviews-table"><thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody><tr><td colspan="2" style="text-align:center;"></td></tr></tbody></table></div>`; return; }}
            const filteredData = getFilteredData();
            const reviews = filteredData.filter(item => item['감정_분류'] === sentiment && Array.isArray(item['핵심_키워드']) && item['핵심_키워드'].includes(keyword));
            let content = `<h4>'${{keyword}}' (${{sentiment}}) 관련 리뷰 (${{reviews.length}}건)</h4>`;
            if (reviews.length > 0) {{
                content += `<div id="keyword-reviews-table-container"><table id="keyword-reviews-table"><thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody>`;
                content += reviews.slice(0, 50).map(r => `<tr><td>${{r['설문시행연도']}}</td><td>${{r['정제된_텍스트']}}</td></tr>`).join('');
                content += `</tbody></table></div>`;
            }} else {{ content += '<p>관련 리뷰가 없습니다.</p>'; }}
            container.innerHTML = content;
        }}

        function setupTeamRankingChart() {{
            const yearSelect = document.getElementById('team-ranking-year-filter');
            const divisionSelect = document.getElementById('team-ranking-division-filter');
            yearSelect.innerHTML = allYears.map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = allYears[allYears.length - 1];
            divisionSelect.innerHTML = `<option value="${{targetDivision}}">${{targetDivision}}</option>`;
            divisionSelect.value = targetDivision;
            yearSelect.addEventListener('change', updateTeamRankingChart);
            divisionSelect.addEventListener('change', updateTeamRankingChart);
            updateTeamRankingChart();
        }}

        function updateTeamRankingChart() {{
            const container = document.getElementById('team-ranking-chart-container');
            const selectedYear = document.getElementById('team-ranking-year-filter').value;
            const teamRankingData = aggregatedData.team_ranking[selectedYear] || [];
            const teamRankings = teamRankingData.filter(team => divisionDepartments.includes(team.department));
            if (teamRankings.length === 0) {{
                Plotly.react(container, [], {{ height: 600, annotations: [{{ text: '선택된 조건에 해당하는 부서 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }});
                return;
            }}
            const departments = teamRankings.map(item => item.department);
            const scores = teamRankings.map(item => parseFloat(item.score));
            const colors = teamRankings.map(item => '#9467bd');
            const hoverTexts = teamRankings.map(item => `부서: ${{item.department}}<br>순위: ${{item.rank}}위<br>점수: ${{item.score.toFixed(1)}}<br>응답수: ${{item.count}}건`);
            const yearlyOverallAverage = aggregatedData.hospital_yearly[selectedYear] ? aggregatedData.hospital_yearly[selectedYear]['종합점수'].toFixed(1) : '0.0';
            const trace = {{ x: departments, y: scores, type: 'bar', text: scores.map(score => score.toFixed(1)), textposition: 'outside', textfont: {{ size: 12 }}, marker: {{ color: colors }}, hovertemplate: '%{{hovertext}}<extra></extra>', hovertext: hoverTexts }};
            const avgLine = {{ x: [departments[0], departments[departments.length - 1]], y: [yearlyOverallAverage, yearlyOverallAverage], type: 'scatter', mode: 'lines', line: {{ color: 'red', width: 2, dash: 'dash' }}, name: `${{selectedYear}} 전체 평균: ${{yearlyOverallAverage}}`, hoverinfo: 'skip' }};
            const layout = {{ title: `<b>${{selectedYear}} 부문별 부서 점수 순위 (점수 높은 순)</b>`, height: 600, xaxis: {{ title: '부서', tickangle: -45, automargin: true }}, yaxis: {{ title: '점수', range: [Math.min(...scores) - 5, Math.max(...scores) + 5] }}, font: layoutFont, hovermode: 'closest', showlegend: false, legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }}, annotations: [{{ text: `${{selectedYear}} 전체 평균: ${{yearlyOverallAverage}}점`, xref: 'paper', yref: 'y', x: 0.02, y: parseFloat(yearlyOverallAverage), showarrow: false, font: {{ color: 'red', size: 12 }}, bgcolor: 'rgba(255,255,255,0.8)', bordercolor: 'red', borderwidth: 1 }}], margin: {{ l: 60, r: 60, t: 80, b: 100 }} }};
            Plotly.react(container, [trace, avgLine], layout);
        }}

        function updateYearlyComparisonChart() {{
            const container = document.getElementById('yearly-comparison-chart-container');
            const selectedDept = document.getElementById('department-filter').value;
            const selectedUnit = document.getElementById('unit-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);
            if (selectedScores.length === 0) {{ Plotly.react(container, [], {{ height: 500, annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); return; }}
            let targetData = [...rawData];
            if (selectedDept !== '전체') {{ targetData = targetData.filter(item => item['피평가부서'] === selectedDept); }}
            if (selectedUnit !== '전체') {{ targetData = targetData.filter(item => item['피평가Unit'] === selectedUnit); }}
            if (targetData.length === 0) {{ Plotly.react(container, [], {{ height: 500, annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); return; }}
            const years = [...new Set(targetData.map(item => item['설문시행연도']))].sort();
            const traces = [];
            selectedScores.forEach(col => {{
                const y_values = years.map(year => {{ const yearData = targetData.filter(d => d['설문시행연도'] === year); return yearData.length > 0 ? (yearData.reduce((sum, item) => sum + (item[col] || 0), 0) / yearData.length).toFixed(1) : 0; }});
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            const yearly_counts = years.map(year => targetData.filter(d => d['설문시행연도'] === year).length);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3 }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}건`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}건<br>연도: %{{x}}<extra></extra>' }});
            let titleText = '연도별 문항 점수';
            if (selectedDept !== '전체' && selectedUnit !== '전체') {{ titleText = `[${{selectedDept}} > ${{selectedUnit}}] 연도별 문항 점수`; }}
            else if (selectedDept !== '전체') {{ titleText = `[${{selectedDept}}] 연도별 문항 점수`; }}
            else if (selectedUnit !== '��체') {{ titleText = `[${{selectedUnit}}] 연도별 문항 점수`; }}
            const layout = {{ title: `<b>${{titleText}}</b>`, barmode: 'group', height: 500, xaxis: {{ type: 'category', title: '설문 연도' }}, yaxis: {{ title: '점수', range: [0, 100] }}, yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }}, legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'right', x: 1 }}, font: layoutFont, hovermode: 'closest', margin: {{ l: 60, r: 60, t: 120, b: 60 }} }};
            Plotly.react(container, traces, layout);
        }}

        function setupUnitComparisonChart() {{}}

        function updateUnitComparisonChart() {{
            const container = document.getElementById('unit-comparison-chart-container');
            const selectedDepartment = document.getElementById('department-filter').value;
            const selectedYear = document.getElementById('year-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);
            if (selectedDepartment === '전체') {{ Plotly.react(container, [], {{ height: 400, annotations: [{{ text: 'Unit 간 비교를 위해 부서를 선택해 주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); return; }}
            if (selectedScores.length === 0) {{ Plotly.react(container, [], {{ height: 400, annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); return; }}
            let departmentData = rawData.filter(item => item['피평가부서'] === selectedDepartment);
            if (selectedYear !== '전체') {{ departmentData = departmentData.filter(item => item['설문시행연도'] === selectedYear); }}
            const unitsInDepartment = [...new Set(departmentData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));
            if (unitsInDepartment.length === 0) {{ Plotly.react(container, [], {{ height: 400, annotations: [{{ text: '선택된 조건에 해당하는 Unit이 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); return; }}
            const traces = [];
            selectedScores.forEach(col => {{
                const y_values = unitsInDepartment.map(unit => {{ const unitData = departmentData.filter(item => item['피평가Unit'] === unit); return unitData.length > 0 ? (unitData.reduce((sum, item) => sum + (item[col] || 0), 0) / unitData.length).toFixed(1) : 0; }});
                traces.push({{ x: unitsInDepartment, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>Unit: %{{x}}<extra></extra>' }});
            }});
            const yearTitle = selectedYear === '전체' ? '전체 연도' : selectedYear;
            const layout = {{ title: `<b>[${{selectedDepartment}}] Unit별 문항 점수 비교 (${{yearTitle}})</b>`, barmode: 'group', height: 400, xaxis: {{ title: 'Unit' }}, yaxis: {{ title: '점수', range: [0, 100] }}, legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'right', x: 1 }}, font: layoutFont, hovermode: 'closest', margin: {{ l: 60, r: 60, t: 120, b: 60 }} }};
            Plotly.react(container, traces, layout);
        }}

        function toggleExpander(expanderId) {{
            const content = document.getElementById(expanderId);
            const arrow = document.getElementById(expanderId.replace('-expander', '-arrow'));
            if (content.classList.contains('expanded')) {{ content.classList.remove('expanded'); arrow.classList.remove('expanded'); }}
            else {{ content.classList.add('expanded'); arrow.classList.add('expanded'); }}
        }}

        function updateExpanderHeader(groupName, selectedCount, totalCount) {{
            const headerId = groupName.replace('-filter', '-header');
            const headerSpan = document.querySelector(`#${{headerId}} span:first-child`);
            if (headerSpan) {{
                if (groupName.includes('division-filter')) {{ headerSpan.textContent = `부문 선택 (${{selectedCount}}개 선택됨)`; }}
                else {{ headerSpan.textContent = `문항 선택 (${{selectedCount}}개 선택됨)`; }}
            }}
        }}

        function createCheckboxFilter(containerId, items, groupName, updateFunction, startChecked = true) {{
            const container = document.getElementById(containerId);
            const selectAllDiv = document.createElement('div');
            selectAllDiv.className = 'checkbox-item';
            selectAllDiv.innerHTML = `<input type="checkbox" id="${{groupName}}-select-all" ${{startChecked ? 'checked' : ''}}><label for="${{groupName}}-select-all"><b>전체 선택</b></label>`;
            container.appendChild(selectAllDiv);
            items.forEach(item => {{
                const itemDiv = document.createElement('div');
                itemDiv.className = 'checkbox-item';
                itemDiv.innerHTML = `<input type="checkbox" id="${{groupName}}-${{item}}" name="${{groupName}}" value="${{item}}" ${{startChecked ? 'checked' : ''}}><label for="${{groupName}}-${{item}}">${{item}}</label>`;
                container.appendChild(itemDiv);
            }});
            const selectAllCheckbox = container.querySelector(`#${{groupName}}-select-all`);
            const itemCheckboxes = container.querySelectorAll(`input[name="${{groupName}}"]`);
            function updateSelectAllState() {{
                const allChecked = [...itemCheckboxes].every(cb => cb.checked);
                const someChecked = [...itemCheckboxes].some(cb => cb.checked);
                const checkedCount = [...itemCheckboxes].filter(cb => cb.checked).length;
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = !allChecked && someChecked;
                updateExpanderHeader(containerId, checkedCount, items.length);
            }}
            selectAllCheckbox.addEventListener('change', (e) => {{ itemCheckboxes.forEach(checkbox => {{ checkbox.checked = e.target.checked; }}); updateSelectAllState(); updateFunction(); }});
            itemCheckboxes.forEach(checkbox => {{ checkbox.addEventListener('change', () => {{ updateSelectAllState(); updateFunction(); }}); }});
            updateSelectAllState();
        }}

        const divisionDepartmentMap = rawData.reduce((acc, item) => {{
            const division = item['피평가부문']; const department = item['피평가부서'];
            if (division && division !== 'N/A' && department && department !== 'N/A') {{
                if (!acc[division]) {{ acc[division] = new Set(); }}
                acc[division].add(department);
            }}
            return acc;
        }}, {{}});
        for (const division in divisionDepartmentMap) {{ divisionDepartmentMap[division] = [...divisionDepartmentMap[division]].sort((a, b) => String(a).localeCompare(String(b), 'ko')); }}

        function setupNetworkAnalysis() {{
            const yearSelect = document.getElementById('network-year-filter');
            const divisionSelect = document.getElementById('network-division-filter');
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const minCollabSelect = document.getElementById('min-collaboration-filter');
            const sentimentSelect = document.getElementById('network-sentiment-filter');
            yearSelect.innerHTML = ['전체', ...allYears].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            divisionSelect.innerHTML = `<option value="${{targetDivision}}">${{targetDivision}}</option>`;
            divisionSelect.value = targetDivision;
            departmentSelect.innerHTML = '<option value="전체">전체</option>';
            unitSelect.innerHTML = '<option value="전체">전체</option>';
            yearSelect.addEventListener('change', updateNetworkAnalysis);
            divisionSelect.addEventListener('change', updateNetworkDepartments);
            departmentSelect.addEventListener('change', updateNetworkUnits);
            unitSelect.addEventListener('change', updateNetworkAnalysis);
            minCollabSelect.addEventListener('change', updateNetworkAnalysis);
            sentimentSelect.addEventListener('change', updateNetworkReviews);
            updateNetworkDepartments();
            updateNetworkAnalysis();
        }}

        function updateNetworkDepartments() {{
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            departmentSelect.innerHTML = `<option value="${{targetDepartment}}">${{targetDepartment}}</option>`;
            departmentSelect.value = targetDepartment;
            unitSelect.innerHTML = '<option value="전체">전체</option>';
            unitSelect.value = '전체';
            updateNetworkAnalysis();
        }}

        function updateNetworkUnits() {{
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const selectedDept = departmentSelect.value;
            const allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
            const units = (selectedDept === '전체' || !departmentUnitMap[selectedDept]) ? allUnits : departmentUnitMap[selectedDept];
            unitSelect.innerHTML = ['전체', ...units].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            unitSelect.value = '전체';
            updateNetworkAnalysis();
        }}

        function getNetworkFilteredData() {{
            let filteredData = [...rawData];
            const selectedYear = document.getElementById('network-year-filter').value;
            const selectedDivision = document.getElementById('network-division-filter').value;
            const selectedDepartment = document.getElementById('network-department-filter').value;
            const selectedUnit = document.getElementById('network-unit-filter').value;
            if (selectedYear !== '전체') {{ filteredData = filteredData.filter(item => String(item['설문시행연도']) === String(selectedYear)); }}
            if (selectedDivision !== '전체') {{ filteredData = filteredData.filter(item => item['피평가부문'] === selectedDivision); }}
            if (selectedDepartment !== '전체') {{ filteredData = filteredData.filter(item => item['피평가부서'] === selectedDepartment); }}
            if (selectedUnit !== '전체') {{ filteredData = filteredData.filter(item => item['피평가Unit'] === selectedUnit); }}
            return filteredData;
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
            if (filteredData.length === 0) {{ Plotly.react(container, [], {{ height: 400, annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); return; }}
            const collaborationCounts = {{}};
            filteredData.forEach(item => {{
                const evaluator = item['평가부서']; const evaluated = item['피평가부서'];
                if (evaluator !== evaluated && evaluator && evaluated && evaluator !== 'N/A' && evaluated !== 'N/A') {{
                    const key = `${{evaluator}} → ${{evaluated}}`;
                    collaborationCounts[key] = (collaborationCounts[key] || 0) + 1;
                }}
            }});
            const filteredCollaborations = Object.entries(collaborationCounts).filter(([_, count]) => count >= minCollabCount).sort((a, b) => b[1] - a[1]);
            if (filteredCollaborations.length === 0) {{ Plotly.react(container, [], {{ height: 400, annotations: [{{ text: `최소 ${{minCollabCount}}회 이상 협업한 관계가 없습니다.`, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); return; }}
            const trace = {{ y: filteredCollaborations.map(([key, _]) => key).reverse(), x: filteredCollaborations.map(([_, count]) => count).reverse(), type: 'bar', orientation: 'h', text: filteredCollaborations.map(([_, count]) => `${{count}}회`).reverse(), textposition: 'outside', textfont: {{ size: 12 }}, marker: {{ color: '#4a69bd' }}, hovertemplate: '협업 횟수: %{{x}}회<extra></extra>' }};
            const barHeight = 25; const dynamicHeight = Math.max(400, filteredCollaborations.length * barHeight + 100);
            const layout = {{ title: '<b>부서 리스트</b>', height: dynamicHeight, margin: {{ l: 150, r: 40, t: 80, b: 60 }}, xaxis: {{ title: '협업 횟수' }}, yaxis: {{ automargin: true, fixedrange: true, categoryorder: 'total ascending' }}, font: layoutFont }};
            Plotly.react(container, [trace], layout);
        }}

        function updateCollaborationStatusChart() {{
            const container = document.getElementById('collaboration-status-chart-container');
            const filteredData = getNetworkFilteredData();
            const minCollabCount = parseInt(document.getElementById('min-collaboration-filter').value);
            if (filteredData.length === 0) {{ Plotly.react(container, [], {{ height: 400, annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); updateStatusDropdowns({{}}); return; }}
            const relationshipScores = {{}};
            filteredData.forEach(item => {{
                const evaluator = item['평가부서']; const evaluated = item['피평가부서']; const score = item['종합점수'];
                if (evaluator !== evaluated && evaluator && evaluated && evaluator !== 'N/A' && evaluated !== 'N/A' && score != null) {{
                    const key = `${{evaluator}} → ${{evaluated}}`;
                    if (!relationshipScores[key]) {{ relationshipScores[key] = {{ scores: [], count: 0 }}; }}
                    relationshipScores[key].scores.push(score); relationshipScores[key].count++;
                }}
            }});
            const statusCounts = {{ '우수 (75점 이상)': 0, '양호 (60-74점)': 0, '주의 (50-59점)': 0, '문제 (50점 미만)': 0 }};
            const statusDepartments = {{ '우수': [], '양호': [], '주의': [], '문제': [] }};
            Object.entries(relationshipScores).filter(([_, data]) => data.count >= minCollabCount).forEach(([relationship, data]) => {{
                const avgScore = data.scores.reduce((sum, score) => sum + score, 0) / data.scores.length;
                const [evaluator, evaluated] = relationship.split(' → ');
                const relationshipInfo = {{ relationship: relationship, avgScore: avgScore.toFixed(1), count: data.count, evaluator: evaluator, evaluated: evaluated }};
                if (avgScore >= 75) {{ statusCounts['우수 (75점 이상)']++; statusDepartments['우수'].push(relationshipInfo); }}
                else if (avgScore >= 60) {{ statusCounts['양호 (60-74점)']++; statusDepartments['양호'].push(relationshipInfo); }}
                else if (avgScore >= 50) {{ statusCounts['주의 (50-59점)']++; statusDepartments['주의'].push(relationshipInfo); }}
                else {{ statusCounts['문제 (50점 미만)']++; statusDepartments['문제'].push(relationshipInfo); }}
            }});
            const statusLabels = Object.keys(statusCounts); const statusValues = Object.values(statusCounts); const statusColors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545'];
            if (statusValues.every(val => val === 0)) {{ Plotly.react(container, [], {{ height: 400, annotations: [{{ text: `최소 ${{minCollabCount}}회 이상 협업한 관계가 없습니다.`, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); updateStatusDropdowns({{}}); return; }}
            const trace = {{ x: statusLabels, y: statusValues, type: 'bar', text: statusValues.map(val => `${{val}}개`), textposition: 'outside', textfont: {{ size: 12 }}, marker: {{ color: statusColors }}, hovertemplate: '%{{x}}: %{{y}}개 부서<extra></extra>' }};
            const layout = {{ title: '<b>협업 관계 현황</b>', height: 400, xaxis: {{ title: '상태' }}, yaxis: {{ title: '부서 수', rangemode: 'tozero', range: [0, Math.max(...statusValues) * 1.2] }}, font: layoutFont, margin: {{ l: 60, r: 60, t: 80, b: 60 }} }};
            Plotly.react(container, [trace], layout);
            updateStatusDropdowns(statusDepartments);
        }}
        
        function updateStatusDropdowns(statusData) {{
            const statusMappings = {{ '우수': 'excellent', '양호': 'good', '주의': 'caution', '문제': 'problem' }};
            Object.entries(statusMappings).forEach(([status, prefix]) => {{
                const container = document.getElementById(`${{prefix}}-dept-filter`);
                const countElement = document.getElementById(`${{prefix}}-count`);
                container.innerHTML = '';
                if (statusData[status] && statusData[status].length > 0) {{
                    createCheckboxFilterForStatus(container, statusData[status], `${{prefix}}-dept`, updateCollaborationTrendChart);
                    countElement.textContent = `${{statusData[status].length}}개 관계`;
                }} else {{
                    container.innerHTML = '<div class="checkbox-item"><label>해당 관계 없음</label></div>';
                    countElement.textContent = '0개 관계';
                }}
            }});
        }}

        function createCheckboxFilterForStatus(container, items, groupName, updateFunction) {{
            const selectAllDiv = document.createElement('div');
            selectAllDiv.className = 'checkbox-item';
            selectAllDiv.innerHTML = `<input type="checkbox" id="${{groupName}}-select-all"><label for="${{groupName}}-select-all"><b>전체 선택</b></label>`;
            container.appendChild(selectAllDiv);
            items.sort((a, b) => b.avgScore - a.avgScore).forEach(item => {{
                const itemDiv = document.createElement('div');
                itemDiv.className = 'checkbox-item';
                itemDiv.innerHTML = `<input type="checkbox" id="${{groupName}}-${{item.relationship}}" name="${{groupName}}" value="${{item.relationship}}"><label for="${{groupName}}-${{item.relationship}}">${{item.relationship}} (${{item.avgScore}}점, ${{item.count}}회)</label>`;
                container.appendChild(itemDiv);
            }});
            const selectAllCheckbox = container.querySelector(`#${{groupName}}-select-all`);
            const itemCheckboxes = container.querySelectorAll(`input[name="${{groupName}}"]`);
            function updateSelectAllState() {{
                const allChecked = [...itemCheckboxes].every(cb => cb.checked);
                const someChecked = [...itemCheckboxes].some(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = !allChecked && someChecked;
            }}
            selectAllCheckbox.addEventListener('change', (e) => {{ itemCheckboxes.forEach(checkbox => {{ checkbox.checked = e.target.checked; }}); updateSelectAllState(); updateFunction(); }});
            itemCheckboxes.forEach(checkbox => {{ checkbox.addEventListener('change', () => {{ updateSelectAllState(); updateFunction(); }}); }});
            updateSelectAllState();
        }}

        function updateCollaborationTrendChart() {{
            const container = document.getElementById('collaboration-trend-chart-container');
            const selectedRelationships = [];
            document.querySelectorAll('.expander-content input[type="checkbox"]:checked').forEach(cb => {{
                if (cb.value && !cb.id.includes('select-all')) {{ selectedRelationships.push(cb.value); }}
            }});
            if (selectedRelationships.length === 0) {{ Plotly.react(container, [], {{ height: 400, annotations: [{{ text: '분석할 협업 관계를 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); return; }}
            const traces = [];
            const trendData = getNetworkFilteredData();
            selectedRelationships.forEach((relationship, index) => {{
                const [evaluator, evaluated] = relationship.split(' → ');
                const relationshipData = trendData.filter(item => item['평가부서'] === evaluator && item['피평가부서'] === evaluated && item['종합점수'] != null);
                const yearlyScores = {{}};
                relationshipData.forEach(item => {{
                    const year = item['설문시행연도'];
                    if (!yearlyScores[year]) {{ yearlyScores[year] = []; }}
                    yearlyScores[year].push(item['종합점수']);
                }});
                const years = Object.keys(yearlyScores).sort();
                const avgScores = years.map(year => (yearlyScores[year].reduce((a, b) => a + b, 0) / yearlyScores[year].length).toFixed(1));
                if (years.length > 0) {{ traces.push({{ x: years, y: avgScores, name: relationship, type: 'scatter', mode: 'lines+markers', hovertemplate: '%{{fullData.name}}<br>점수: %{{y}}점<br>연도: %{{x}}<extra></extra>' }}); }}
            }});
            if (traces.length === 0) {{ Plotly.react(container, [], {{ height: 400, annotations: [{{ text: '선택된 관계에 대한 연도별 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}], xaxis: {{visible: false}}, yaxis: {{visible: false}} }}); return; }}
            const layout = {{ title: '<b>협업 관계 변화 트렌드</b>', height: 400, xaxis: {{ title: '연도', type: 'category' }}, yaxis: {{ title: '평균 종합점수', range: [0, 100] }}, legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }}, font: layoutFont, hovermode: 'closest', margin: {{ l: 60, r: 60, t: 80, b: 60 }} }};
            Plotly.react(container, traces, layout);
        }}

        function updateNetworkReviews() {{
            const tableBody = document.querySelector('#network-reviews-table tbody');
            const countDisplay = document.getElementById('network-reviews-count-display');
            const sentimentFilter = document.getElementById('network-sentiment-filter').value;
            let filteredData = getNetworkFilteredData();
            if (sentimentFilter !== '전체') {{ filteredData = filteredData.filter(item => item['감정_분류'] === sentimentFilter); }}
            const reviewData = filteredData.filter(item => item['정제된_텍스트'] && item['정제된_텍스트'] !== 'N/A');
            countDisplay.textContent = `(${{reviewData.length}}건)`;
            if (reviewData.length === 0) {{ tableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">표시할 후기가 없습니다.</td></tr>'; return; }}
            const sortedData = reviewData.sort((a, b) => b['설문시행연도'] - a['설문시행연도']).slice(0, 100);
            tableBody.innerHTML = sortedData.map(item => `<tr><td>${{item['설문시행연도']}}</td><td>${{item['평가부서']}}</td><td>${{item['정제된_텍스트']}}</td></tr>`).join('');
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            try {{
                populateFilters();
                createCheckboxFilter('drilldown-score-filter', scoreCols, 'drilldown-score', updateDashboard);
                createCheckboxFilter('review-sentiment-filter', ['긍정', '부정', '중립', '알 수 없음'], 'review-sentiment', () => updateReviewsTable(), true);
                createCheckboxFilter('hospital-score-filter', scoreCols, 'hospital-score', updateHospitalYearlyChart);
                setupDivisionChart();
                setupComparisonChart();
                setupTeamRankingChart();
                setupUnitComparisonChart();
                setupNetworkAnalysis();
                updateDashboard();
                updateHospitalYearlyChart();
                updateYearlyDivisionComparisonChart();
            }} catch (e) {{
                console.error("대시보드 초기화 오류:", e);
                document.body.innerHTML = `<div style="padding: 20px;"><h1>대시보드 로딩 실패</h1><p>데이터를 불러오는 중 오류가 발생했습니다. 콘솔을 확인해주세요.</p><pre>${{e.stack}}</pre></div>`;
            }}
        }});
    </script>
</body>
</html>
    """

def main():
    """
    메인 실행 함수 - 커뮤니케이션실 모든 부서 보고서 생성
    """
    try:
        log_message("=" * 70, "INFO")
        log_message(f"🚀 {TARGET_DIVISION} 부서별 보고서 생성 시작", "INFO")
        log_message(f"📅 실행 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}", "INFO")
        log_message("=" * 70, "INFO")

        # 1. 데이터 로드 및 전처리
        df = load_excel_data()
        df = preprocess_data_types(df)
        df = clean_data(df)

        # 2. 대상 부서 목록 가져오기
        target_departments = sorted(list(df[df['피평가부문'] == TARGET_DIVISION]['피평가부서'].unique()))
        if not target_departments:
            log_message(f"'{TARGET_DIVISION}'에 속한 부서를 찾을 수 없습니다. 작업을 중단합니다.", "ERROR")
            return

        log_message(f"🎯 대상 부서: {', '.join(target_departments)} ({len(target_departments)}개)", "INFO")

        # 3. 부문 전체에 대한 집계 데이터 계산 (한 번만)
        aggregated_data = calculate_aggregated_data(df, TARGET_DIVISION)

        # 4. 각 부서에 대한 보고서 생성
        success_count = 0
        for dept_name in target_departments:
            try:
                log_message("-" * 50, "INFO")
                log_message(f"🏢 '{dept_name}' 보고서 생성 중...", "INFO")

                # 4.1. 해당 부서 데이터만 필터링
                filtered_data_json = prepare_department_filtered_data(df, dept_name)
                
                # 4.2. HTML 생성
                html_content = build_secure_html(aggregated_data, filtered_data_json, dept_name)
                
                # 4.3. 파일 저장
                output_filename = f"서울아산병원_협업평가_대시보드_{dept_name}.html"
                with open(output_filename, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                log_message(f"✅ '{dept_name}' 보고서 저장 완료: {output_filename}", "SUCCESS")
                success_count += 1

            except Exception as e:
                log_message(f"❌ '{dept_name}' 보고서 생성 실패: {e}", "ERROR")
                traceback.print_exc()

        log_message("=" * 70, "INFO")
        log_message("🎉 전체 작업 완료!", "SUCCESS")
        log_message(f"총 {len(target_departments)}개 부서 중 {success_count}개 보고서 생성 성공.", "INFO")
        log_message("=" * 70, "INFO")

    except Exception as e:
        log_message(f"스크립트 실행 중 심각한 오류 발생: {e}", "ERROR")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
