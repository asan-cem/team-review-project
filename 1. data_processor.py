#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local version of the Colab environment analyzer
Adapted from 협업평가_250619.ipynb for local execution

This script provides the same functionality as the Colab notebook
but adapted for local environment without Google Colab dependencies.
"""

import pandas as pd
import datetime
from pathlib import Path
import numpy as np
import re
import time
import unicodedata
import os

# Google Cloud libraries (available in local environment)
import vertexai
from vertexai.generative_models import GenerativeModel
from tqdm.auto import tqdm

# Enable tqdm integration with pandas
tqdm.pandas()

class LocalGoogleSheetsAnalyzer:
    """Local version of the Google Sheets analyzer from Colab"""

    def __init__(self, base_path: str, mapping_file_path: str = None, output_path: str = None, **kwargs):
        self.base_path = Path(base_path)
        self.mapping_file_path = mapping_file_path
        self.standard_map_path = kwargs.get('standard_map_path')
        self.output_path = Path(output_path) if output_path else Path(base_path).parent
        self.department_mapping = {}
        self.department_standard_map = {}

        self.question_columns = [
            '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.',
            '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.',
            '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.',
            '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.',
            '전반적으로 ○○과의 협업에 대해 만족한다.'
        ]

    def load_department_standard_map(self):
        """부서명 표준화 매핑 로드"""
        if not self.standard_map_path or not Path(self.standard_map_path).exists():
            print(f"⚠️ 부서명 표준화 매핑 파일이 없습니다. 부서명을 그대로 사용합니다.")
            return
        try:
            map_df = pd.read_excel(self.standard_map_path)
            if '변경전_부서명' in map_df.columns and '표준_부서명' in map_df.columns:
                self.department_standard_map = dict(zip(map_df['변경전_부서명'], map_df['표준_부서명']))
                print(f"✅ 부서명 표준화 매핑 로드 완료: {len(self.department_standard_map)}개")
        except Exception as e:
            print(f"❌ 부서명 표준화 매핑 파일 로드 오류: {e}")

    def load_department_mapping(self):
        """부서-부문 매핑 로드"""
        if not self.mapping_file_path or not Path(self.mapping_file_path).exists(): 
            return
        try:
            mapping_df = pd.read_excel(self.mapping_file_path)
            if '부서명' in mapping_df.columns and '부문' in mapping_df.columns:
                self.department_mapping = dict(zip(
                    mapping_df.dropna(subset=['부서명', '부문'])['부서명'], 
                    mapping_df.dropna(subset=['부서명', '부문'])['부문']
                ))
                print(f"✅ 부문 매핑 로드 완료: {len(self.department_mapping)}개")
        except Exception as e:
            print(f"❌ 부문 매핑 파일 로드 오류: {e}")

    def load_and_process_data(self, file_identifiers):
        """데이터 로드 및 처리"""
        print("📂 데이터 로드 시작...")
        self.load_department_mapping()
        self.load_department_standard_map()

        integrated_df = pd.DataFrame()
        for identifier in file_identifiers:
            normalized_identifier = unicodedata.normalize('NFKC', identifier)
            file_name_base = unicodedata.normalize('NFKC', '설문조사진행현황[VCRCRIC120S]_')
            file_name = f"{file_name_base}{normalized_identifier}.xlsx"

            actual_file_path = None
            for item in self.base_path.iterdir():
                if unicodedata.normalize('NFKC', item.name) == file_name:
                    actual_file_path = item
                    break

            if not actual_file_path:
                print(f"⚠️ 파일 없음: {file_name}")
                continue

            try:
                df = pd.read_excel(actual_file_path, sheet_name='직원별대상문항 현황')
                
                # Check if '설문시행연도' column exists in original data
                if '설문시행연도' in df.columns:
                    # Use original data as-is
                    pass
                else:
                    # Extract year from identifier (e.g., "2022_1" -> "2022")
                    year = identifier.split('_')[0] if '_' in identifier else identifier
                    df['설문시행연도'] = year
                
                df['response_id'] = [f"{identifier}_{i+1}" for i in range(len(df))]
                integrated_df = pd.concat([integrated_df, df], ignore_index=True)
                print(f"  -> {actual_file_path.name} ({len(df)}행 로드)")
            except Exception as e:
                print(f"❌ 파일 처리 오류 {actual_file_path.name}: {e}")

        if integrated_df.empty: 
            return pd.DataFrame(), {}
        
        processed_df = self._preprocess_data(integrated_df)
        self._print_processing_summary(processed_df, {})
        return processed_df, {}

    def _preprocess_data(self, df):
        """데이터 전처리"""
        print("\n🔄 데이터 전처리 시작...")
        df = df.drop_duplicates(keep='first')

        def convert_score(score):
            if pd.isna(score): return None
            try:
                score_float = float(score)
                return ((score_float - 1) / 4) * 100 if score_float in [1, 2, 3, 4, 5] else None
            except (ValueError, TypeError): return None
        
        for q_col in self.question_columns:
            if q_col in df.columns: 
                df[q_col] = df[q_col].apply(convert_score)

        # Column renaming
        rename_map = {'UNIT명': '평가_Unit명'}
        for col in df.columns:
            if '어떤 업무를 협력하여' in str(col):
                rename_map[col] = '협업 유형'
            elif '만족스러웠거나 아쉬웠던 경험' in str(col):
                rename_map[col] = '협업 후기'

        df.rename(columns=rename_map, inplace=True)
        print("✅ 서술형 컬럼 및 Unit명 변경 완료")

        # Standardize department names
        cols_to_standardize = ['평가_부서명', '피평가대상 부서명']
        if '부서명' in df.columns: 
            df.rename(columns={'부서명': '평가_부서명'}, inplace=True)

        if self.department_standard_map:
            for col_name in cols_to_standardize:
                if col_name in df.columns:
                    original_col_name = f"{col_name.replace(' ', '_')}_원본"
                    df.rename(columns={col_name: original_col_name}, inplace=True)
                    df[col_name] = df[original_col_name].map(self.department_standard_map).fillna(df[original_col_name])
                    print(f"✅ '{col_name}' 컬럼 표준화 적용 완료")

        # Calculate scores
        available_q_cols = [col for col in self.question_columns if col in df.columns]
        if available_q_cols:
            df['결측값'] = df[available_q_cols].isnull().any(axis=1).apply(lambda x: 'Y' if x else 'N')
            df['종합점수'] = df[available_q_cols].mean(axis=1, skipna=True).round(2)
        
        def check_extreme_value(row):
            return '극단값' if pd.notna(row.get('종합점수')) and row['종합점수'] == 0 else '정상'
        df['극단값'] = df.apply(check_extreme_value, axis=1)

        # Map departments to divisions
        if '피평가대상 부서명' in df.columns:
            df['부문'] = df['피평가대상 부서명'].map(self.department_mapping).fillna('미분류')
            print("🏢 피평가대상 부문 매핑 완료")

        if '평가_부서명' in df.columns:
            df['평가_부문'] = df['평가_부서명'].map(self.department_mapping).fillna('미분류')
            print("🏢 평가자 부문 매핑 완료")

        return df

    def _print_processing_summary(self, df, processing_stats):
        """처리 결과 요약 출력"""
        print("\n" + "="*60 + "\n📊 데이터 처리 결과 요약\n" + "="*60)
        print(f"📋 총 응답 수: {len(df):,}개")
        if '결측값' in df.columns:
            print(f"❓ 결측값 포함 응답: {(df['결측값'] == 'Y').sum():,}개")
        if '극단값' in df.columns:
            print(f"⚠️ 극단값(종합점수 0점) 응답: {(df['극단값'] == '극단값').sum():,}개")
        if '종합점수' in df.columns and df['종합점수'].notna().any():
            print(f"📊 전체 평균 점수 (0-100점 척도): {df['종합점수'].mean():.2f}점")
        print("="*60)

    def prepare_final_output(self, df):
        """최종 출력을 위한 컬럼 순서 정리"""
        desired_columns = [
            'response_id', '설문시행연도', '평가_부서명', '평가_부서명_원본', '평가_Unit명', '평가_부문',
            '피평가대상 부서명', '피평가대상_부서명_원본', '피평가대상 UNIT명', '피평가대상 부문',
            '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.',
            '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.',
            '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.',
            '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.',
            '전반적으로 ○○과의 협업에 대해 만족한다.',
            '종합점수', '극단값', '결측값', '협업 유형', '협업 후기'
        ]
        
        # 컬럼명 매핑 (기존 컬럼명 → 원하는 컬럼명)
        column_mapping = {
            '부문': '피평가대상 부문'
        }
        
        # 컬럼명 변경
        df_final = df.copy()
        for old_name, new_name in column_mapping.items():
            if old_name in df_final.columns and new_name != old_name:
                df_final.rename(columns={old_name: new_name}, inplace=True)
                # 원하는 순서로 컬럼 재정렬 (존재하는 컬럼만)
        available_columns = [col for col in desired_columns if col in df_final.columns]
        df_final = df_final[available_columns]
        
        print(f"✅ 최종 출력 형식 정리 완료: {len(available_columns)}개 컬럼")
        return df_final


def main_local_analysis(base_path: str, project_id: str = None):
    """메인 로컬 분석 함수"""
    print("🚀 로컬 환경에서 협업 평가 분석 시작")
    
    # 파일 인식
    raw_data_path = Path(base_path)
    file_prefix = "설문조사진행현황[VCRCRIC120S]_"
    file_suffix = ".xlsx"
    file_identifiers = []
    
    if raw_data_path.exists():
        normalized_prefix = unicodedata.normalize('NFKC', file_prefix)
        for item in raw_data_path.iterdir():
            if item.is_file():
                normalized_filename = unicodedata.normalize('NFKC', item.name)
                if normalized_filename.startswith(normalized_prefix) and normalized_filename.endswith(file_suffix):
                    identifier = normalized_filename.replace(normalized_prefix, "").replace(file_suffix, "")
                    file_identifiers.append(identifier)
        file_identifiers.sort()

    if not file_identifiers:
        print(f"\n❌ 분석할 설문 파일을 찾을 수 없습니다.")
        return None

    print(f"\n✅ {len(file_identifiers)}개의 설문 파일을 찾았습니다: {file_identifiers}")

    # 매핑 파일 경로 설정
    standard_map_path = raw_data_path / "부서명_표준화_매핑.xlsx"
    mapping_file_path = raw_data_path / "부서_부문_매핑.xlsx"

    
    # 데이터 분석기 실행
    analyzer = LocalGoogleSheetsAnalyzer(
        base_path, 
        mapping_file_path=str(mapping_file_path) if mapping_file_path.exists() else None,
        standard_map_path=str(standard_map_path) if standard_map_path.exists() else None
    )
    processed_df, _ = analyzer.load_and_process_data(file_identifiers)
    
    if processed_df.empty:
        print("❌ 처리할 데이터가 없습니다.")
        return None

    # AI 분석 (옵션)
    if project_id:
        ai_analyzer = LocalAIAnalyzer(project_id)
        processed_df = ai_analyzer.analyze_dataframe(processed_df)

    # 최종 출력 형식 정리
    analyzer = LocalGoogleSheetsAnalyzer(
        base_path, 
        mapping_file_path=str(mapping_file_path) if mapping_file_path.exists() else None,
        standard_map_path=str(standard_map_path) if standard_map_path.exists() else None
    )
    final_df = analyzer.prepare_final_output(processed_df)
    
    # 결과 저장
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"1. data_processor_결과_{timestamp}.xlsx"
    output_path = Path(base_path) / output_filename
    final_df.to_excel(output_path, index=False)
    print(f"✅ 결과 파일 저장 완료: {output_path}")

    return final_df


if __name__ == "__main__":
    # 사용 예시
    BASE_PATH = "./rawdata"  # rawdata 폴더에서 파일 검색
    PROJECT_ID = None  # Google Cloud 프로젝트 ID (옵션)
    
    result_df = main_local_analysis(BASE_PATH, PROJECT_ID)
    if result_df is not None:
        print("\n🎉 로컬 분석 완료!")
        print(f"총 {len(result_df)}개의 레코드가 처리되었습니다.")