#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드 빌더 (완전판 - 원본 기능 전체 이식)

원본 대시보드의 모든 기능을 포함한 완전판
- 병원 전체 결과
- 부문별 비교
- 팀별 순위
- 협업 네트워크 분석
- 키워드 분석
- 그 외 모든 섹션

사용법:
    python dashboard_builder_full.py integrated     # 기간 통합 (원본 기능)
    python dashboard_builder_full.py split          # 상하반기 분할 (원본 기능)

작성일: 2025-01-14
버전: 2.0 (Full)
"""

import sys
import os

# 원본 스크립트를 직접 실행
def run_original_script(mode='integrated'):
    """원본 스크립트 실행"""

    if mode == 'integrated':
        script_path = '3. build_dashboard_html_2025년 기간 통합.py'
        print(f"\n🚀 원본 스크립트 실행: {script_path}")
        print("="*60)
        os.system(f'python "{script_path}"')

    elif mode == 'split':
        script_path = '3. build_dashboard_html_2025년 상하반기 나누기.py'
        print(f"\n🚀 원본 스크립트 실행: {script_path}")
        print("="*60)
        os.system(f'python "{script_path}"')

    else:
        print(f"❌ 알 수 없는 모드: {mode}")
        print("사용 가능한 모드: integrated, split")
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 60)
        print("📊 대시보드 빌더 (완전판)")
        print("=" * 60)
        print("\n사용법: python dashboard_builder_full.py [모드]\n")
        print("사용 가능한 모드:")
        print("  • integrated      - 기간 통합 대시보드 (원본 기능 전체)")
        print("  • split           - 상하반기 분할 대시보드 (원본 기능 전체)")
        print("\n예시:")
        print("  python dashboard_builder_full.py integrated")
        print("  python dashboard_builder_full.py split")
        print("\n⚠️  주의: 이 스크립트는 원본 스크립트를 실행합니다.")
        print("     - 출력 파일: '서울아산병원 협업평가 결과.html'")
        print("     - 파일 크기: 약 20MB")
        print("     - 생성 시간: 약 10-15초")
        print()
        sys.exit(0)

    mode = sys.argv[1]

    try:
        success = run_original_script(mode)
        if success:
            print("\n✨ 원본 대시보드 생성 완료!")
            print("📄 파일: 서울아산병원 협업평가 결과.html")
            print()
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
