#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드 빌더 - 메인 실행 스크립트

프로젝트 루트에서 실행하는 간단한 래퍼 스크립트
실제 로직은 src/ 폴더의 모듈에 있음

사용법:
    python dashboard_builder.py full          # 원본 완전판
    python dashboard_builder.py integrated    # 간소화 버전
    python dashboard_builder.py split
    python dashboard_builder.py departments
    python dashboard_builder.py standalone

작성일: 2025-01-14
버전: 2.0 (리팩토링 완료)
"""

import sys
from pathlib import Path

# src 폴더를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.dashboard_builder import build_dashboard
from src.config import DASHBOARD_CONFIGS


if __name__ == "__main__":
    # CLI 인자 처리
    if len(sys.argv) < 2:
        print("=" * 60)
        print("📊 대시보드 빌더")
        print("=" * 60)
        print("\n사용법: python dashboard_builder.py [모드]\n")
        print("사용 가능한 모드:")
        for key, config in DASHBOARD_CONFIGS.items():
            print(f"  • {key:15} - {config['description']}")
        print("\n예시:")
        print("  python dashboard_builder.py full")
        print("  python dashboard_builder.py integrated")
        print("  python dashboard_builder.py split")
        print("  python dashboard_builder.py departments")
        print("  python dashboard_builder.py standalone")
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
