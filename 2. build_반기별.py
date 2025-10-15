#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
상하반기 분할 대시보드 생성 (Split 모드 - 원본 완전판)

2025년을 상반기/하반기로 구분하여 표시하는 원본 완전판:
- 병원 전체 결과
- 부문별 비교
- 팀별 순위
- 협업 네트워크 분석
- 키워드 분석
- 상하반기 구분 표시
- 모든 섹션 포함

출력: outputs/dashboard_split.html (약 20MB)

사용법:
    python "2. build_반기별.py"

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
    print("📊 반기별 대시보드 생성 (2025년 상하반기 구분)")
    print("=" * 60)
    print("\n🎯 모드: 반기별 (split)")
    print("📋 기간: 2022년, 2023년, 2024년, 2025년 상반기, 2025년 하반기")
    print("📄 출력 경로: outputs/dashboard_split.html")
    print("📦 예상 크기: 약 20MB")
    print("⏱️  처리 시간: 10-15초\n")

    try:
        output_path = Path('outputs/dashboard_split.html').absolute()
        build_dashboard('split')
        print("✨ 반기별 대시보드 생성 완료!\n")
        print("📂 생성된 파일:")
        print(f"   - {output_path}\n")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
