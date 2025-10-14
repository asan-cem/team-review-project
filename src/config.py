#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드 설정 파일

각 모드별 설정을 딕셔너리로 관리합니다.
새로운 모드를 추가하거나 설정을 변경할 때 이 파일만 수정하면 됩니다.

작성일: 2025-01-14
버전: 1.0
"""

# ============================================================================
# 공통 설정
# ============================================================================

COMMON_CONFIG = {
    'input_file': 'rawdata/2. text_processor_결과_20251013_093925.xlsx',
    'output_dir': 'outputs'
}


# ============================================================================
# 각 모드별 설정
# ============================================================================

DASHBOARD_CONFIGS = {
    # 모드 0: 원본 완전판 (20MB HTML, 모든 기능 포함)
    'full': {
        'name': '서울아산병원 협업평가 결과 보고 (완전판)',
        'output_file': '서울아산병원 협업평가 결과.html',
        'mode': 'full',
        'use_original': True,
        'original_script': 'legacy/3. build_dashboard_html_2025년 기간 통합.py',
        'description': '원본 대시보드의 모든 기능 포함 (병원 전체, 부문별, 팀 순위, 네트워크, 키워드 분석 등)'
    },

    # 모드 1: 기간 통합 (2025년으로 통합) - 원본 완전판
    'integrated': {
        'name': '2025년 통합 대시보드 (완전판)',
        'output_file': 'outputs/dashboard_integrated.html',
        'mode': 'integrated',
        'use_original': True,
        'original_script': 'legacy/3. build_dashboard_html_2025년 기간 통합.py',
        'description': '2025년 전체 기간 통합 - 원본 완전판 (모든 분석 기능 포함)'
    },

    # 모드 2: 상하반기 분할 (2025년 상반기/하반기) - 원본 완전판
    'split': {
        'name': '2025년 상하반기 대시보드 (완전판)',
        'output_file': 'outputs/dashboard_split.html',
        'mode': 'split',
        'use_original': True,
        'original_script': 'legacy/3. build_dashboard_html_2025년 상하반기 나누기.py',
        'description': '2025년 상하반기 구분 - 원본 완전판 (모든 분석 기능 포함)'
    },

    # 모드 3: 부서별 리포트 (외부망 접근 가능) - 원본 완전판
    'departments': {
        'name': '부서별 협업 리포트 (완전판)',
        'output_file': 'outputs/dashboard_departments.html',
        'mode': 'departments',
        'use_original': True,
        'original_script': 'legacy/4. team_reports_외부망접근가능한부서.py',
        'description': '부서별 협업 분석 - 원본 완전판 (외부망 접근 가능 부서용)'
    },

    # 모드 4: Standalone (외부망 불가 부서용) - 원본 완전판
    'standalone': {
        'name': 'Standalone 부서별 리포트 (완전판)',
        'output_file': 'outputs/dashboard_standalone.html',
        'mode': 'standalone',
        'use_original': True,
        'original_script': 'legacy/4. team_reports_외부망불가능부서(디지털).py',
        'description': '독립형 부서별 리포트 - 원본 완전판 (외부망 불가 부서용)'
    }
}


# ============================================================================
# Plotly standalone 설정
# ============================================================================

PLOTLY_JS_PATH = 'libs/plotly-latest.min.js'
