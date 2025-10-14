#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
독립형 부서별 리포트 생성 (Standalone 모드 - 부서별 개별 보고서, 외부망 불가)

각 부서별로 개별 HTML 보고서를 생성합니다 (외부망 불가 부서용):
- 부문별 폴더 구조로 정리
- 각 부서의 상세 협업 분석
- 병원 전체 결과
- 부문별 비교
- 팀별 순위
- 협업 네트워크 분석
- 키워드 분석
- Plotly JS 임베드 (인터넷 불필요)

출력: 개별보고서/[부문명]/[부서명].html

⚠️  주의: 외부망 불가 부서(디지털정보혁신본부 등)용 버전입니다.

사용법:
    python "3. build_부서별.py"

내부 구조:
    src/department_report_builder.py 호출 → 79개 부서 개별 HTML 생성

작성일: 2025-01-14
버전: 3.2 (파일명 수정)
"""

import sys
import importlib.util
import os
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 경로
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def generate_all_department_reports_standalone():
    """모든 부서의 개별 보고서 생성 (독립형)"""
    print("=" * 70)
    print("🚀 독립형 부서별 협업 리포트 생성 (외부망 불가)")
    print("=" * 70)
    print(f"\n📅 실행 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}")
    print("📂 출력: 개별보고서/")
    print("⏱️  예상 시간: 부서당 5-10초\n")
    print("ℹ️  Plotly 라이브러리는 자동으로 인라인 포함됩니다 (외부망 불필요)\n")

    try:
        # 부서별 개별 보고서 생성기 로드 (Plotly 인라인 기능 내장)
        report_builder_script = project_root / "src" / "department_report_builder.py"

        print("📦 부서별 보고서 생성기 로딩...")
        spec = importlib.util.spec_from_file_location("department_report_builder", str(report_builder_script))
        report_module = importlib.util.module_from_spec(spec)
        sys.modules["department_report_builder"] = report_module
        spec.loader.exec_module(report_module)
        print("✅ 모듈 로드 완료\n")

        # 부서별 보고서 생성기의 generate_all_department_reports 함수 사용
        print("📊 부서별 보고서 생성 중 (Plotly 인라인 자동 포함)...\n")
        success = report_module.generate_all_department_reports()

        if not success:
            print("\n❌ 부서별 리포트 생성 실패\n")
            return 1

        print("\n✅ 부서별 보고서 생성 완료\n")
        print("✨ 독립형 부서별 협업 리포트 생성 완료!\n")
        print("💡 생성된 HTML 파일은 외부망 없이도 그래프가 표시됩니다.\n")
        return 0

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(generate_all_department_reports_standalone())
