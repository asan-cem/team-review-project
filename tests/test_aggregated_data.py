#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
원본 집계 함수 테스트 스크립트

이식한 calculate_aggregated_data() 함수가 제대로 작동하는지 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard_builder import (
    load_data,
    preprocess_data_types,
    clean_data,
    calculate_aggregated_data,
    prepare_json_data
)
import json

def main():
    print("=" * 60)
    print("📊 원본 집계 함수 테스트")
    print("=" * 60)
    print()

    # 데이터 파일 경로
    data_file = "rawdata/2. text_processor_결과_20251013_093925.xlsx"

    try:
        # 1. 데이터 로드
        print("📂 Step 1: 데이터 로드...")
        df = load_data(data_file)
        print(f"   ✅ {len(df):,}행 로드 완료\n")

        # 2. 데이터 전처리
        print("🔄 Step 2: 데이터 타입 변환...")
        df = preprocess_data_types(df)
        print(f"   ✅ 타입 변환 완료\n")

        # 3. 데이터 정제
        print("🧹 Step 3: 데이터 정제...")
        df = clean_data(df)
        print(f"   ✅ 정제 완료: {len(df):,}행\n")

        # 4. 집계 데이터 계산
        print("📊 Step 4: 집계 데이터 계산...")
        aggregated = calculate_aggregated_data(df)
        print(f"   ✅ 집계 완료\n")

        # 5. 결과 요약 출력
        print("=" * 60)
        print("📈 집계 결과 요약")
        print("=" * 60)
        print()

        # 병원 전체 연도별 점수
        print("1️⃣ 병원 전체 연도별 점수:")
        for year, data in sorted(aggregated['hospital_yearly'].items()):
            print(f"   {year}년: 종합점수 {data['종합점수']:.1f} ({data['응답수']:,}건)")
        print()

        # 부문 수
        print(f"2️⃣ 부문 수: {len(aggregated['division_yearly'])}개")
        for division in list(aggregated['division_yearly'].keys())[:5]:
            print(f"   - {division}")
        if len(aggregated['division_yearly']) > 5:
            print(f"   ... 외 {len(aggregated['division_yearly']) - 5}개")
        print()

        # 팀 순위 데이터
        total_rankings = sum(
            len(divisions)
            for year_data in aggregated['team_ranking'].values()
            for divisions in year_data.values()
        )
        print(f"3️⃣ 팀 순위 데이터: {len(aggregated['team_ranking'])}년치")
        print(f"   총 순위 데이터: {total_rankings}개 팀\n")

        # 6. JSON 데이터 준비 테스트
        print("📄 Step 5: JSON 데이터 준비...")
        json_data = prepare_json_data(df)
        json_obj = json.loads(json_data)
        print(f"   ✅ JSON 생성 완료: {len(json_obj):,}건\n")

        # 7. 메타데이터
        print("=" * 60)
        print("📋 메타데이터")
        print("=" * 60)
        for key, value in aggregated['metadata'].items():
            print(f"   {key}: {value}")
        print()

        print("=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
