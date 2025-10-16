import pandas as pd
from pathlib import Path


def get_latest_text_processor_file():
    """
    rawdata 폴더에서 가장 최신의 text_processor_결과 파일을 찾아 반환합니다.

    Returns:
        str: 가장 최신 파일의 경로
    """
    rawdata_path = Path("rawdata")
    pattern = "2. text_processor_결과_*.xlsx"

    # _partial.xlsx 파일은 제외하고 검색
    files = [f for f in rawdata_path.glob(pattern) if not f.name.endswith('_partial.xlsx')]

    if not files:
        print(f"⚠️  '{pattern}' 패턴의 파일을 찾을 수 없습니다.")
        return "rawdata/2. text_processor_결과_20251013_093925.xlsx"  # 기본값

    # 파일명에서 타임스탬프를 추출하여 최신 파일 선택
    if len(files) > 1:
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        print(f"📁 최신 데이터 파일 자동 선택: {latest_file.name}")
        return str(latest_file)
    else:
        return str(files[0])


def summarize_mutual_reviews_by_period(include_half_year=False):
    """
    상호평가 요약 분석 (연도별 또는 반기별)

    Args:
        include_half_year (bool): True면 2025년을 상반기/하반기로 세분화
    """
    if include_half_year:
        print("🚀 상호평가 요약 분석을 시작합니다 (2025년 상하반기 구분)...")
    else:
        print("🚀 상호평가 요약 분석을 시작합니다 (연도별 통합)...")

    # 1. 데이터 로드
    try:
        input_file = get_latest_text_processor_file()
        df = pd.read_excel(input_file)
        print("✅ 엑셀 파일 로드 완료")
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")
        return

    original_cols = [
        'response_id', '설문시행연도', '평가_부서명', '평가_부서명_원본', '평가_Unit명', '평가_부문',
        '피평가대상 부서명', '피평가대상_부서명_원본', '피평가대상 UNIT명', '피평가대상 부문',
        '○○은 타 부서의 입장을 존중하고 배려하여 협력해주며. 협업 관련 의견을 경청해준다.',
        '○○은 업무상 필요한 정보에 대해 공유가 잘 이루어진다.',
        '○○은 업무에 대한 명확한 담당자가 있고 업무를 일관성있게 처리해준다.',
        '○○은 이전보다 업무 협력에 대한 태도나 의지가 개선되고 있다.',
        '전반적으로 ○○과의 협업에 대해 만족한다.',
        '종합점수', '극단값', '결측값', '협업 유형', '협업 후기', '정제된_텍스트', 
        '비식별_처리', '감정_분류', '감정_강도_점수', '핵심_키워드', '의료_맥락', '신뢰도_점수'
    ]
    df.columns = original_cols

    # 2. 데이터 전처리
    df['설문시행연도'] = df['설문시행연도'].astype(str)
    df.dropna(subset=['평가_부서명', '피평가대상 부서명', '종합점수'], inplace=True)

    # Unit 컬럼의 결측값을 'N/A'로 처리
    df['평가_Unit명'] = df['평가_Unit명'].fillna('N/A')
    df['피평가대상 UNIT명'] = df['피평가대상 UNIT명'].fillna('N/A')

    # 반기 정보 추출 (response_id에서)
    df['반기'] = df['response_id'].str.split('_').str[1]

    # 3. 분석 기간 설정
    if include_half_year:
        # 2025년만 상반기/하반기로 분리
        periods = []
        for year in sorted(df['설문시행연도'].unique()):
            year_data = df[df['설문시행연도'] == year]
            half_years = sorted(year_data['반기'].unique())

            if year == '2025' and len(half_years) > 1:
                periods.append(f"{year}_상반기")
                periods.append(f"{year}_하반기")
            else:
                periods.append(year)
        print(f"🔍 분석할 기간: {', '.join(periods)}")
    else:
        periods = sorted(df['설문시행연도'].unique())
        print(f"🔍 분석할 연도: {', '.join(periods)}")

    # 4. 기간별 결과를 저장할 딕셔너리
    period_results = {}
    period_unit_results = {}

    for period in periods:
        # 기간별 데이터 필터링
        if '_상반기' in period or '_하반기' in period:
            year = period.split('_')[0]
            half = '1' if '상반기' in period else '2'
            df_period = df[(df['설문시행연도'] == year) & (df['반기'] == half)].copy()
            print(f"\n📅 {period} 데이터 분석 중...")
            print(f"   - {period} 데이터: {len(df_period)}건")
        else:
            df_period = df[df['설문시행연도'] == period].copy()
            print(f"\n📅 {period}년 데이터 분석 중...")
            print(f"   - {period}년 데이터: {len(df_period)}건")

        if df_period.empty:
            print(f"   - {period} 데이터가 없어 건너뜁니다.")
            continue

        # === 부서별 상호평가 분석 ===
        # 부서별 종합점수 및 응답 수 집계
        agg_data = df_period.groupby(['평가_부서명', '피평가대상 부서명']).agg(
            종합점수=('종합점수', 'mean'),
            응답수=('종합점수', 'size')
        ).reset_index()

        # 상호평가 쌍 찾기 (표본수 제약 없음)
        summary_list = []
        processed_pairs = set()

        for _, row in agg_data.iterrows():
            team_a = row['평가_부서명']
            team_b = row['피평가대상 부서명']

            # 중복 처리를 피하기 위해 정렬된 튜플 사용
            pair_key = tuple(sorted((team_a, team_b)))
            if pair_key in processed_pairs:
                continue

            # B -> A 평가 데이터 찾기
            mutual_row = agg_data[
                (agg_data['평가_부서명'] == team_b) & (agg_data['피평가대상 부서명'] == team_a)
            ]

            if not mutual_row.empty:
                # A -> B 평가 데이터 (현재 row)
                stats_b_by_a = row
                # B -> A 평가 데이터
                stats_a_by_b = mutual_row.iloc[0]

                # 표본수 제약 없이 모든 상호평가 쌍 포함
                summary_list.append({
                    '부서 A': team_a,
                    '부서 B': team_b,
                    'A팀 종합점수 (B팀 평가)': round(stats_a_by_b['종합점수'], 2),
                    'B팀 종합점수 (A팀 평가)': round(stats_b_by_a['종합점수'], 2),
                    'A팀 응답수 (B팀 평가)': stats_a_by_b['응답수'],
                    'B팀 응답수 (A팀 평가)': stats_b_by_a['응답수'],
                    '총 응답수': stats_a_by_b['응답수'] + stats_b_by_a['응답수']
                })

                processed_pairs.add(pair_key)

        print(f"   - {period} 상호평가 부서 쌍: {len(summary_list)}개")

        if summary_list:
            period_results[period] = pd.DataFrame(summary_list)

        # === Unit별 상호평가 분석 ===
        # Unit별 종합점수 및 응답 수 집계
        agg_unit_data = df_period.groupby(['평가_Unit명', '피평가대상 UNIT명']).agg(
            종합점수=('종합점수', 'mean'),
            응답수=('종합점수', 'size')
        ).reset_index()

        # Unit별 상호평가 쌍 찾기
        unit_summary_list = []
        processed_unit_pairs = set()

        for _, row in agg_unit_data.iterrows():
            unit_a = row['평가_Unit명']
            unit_b = row['피평가대상 UNIT명']

            # 자기 자신 평가는 제외
            if unit_a == unit_b:
                continue

            # 중복 처리를 피하기 위해 정렬된 튜플 사용
            pair_key = tuple(sorted((unit_a, unit_b)))
            if pair_key in processed_unit_pairs:
                continue

            # B -> A 평가 데이터 찾기
            mutual_row = agg_unit_data[
                (agg_unit_data['평가_Unit명'] == unit_b) & (agg_unit_data['피평가대상 UNIT명'] == unit_a)
            ]

            if not mutual_row.empty:
                # A -> B 평가 데이터 (현재 row)
                stats_b_by_a = row
                # B -> A 평가 데이터
                stats_a_by_b = mutual_row.iloc[0]

                unit_summary_list.append({
                    'Unit A': unit_a,
                    'Unit B': unit_b,
                    'A Unit 종합점수 (B Unit 평가)': round(stats_a_by_b['종합점수'], 2),
                    'B Unit 종합점수 (A Unit 평가)': round(stats_b_by_a['종합점수'], 2),
                    'A Unit 응답수 (B Unit 평가)': stats_a_by_b['응답수'],
                    'B Unit 응답수 (A Unit 평가)': stats_b_by_a['응답수'],
                    '총 응답수': stats_a_by_b['응답수'] + stats_b_by_a['응답수']
                })

                processed_unit_pairs.add(pair_key)

        print(f"   - {period} 상호평가 Unit 쌍: {len(unit_summary_list)}개")

        if unit_summary_list:
            period_unit_results[period] = pd.DataFrame(unit_summary_list)

    # 5. 엑셀 파일에 기간별 시트로 저장
    if period_results or period_unit_results:
        if include_half_year:
            output_filename = "상호평가_부서추출.xlsx"
        else:
            output_filename = "상호평가_부서추출.xlsx"

        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            # 부서별 결과 저장
            for period, df_result in period_results.items():
                # 총 응답수 기준으로 정렬
                df_result = df_result.sort_values('총 응답수', ascending=False)
                sheet_name = f'{period}_부서별' if '_' in period else f'{period}년_부서별'
                df_result.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"   - {period} 부서별 결과를 '{sheet_name}' 시트에 저장")

            # Unit별 결과 저장
            for period, df_result in period_unit_results.items():
                # 총 응답수 기준으로 정렬
                df_result = df_result.sort_values('총 응답수', ascending=False)
                sheet_name = f'{period}_Unit별' if '_' in period else f'{period}년_Unit별'
                df_result.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"   - {period} Unit별 결과를 '{sheet_name}' 시트에 저장")

        print(f"\n🎉 분석 완료! 결과가 '{output_filename}' 파일로 저장되었습니다.")
    else:
        print("\n⚠️ 상호평가 데이터가 없습니다.")

if __name__ == "__main__":
    import sys

    # 기본: 연도별 분석
    # --half-year 옵션: 반기별 분석 (2025년만 상반기/하반기 구분)
    # --both 옵션: 연도별과 반기별 모두 실행

    if len(sys.argv) > 1:
        if '--half-year' in sys.argv:
            print("📋 반기별 분석 모드\n")
            summarize_mutual_reviews_by_period(include_half_year=True)
        elif '--both' in sys.argv:
            print("📋 연도별 + 반기별 분석 모드\n")
            print("=" * 60)
            print("1️⃣ 연도별 분석")
            print("=" * 60)
            summarize_mutual_reviews_by_period(include_half_year=False)
            print("\n" + "=" * 60)
            print("2️⃣ 반기별 분석")
            print("=" * 60)
            summarize_mutual_reviews_by_period(include_half_year=True)
        else:
            print("❓ 사용법:")
            print("  python summarize_mutual_reviews.py           # 연도별 분석")
            print("  python summarize_mutual_reviews.py --half-year    # 반기별 분석")
            print("  python summarize_mutual_reviews.py --both         # 연도별+반기별 모두")
    else:
        # 기본: 연도별 분석
        summarize_mutual_reviews_by_period(include_half_year=False)