#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
공통 분석 패키지

리팩토링된 데이터 분석 시스템
모든 스크립트에서 공통으로 사용하는 함수와 상수를 제공합니다.

사용법:
    from src.common import load_data, clean_data, SCORE_COLUMNS
    from src.config import DASHBOARD_CONFIGS
"""

from .common import (
    # 데이터 로드 및 전처리 함수
    load_data,
    preprocess_data_types,
    clean_data,

    # 유틸리티 함수
    get_latest_text_processor_file,
    log_message,
    safe_literal_eval,

    # 상수 정의
    SCORE_COLUMNS,
    EXCEL_COLUMNS,
    COLUMN_MAPPING,
    FILL_NA_COLUMNS,
    EXCLUDE_DEPARTMENTS,
    EXCLUDE_TEAMS
)

from .config import DASHBOARD_CONFIGS, COMMON_CONFIG

__all__ = [
    # 데이터 처리 함수
    'load_data',
    'preprocess_data_types',
    'clean_data',

    # 유틸리티 함수
    'get_latest_text_processor_file',
    'log_message',
    'safe_literal_eval',

    # 상수
    'SCORE_COLUMNS',
    'EXCEL_COLUMNS',
    'COLUMN_MAPPING',
    'FILL_NA_COLUMNS',
    'EXCLUDE_DEPARTMENTS',
    'EXCLUDE_TEAMS',

    # 설정
    'DASHBOARD_CONFIGS',
    'COMMON_CONFIG'
]
