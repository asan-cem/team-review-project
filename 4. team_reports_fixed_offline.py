#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
서울아산병원 협업 평가 결과 생성기 (오프라인 수정 버전)

이 파일은 데이터 처리부터 HTML 생성까지 모든 기능을 포함합니다.
비개발자 실무진이 쉽게 유지보수할 수 있도록 설계되었습니다.

📋 주요 기능:
1. 엑셀 데이터 로드 및 전처리
2. 데이터 품질 검증 및 정제
3. 대화형 HTML 대시보드 생성
4. 상세한 로그 및 오류 추적

🔧 유지보수 방법:
- 파일 경로, 컬럼명 등은 아래 설정 섹션에서 수정
- 데이터 처리 로직은 함수별로 분리되어 있음
- 각 함수는 명확한 목적과 설명을 가짐

작성자: Claude AI
버전: 3.0-offline-fixed
업데이트: 2025년 7월 30일
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
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
# OUTPUT_HTML_FILE은 이제 동적으로 생성됩니다 (전체 부서 보고서 생성)

# 📊 데이터 컬럼 정의 (실제 데이터 구조와 일치)
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
EXCLUDE_DEPARTMENTS = ['미분류', '윤리경영실']  # 부문 기준 제외할 값들
EXCLUDE_TEAMS = ['내분비외과']  # 부서 기준 제외할 값들

# 📊 대시보드 정보
# DASHBOARD_TITLE은 이제 동적으로 생성됩니다 (전체 부서 보고서 생성)
DASHBOARD_SUBTITLE = "설문 데이터: 2022년 ~ 2025년 상반기(2025년 7월 9일 기준)"

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

def get_data_summary(df):
    """
    데이터 요약 정보 생성
    
    Args:
        df (pd.DataFrame): 분석할 데이터프레임
        
    Returns:
        dict: 데이터 요약 정보
    """
    return {
        "총_응답수": len(df),
        "연도별_응답수": df['설문시행연도'].value_counts().to_dict(),
        "부문별_응답수": df['피평가부문'].value_counts().to_dict(),
        "평균_종합점수": df['종합점수'].mean().round(2),
        "데이터_기간": f"{df['설문시행연도'].min()}년 ~ {df['설문시행연도'].max()}년"
    }

# ============================================================================
# 📊 데이터 로드 및 전처리 함수들
# ============================================================================

def safe_literal_eval(s):
    """
    문자열을 안전하게 파이썬 리터럴(리스트)로 변환
    
    Args:
        s: 변환할 문자열 (예: "['키워드1', '키워드2']")
        
    Returns:
        list: 변환된 리스트 또는 빈 리스트
        
    예시:
        safe_literal_eval("['긍정', '만족']") → ['긍정', '만족']
        safe_literal_eval("잘못된 형식") → []
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
    
    Args:
        file_path (str): 엑셀 파일 경로
        
    Returns:
        pd.DataFrame: 로드된 원본 데이터프레임
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        Exception: 파일 로드 중 기타 오류
    """
    try:
        log_message("📁 엑셀 데이터 로드 시작")
        
        # 파일 존재 확인
        if not check_file_exists(file_path):
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

def preprocess_data_types(df):
    """
    데이터 타입 변환 및 기본 전처리
    
    Args:
        df (pd.DataFrame): 원본 데이터프레임
        
    Returns:
        pd.DataFrame: 타입 변환된 데이터프레임
    """
    log_message("🔄 데이터 타입 변환 시작")
    
    # 설문시행연도를 문자열로 변환 (연도는 카테고리로 취급)
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
    
    log_message("✅ 데이터 타입 변환 완료")
    return df

def clean_data(df):
    """
    데이터 정제 및 품질 관리
    
    Args:
        df (pd.DataFrame): 전처리된 데이터프레임
        
    Returns:
        pd.DataFrame: 정제된 데이터프레임
    """
    log_message("🧹 데이터 정제 시작")
    original_count = len(df)
    
    # 1. 부문 기준 제외할 값들 필터링 (미분류 등)
    for exclude_dept in EXCLUDE_DEPARTMENTS:
        condition = (df['평가부문'] != exclude_dept) & (df['피평가부문'] != exclude_dept)
        df = df[condition]
    
    division_excluded_count = original_count - len(df)
    if division_excluded_count > 0:
        log_message(f"🗑️ 부문 기준 제외된 데이터: {division_excluded_count}행 ({division_excluded_count/original_count*100:.1f}%)")
    
    # 2. 부서 기준 제외할 값들 필터링 
    current_count = len(df)
    for exclude_team in EXCLUDE_TEAMS:
        condition = (df['평가부서'] != exclude_team) & (df['피평가부서'] != exclude_team)
        df = df[condition]
    
    team_excluded_count = current_count - len(df)
    if team_excluded_count > 0:
        log_message(f"🗑️ 부서 기준 제외된 데이터: {team_excluded_count}행 ({team_excluded_count/current_count*100:.1f}%)")
    
    total_excluded_count = original_count - len(df)
    if total_excluded_count > 0:
        log_message(f"🗑️ 총 제외된 데이터: {total_excluded_count}행 ({total_excluded_count/original_count*100:.1f}%)")
    
    # 2. 종합점수 결측값 제거 (가장 중요한 지표)
    df = df.dropna(subset=['종합점수'])
    final_count = len(df)
    
    # 3. 결측값 처리 (지정된 컬럼들을 'N/A'로 채움)
    for col in FILL_NA_COLUMNS:
        if col in df.columns:
            na_count = df[col].isna().sum()
            if na_count > 0:
                df[col] = df[col].fillna('N/A')
                log_message(f"📝 {col}: {na_count}개 결측값을 'N/A'로 처리")
    
    log_message(f"✅ 데이터 정제 완료: {original_count:,}행 → {final_count:,}행")
    return df

def prepare_json_data(df):
    """
    대시보드용 JSON 데이터 준비
    
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
# 📊 부서별 데이터 처리 함수들
# ============================================================================

def calculate_aggregated_data(df):
    """
    섹션 1-4용 집계 데이터 미리 계산
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
    
    # 3. 소속 부문 결과 ([부문별] 연도별 문항 점수 - 커뮤니케이션실만)
    comm_data = df[df['피평가부문'] == '커뮤니케이션실']
    aggregated["division_yearly"]["커뮤니케이션실"] = {}
    for year in comm_data['설문시행연도'].unique():
        if pd.notna(year):
            year_data = comm_data[comm_data['설문시행연도'] == year]
            aggregated["division_yearly"]["커뮤니케이션실"][str(year)] = {
                col: float(year_data[col].mean()) if col in year_data.columns else 0.0
                for col in SCORE_COLUMNS
            }
            aggregated["division_yearly"]["커뮤니케이션실"][str(year)]["응답수"] = len(year_data)
    
    # 4. 부문별 팀 점수 순위 - 커뮤니케이션실 부서들만
    for year in comm_data['설문시행연도'].unique():
        if pd.notna(year):
            year_str = str(year)
            year_data = comm_data[comm_data['설문시행연도'] == year]
            dept_scores = []
            
            for dept in year_data['피평가부서'].unique():
                if pd.notna(dept):
                    dept_data = year_data[year_data['피평가부서'] == dept]
                    avg_score = dept_data['종합점수'].mean() if len(dept_data) > 0 else 0.0
                    dept_scores.append({
                        "department": dept,
                        "score": round(float(avg_score), 1),  # 소수점 첫째 자리로 반올림
                        "count": len(dept_data)
                    })
            
            # 점수 순으로 정렬하고 순위 부여
            dept_scores.sort(key=lambda x: x["score"], reverse=True)
            for i, dept in enumerate(dept_scores):
                dept["rank"] = i + 1
            
            aggregated["team_ranking"][year_str] = dept_scores
    
    log_message(f"✅ 집계 데이터 계산 완료: {len(aggregated['hospital_yearly'])}년치 데이터")
    return aggregated

def prepare_department_filtered_data(df, target_department):
    """
    섹션 5-6용 부서별 필터링된 데이터 준비
    해당 부서가 피평가 대상인 데이터만 포함
    
    Args:
        df (pd.DataFrame): 전체 데이터프레임
        target_department (str): 대상 부서명
        
    Returns:
        str: 필터링된 JSON 데이터
    """
    log_message(f"📊 부서별 데이터 필터링: {target_department}")
    
    # 해당 부서가 피평가 대상인 데이터만 추출
    dept_data = df[df['피평가부서'] == target_department].copy()
    
    # 보안을 위한 컬럼 선택 (평가부서 정보 제외)
    safe_columns = [
        '설문시행연도', '피평가부문', '피평가부서', '피평가Unit',
        '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수',
        '정제된_텍스트', '감정_분류', '핵심_키워드'
    ]
    
    # 사용 가능한 컬럼만 선택
    available_columns = [col for col in safe_columns if col in dept_data.columns]
    filtered_data = dept_data[available_columns].copy()
    
    # JSON 변환
    filtered_json = filtered_data.to_json(orient='records', force_ascii=False)
    
    log_message(f"✅ 부서별 필터링 완료: {len(filtered_data):,}건 (필터링된 데이터: {((len(df)-len(filtered_data))/len(df)*100):.1f}% 제외)")
    return filtered_json

def build_secure_html(aggregated_data, filtered_rawdata, target_department, target_division):
    """
    부서별 맞춤 HTML 생성
    
    Args:
        aggregated_data (dict): 집계된 통계 데이터
        filtered_rawdata (str): 필터링된 개별 데이터
        target_department (str): 대상 부서명
        target_division (str): 대상 부문명
        
    Returns:
        str: 부서별 HTML 대시보드
    """
    log_message(f"🎨 부서별 HTML 생성: {target_department} ({target_division})")
    
    # 보안 메타데이터 추가
    security_metadata = {
        "target_department": target_department,
        "target_division": target_division,
        "data_scope": f"{target_department} 관련 데이터만 포함",
        "security_level": "HIGH",
        "aggregated_sections": ["전체 연도별", "부문별 연도별", "부문 비교", "팀 순위"],
        "filtered_sections": ["부서 상세분석", "네트워크 분석"]
    }
    
    # 기존 build_html 함수 호출하되 하이브리드 데이터 구조로 수정
    import json
    
    # JavaScript에서 사용할 하이브리드 데이터 구조
    hybrid_data = {
        "aggregated": aggregated_data,
        "rawData": json.loads(filtered_rawdata) if isinstance(filtered_rawdata, str) else filtered_rawdata,
        "security": security_metadata
    }
    
    return build_html_with_hybrid_data(hybrid_data, target_department, target_division)

def load_data():
    """
    전체 데이터 로드 및 전처리 프로세스 (기존 함수와 호환성 유지)
    
    Returns:
        pd.DataFrame: 전처리된 데이터프레임
    """
    # 데이터 로드 및 전처리
    df = load_excel_data()
    df = preprocess_data_types(df)
    df = clean_data(df)
    return df

# --- 2. 부서별 HTML 생성 ---
def build_html_with_hybrid_data(hybrid_data, target_department, target_division):
    """부서별 맞춤 대시보드 HTML 생성"""
    
    # JavaScript용 데이터를 JSON으로 변환
    import json
    hybrid_data_json = json.dumps(hybrid_data, ensure_ascii=False, default=str)
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>서울아산병원 협업 평가 결과 보고</title>
    <script>
    {get_plotlyjs}
    </script>
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
        
        /* 차트 컨테이너 스타일 */
        .chart-container {{ margin: 20px 0; }}
        .subsection {{ margin: 30px 0; }}
        
        /* 협업 빈도 차트 스크롤 컨테이너 */
        #collaboration-frequency-chart-container {{ max-height: 600px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 5px; }}
        
    </style>
</head>
<body>
    <div class="header">
        <h1> 서울아산병원 협업 평가 결과 보고 - {target_department} </h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">설문 데이터: 2022년 ~ 2025년 상반기(2025년 7월 9일 기준) </p>
    </div>
    
    <!-- 안내 문구 섹션 -->
    <div style="max-width: 1400px; margin: 20px auto; padding: 0 20px;">
        <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
            
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
            <h2>병원 전체 결과</h2>
            <div class="filters">
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="hospital-score-header" onclick="toggleExpander('hospital-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="hospital-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="hospital-score-expander">
                            <div id="hospital-score-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="hospital-yearly-chart-container" class="chart-container"></div>
        </div>

        <div class="part-divider"></div>

        <div class="section">
            <h2>부문별 종합 점수</h2>
            <div class="filters">
                <div class="filter-group">
                    <label for="comparison-year-filter">연도 선택</label>
                    <select id="comparison-year-filter"></select>
                </div>
                <div class="filter-group">
                    <label>부문 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="comparison-division-header" onclick="toggleExpander('comparison-division-expander')">
                            <span>부문 선택 (0개 선택됨)</span>
                            <span class="expander-arrow" id="comparison-division-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="comparison-division-expander">
                            <div id="comparison-division-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="comparison-chart-container" class="chart-container"></div>
        </div>

        <div class="section">
            <h2>소속 부문 결과</h2>
            <div class="filters">
                <div class="filter-group">
                    <label for="division-chart-filter">부문 선택</label>
                    <select id="division-chart-filter"></select>
                </div>
                <div class="filter-group">
                    <label>문항 선택</label>
                    <div class="expander-container">
                        <div class="expander-header" id="division-score-header" onclick="toggleExpander('division-score-expander')">
                            <span>문항 선택 (6개 선택됨)</span>
                            <span class="expander-arrow" id="division-score-arrow">▼</span>
                        </div>
                        <div class="expander-content" id="division-score-expander">
                            <div id="division-score-filter"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="division-yearly-chart-container" class="chart-container"></div>
        </div>

        <div class="part-divider"></div>
        
        
        <div class="section">
            <h2>소속 부문 팀별 종합 점수</h2>
            <div class="filters">
                <div class="filter-group">
                    <label for="team-ranking-year-filter">연도 선택</label>
                    <select id="team-ranking-year-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="team-ranking-division-filter">부문 선택</label>
                    <select id="team-ranking-division-filter"></select>
                </div>
            </div>
            <div id="team-ranking-chart-container" class="chart-container"></div>
        </div>

        <div class="part-divider"></div>
        
        
        <div class="section">
            <h2>부서/Unit 결과</h2>
            
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
            
            <!-- 5.1 부서/Unit 결과 -->
            <div class="subsection">
                <h3>부서/Unit 결과</h3>
                <div id="metrics-container"></div>
                <div id="yearly-comparison-chart-container" class="chart-container"></div>
                
            </div>
            
            <!-- 5.2 부서 내 Unit 결과 -->
            <div class="subsection">
                <h3>부서 내 Unit 결과</h3>
                <div id="unit-comparison-chart-container" class="chart-container"></div>
            </div>
            
            <!-- 5.3 감정 분석 -->
            <div class="subsection">
                <h3>평가 부서 의견</h3>
                <div id="sentiment-chart-container" class="chart-container"></div>
                
                <!-- 협업 후기 -->
                <div style="margin-top: 30px;">
                    <h4>협업 후기 <span id="reviews-count-display" style="color: #666; font-size: 0.9em;"></span></h4>
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

        </div>

        <div class="part-divider"></div>
        
        
        <div class="section">
            <h2>다빈도 평가 부서</h2>
            
            <!-- 공통 필터 -->
            <div class="filters">
                <div class="filter-group">
                    <label for="network-year-filter">연도 (전체)</label>
                    <select id="network-year-filter"></select>
                </div>
                <div class="filter-group">
                    <label for="min-collaboration-filter">평가 횟수</label>
                    <select id="min-collaboration-filter">
                        <option value="5">5회 이상</option>
                        <option value="10" selected>10회 이상</option>
                        <option value="30">30회 이상</option>
                    </select>
                </div>
            </div>
            <!-- 부문/부서/Unit 필터는 집계 데이터 사용으로 제거 -->
            <div style="display: none;">
                <select id="network-division-filter"><option value="전체">전체</option></select>
                <select id="network-department-filter"><option value="{target_department}">{target_department}</option></select>
                <select id="network-unit-filter"><option value="전체">전체</option></select>
            </div>
            
            <div class="subsection">
                <div id="collaboration-frequency-chart-container" class="chart-container"></div>
            </div>


        </div>

    </div>
    <script>
        // 부서별 데이터 구조
        const hybridData = {hybrid_data_json};
        const rawData = hybridData.rawData;  // 필터링된 부서 데이터만 포함
        const aggregatedData = hybridData.aggregated;  // 미리 계산된 집계 데이터
        const securityInfo = hybridData.security;
        
        const scoreCols = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수'];
        const allYears = [...new Set(rawData.map(item => item['설문시행연도']))].sort();
        // 부문 비교용: 집계 데이터에서 모든 부문 가져오기
        const allDivisions = Object.keys(aggregatedData.division_comparison).length > 0 
            ? [...new Set(Object.values(aggregatedData.division_comparison).flatMap(yearData => Object.keys(yearData)))].sort((a, b) => a.localeCompare(b, 'ko'))
            : ["{target_division}"];
        const layoutFont = {{ size: 14 }};
        
        // 보안 정보 콘솔 출력
        console.log('🔒 보안 정보:', securityInfo);
        console.log('📊 데이터 범위:', securityInfo.data_scope);

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
            // 연도 필터 설정
            const yearSelect = document.getElementById('year-filter');
            const years = [...new Set(rawData.map(item => item['설문시행연도']))].sort((a, b) => String(a).localeCompare(String(b), 'ko'));
            yearSelect.innerHTML = ['전체', ...years].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.addEventListener('change', updateDashboard);
            
            // 부서 필터를 {target_department}으로 고정
            const deptSelect = document.getElementById('department-filter');
            deptSelect.innerHTML = `<option value="{target_department}">{target_department}</option>`;
            deptSelect.value = "{target_department}";
            deptSelect.addEventListener('change', updateUnitFilter);
            
            // Unit 필터 초기화
            updateUnitFilter();
        }}

        function updateUnitFilter() {{
            const deptSelect = document.getElementById('department-filter');
            const unitSelect = document.getElementById('unit-filter');
            const selectedDept = deptSelect.value;

            const allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
            const units = (selectedDept === '전체' || !departmentUnitMap[selectedDept])
                ? allUnits
                : departmentUnitMap[selectedDept];

            unitSelect.innerHTML = ['전체', ...units].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            unitSelect.value = '전체';
            
            // Unit 필터 변경 시 차트 실시간 업데이트
            unitSelect.addEventListener('change', updateDashboard);
        }}

        function setupDivisionChart() {{
            const select = document.getElementById('division-chart-filter');
            // 고정값: {target_division}만 선택 가능
            select.innerHTML = `<option value="{target_division}">{target_division}</option>`;
            select.value = "{target_division}";
            select.addEventListener('change', updateDivisionYearlyChart);
            createCheckboxFilter('division-score-filter', scoreCols, 'division-score', updateDivisionYearlyChart);
            // 초기 차트 표시
            updateDivisionYearlyChart();
        }}
        
        function setupComparisonChart() {{
            const yearSelect = document.getElementById('comparison-year-filter');
            yearSelect.innerHTML = allYears.map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = allYears[allYears.length - 1]; // Default to last year
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
            if (!container) {{
                console.warn('Container not found: drilldown-chart-container');
                return;
            }}
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);

            if (data.length === 0 || selectedScores.length === 0) {{ 
                const message = data.length > 0 ? '표시할 문항을 선택해주세요.' : '';
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: message, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const averages = calculateAverages(data);
            const barColors = ['#FFF6F5', '#72B0AB', '#BCDDDC', '#FFEDD1', '#FDC1B4', '#FE9179'];
            const chartData = [{{ x: selectedScores, y: selectedScores.map(col => averages[col].toFixed(1)), type: 'bar', text: selectedScores.map(col => averages[col].toFixed(1)), textposition: 'outside', textfont: {{ size: 14 }}, marker: {{ color: barColors[0], line: {{ color: '#000000', width: 1 }} }}, hovertemplate: '%{{x}}: %{{y}}<extra></extra>' }}];
            const selectedYear = document.getElementById('year-filter').value;
            const selectedDept = document.getElementById('department-filter').value;
            const selectedUnit = document.getElementById('unit-filter').value;
            
            // 제목 생성
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
            if (!container) {{
                console.warn('Container not found: hospital-yearly-chart-container');
                return;
            }}
            const selectedScores = Array.from(document.querySelectorAll('input[name="hospital-score"]:checked')).map(cb => cb.value);
            
            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 미리 계산된 집계 데이터 사용
            const hospitalData = aggregatedData.hospital_yearly;
            const years = Object.keys(hospitalData).sort();
            const traces = [];

            const barColors = ['#FFF6F5', '#72B0AB', '#BCDDDC', '#FFEDD1', '#FDC1B4', '#FE9179'];
            selectedScores.forEach((col, index) => {{
                const y_values = years.map(year => hospitalData[year][col] ? hospitalData[year][col].toFixed(1) : '0.0');
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, marker: {{ color: barColors[index % barColors.length], line: {{ color: '#000000', width: 1 }} }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            
            const yearly_counts = years.map(year => hospitalData[year]['응답수'] || 0);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3, color: '#355e58' }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}건`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}건<br>연도: %{{x}}<extra></extra>' }});

            const layout = {{
                title: '<b>병원 전체 결과</b>',
                barmode: 'group', height: 500,
                xaxis: {{ type: 'category', title: '설문 연도' }},
                yaxis: {{ title: '점수', range: [0, 100] }},
                yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'right', x: 1 }},
                font: layoutFont,
                hovermode: 'closest',
                margin: {{ l: 60, r: 60, t: 120, b: 60 }}
            }};
            Plotly.react(container, traces, layout);
        }}

        function updateDivisionYearlyChart() {{
            const container = document.getElementById('division-yearly-chart-container');
            if (!container) {{
                console.warn('Container not found: division-yearly-chart-container');
                return;
            }}
            const selectedDivision = document.getElementById('division-chart-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="division-score"]:checked')).map(cb => cb.value);

            // {target_division}로 고정되어 있으므로 선택 확인 불필요

            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 미리 계산된 부문별 집계 데이터 사용
            const divisionData = aggregatedData.division_yearly[selectedDivision] || {{}};
            const years = Object.keys(divisionData).sort();
            const traces = [];

            const barColors = ['#FFF6F5', '#72B0AB', '#BCDDDC', '#FFEDD1', '#FDC1B4', '#FE9179'];
            selectedScores.forEach((col, index) => {{
                const y_values = years.map(year => divisionData[year] && divisionData[year][col] ? divisionData[year][col].toFixed(1) : '0.0');
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, marker: {{ color: barColors[index % barColors.length], line: {{ color: '#000000', width: 1 }} }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            
            const yearly_counts = years.map(year => divisionData[year] ? divisionData[year]['응답수'] || 0 : 0);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3, color: '#355e58' }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}건`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}건<br>연도: %{{x}}<extra></extra>' }});

            const layout = {{
                title: `<b>[${{selectedDivision}}] 결과</b>`,
                barmode: 'group', height: 500,
                xaxis: {{ type: 'category', title: '설문 연도' }},
                yaxis: {{ title: '점수', range: [0, 100] }},
                yaxis2: {{ title: '응답 수', overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero', tickformat: 'd' }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'right', x: 1 }},
                font: layoutFont,
                hovermode: 'closest',
                margin: {{ l: 60, r: 60, t: 120, b: 60 }}
            }};
            Plotly.react(container, traces, layout);
        }}

        function updateYearlyDivisionComparisonChart() {{
            const container = document.getElementById('comparison-chart-container');
            if (!container) {{
                console.warn('Container not found: comparison-chart-container');
                return;
            }}
            const selectedYear = document.getElementById('comparison-year-filter').value;
            const selectedDivisions = Array.from(document.querySelectorAll('input[name="comparison-division"]:checked')).map(cb => cb.value);

            if (selectedDivisions.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '비교할 부문을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 미리 계산된 부문 비교 집계 데이터 사용 (모든 부문 포함)
            const comparisonData = aggregatedData.division_comparison[selectedYear] || {{}};
            
            const divisions = selectedDivisions.filter(div => comparisonData[div]).sort((a,b) => a.localeCompare(b, 'ko'));
            const avgScores = divisions.map(div => comparisonData[div]['종합점수'] ? comparisonData[div]['종합점수'].toFixed(1) : '0.0');
            const responseCounts = divisions.map(div => comparisonData[div]['응답수'] || 0);

            // 미리 계산된 전체 평균 사용
            const yearlyOverallAverage = aggregatedData.hospital_yearly[selectedYear] ? aggregatedData.hospital_yearly[selectedYear]['종합점수'].toFixed(1) : '0.0';

            const trace = {{ x: divisions, y: avgScores, type: 'bar', text: avgScores, textposition: 'outside', textfont: {{ size: 14 }}, marker: {{ color: '#FDC1B4', line: {{ color: '#000000', width: 1 }} }}, customdata: responseCounts, hovertemplate: '%{{x}}: %{{y}}점<br>응답수: %{{customdata}}건<extra></extra>' }};
            
            const avgLine = {{
                x: [divisions[0], divisions[divisions.length - 1]], y: [yearlyOverallAverage, yearlyOverallAverage],
                type: 'scatter', mode: 'lines', line: {{ color: 'red', width: 2, dash: 'dash' }},
                name: `${{selectedYear}} 종합 점수: ${{yearlyOverallAverage}}`, hoverinfo: 'skip'
            }};
            
            const layout = {{
                title: `<b>${{selectedYear}} 부문별 종합 점수</b>`,
                yaxis: {{ title: '점수', range: [0, 100] }},
                font: layoutFont,
                height: 500,
                barmode: 'group',
                hovermode: 'closest',
                showlegend: false,
                annotations: [{{
                    text: `${{selectedYear}} 종합 점수: ${{yearlyOverallAverage}}점`, xref: 'paper', yref: 'y',
                    x: 0.02, y: parseFloat(yearlyOverallAverage), showarrow: false,
                    font: {{ color: 'red', size: 12 }}, bgcolor: 'rgba(255,255,255,0.8)',
                    bordercolor: 'red', borderwidth: 1
                }}],
                margin: {{ l: 60, r: 60, t: 80, b: 60 }}
            }};
            Plotly.react(container, [trace, avgLine], layout);
        }}

        function updateSentimentChart(data) {{
            const container = document.getElementById('sentiment-chart-container');
            if (!container) {{
                console.warn('Container not found: sentiment-chart-container');
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

            // 감정 분류가 있는 데이터만 필터링
            const validSentimentData = data.filter(item => {{
                const sentiment = item['감정_분류'];
                return sentiment && sentiment !== 'N/A' && sentiment !== '알 수 없음';
            }});

            if (validSentimentData.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '감정 분류 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 감정 분류별 집계 (알 수 없음 제외)
            const sentimentCounts = {{}};
            validSentimentData.forEach(item => {{
                const sentiment = item['감정_분류'];
                sentimentCounts[sentiment] = (sentimentCounts[sentiment] || 0) + 1;
            }});

            // 원하는 순서로 감정 분류 고정
            const desiredOrder = ['긍정', '부정', '중립'];
            const sentiments = desiredOrder.filter(sentiment => sentimentCounts[sentiment] > 0);
            const counts = sentiments.map(sentiment => sentimentCounts[sentiment]);
            const total = counts.reduce((sum, count) => sum + count, 0);
            const percentages = counts.map(count => ((count / total) * 100).toFixed(1));

            // 색상 매핑
            const colorMap = {{
                '긍정': '#72B0AB',
                '부정': '#FE9179', 
                '중립': '#FFF6F5',
                '알 수 없음': '#808080'
            }};
            const colors = sentiments.map(sentiment => colorMap[sentiment] || '#808080');

            const trace = {{
                x: sentiments,
                y: counts,
                type: 'bar',
                text: counts.map((count, idx) => `${{count}}건 (${{percentages[idx]}}%)`),
                textposition: 'outside',
                textfont: {{ size: 12 }},
                marker: {{ color: colors, line: {{ color: '#000000', width: 1 }} }},
                hovertemplate: '%{{x}}: %{{y}}건 (%{{text}})<extra></extra>'
            }};

            const layout = {{
                title: '',
                height: 400,
                xaxis: {{ title: '감정 분류' }},
                yaxis: {{ title: '응답 수', rangemode: 'tozero', range: [0, Math.max(...counts) * 1.15] }},
                font: layoutFont,
                hovermode: 'closest',
                showlegend: false,
                margin: {{ l: 60, r: 60, t: 80, b: 60 }}
            }};

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
            
            const reviews = filteredData.map(item => ({{ 
                year: item['설문시행연도'], 
                review: item['정제된_텍스트'],
                sentiment: item['감정_분류'] || '알 수 없음'
            }})).filter(r => r.review && r.review !== 'N/A')
            .sort((a, b) => b.year - a.year)
            .slice(0, 40000); // 최대 40000개만 표시
            
            // 후기 개수 표시 업데이트
            const countDisplay = document.getElementById('reviews-count-display');
            if (countDisplay) {{
                countDisplay.textContent = `(${{reviews.length}}건)`;
            }}
            
            tbody.innerHTML = (reviews.length > 0) ? 
                reviews.map(r => `<tr><td>${{r.year}}</td><td>${{r.review}} <span style="color: #666; font-size: 0.9em;">[${{r.sentiment}}]</span></td></tr>`).join('') : 
                '<tr><td colspan="2">해당 조건의 후기가 없습니다.</td></tr>';
        }}

        function updateKeywordAnalysis(data) {{
            const positiveCounts = {{}};
            const negativeCounts = {{}};

            data.forEach(item => {{
                const keywords = item['핵심_키워드'];
                if (keywords && Array.isArray(keywords) && keywords.length > 0) {{
                    const sentiment = item['감정_분류'];
                    keywords.forEach(kw => {{
                        if (sentiment === '긍정') {{
                            positiveCounts[kw] = (positiveCounts[kw] || 0) + 1;
                        }} else if (sentiment === '부정') {{
                            negativeCounts[kw] = (negativeCounts[kw] || 0) + 1;
                        }}
                    }});
                }}
            }});

            const topPositive = Object.entries(positiveCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
            const topNegative = Object.entries(negativeCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);

            const posChartContainer = document.getElementById('positive-keywords-chart');
            const negChartContainer = document.getElementById('negative-keywords-chart');

            if (posChartContainer) plotKeywordChart(posChartContainer, '긍정 키워드 Top 10', topPositive, '긍정');
            if (negChartContainer) plotKeywordChart(negChartContainer, '부정 키워드 Top 10', topNegative, '부정');
            
            displayKeywordReviews(null, null, true);
        }}

        function plotKeywordChart(container, title, data, sentiment) {{
            if (!container) return;
            if (data.length === 0) {{
                Plotly.react(container, [], { title: `<b>${title}</b>`, height: 400, annotations: [{ text: '데이터 없음', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false }] });
                return;
            }}

            const trace = {{
                y: data.map(d => d[0]).reverse(),
                x: data.map(d => d[1]).reverse(),
                type: 'bar',
                orientation: 'h',
                marker: {{ color: sentiment === '긍정' ? '#72B0AB' : '#FE9179', line: {{ color: '#000000', width: 1 }} }},
                hovertemplate: '언급 횟수: %{{x}}<extra></extra>'
            }};

            const layout = {{
                title: `<b>${{title}}</b>`,
                height: 400,
                margin: {{ l: 120, r: 40, t: 80, b: 60 }},
                xaxis: {{ title: '언급 횟수' }},
                yaxis: {{ automargin: true }}
            }};

            Plotly.react(container, [trace], layout);
            container.removeAllListeners('plotly_click');
            container.on('plotly_click', (eventData) => {{
                const keyword = eventData.points[0].y;
                displayKeywordReviews(keyword, sentiment);
            }});
        }}

        function displayKeywordReviews(keyword, sentiment, isInitial = false) {{
            const container = document.getElementById('keyword-reviews-container');
            if (!container) return;
            
            if (isInitial) {{
                container.innerHTML = `<h4>관련 리뷰</h4><p>위 그래프의 막대를 클릭하면 관련 리뷰를 확인할 수 있습니다.</p><div id="keyword-reviews-table-container"><table id="keyword-reviews-table"><thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody><tr><td colspan="2" style="text-align:center;"></td></tr></tbody></table></div>`;
                return;
            }}

            const filteredData = getFilteredData();
            
            const reviews = filteredData.filter(item => 
                item['감정_분류'] === sentiment && 
                Array.isArray(item['핵심_키워드']) && 
                item['핵심_키워드'].includes(keyword)
            );

            let content = `<h4>'${{keyword}}' (${{sentiment}}) 관련 리뷰 (${{reviews.length}}건)</h4>`;
            if (reviews.length > 0) {{
                content += `<div id="keyword-reviews-table-container"><table id="keyword-reviews-table">
                    <thead><tr><th style="width: 100px;">연도</th><th>후기 내용</th></tr></thead><tbody>`;
                content += reviews.slice(0, 40000).map(r => `<tr><td>${{r['설문시행연도']}}</td><td>${{r['정제된_텍스트']}}</td></tr>`).join(''); // 최대 40000개만 표시
                content += `</tbody></table></div>`;
            }} else {{
                content += '<p>관련 리뷰가 없습니다.</p>';
            }}
            container.innerHTML = content;
        }}

        function setupTeamRankingChart() {{
            const yearSelect = document.getElementById('team-ranking-year-filter');
            const divisionSelect = document.getElementById('team-ranking-division-filter');
            
            yearSelect.innerHTML = allYears.map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            yearSelect.value = allYears[allYears.length - 1];
            
            // 고정값: {target_division}만 선택 가능
            divisionSelect.innerHTML = `<option value="{target_division}">{target_division}</option>`;
            divisionSelect.value = "{target_division}";
            
            yearSelect.addEventListener('change', updateTeamRankingChart);
            divisionSelect.addEventListener('change', updateTeamRankingChart);
            // 초기 차트 표시
            updateTeamRankingChart();
        }}

        function updateTeamRankingChart() {{
            const container = document.getElementById('team-ranking-chart-container');
            if (!container) {{
                console.warn('Container not found: team-ranking-chart-container');
                return;
            }}
            const selectedYear = document.getElementById('team-ranking-year-filter').value;
            const selectedDivision = document.getElementById('team-ranking-division-filter').value;

            // {target_division}로 고정되어 있으므로 선택 확인 불필요

            // 미리 계산된 팀 순위 집계 데이터 사용
            const teamRankingData = aggregatedData.team_ranking[selectedYear] || [];
            
            // 해당 부문에 속한 팀들만 필터링 ({target_division} 소속 부서들)
            const teamRankings = teamRankingData.filter(team => {{
                // 동적으로 해당 부문의 부서들을 포함
                return true; // 이미 집계 데이터에서 해당 부문만 포함되어 있음
            }});

            if (teamRankings.length === 0) {{
                Plotly.react(container, [], {{
                    height: 600,
                    annotations: [{{ text: '선택된 조건에 해당하는 부서 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            // 모든 부문 동일 색상 사용
            const departments = teamRankings.map(item => item.department);
            const scores = teamRankings.map(item => parseFloat(item.score));
            const colors = teamRankings.map(() => '#FDC1B4');
            const hoverTexts = teamRankings.map(item => `부서: ${{item.department}}<br>점수: ${{item.score.toFixed(1)}}<br>응답수: ${{item.count}}건`);

            // 미리 계산된 전체 평균 사용
            const yearlyOverallAverage = aggregatedData.hospital_yearly[selectedYear] ? aggregatedData.hospital_yearly[selectedYear]['종합점수'].toFixed(1) : '0.0';

            const trace = {{
                x: departments, y: scores, type: 'bar', text: scores.map(score => score.toFixed(1)),
                textposition: 'outside', textfont: {{ size: 12 }}, marker: {{ color: colors, line: {{ color: '#000000', width: 1 }} }},
                hovertemplate: '%{{hovertext}}<extra></extra>', hovertext: hoverTexts
            }};

            const avgLine = {{
                x: [departments[0], departments[departments.length - 1]], y: [yearlyOverallAverage, yearlyOverallAverage],
                type: 'scatter', mode: 'lines', line: {{ color: 'red', width: 2, dash: 'dash' }},
                name: `${{selectedYear}} 종합 점수: ${{yearlyOverallAverage}}`, hoverinfo: 'skip'
            }};

            const layout = {{
                title: `<b>${{selectedYear}} 팀별 종합점수</b>`, height: 600,
                xaxis: {{ title: '부서', tickangle: -45, automargin: true }},
                yaxis: {{ title: '점수', range: [Math.min(...scores) - 5, Math.max(...scores) + 5] }},
                font: layoutFont, hovermode: 'closest', showlegend: false,
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }},
                annotations: [{{
                    text: `${{selectedYear}} 종합 점수: ${{yearlyOverallAverage}}점`, xref: 'paper', yref: 'y',
                    x: 0.02, y: parseFloat(yearlyOverallAverage), showarrow: false,
                    font: {{ color: 'red', size: 12 }}, bgcolor: 'rgba(255,255,255,0.8)',
                    bordercolor: 'red', borderwidth: 1
                }}],
                margin: {{ l: 60, r: 60, t: 80, b: 100 }}
            }};

            Plotly.react(container, [trace, avgLine], layout);
        }}

        function updateYearlyComparisonChart() {{
            const container = document.getElementById('yearly-comparison-chart-container');
            if (!container) {{
                console.warn('Container not found: yearly-comparison-chart-container');
                return;
            }}
            const selectedDept = document.getElementById('department-filter').value;
            const selectedUnit = document.getElementById('unit-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);

            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 500,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            let targetData = [...rawData];
            if (selectedDept !== '전체') {{ targetData = targetData.filter(item => item['피평가부서'] === selectedDept); }}
            if (selectedUnit !== '전체') {{ targetData = targetData.filter(item => item['피평가Unit'] === selectedUnit); }}

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

            const barColors = ['#FFF6F5', '#72B0AB', '#BCDDDC', '#FFEDD1', '#FDC1B4', '#FE9179'];
            selectedScores.forEach((col, index) => {{
                const y_values = years.map(year => {{
                    const yearData = targetData.filter(d => d['설문시행연도'] === year);
                    return yearData.length > 0 ? (yearData.reduce((sum, item) => sum + (item[col] || 0), 0) / yearData.length).toFixed(1) : 0;
                }});
                traces.push({{ x: years, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, marker: {{ color: barColors[index % barColors.length], line: {{ color: '#000000', width: 1 }} }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>연도: %{{x}}<extra></extra>' }});
            }});
            
            const yearly_counts = years.map(year => targetData.filter(d => d['설문시행연도'] === year).length);
            traces.push({{ x: years, y: yearly_counts, name: '응답수', type: 'scatter', mode: 'lines+markers+text', line: {{ shape: 'spline', smoothing: 0.3, width: 3, color: '#355e58' }}, text: yearly_counts.map(count => `${{count.toLocaleString()}}건`), textposition: 'top center', textfont: {{ size: 12 }}, yaxis: 'y2', hovertemplate: '응답수: %{{y}}건<br>연도: %{{x}}<extra></extra>' }});

            let titleText = '결과';
            if (selectedDept !== '전체' && selectedUnit !== '전체') {{ titleText = `[${{selectedDept}} > ${{selectedUnit}}] 결과`; }}
            else if (selectedDept !== '전체') {{ titleText = `[${{selectedDept}}] 결과`; }}
            else if (selectedUnit !== '전체') {{ titleText = `[${{selectedUnit}}] 결과`; }}
            
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

        function setupUnitComparisonChart() {{
            // Unit comparison chart uses main filters from detailed analysis section
            // No separate filters needed
        }}

        function updateUnitComparisonChart() {{
            const container = document.getElementById('unit-comparison-chart-container');
            if (!container) {{
                console.warn('Container not found: unit-comparison-chart-container');
                return;
            }}
            const selectedDepartment = document.getElementById('department-filter').value;
            const selectedYear = document.getElementById('year-filter').value;
            const selectedScores = Array.from(document.querySelectorAll('input[name="drilldown-score"]:checked')).map(cb => cb.value);

            if (selectedDepartment === '전체') {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: 'Unit 간 비교를 위해 부서를 선택해 주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            if (selectedScores.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '표시할 문항을 선택해주세요.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            let departmentData = rawData.filter(item => item['피평가부서'] === selectedDepartment);
            if (selectedYear !== '전체') {{ departmentData = departmentData.filter(item => item['설문시행연도'] === selectedYear); }}

            const unitsInDepartment = [...new Set(departmentData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a, b) => String(a).localeCompare(String(b), 'ko'));

            if (unitsInDepartment.length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '선택된 조건에 해당하는 Unit이 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}

            const traces = [];
            const barColors = ['#FFF6F5', '#72B0AB', '#BCDDDC', '#FFEDD1', '#FDC1B4', '#FE9179'];
            selectedScores.forEach((col, index) => {{
                const y_values = unitsInDepartment.map(unit => {{
                    const unitData = departmentData.filter(item => item['피평가Unit'] === unit);
                    return unitData.length > 0 ? (unitData.reduce((sum, item) => sum + (item[col] || 0), 0) / unitData.length).toFixed(1) : 0;
                }});
                traces.push({{ x: unitsInDepartment, y: y_values, name: col, type: 'bar', text: y_values, textposition: 'outside', textfont: {{ size: 14 }}, marker: {{ color: barColors[index % barColors.length], line: {{ color: '#000000', width: 1 }} }}, hovertemplate: '%{{fullData.name}}: %{{y}}<br>Unit: %{{x}}<extra></extra>' }});
            }});

            const layout = {{
                title: `<b>[${{selectedDepartment}}] Unit별 결과</b>`, barmode: 'group', height: 400,
                xaxis: {{ title: 'Unit' }}, yaxis: {{ title: '점수', range: [0, 100] }},
                legend: {{ orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'right', x: 1 }},
                font: layoutFont, hovermode: 'closest',
                margin: {{ l: 60, r: 60, t: 120, b: 60 }}
            }};

            Plotly.react(container, traces, layout);
        }}

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

        function updateExpanderHeader(groupName, selectedCount, totalCount) {{
            const headerId = groupName.replace('-filter', '-header');
            const headerSpan = document.querySelector(`#${{headerId}} span:first-child`);
            if (headerSpan) {{
                if (groupName.includes('division-filter')) {{
                    headerSpan.textContent = `부문 선택 (${{selectedCount}}개 선택됨)`;
                }} else {{
                    headerSpan.textContent = `문항 선택 (${{selectedCount}}개 선택됨)`;
                }}
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

            selectAllCheckbox.addEventListener('change', (e) => {{
                itemCheckboxes.forEach(checkbox => {{ checkbox.checked = e.target.checked; }});
                updateSelectAllState();
                updateFunction();
            }});

            itemCheckboxes.forEach(checkbox => {{
                checkbox.addEventListener('change', () => {{
                    updateSelectAllState();
                    updateFunction();
                }});
            }});

            updateSelectAllState();
        }}

        // === 협업 네트워크 분석 기능 ===
        
        // 부문-부서-Unit 매핑 생성
        const divisionDepartmentMap = rawData.reduce((acc, item) => {{
            const division = item['피평가부문'];
            const department = item['피평가부서'];
            if (division && division !== 'N/A' && department && department !== 'N/A') {{
                if (!acc[division]) {{ acc[division] = new Set(); }}
                acc[division].add(department);
            }}
            return acc;
        }}, {{}});
        for (const division in divisionDepartmentMap) {{
            divisionDepartmentMap[division] = [...divisionDepartmentMap[division]].sort((a, b) => String(a).localeCompare(String(b), 'ko'));
        }}

        function setupNetworkAnalysis() {{
            const yearSelect = document.getElementById('network-year-filter');
            const divisionSelect = document.getElementById('network-division-filter');
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const minCollabSelect = document.getElementById('min-collaboration-filter');
            
            // 연도 필터 설정
            yearSelect.innerHTML = ['전체', ...allYears].map(opt => `<option value="${{opt}}">${{opt}}</option>`).join('');
            
            // 부문 필터 설정 - 고정값: {target_division}만 선택 가능
            divisionSelect.innerHTML = `<option value="{target_division}">{target_division}</option>`;
            divisionSelect.value = "{target_division}";
            
            // 초기 부서, Unit 설정
            departmentSelect.innerHTML = '<option value="전체">전체</option>';
            unitSelect.innerHTML = '<option value="전체">전체</option>';
            
            // 이벤트 리스너 추가 (연도와 최소 횟수 필터만)
            yearSelect.addEventListener('change', updateNetworkAnalysis);
            minCollabSelect.addEventListener('change', updateNetworkAnalysis);
            
            // 초기 네트워크 분석 표시
            updateNetworkAnalysis();
        }}

        function updateNetworkDepartments() {{
            const divisionSelect = document.getElementById('network-division-filter');
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const selectedDivision = divisionSelect.value;
            
            // 부서 드롭다운을 {target_department}으로 고정
            departmentSelect.innerHTML = `<option value="{target_department}">{target_department}</option>`;
            departmentSelect.value = "{target_department}";
            
            // 부서 필터가 변경되었으므로, Unit 필터를 업데이트하고 분석을 새로고침합니다.
            updateNetworkUnits();
        }}

        function updateNetworkUnits() {{
            const departmentSelect = document.getElementById('network-department-filter');
            const unitSelect = document.getElementById('network-unit-filter');
            const selectedDept = departmentSelect.value;
            
            // Unit 드롭다운 업데이트
            const allUnits = [...new Set(rawData.map(item => item['피평가Unit']))].filter(u => u && u !== 'N/A').sort((a,b) => a.localeCompare(b, 'ko'));
            const units = (selectedDept === '전체' || !departmentUnitMap[selectedDept])
                ? allUnits
                : departmentUnitMap[selectedDept];
            
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
        
        function getNetworkFilteredDataWithoutYear() {{
            let filteredData = [...rawData];
            
            const selectedDivision = document.getElementById('network-division-filter').value;
            const selectedDepartment = document.getElementById('network-department-filter').value;
            const selectedUnit = document.getElementById('network-unit-filter').value;
            
            if (selectedDivision !== '전체') {{ filteredData = filteredData.filter(item => item['피평가부문'] === selectedDivision); }}
            if (selectedDepartment !== '전체') {{ filteredData = filteredData.filter(item => item['피평가부서'] === selectedDepartment); }}
            if (selectedUnit !== '전체') {{ filteredData = filteredData.filter(item => item['피평가Unit'] === selectedUnit); }}
            
            return filteredData;
        }}

        function updateNetworkAnalysis() {{
            updateCollaborationFrequencyChart();
        }}

        function updateCollaborationFrequencyChart() {{
            const container = document.getElementById('collaboration-frequency-chart-container');
            if (!container) {{
                console.warn('Container not found: collaboration-frequency-chart-container');
                return;
            }}
            const selectedYear = document.getElementById('network-year-filter').value;
            const minCollabCount = parseInt(document.getElementById('min-collaboration-filter').value);
            
            // 집계된 네트워크 분석 데이터 사용
            let collaborationCounts = {{}};
            if (selectedYear === '전체') {{
                // 모든 연도의 협업 횟수 합산
                Object.keys(aggregatedData.network_analysis || {{}}).forEach(year => {{
                    const yearData = aggregatedData.network_analysis[year];
                    if (yearData && yearData.collaboration_counts) {{
                        Object.entries(yearData.collaboration_counts).forEach(([relation, count]) => {{
                            collaborationCounts[relation] = (collaborationCounts[relation] || 0) + count;
                        }});
                    }}
                }});
            }} else {{
                // 특정 연도의 협업 횟수만 사용
                const yearData = aggregatedData.network_analysis && aggregatedData.network_analysis[selectedYear];
                if (yearData && yearData.collaboration_counts) {{
                    collaborationCounts = yearData.collaboration_counts;
                }}
            }}
            
            // 데이터가 없는 경우 처리
            if (Object.keys(collaborationCounts).length === 0) {{
                Plotly.react(container, [], {{
                    height: 400,
                    annotations: [{{ text: '선택된 조건에 해당하는 데이터가 없습니다.', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: {{size: 16, color: '#888'}} }}],
                    xaxis: {{visible: false}}, yaxis: {{visible: false}}
                }});
                return;
            }}
            
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
                marker: {{ color: '#355E58', line: {{ color: '#000000', width: 1 }} }},
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

        



        // 📊 차트 렌더링 안정성 개선 함수들
        function validatePlotlyReady() {{
            return new Promise((resolve) => {{
                if (typeof Plotly !== 'undefined' && Plotly.react) {
                    console.log('✅ Plotly ready');
                    resolve();
                } else {
                    console.log('⏳ Waiting for Plotly...');
                    setTimeout(() => validatePlotlyReady().then(resolve), 100);
                }
            });
        }
        
        function safeRenderChart(renderFunction, chartName) {{
            return new Promise((resolve) => {{
                try {
                    const startTime = performance.now();
                    const result = renderFunction();
                    const endTime = performance.now();
                    console.log(`✅ ${chartName} rendered in ${(endTime - startTime).toFixed(1)}ms`);
                    resolve(result);
                } catch (error) {
                    console.error(`❌ Chart render failed: ${chartName}`, error);
                    resolve();
                }
            });
        }
        
        async function initChartsSequentially() {
            // 기본 설정 먼저 초기화
            populateFilters();
            createCheckboxFilter('hospital-score-filter', scoreCols, 'hospital-score', updateHospitalYearlyChart);
            createCheckboxFilter('drilldown-score-filter', scoreCols, 'drilldown-score', updateDashboard);
            createCheckboxFilter('review-sentiment-filter', ['긍정', '부정', '중립'], 'review-sentiment', updateReviewsTable, true);
            
            // 차트 설정 초기화
            setupDivisionChart();
            setupComparisonChart();
            setupTeamRankingChart();
            setupUnitComparisonChart();
            setupNetworkAnalysis();
            
            // 차트 순차 렌더링 (100ms 간격)
            const chartRenderTasks = [
                { func: updateDashboard, name: 'Dashboard' },
                { func: updateHospitalYearlyChart, name: 'Hospital Yearly Chart' },
                { func: updateDivisionYearlyChart, name: 'Division Yearly Chart' },
                { func: updateYearlyDivisionComparisonChart, name: 'Division Comparison Chart' },
                { func: updateTeamRankingChart, name: 'Team Ranking Chart' },
                { func: updateUnitComparisonChart, name: 'Unit Comparison Chart' },
                { func: updateNetworkAnalysis, name: 'Network Analysis' }
            ];
            
            console.log('🚀 Starting sequential chart rendering...');
            for (let i = 0; i < chartRenderTasks.length; i++) {
                const task = chartRenderTasks[i];
                await new Promise(resolve => setTimeout(resolve, 100)); // 100ms 대기
                await safeRenderChart(task.func, task.name);
            }
            console.log('✅ All charts rendered successfully');
        }
        
        // 페이지 로드 시 안전한 초기화
        window.onload = async () => {
            try {
                console.log('📊 Initializing charts with enhanced stability...');
                await validatePlotlyReady();
                await initChartsSequentially();
            } catch (error) {
                console.error('❌ Chart initialization failed:', error);
                // 폴백: 기본 방식으로 재시도
                setTimeout(() => {
                    console.log('🔄 Retrying with fallback method...');
                    populateFilters();
                    updateDashboard();
                }, 1000);
            }
        }};
    </script>
</body>
</html>
    """.replace('{get_plotlyjs}', get_plotlyjs()).replace('{hybrid_data_json}', hybrid_data_json).replace('{target_department}', target_department).replace('{target_division}', target_division)

# ============================================================================
# 🚀 메인 실행 함수
# ============================================================================

def get_all_departments(df):
    """
    데이터에서 모든 부서 목록과 해당 부문을 추출
    
    Args:
        df (pd.DataFrame): 전체 데이터프레임
        
    Returns:
        dict: {부서명: 부문명} 형태의 딕셔너리
    """
    log_message("🔍 전체 부서 목록 추출 시작")
    
    # 피평가부서와 피평가부문 조합으로 부서별 부문 매핑 생성
    dept_division_data = df[['피평가부서', '피평가부문']].dropna()
    
    # 중복 제거하고 부서별 부문 매핑
    dept_division_map = {}
    for _, row in dept_division_data.drop_duplicates().iterrows():
        dept = row['피평가부서']
        division = row['피평가부문']
        
        if dept and dept != 'N/A' and division and division != 'N/A':
            # 하나의 부서가 여러 부문에 속할 수 있지만, 가장 빈도가 높은 부문을 사용
            if dept not in dept_division_map:
                dept_division_map[dept] = division
    
    # 부서별 데이터 건수 확인
    dept_counts = df['피평가부서'].value_counts()
    valid_departments = {}
    
    for dept, division in dept_division_map.items():
        count = dept_counts.get(dept, 0)
        if count > 0:  # 최소 1건 이상의 데이터가 있는 부서만 포함
            valid_departments[dept] = division
    
    log_message(f"✅ 추출된 부서: {len(valid_departments)}개")
    for dept, division in sorted(valid_departments.items()):
        count = dept_counts.get(dept, 0)
        log_message(f"   📂 {dept} ({division}) - {count}건")
    
    return valid_departments

def create_output_directory_structure():
    """
    출력 디렉토리 구조 생성
    
    Returns:
        str: 출력 디렉토리 경로
    """
    base_dir = Path("generated_reports")
    base_dir.mkdir(exist_ok=True)
    
    # 타임스탬프 폴더 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = base_dir / f"reports_{timestamp}"
    output_dir.mkdir(exist_ok=True)
    
    log_message(f"📁 출력 디렉토리 생성: {output_dir}")
    return str(output_dir)

def create_division_directories(output_dir, departments):
    """
    부문별 디렉토리 생성
    
    Args:
        output_dir (str): 기본 출력 디렉토리
        departments (dict): 부서별 부문 매핑
        
    Returns:
        dict: 부문별 디렉토리 경로 매핑
    """
    division_dirs = {}
    divisions = set(departments.values())
    
    for division in divisions:
        division_path = Path(output_dir) / division
        division_path.mkdir(exist_ok=True)
        division_dirs[division] = str(division_path)
        log_message(f"📁 부문 디렉토리 생성: {division}")
    
    return division_dirs

def calculate_aggregated_data_for_department(df, target_department, target_division):
    """
    특정 부서용 집계 데이터 계산 (동적 처리)
    
    Args:
        df (pd.DataFrame): 전체 데이터프레임
        target_department (str): 대상 부서명
        target_division (str): 대상 부문명
        
    Returns:
        dict: 집계된 통계 데이터
    """
    log_message(f"📊 집계 데이터 계산 시작: {target_department} ({target_division})")
    
    aggregated = {
        "hospital_yearly": {},
        "division_yearly": {},
        "division_comparison": {},
        "team_ranking": {},
        "network_analysis": {},
        "metadata": {
            "calculation_date": datetime.now().isoformat(),
            "total_responses": len(df),
            "target_department": target_department,
            "target_division": target_division,
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
    
    # 3. 소속 부문 결과 ([부문별] 연도별 문항 점수 - 대상 부문만)
    division_data = df[df['피평가부문'] == target_division]
    aggregated["division_yearly"][target_division] = {}
    for year in division_data['설문시행연도'].unique():
        if pd.notna(year):
            year_data = division_data[division_data['설문시행연도'] == year]
            aggregated["division_yearly"][target_division][str(year)] = {
                col: float(year_data[col].mean()) if col in year_data.columns else 0.0
                for col in SCORE_COLUMNS
            }
            aggregated["division_yearly"][target_division][str(year)]["응답수"] = len(year_data)
    
    # 4. 부문별 팀 점수 순위 - 대상 부문 부서들만
    for year in division_data['설문시행연도'].unique():
        if pd.notna(year):
            year_str = str(year)
            year_data = division_data[division_data['설문시행연도'] == year]
            dept_scores = []
            
            for dept in year_data['피평가부서'].unique():
                if pd.notna(dept):
                    dept_data = year_data[year_data['피평가부서'] == dept]
                    avg_score = dept_data['종합점수'].mean() if len(dept_data) > 0 else 0.0
                    dept_scores.append({
                        "department": dept,
                        "score": round(float(avg_score), 1),
                        "count": len(dept_data)
                    })
            
            # 점수 순으로 정렬하고 순위 부여
            dept_scores.sort(key=lambda x: x["score"], reverse=True)
            for i, dept in enumerate(dept_scores):
                dept["rank"] = i + 1
            
            aggregated["team_ranking"][year_str] = dept_scores
    
    # 5. 네트워크 분석용 집계 데이터 (평가부서 정보를 집계하여 응답수만 저장)
    # 해당 부서가 피평가 대상인 데이터만 필터링
    target_dept_data = df[df['피평가부서'] == target_department]
    
    for year in target_dept_data['설문시행연도'].unique():
        if pd.notna(year):
            year_str = str(year)
            year_data = target_dept_data[target_dept_data['설문시행연도'] == year]
            
            # 협업 관계별 응답수 집계 (평가부서별로 그룹화)
            collaboration_counts = {}
            for evaluator in year_data['평가부서'].unique():
                if pd.notna(evaluator) and evaluator != 'N/A':
                    count = len(year_data[year_data['평가부서'] == evaluator])
                    if count > 0:
                        # 평가부서 → 피평가부서(target_department) 형태로 저장
                        collaboration_counts[f"{evaluator} → {target_department}"] = count
            
            aggregated["network_analysis"][year_str] = {
                "collaboration_counts": collaboration_counts,
                "total_evaluators": len(year_data['평가부서'].unique()),
                "total_responses": len(year_data)
            }
    
    log_message(f"✅ 집계 데이터 계산 완료: {len(aggregated['hospital_yearly'])}년치 데이터")
    return aggregated

def calculate_aggregated_data_for_department_v2(df, target_department, target_division, exclude_dept=None):
    """
    특정 부서용 집계 데이터 계산 (v2 - 특정 부서 제외 가능)
    
    Args:
        df (pd.DataFrame): 전체 데이터프레임
        target_department (str): 대상 부서명
        target_division (str): 대상 부문명
        exclude_dept (str): 제외할 부서명 (optional)
        
    Returns:
        dict: 집계된 통계 데이터
    """
    log_message(f"📊 집계 데이터 계산 시작: {target_department} ({target_division})")
    
    aggregated = {
        "hospital_yearly": {},
        "division_yearly": {},
        "division_comparison": {},
        "team_ranking": {},
        "network_analysis": {},
        "metadata": {
            "calculation_date": datetime.now().isoformat(),
            "total_responses": len(df),
            "target_department": target_department,
            "target_division": target_division,
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
    
    # 3. 소속 부문 결과 ([부문별] 연도별 문항 점수 - 대상 부문만)
    division_data = df[df['피평가부문'] == target_division]
    aggregated["division_yearly"][target_division] = {}
    for year in division_data['설문시행연도'].unique():
        if pd.notna(year):
            year_data = division_data[division_data['설문시행연도'] == year]
            aggregated["division_yearly"][target_division][str(year)] = {
                col: float(year_data[col].mean()) if col in year_data.columns else 0.0
                for col in SCORE_COLUMNS
            }
            aggregated["division_yearly"][target_division][str(year)]["응답수"] = len(year_data)
    
    # 4. 부문별 팀 점수 순위 - 대상 부문 부서들만
    for year in division_data['설문시행연도'].unique():
        if pd.notna(year):
            year_str = str(year)
            year_data = division_data[division_data['설문시행연도'] == year]
            dept_scores = []
            
            for dept in year_data['피평가부서'].unique():
                # exclude_dept가 지정되면 해당 부서는 제외
                if pd.notna(dept) and (exclude_dept is None or dept != exclude_dept):
                    dept_data = year_data[year_data['피평가부서'] == dept]
                    avg_score = dept_data['종합점수'].mean() if len(dept_data) > 0 else 0.0
                    dept_scores.append({
                        "department": dept,
                        "score": round(float(avg_score), 1),
                        "count": len(dept_data)
                    })
            
            # 점수 순으로 정렬하고 순위 부여
            dept_scores.sort(key=lambda x: x["score"], reverse=True)
            for i, dept in enumerate(dept_scores):
                dept["rank"] = i + 1
            
            aggregated["team_ranking"][year_str] = dept_scores
    
    # 5. 네트워크 분석용 집계 데이터 (평가부서 정보를 집계하여 응답수만 저장)
    # 해당 부서가 피평가 대상인 데이터만 필터링
    target_dept_data = df[df['피평가부서'] == target_department]
    
    for year in target_dept_data['설문시행연도'].unique():
        if pd.notna(year):
            year_str = str(year)
            year_data = target_dept_data[target_dept_data['설문시행연도'] == year]
            
            # 협업 관계별 응답수 집계 (평가부서별로 그룹화)
            collaboration_counts = {}
            for evaluator in year_data['평가부서'].unique():
                if pd.notna(evaluator) and evaluator != 'N/A':
                    count = len(year_data[year_data['평가부서'] == evaluator])
                    if count > 0:
                        # 평가부서 → 피평가부서(target_department) 형태로 저장
                        collaboration_counts[f"{evaluator} → {target_department}"] = count
            
            aggregated["network_analysis"][year_str] = {
                "collaboration_counts": collaboration_counts,
                "total_evaluators": len(year_data['평가부서'].unique()),
                "total_responses": len(year_data)
            }
    
    log_message(f"✅ 집계 데이터 계산 완료: {len(aggregated['hospital_yearly'])}년치 데이터")
    return aggregated

def generate_department_report(df, department, division, output_path, progress_info):
    """
    개별 부서 보고서 생성
    
    Args:
        df (pd.DataFrame): 전체 데이터프레임
        department (str): 대상 부서명
        division (str): 해당 부서의 부문명
        output_path (str): 출력 파일 경로
        progress_info (dict): 진행 상황 정보
        
    Returns:
        dict: 생성 결과 정보
    """
    try:
        log_message(f"🔄 {department} 보고서 생성 시작 ({progress_info['current']}/{progress_info['total']})")
        
        # 1. 집계 데이터 계산 (부서별 맞춤)
        aggregated_data = calculate_aggregated_data_for_department(df, department, division)
        
        # 2. 부서별 필터링된 데이터 준비
        filtered_rawdata = prepare_department_filtered_data(df, department)
        
        # 3. HTML 생성
        html_content = build_secure_html(aggregated_data, filtered_rawdata, department, division)
        
        # 4. 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        log_message(f"✅ {department} 보고서 생성 완료")
        
        return {
            'department': department,
            'division': division,
            'status': 'success',
            'file_path': output_path,
            'error': None
        }
        
    except Exception as e:
        log_message(f"❌ {department} 보고서 생성 실패: {str(e)}", "ERROR")
        
        return {
            'department': department,
            'division': division,
            'status': 'failed',
            'file_path': output_path,
            'error': str(e)
        }

def generate_department_report_v2(df, department, division, output_path, progress_info):
    """
    개별 부서 보고서 생성 (v2 - 진료부문 전용, 방사성의약품제조소 제외)
    
    Args:
        df (pd.DataFrame): 전체 데이터프레임
        department (str): 대상 부서명
        division (str): 해당 부서의 부문명
        output_path (str): 출력 파일 경로
        progress_info (dict): 진행 상황 정보
        
    Returns:
        dict: 생성 결과 정보
    """
    try:
        log_message(f"🔄 {department} 보고서 생성 시작 ({progress_info['current']}/{progress_info['total']})")
        
        # 1. 집계 데이터 계산 (방사성의약품제조소 제외)
        aggregated_data = calculate_aggregated_data_for_department_v2(df, department, division, exclude_dept='방사성의약품제조소')
        
        # 2. 부서별 필터링된 데이터 준비
        filtered_rawdata = prepare_department_filtered_data(df, department)
        
        # 3. HTML 생성
        html_content = build_secure_html(aggregated_data, filtered_rawdata, department, division)
        
        # 4. 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        log_message(f"✅ {department} 보고서 생성 완료")
        
        return {
            'department': department,
            'division': division,
            'status': 'success',
            'file_path': output_path,
            'error': None
        }
        
    except Exception as e:
        log_message(f"❌ {department} 보고서 생성 실패: {str(e)}", "ERROR")
        
        return {
            'department': department,
            'division': division,
            'status': 'failed',
            'file_path': output_path,
            'error': str(e)
        }

def generate_summary_report(results, output_dir, start_time):
    """
    생성 결과 요약 보고서 생성
    
    Args:
        results (list): 생성 결과 리스트
        output_dir (str): 출력 디렉토리
        start_time (datetime): 시작 시간
    """
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 결과 분석
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']
    
    # 부문별 통계
    division_stats = {}
    for result in successful:
        division = result['division']
        if division not in division_stats:
            division_stats[division] = 0
        division_stats[division] += 1
    
    # 요약 보고서 생성
    summary_content = f"""# 서울아산병원 협업 평가 결과 보고 전체 부서 생성 결과

## 📊 생성 요약
- **생성 일시**: {start_time.strftime('%Y년 %m월 %d일 %H:%M:%S')}
- **소요 시간**: {duration}
- **전체 부서**: {len(results)}개
- **성공**: {len(successful)}개
- **실패**: {len(failed)}개

## 🏢 부문별 생성 현황
"""
    
    for division, count in sorted(division_stats.items()):
        summary_content += f"- **{division}**: {count}개 부서\n"
    
    if successful:
        summary_content += f"\n## ✅ 성공한 부서 ({len(successful)}개)\n"
        for result in successful:
            summary_content += f"- {result['department']} ({result['division']})\n"
    
    if failed:
        summary_content += f"\n## ❌ 실패한 부서 ({len(failed)}개)\n"
        for result in failed:
            summary_content += f"- {result['department']} ({result['division']}): {result['error']}\n"
    
    summary_content += f"\n## 📁 생성된 파일 목록\n"
    for result in successful:
        summary_content += f"- {result['file_path']}\n"
    
    # 요약 파일 저장
    summary_path = Path(output_dir) / "생성_결과_요약.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    log_message(f"📋 생성 결과 요약 저장: {summary_path}")

def main():
    """
    메인 실행 함수 - 전체 부서 보고서 자동 생성
    """
    start_time = datetime.now()
    
    try:
        # 시작 메시지
        print("=" * 70)
        print("🚀 서울아산병원 협업 평가 결과 보고 전체 부서 생성 시작")
        print(f"📅 실행 시간: {start_time.strftime('%Y년 %m월 %d일 %H:%M:%S')}")
        print("=" * 70)
        
        # 1. 데이터 로드 및 전처리
        log_message("📊 데이터 로드 및 전처리")
        df = load_data()
        
        # 2. 데이터 요약 정보 출력
        summary = get_data_summary(df)
        log_message(f"📊 데이터 요약: {summary['총_응답수']:,}건, 평균 점수: {summary['평균_종합점수']}점")
        
        # 3. 전체 부서 목록 추출
        log_message("📁 대상 부서 목록 추출")
        departments = get_all_departments(df)
        
        if not departments:
            log_message("❌ 생성할 부서가 없습니다.", "ERROR")
            return False
        
        # 4. 출력 디렉토리 구조 생성
        log_message("📁 출력 디렉토리 생성")
        output_dir = create_output_directory_structure()
        division_dirs = create_division_directories(output_dir, departments)
        
        # 5. 부서별 보고서 생성
        log_message("📄 부서별 보고서 생성")
        
        results = []
        total_departments = len(departments)
        
        for idx, (department, division) in enumerate(departments.items(), 1):
            # 진행 상황 정보
            progress_info = {
                'current': idx,
                'total': total_departments,
                'percentage': (idx / total_departments) * 100
            }
            
            # 출력 파일 경로 생성
            division_dir = division_dirs[division]
            filename = f"서울아산병원 협업평가 결과_{department}_offline_fixed.html"
            output_path = str(Path(division_dir) / filename)
            
            # 부서별 보고서 생성
            result = generate_department_report(df, department, division, output_path, progress_info)
            results.append(result)
            
            # 진행률 표시
            log_message(f"📊 진행률: {progress_info['percentage']:.1f}% ({idx}/{total_departments})")
        
        # 6. 생성 결과 요약
        log_message("📊 생성 결과 요약")
        generate_summary_report(results, output_dir, start_time)
        
        # 7. 최종 결과 출력
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len([r for r in results if r['status'] == 'failed'])
        
        print("\n" + "=" * 70)
        print("🎉 전체 부서 보고서 생성 완료!")
        print("=" * 70)
        print(f"📊 성공: {successful}개, 실패: {failed}개")
        print(f"📁 출력 위치: {output_dir}")
        print(f"⏱️ 소요 시간: {datetime.now() - start_time}")
        print("=" * 70)
        
        return failed == 0  # 실패가 없으면 True
        
    except Exception as e:
        log_message(f"❌ 전체 프로세스 오류: {str(e)}", "ERROR")
        
        # 상세한 오류 정보 출력
        print("\n" + "=" * 70)
        print("❌ 오류 발생!")
        print("=" * 70)
        print(f"오류 내용: {str(e)}")
        print("\n📋 문제 해결 방법:")
        print("   1. 데이터 파일 경로를 확인하세요")
        print("   2. 데이터 파일이 올바른 형식인지 확인하세요")
        print("   3. 필요한 라이브러리가 설치되어 있는지 확인하세요")
        print("   4. 설정 섹션의 컬럼명이 데이터와 일치하는지 확인하세요")
        print("   5. 파일 경로에 한글이나 특수문자가 있는지 확인하세요")
        
        # 개발자용 상세 오류 정보
        print("\n🔧 개발자용 상세 오류 정보:")
        print("-" * 50)
        traceback.print_exc()
        print("=" * 70)
        
        return False

def main_clinical_v2():
    """
    메인 실행 함수 - 진료부문 버전2 (방사성의약품제조소 제외)
    """
    start_time = datetime.now()
    
    try:
        # 시작 메시지
        print("=" * 70)
        print("🚀 서울아산병원 협업 평가 결과 보고 진료부문 버전2 생성 시작")
        print("📌 방사성의약품제조소 제외")
        print(f"📅 실행 시간: {start_time.strftime('%Y년 %m월 %d일 %H:%M:%S')}")
        print("=" * 70)
        
        # 1. 데이터 로드 및 전처리
        log_message("📊 데이터 로드 및 전처리")
        df = load_data()
        
        # 2. 데이터 요약 정보 출력
        summary = get_data_summary(df)
        log_message(f"📊 데이터 요약: {summary['총_응답수']:,}건, 평균 점수: {summary['평균_종합점수']}점")
        
        # 3. 전체 부서 목록 추출
        log_message("📁 대상 부서 목록 추출")
        all_departments = get_all_departments(df)
        
        # 4. 진료부문 부서만 필터링 (방사성의약품제조소 제외)
        clinical_departments = {
            dept: div for dept, div in all_departments.items() 
            if div == '진료부문' and dept != '방사성의약품제조소'
        }
        
        if not clinical_departments:
            log_message("❌ 생성할 진료부문 부서가 없습니다.", "ERROR")
            return False
        
        log_message(f"📋 진료부문 부서 수: {len(clinical_departments)}개 (방사성의약품제조소 제외)")
        
        # 5. 출력 디렉토리 구조 생성 (진료부문_v2)
        log_message("📁 출력 디렉토리 생성")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"generated_reports/진료부문_v2_{timestamp}"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 진료부문 디렉토리 생성
        clinical_dir = Path(output_dir) / "진료부문"
        clinical_dir.mkdir(exist_ok=True)
        
        # 6. 부서별 보고서 생성
        log_message("📄 진료부문 부서별 보고서 생성 (방사성의약품제조소 제외)")
        
        results = []
        total_departments = len(clinical_departments)
        
        for idx, (department, division) in enumerate(clinical_departments.items(), 1):
            # 진행 상황 정보
            progress_info = {
                'current': idx,
                'total': total_departments,
                'percentage': (idx / total_departments) * 100
            }
            
            # 출력 파일 경로 생성
            filename = f"서울아산병원 협업평가 결과_{department}_offline_fixed.html"
            output_path = str(clinical_dir / filename)
            
            # 부서별 보고서 생성 (v2 버전 사용)
            result = generate_department_report_v2(df, department, division, output_path, progress_info)
            results.append(result)
            
            # 진행률 표시
            log_message(f"📊 진행률: {progress_info['percentage']:.1f}% ({idx}/{total_departments})")
        
        # 7. 생성 결과 요약
        log_message("📊 생성 결과 요약")
        generate_summary_report(results, output_dir, start_time)
        
        # 8. 최종 결과 출력
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len([r for r in results if r['status'] == 'failed'])
        
        print("\n" + "=" * 70)
        print("🎉 진료부문 버전2 보고서 생성 완료!")
        print("📌 방사성의약품제조소 제외")
        print("=" * 70)
        print(f"📊 성공: {successful}개, 실패: {failed}개")
        print(f"📁 출력 위치: {output_dir}")
        print(f"⏱️ 소요 시간: {datetime.now() - start_time}")
        print("=" * 70)
        
        return failed == 0  # 실패가 없으면 True
        
    except Exception as e:
        log_message(f"❌ 전체 프로세스 오류: {str(e)}", "ERROR")
        
        # 상세한 오류 정보 출력
        print("\n" + "=" * 70)
        print("❌ 오류 발생!")
        print("=" * 70)
        print(f"오류 내용: {str(e)}")
        print("\n📋 문제 해결 방법:")
        print("   1. 데이터 파일 경로를 확인하세요")
        print("   2. 데이터 파일이 올바른 형식인지 확인하세요")
        print("   3. 필요한 라이브러리가 설치되어 있는지 확인하세요")
        print("   4. 설정 섹션의 컬럼명이 데이터와 일치하는지 확인하세요")
        print("   5. 파일 경로에 한글이나 특수문자가 있는지 확인하세요")
        
        # 개발자용 상세 오류 정보
        print("\n🔧 개발자용 상세 오류 정보:")
        print("-" * 50)
        traceback.print_exc()
        print("=" * 70)
        
        return False

if __name__ == "__main__":
    # 실행 옵션을 인자로 받을 수 있도록 수정
    if len(sys.argv) > 1 and sys.argv[1] == "clinical_v2":
        success = main_clinical_v2()
    else:
        success = main()
    sys.exit(0 if success else 1)