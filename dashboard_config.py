"""
대시보드 설정 및 상수 정의
"""
from typing import Dict, List, Any

class DashboardConfig:
    """대시보드 설정 클래스"""
    
    # 데이터 관련 설정
    DATA_FILE = "설문조사_전처리데이터_20250620_0731_processed.xlsx"
    OUTPUT_FILE = "서울아산병원 협업평가 대시보드.html"
    
    # 컬럼 매핑
    COLUMN_MAPPING = [
        'response_id', '설문연도', '평가부서', '평가부서_원본', '평가Unit', '평가부문',
        '피평가부서', '피평가부서_원본', '피평가Unit', '피평가부문',
        '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수',
        '극단값', '결측값', '협업내용', '협업내용상세', '협업후기', '정제된_텍스트', 
        '비식별_처리', '감정_분류', '감정_강도_점수', '핵심_키워드', '의료_맥락', '신뢰도_점수'
    ]
    
    # 점수 컬럼
    SCORE_COLUMNS = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수']
    
    # 필터 매핑
    FILTER_MAPPING = {
        'year-filter': '설문연도',
        'department-filter': '피평가부서',
        'unit-filter': '피평가Unit'
    }
    
    # 감정 분류
    SENTIMENT_CATEGORIES = ['긍정', '부정', '중립', '알 수 없음']
    SENTIMENT_ORDER = ['긍정', '부정', '중립']
    
    # 색상 매핑
    SENTIMENT_COLORS = {
        '긍정': '#2E8B57',
        '부정': '#DC143C', 
        '중립': '#4682B4',
        '알 수 없음': '#808080'
    }
    
    DIVISION_COLORS = {
        '진료부문': '#1f77b4',
        '간호부문': '#ff7f0e',
        '관리부문': '#2ca02c',
        '의료지원부문': '#d62728',
        '기타': '#9467bd'
    }
    
    # 차트 설정
    CHART_CONFIG = {
        'default_height': 400,
        'ranking_height': 600,
        'large_height': 500,
        'font_size': 14,
        'text_font_size': 12,
        'marker_font_size': 14,
        'score_range': [0, 100],
        'intensity_range': [1, 10]
    }
    
    # CSS 클래스
    CSS_CLASSES = {
        'container': 'container',
        'section': 'section',
        'filters': 'filters',
        'filter_group': 'filter-group',
        'metric': 'metric',
        'keyword_chart': 'keyword-chart'
    }
    
    # JavaScript 설정
    JS_CONFIG = {
        'plotly_cdn': 'https://cdn.plot.ly/plotly-latest.min.js',
        'cache_enabled': True,
        'debounce_delay': 300,
        'max_keywords': 10
    }
    
    @classmethod
    def get_export_columns(cls) -> List[str]:
        """JSON 내보내기용 컬럼 반환"""
        return [
            '설문연도', '피평가부문', '피평가부서', '피평가Unit',
            *cls.SCORE_COLUMNS,
            '정제된_텍스트', '감정_분류', '감정_강도_점수', '핵심_키워드'
        ]
    
    @classmethod
    def get_fillna_columns(cls) -> List[str]:
        """NA 값 처리할 컬럼 반환"""
        return ['피평가부문', '피평가부서', '피평가Unit', '정제된_텍스트']