"""
데이터 처리 및 분석 모듈
"""
import pandas as pd
import ast
import json
from typing import Dict, List, Any, Optional, Union
import logging
from dashboard_config import DashboardConfig

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """데이터 로드 및 전처리를 담당하는 클래스"""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.data: Optional[pd.DataFrame] = None
        self._cache: Dict[str, Any] = {}
    
    def safe_literal_eval(self, s: Union[str, Any]) -> List[Any]:
        """문자열을 안전하게 파이썬 리터럴로 변환"""
        if not isinstance(s, str):
            return []
        
        if not (s.startswith('[') and s.endswith(']')):
            return []
        
        try:
            result = ast.literal_eval(s)
            return result if isinstance(result, list) else []
        except (ValueError, SyntaxError, TypeError) as e:
            logger.warning(f"literal_eval 실패: {s[:50]}... - {e}")
            return []
    
    def load_data(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """데이터 로드 및 기본 전처리"""
        try:
            file_path = file_path or self.config.DATA_FILE
            logger.info(f"데이터 로드 시작: {file_path}")
            
            # 데이터 로드
            df = pd.read_excel(file_path)
            
            # 컬럼 매핑
            if len(df.columns) >= len(self.config.COLUMN_MAPPING):
                df.columns = self.config.COLUMN_MAPPING
            else:
                logger.warning(f"컬럼 수 불일치: 예상 {len(self.config.COLUMN_MAPPING)}, 실제 {len(df.columns)}")
            
            # 설문연도를 문자열로 변환
            df['설문연도'] = df['설문연도'].astype(str)
            
            # 점수 컬럼 숫자형 변환
            for col in self.config.SCORE_COLUMNS:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 종합 점수가 없는 행 제거
            df = df.dropna(subset=['종합 점수'])
            
            # NA 값 처리
            for col in self.config.get_fillna_columns():
                if col in df.columns:
                    df[col] = df[col].fillna('N/A')
            
            # 핵심 키워드 컬럼 처리
            if '핵심_키워드' in df.columns:
                df['핵심_키워드'] = df['핵심_키워드'].apply(self.safe_literal_eval)
            
            self.data = df
            logger.info(f"데이터 로드 완료: {len(df)}행")
            return df
            
        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            raise
    
    def get_export_data(self) -> str:
        """JSON 내보내기용 데이터 반환"""
        if self.data is None:
            raise ValueError("데이터가 로드되지 않았습니다. load_data()를 먼저 호출하세요.")
        
        export_columns = self.config.get_export_columns()
        available_columns = [col for col in export_columns if col in self.data.columns]
        
        if len(available_columns) != len(export_columns):
            missing = set(export_columns) - set(available_columns)
            logger.warning(f"일부 컬럼이 누락됨: {missing}")
        
        df_export = self.data[available_columns].copy()
        return df_export.to_json(orient='records', force_ascii=False)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """데이터 요약 통계 반환"""
        if self.data is None:
            return {}
        
        stats = {
            'total_records': len(self.data),
            'years': sorted(self.data['설문연도'].unique().tolist()),
            'divisions': sorted([d for d in self.data['피평가부문'].unique() if d != 'N/A']),
            'departments': len(self.data['피평가부서'].unique()),
            'units': len(self.data['피평가Unit'].unique()),
        }
        
        # 점수 통계
        score_stats = {}
        for col in self.config.SCORE_COLUMNS:
            if col in self.data.columns:
                score_stats[col] = {
                    'mean': round(self.data[col].mean(), 2),
                    'std': round(self.data[col].std(), 2),
                    'min': self.data[col].min(),
                    'max': self.data[col].max()
                }
        
        stats['score_statistics'] = score_stats
        return stats
    
    def validate_data(self) -> Dict[str, Any]:
        """데이터 품질 검증"""
        if self.data is None:
            return {'valid': False, 'errors': ['데이터가 로드되지 않음']}
        
        errors = []
        warnings = []
        
        # 필수 컬럼 확인
        required_columns = ['설문연도', '피평가부문', '종합 점수']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        if missing_columns:
            errors.append(f"필수 컬럼 누락: {missing_columns}")
        
        # 점수 범위 확인
        for col in self.config.SCORE_COLUMNS:
            if col in self.data.columns:
                invalid_scores = self.data[
                    (self.data[col] < 0) | (self.data[col] > 100)
                ]
                if len(invalid_scores) > 0:
                    warnings.append(f"{col} 컬럼에 범위 외 값 {len(invalid_scores)}개")
        
        # 감정 분류 확인
        if '감정_분류' in self.data.columns:
            valid_sentiments = set(self.config.SENTIMENT_CATEGORIES)
            invalid_sentiments = set(self.data['감정_분류'].dropna().unique()) - valid_sentiments
            if invalid_sentiments:
                warnings.append(f"알 수 없는 감정 분류: {invalid_sentiments}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'record_count': len(self.data)
        }
    
    def get_department_unit_mapping(self) -> Dict[str, List[str]]:
        """부서-Unit 매핑 반환"""
        if self.data is None:
            return {}
        
        cache_key = 'dept_unit_mapping'
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        mapping = {}
        for _, row in self.data.iterrows():
            dept = row['피평가부서']
            unit = row['피평가Unit']
            
            if dept and dept != 'N/A' and unit and unit != 'N/A':
                if dept not in mapping:
                    mapping[dept] = set()
                mapping[dept].add(unit)
        
        # set을 list로 변환하고 정렬
        for dept in mapping:
            mapping[dept] = sorted(list(mapping[dept]), key=lambda x: str(x))
        
        self._cache[cache_key] = mapping
        return mapping
    
    def clear_cache(self):
        """캐시 정리"""
        self._cache.clear()
        logger.info("데이터 처리 캐시 정리됨")