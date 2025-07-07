import pandas as pd

def summarize_mutual_reviews_by_year():
    """
    Finds mutually reviewing department pairs for all years without sample size constraints
    and creates a summary Excel file with separate sheets for each year.
    """
    print("🚀 연도별 상호평가 요약 분석을 시작합니다...")

    # 1. 데이터 로드
    try:
        df = pd.read_excel("설문조사_전처리데이터_20250620_0731_processed.xlsx")
        print("✅ 엑셀 파일 로드 완료")
    except FileNotFoundError:
        print("❌ '설문조사_전처리데이터_20250620_0731_processed.xlsx' 파일을 찾을 수 없습니다.")
        return

    original_cols = [
        'response_id', '설문연도', '평가부서', '평가부서_원본', '평가Unit', '평가부문',
        '피평가부서', '피평가부서_원본', '피평가Unit', '피평가부문',
        '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수',
        '극단값', '결측값', '협업내용', '협업내용상세', '협업후기', '정제된_텍스트', 
        '비식별_처리', '감정_분류', '감정_강도_점수', '핵심_키워드', '의료_맥락', '신뢰도_점수'
    ]
    df.columns = original_cols

    # 2. 데이터 전처리
    df['설문연도'] = df['설문연도'].astype(str)
    df.dropna(subset=['평가부서', '피평가부서', '종합 점수'], inplace=True)

    # 3. 연도별 데이터 분석
    years = sorted(df['설문연도'].unique())
    print(f"🔍 분석할 연도: {', '.join(years)}")

    # 4. 연도별 결과를 저장할 딕셔너리
    year_results = {}

    for year in years:
        print(f"\n📅 {year}년 데이터 분석 중...")
        
        # 연도별 데이터 필터링
        df_year = df[df['설문연도'] == year].copy()
        print(f"   - {year}년 데이터: {len(df_year)}건")

        if df_year.empty:
            print(f"   - {year}년 데이터가 없어 건너뜁니다.")
            continue

        # 부서별 종합점수 및 응답 수 집계
        agg_data = df_year.groupby(['평가부서', '피평가부서']).agg(
            종합점수=('종합 점수', 'mean'),
            응답수=('종합 점수', 'size')
        ).reset_index()

        # 상호평가 쌍 찾기 (표본수 제약 없음)
        summary_list = []
        processed_pairs = set()

        for _, row in agg_data.iterrows():
            team_a = row['평가부서']
            team_b = row['피평가부서']

            # 중복 처리를 피하기 위해 정렬된 튜플 사용
            pair_key = tuple(sorted((team_a, team_b)))
            if pair_key in processed_pairs:
                continue

            # B -> A 평가 데이터 찾기
            mutual_row = agg_data[
                (agg_data['평가부서'] == team_b) & (agg_data['피평가부서'] == team_a)
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

        print(f"   - {year}년 상호평가 부서 쌍: {len(summary_list)}개")
        
        if summary_list:
            year_results[year] = pd.DataFrame(summary_list)

    # 5. 엑셀 파일에 연도별 시트로 저장
    if year_results:
        output_filename = "상호평가_요약_연도별.xlsx"
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            for year, df_result in year_results.items():
                # 총 응답수 기준으로 정렬
                df_result = df_result.sort_values('총 응답수', ascending=False)
                df_result.to_excel(writer, sheet_name=f'{year}년', index=False)
                print(f"   - {year}년 결과를 '{year}년' 시트에 저장")
        
        print(f"\n🎉 분석 완료! 결과가 '{output_filename}' 파일로 저장되었습니다.")
    else:
        print("\n⚠️ 상호평가 데이터가 없습니다.")

if __name__ == "__main__":
    summarize_mutual_reviews_by_year()