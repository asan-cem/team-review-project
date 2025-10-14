#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
원본 완전판 대시보드 생성 (Full 모드)

원본 대시보드의 모든 기능 포함:
- 병원 전체 결과
- 부문별 비교
- 팀별 순위
- 협업 네트워크 분석
- 키워드 분석
- 모든 섹션

출력: 서울아산병원 협업평가 결과.html (약 20MB)

사용법:
    python build_full.py

작성일: 2025-01-14
버전: 2.0
"""

import sys
from pathlib import Path

# src 폴더를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.dashboard_builder import build_dashboard


if __name__ == "__main__":
    print("=" * 60)
    print("📊 원본 완전판 대시보드 생성")
    print("=" * 60)
    print("\n🎯 모드: full")
    print("📄 출력: 서울아산병원 협업평가 결과.html")
    print("📦 크기: 약 20MB")
    print("⏱️  예상 시간: 10-15초\n")

    try:
        build_dashboard('full')
        print("✨ 원본 완전판 대시보드 생성 완료!\n")
        print("📂 생성된 파일:")
        print("   - 서울아산병원 협업평가 결과.html\n")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
