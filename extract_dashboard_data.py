#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드 섹션 1-4 데이터 추출기
3. build_dashboard_html.py의 섹션 1-4 모든 데이터를 엑셀로 추출합니다.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# 기존 build_dashboard_html.py와 동일한 설정
def get_latest_text_processor_file():
    """rawdata 폴더에서 가장 최근 text_processor 결과 파일 찾기"""
    rawdata_path = Path("rawdata")
    pattern = "2. text_processor_결과_*.xlsx"
    
    files = [f for f in rawdata_path.glob(pattern) if not f.name.endswith('_partial.xlsx')]
    
    if not files:
        files = list(rawdata_path.glob(pattern))
    
    if files:
        latest_file = max(files, key=lambda x: x.stat().st_mtime)
        return str(latest_file)
    else:
        return "rawdata/2. text_processor_결과_20250710_153008.xlsx"

INPUT_DATA_FILE = get_latest_text_processor_file()
OUTPUT_FILE = "대시보드_섹션1234_데이터.xlsx"

# 데이터 컬럼 정의
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

SCORE_COLUMNS = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수']

def load_and_process_data():
    """데이터 로드 및 전처리"""
    print("🚀 데이터 로드 및 전처리 시작...")
    
    try:
        df = pd.read_excel(INPUT_DATA_FILE)
        print(f"✅ 데이터 로드 완료: {len(df):,}건")
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {INPUT_DATA_FILE}")
        return None
    
    # 컬럼명 설정
    df.columns = EXCEL_COLUMNS
    
    # 컬럼명 단순화
    column_mapping = {
        '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.': '존중배려',
        '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.': '정보공유',
        '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.': '명확처리',
        '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.': '태도개선',
        '전반적으로 ○○과의 협업에 대해 만족한다.': '전반만족'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 데이터 전처리
    df['설문시행연도'] = df['설문시행연도'].astype(str)
    
    # 결측값 처리
    fill_na_columns = ['피평가대상 부문', '피평가대상 부서명', '피평가대상 UNIT명']
    for col in fill_na_columns:
        if col in df.columns:
            df[col] = df[col].fillna('N/A')
    
    # 제외 값 필터링
    exclude_values = ['미분류', '윤리경영실']
    for col in ['피평가대상 부문', '피평가대상 부서명']:
        if col in df.columns:
            df = df[~df[col].isin(exclude_values)]
    
    # 필수 컬럼 확인
    for col in SCORE_COLUMNS:
        if col not in df.columns:
            print(f"❌ 필수 컬럼이 없습니다: {col}")
            return None
    
    print(f"📊 전처리 완료: {len(df):,}건")
    return df

def extract_section1_data(df):
    """섹션 1: [전체] 연도별 문항 점수"""
    print("📊 섹션 1 데이터 추출 중...")
    
    section1_data = []
    years = sorted(df['설문시행연도'].unique())
    
    for year in years:
        year_data = df[df['설문시행연도'] == year]
        
        if len(year_data) == 0:
            continue
            
        row = {'연도': year, '응답수': len(year_data)}
        
        for col in SCORE_COLUMNS:
            if col in year_data.columns:
                row[col] = round(float(year_data[col].mean()), 2)
            else:
                row[col] = 0
        
        section1_data.append(row)
    
    return pd.DataFrame(section1_data)

def extract_section2_data(df):
    """섹션 2: [부문별] 연도별 문항 점수"""
    print("📊 섹션 2 데이터 추출 중...")
    
    section2_data = []
    divisions = sorted(df['피평가대상 부문'].unique())
    years = sorted(df['설문시행연도'].unique())
    
    for division in divisions:
        div_data = df[df['피평가대상 부문'] == division]
        
        for year in years:
            year_data = div_data[div_data['설문시행연도'] == year]
            
            if len(year_data) == 0:
                continue
                
            row = {
                '부문': division,
                '연도': year, 
                '응답수': len(year_data)
            }
            
            for col in SCORE_COLUMNS:
                if col in year_data.columns:
                    row[col] = round(float(year_data[col].mean()), 2)
                else:
                    row[col] = 0
            
            section2_data.append(row)
    
    return pd.DataFrame(section2_data)

def extract_section3_data(df):
    """섹션 3: 연도별 부문 비교"""
    print("📊 섹션 3 데이터 추출 중...")
    
    section3_data = []
    years = sorted(df['설문시행연도'].unique())
    
    for year in years:
        year_data = df[df['설문시행연도'] == year]
        divisions = sorted(year_data['피평가대상 부문'].unique())
        
        for division in divisions:
            div_year_data = year_data[year_data['피평가대상 부문'] == division]
            
            if len(div_year_data) == 0:
                continue
                
            row = {
                '연도': year,
                '부문': division,
                '응답수': len(div_year_data)
            }
            
            for col in SCORE_COLUMNS:
                if col in div_year_data.columns:
                    row[col] = round(float(div_year_data[col].mean()), 2)
                else:
                    row[col] = 0
            
            section3_data.append(row)
    
    return pd.DataFrame(section3_data)

def extract_section4_data(df):
    """섹션 4: 부문별 팀 점수 순위"""
    print("📊 섹션 4 데이터 추출 중...")
    
    section4_data = []
    years = sorted(df['설문시행연도'].unique())
    
    for year in years:
        year_data = df[df['설문시행연도'] == year]
        divisions = sorted(year_data['피평가대상 부문'].unique())
        
        for division in divisions:
            div_year_data = year_data[year_data['피평가대상 부문'] == division]
            
            if len(div_year_data) == 0:
                continue
            
            # 부서별 점수 계산
            dept_scores = []
            departments = div_year_data['피평가대상 부서명'].unique()
            
            for dept in departments:
                dept_data = div_year_data[div_year_data['피평가대상 부서명'] == dept]
                
                if len(dept_data) == 0:
                    continue
                    
                avg_score = dept_data['종합점수'].mean()
                dept_scores.append({
                    '부서': dept,
                    '점수': avg_score,
                    '응답수': len(dept_data)
                })
            
            # 점수 순으로 정렬
            dept_scores.sort(key=lambda x: x['점수'], reverse=True)
            
            # 순위 추가
            for i, dept_info in enumerate(dept_scores):
                row = {
                    '연도': year,
                    '부문': division,
                    '부서': dept_info['부서'],
                    '종합점수': round(float(dept_info['점수']), 2),
                    '응답수': dept_info['응답수'],
                    '순위': i + 1
                }
                
                # 세부 점수도 추가
                dept_data = div_year_data[div_year_data['피평가대상 부서명'] == dept_info['부서']]
                for col in SCORE_COLUMNS[:-1]:  # 종합점수 제외
                    if col in dept_data.columns:
                        row[col] = round(float(dept_data[col].mean()), 2)
                    else:
                        row[col] = 0
                
                section4_data.append(row)
    
    return pd.DataFrame(section4_data)

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("📊 대시보드 섹션 1-4 데이터 추출기")
    print("=" * 80)
    
    # 데이터 로드
    df = load_and_process_data()
    if df is None:
        return
    
    # 각 섹션별 데이터 추출
    section1_df = extract_section1_data(df)
    section2_df = extract_section2_data(df)
    section3_df = extract_section3_data(df)
    section4_df = extract_section4_data(df)
    
    # 엑셀 파일로 저장
    print(f"\n💾 엑셀 파일 저장 중...")
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        section1_df.to_excel(writer, sheet_name='섹션1_전체연도별점수', index=False)
        section2_df.to_excel(writer, sheet_name='섹션2_부문별연도별점수', index=False)
        section3_df.to_excel(writer, sheet_name='섹션3_연도별부문비교', index=False)
        section4_df.to_excel(writer, sheet_name='섹션4_부문별팀순위', index=False)
    
    print(f"🎉 추출 완료! 결과가 '{OUTPUT_FILE}' 파일로 저장되었습니다.")
    
    # 결과 요약
    print(f"\n📈 데이터 추출 결과:")
    print(f"   - 섹션 1 (전체 연도별): {len(section1_df)}개 데이터")
    print(f"   - 섹션 2 (부문별 연도별): {len(section2_df)}개 데이터")
    print(f"   - 섹션 3 (연도별 부문비교): {len(section3_df)}개 데이터")
    print(f"   - 섹션 4 (부문별 팀순위): {len(section4_df)}개 데이터")
    
    # 샘플 데이터 미리보기
    print(f"\n👀 섹션 1 샘플 데이터:")
    print(section1_df.head(3).to_string(index=False))
    
    print(f"\n👀 섹션 4 샘플 데이터:")
    print(section4_df.head(3).to_string(index=False))

if __name__ == "__main__":
    main()