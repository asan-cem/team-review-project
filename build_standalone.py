#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
독립형 부서별 리포트 생성 (Standalone 모드 - 원본 완전판)

외부망 불가 부서(디지털)를 위한 원본 완전판:
- 병원 전체 결과
- 부문별 비교
- 팀별 순위
- 협업 네트워크 분석
- 키워드 분석
- 부서별 상세 분석
- 모든 섹션 포함

출력: outputs/dashboard_standalone.html (약 20MB)

⚠️  주의: 외부망 불가 부서용 버전입니다.

사용법:
    python build_standalone.py

작성일: 2025-01-14
버전: 2.0 (원본 완전판)
"""

import sys
from pathlib import Path

# src 폴더를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.dashboard_builder import build_dashboard


if __name__ == "__main__":
    print("=" * 60)
    print("📊 독립형 부서별 리포트 생성 (원본 완전판)")
    print("=" * 60)
    print("\n🎯 모드: standalone (외부망 불가)")
    print("📄 출력: outputs/dashboard_standalone.html")
    print("📦 크기: 약 20MB")
    print("⏱️  예상 시간: 10-15초\n")

    try:
        build_dashboard('standalone')
        print("✨ 독립형 부서별 리포트 생성 완료!\n")
        print("📂 생성된 파일:")
        print("   - outputs/dashboard_standalone.html\n")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
