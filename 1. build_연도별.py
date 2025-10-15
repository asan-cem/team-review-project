#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기간 통합 대시보드 생성 (Integrated 모드 - 원본 완전판)

2025년 전체 기간을 하나로 통합하여 표시하는 원본 완전판:
- 병원 전체 결과
- 부문별 비교
- 팀별 순위
- 협업 네트워크 분석
- 키워드 분석
- 모든 섹션 포함

출력: outputs/dashboard_integrated.html (약 20MB)

사용법:
    python "1. build_연도별.py"

작성일: 2025-01-14
버전: 2.1 (파일명 수정)
"""

import sys
from pathlib import Path

# src 폴더를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.dashboard_builder import build_dashboard


if __name__ == "__main__":
    print("=" * 60)
    print("📊 연도별 대시보드 생성 (2025년 통합)")
    print("=" * 60)
    print("\n🎯 모드: 연도별 (integrated)")
    print("📋 기간: 2022년, 2023년, 2024년, 2025년")
    print("📄 출력 경로: outputs/dashboard_integrated.html")
    print("📦 예상 크기: 약 20MB")
    print("⏱️  처리 시간: 10-15초\n")

    try:
        output_path = Path('outputs/dashboard_integrated.html').absolute()
        build_dashboard('integrated')
        print("✨ 연도별 대시보드 생성 완료!\n")
        print("📂 생성된 파일:")
        print(f"   - {output_path}\n")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
